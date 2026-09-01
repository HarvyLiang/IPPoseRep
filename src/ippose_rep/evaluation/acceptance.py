"""Evidence-based acceptance checks for experiment run directories."""

from __future__ import annotations

import json
import math
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from ippose_rep.experiments.journal import JournalError, load_json_object
from ippose_rep.experiments.registry import ExperimentDefinition


@dataclass(frozen=True, slots=True)
class AcceptanceIssue:
    """One failed acceptance condition."""

    code: str
    message: str


@dataclass(frozen=True, slots=True)
class VerificationReport:
    """Serializable result from verifying one experiment run."""

    checked_at: str
    ok: bool
    issues: tuple[AcceptanceIssue, ...]
    metrics: dict[str, float]

    def to_dict(self) -> dict[str, object]:
        return {
            "checked_at": self.checked_at,
            "ok": self.ok,
            "issues": [asdict(issue) for issue in self.issues],
            "metrics": self.metrics,
        }


def verify_run(
    run_directory: str | Path,
    definition: ExperimentDefinition,
    *,
    require_completed: bool = True,
) -> VerificationReport:
    """Verify provenance, execution state, artifacts, and required metrics."""

    run_dir = Path(run_directory).resolve()
    issues: list[AcceptanceIssue] = []
    metrics: dict[str, float] = {}

    try:
        journal = load_json_object(run_dir / "run.json")
    except JournalError as error:
        issues.append(AcceptanceIssue("journal_unreadable", str(error)))
        return _report(issues, metrics)

    _expect_equal(
        issues,
        "experiment_mismatch",
        journal.get("experiment_id"),
        definition.experiment_id,
        "experiment id",
    )
    if require_completed and journal.get("status") != "completed":
        issues.append(
            AcceptanceIssue(
                "run_incomplete",
                f"Run status is {journal.get('status')!r}, expected 'completed'",
            )
        )

    provenance = journal.get("provenance")
    if not isinstance(provenance, dict):
        issues.append(
            AcceptanceIssue("provenance_missing", "Run provenance is missing")
        )
        provenance = {}
    git_commit = provenance.get("git_commit")
    if (
        not isinstance(git_commit, str)
        or not git_commit.strip()
        or git_commit == "unknown"
    ):
        issues.append(
            AcceptanceIssue("git_commit_missing", "A resolved Git commit is required")
        )
    _expect_equal(
        issues,
        "config_mismatch",
        provenance.get("config_sha256"),
        definition.config_sha256,
        "configuration fingerprint",
    )
    _expect_equal(
        issues,
        "seed_mismatch",
        provenance.get("seed"),
        definition.seed,
        "random seed",
    )
    _expect_equal(
        issues,
        "command_mismatch",
        provenance.get("command"),
        list(definition.command),
        "command",
    )
    dataset_fingerprint = provenance.get("dataset_fingerprint")
    if not isinstance(dataset_fingerprint, str) or not dataset_fingerprint.strip():
        issues.append(
            AcceptanceIssue(
                "dataset_fingerprint_missing",
                "A non-empty dataset fingerprint is required",
            )
        )

    snapshot = run_dir / "experiment.toml"
    if not snapshot.is_file():
        issues.append(
            AcceptanceIssue("config_snapshot_missing", f"Missing {snapshot.name}")
        )
    else:
        import hashlib

        try:
            digest = hashlib.sha256(snapshot.read_bytes()).hexdigest()
        except OSError as error:
            issues.append(
                AcceptanceIssue(
                    "config_snapshot_unreadable",
                    f"Cannot read experiment.toml: {error}",
                )
            )
        else:
            if digest != definition.config_sha256:
                issues.append(
                    AcceptanceIssue(
                        "config_snapshot_mismatch",
                        "experiment.toml does not match the registered configuration",
                    )
                )

    stages = journal.get("stages")
    execute = stages.get("execute") if isinstance(stages, dict) else None
    if not isinstance(execute, dict) or execute.get("status") != "completed":
        issues.append(
            AcceptanceIssue("execution_incomplete", "Execute stage is not completed")
        )
    elif execute.get("exit_code") != 0:
        issues.append(
            AcceptanceIssue(
                "execution_failed",
                f"Execute stage exit code is {execute.get('exit_code')!r}",
            )
        )

    required_paths = set(definition.required_artifacts)
    required_paths.add(definition.metrics_file)
    for relative_path in sorted(required_paths, key=lambda path: path.as_posix()):
        artifact = _resolve_inside(run_dir, relative_path)
        if artifact is None or not artifact.is_file():
            issues.append(
                AcceptanceIssue(
                    "artifact_missing",
                    f"Missing required artifact: {relative_path.as_posix()}",
                )
            )

    metrics_path = _resolve_inside(run_dir, definition.metrics_file)
    if metrics_path is not None and metrics_path.is_file():
        try:
            raw_metrics = json.loads(metrics_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as error:
            issues.append(
                AcceptanceIssue("metrics_unreadable", f"Cannot read metrics: {error}")
            )
        else:
            if not isinstance(raw_metrics, dict):
                issues.append(
                    AcceptanceIssue(
                        "metrics_invalid", "Metrics file must contain an object"
                    )
                )
            else:
                for name in definition.required_metrics:
                    value = raw_metrics.get(name)
                    if (
                        not isinstance(value, (int, float))
                        or isinstance(value, bool)
                        or not math.isfinite(float(value))
                    ):
                        issues.append(
                            AcceptanceIssue(
                                "metric_missing_or_invalid",
                                f"Metric {name!r} must be a finite number",
                            )
                        )
                    else:
                        metrics[name] = float(value)

    return _report(issues, metrics)


def _resolve_inside(root: Path, relative_path: Path) -> Path | None:
    candidate = (root / relative_path).resolve()
    try:
        candidate.relative_to(root)
    except ValueError:
        return None
    return candidate


def _expect_equal(
    issues: list[AcceptanceIssue],
    code: str,
    actual: Any,
    expected: Any,
    label: str,
) -> None:
    if actual != expected:
        issues.append(
            AcceptanceIssue(
                code, f"Unexpected {label}: {actual!r}; expected {expected!r}"
            )
        )


def _report(
    issues: list[AcceptanceIssue], metrics: dict[str, float]
) -> VerificationReport:
    return VerificationReport(
        checked_at=datetime.now(UTC).isoformat(),
        ok=not issues,
        issues=tuple(issues),
        metrics=metrics,
    )
