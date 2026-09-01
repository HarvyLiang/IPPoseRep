"""Resumable, provenance-aware experiment execution."""

from __future__ import annotations

import os
import shutil
import subprocess
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from ippose_rep.evaluation.acceptance import verify_run

from .journal import (
    JournalError,
    RunJournal,
    RunLock,
    load_json_object,
    resolve_run_directory,
)
from .registry import ExperimentDefinition, ExperimentRegistry


class ExperimentRunError(RuntimeError):
    """Raised when an experiment cannot safely start or pass acceptance."""


class ExperimentRunner:
    """Coordinate preflight, execution, persistence, resume, and verification."""

    def __init__(
        self,
        project_root: str | Path,
        registry: ExperimentRegistry,
        runs_root: str | Path,
    ) -> None:
        self.project_root = Path(project_root).resolve()
        self.registry = registry
        self.runs_root = Path(runs_root).resolve()
        if not self.project_root.is_dir():
            raise ExperimentRunError(
                f"Project root does not exist: {self.project_root}"
            )
        allowed_runs_root = (self.project_root / "data" / "derived").resolve()
        try:
            self.runs_root.relative_to(allowed_runs_root)
        except ValueError as error:
            raise ExperimentRunError(
                f"Runs root must be inside {allowed_runs_root}: {self.runs_root}"
            ) from error

    def dry_run(self, experiment_id: str) -> dict[str, object]:
        """Inspect readiness without creating or modifying run state."""

        definition = self.registry.get(experiment_id)
        issues: list[str] = []
        manifest_path = self._project_path(definition.dataset_manifest)
        if not definition.command:
            issues.append("command is not configured")
        if not manifest_path.is_file():
            issues.append(f"dataset manifest is missing: {manifest_path}")
        else:
            try:
                self._load_manifest(definition)
            except ExperimentRunError as error:
                issues.append(str(error))
        missing_dependencies = self._missing_dependencies(definition)
        if missing_dependencies:
            issues.append(
                "dependencies have no accepted completed run: "
                + ", ".join(missing_dependencies)
            )
        return {
            "experiment_id": definition.experiment_id,
            "description": definition.description,
            "dependencies": list(definition.dependencies),
            "command": list(definition.command),
            "dataset_manifest": str(manifest_path),
            "ready": not issues,
            "issues": issues,
        }

    def run(
        self,
        experiment_id: str,
        *,
        run_id: str | None = None,
        resume: bool = False,
    ) -> dict[str, Any]:
        """Run an experiment or resume a failed/interrupted run."""

        definition = self.registry.get(experiment_id)
        if not definition.command:
            raise ExperimentRunError(
                f"Experiment {experiment_id!r} has no command configured; "
                "edit its versioned TOML configuration before execution"
            )
        manifest_path, manifest = self._load_manifest(definition)
        missing_dependencies = self._missing_dependencies(definition)
        if missing_dependencies:
            raise ExperimentRunError(
                "Dependencies have no accepted completed run: "
                + ", ".join(missing_dependencies)
            )
        git_commit = self._git_commit()
        selected_run_id = run_id or _default_run_id(experiment_id)
        run_dir = resolve_run_directory(self.runs_root, selected_run_id)

        with RunLock(run_dir):
            journal = self._open_or_create_journal(
                run_dir,
                selected_run_id,
                definition,
                manifest_path,
                str(manifest["fingerprint"]),
                git_commit,
                resume,
            )
            current = journal.data
            if current["status"] == "completed":
                report = verify_run(run_dir, definition)
                journal.set_acceptance(report.to_dict())
                if report.ok:
                    return journal.data
                journal.update_stage(
                    "verify",
                    "failed",
                    message="Previously completed run no longer passes acceptance",
                    details={"issue_count": len(report.issues)},
                )
                journal.set_status("failed")
                messages = "; ".join(issue.message for issue in report.issues)
                raise ExperimentRunError(
                    f"Completed run no longer passes acceptance: {messages}"
                )

            execute = current["stages"]["execute"]
            try:
                if execute["status"] != "completed" or execute.get("exit_code") != 0:
                    self._execute(run_dir, definition, journal)
                journal.update_stage("verify", "running")
                report = verify_run(run_dir, definition, require_completed=False)
                journal.set_acceptance(report.to_dict())
                if not report.ok:
                    journal.update_stage(
                        "verify",
                        "failed",
                        message="Acceptance checks failed",
                        details={"issue_count": len(report.issues)},
                    )
                    journal.set_status("failed")
                    messages = "; ".join(issue.message for issue in report.issues)
                    raise ExperimentRunError(f"Acceptance checks failed: {messages}")
                journal.update_stage(
                    "verify",
                    "completed",
                    message="All acceptance checks passed",
                    details={"issue_count": 0},
                )
                journal.set_status("completed")
                return journal.data
            except ExperimentRunError:
                raise
            except Exception as error:
                journal.set_status("failed")
                raise ExperimentRunError(
                    f"Experiment {experiment_id!r} failed: {error}"
                ) from error

    def _open_or_create_journal(
        self,
        run_dir: Path,
        run_id: str,
        definition: ExperimentDefinition,
        manifest_path: Path,
        dataset_fingerprint: str,
        git_commit: str,
        resume: bool,
    ) -> RunJournal:
        journal_path = run_dir / "run.json"
        if journal_path.exists():
            if not resume:
                raise ExperimentRunError(
                    f"Run already exists: {run_id}; use --resume to continue it"
                )
            journal = RunJournal.load(run_dir)
            self._validate_resume(
                journal,
                definition,
                dataset_fingerprint,
                manifest_path,
            )
            return journal

        leftovers = [path for path in run_dir.iterdir() if path.name != ".run.lock"]
        if leftovers:
            raise ExperimentRunError(
                f"Refusing to initialize non-empty run directory: {run_dir}"
            )
        if resume:
            raise ExperimentRunError(f"Cannot resume missing run: {run_id}")

        shutil.copy2(definition.source_path, run_dir / "experiment.toml")
        journal = RunJournal.create(
            run_dir,
            run_id,
            definition,
            git_commit=git_commit,
            dataset_fingerprint=dataset_fingerprint,
            dataset_manifest=manifest_path.relative_to(self.project_root).as_posix(),
        )
        journal.update_stage(
            "preflight",
            "completed",
            message="Configuration, dataset, dependencies, and Git provenance validated",
        )
        return journal

    def _validate_resume(
        self,
        journal: RunJournal,
        definition: ExperimentDefinition,
        dataset_fingerprint: str,
        manifest_path: Path,
    ) -> None:
        data = journal.data
        provenance = data.get("provenance", {})
        expected = {
            "experiment_id": (data.get("experiment_id"), definition.experiment_id),
            "config_sha256": (
                provenance.get("config_sha256"),
                definition.config_sha256,
            ),
            "dataset_fingerprint": (
                provenance.get("dataset_fingerprint"),
                dataset_fingerprint,
            ),
            "dataset_manifest": (
                provenance.get("dataset_manifest"),
                manifest_path.relative_to(self.project_root).as_posix(),
            ),
            "seed": (provenance.get("seed"), definition.seed),
            "command": (provenance.get("command"), list(definition.command)),
        }
        mismatches = [
            name for name, values in expected.items() if values[0] != values[1]
        ]
        if mismatches:
            raise ExperimentRunError(
                "Cannot resume because persisted provenance changed: "
                + ", ".join(mismatches)
            )
        snapshot = journal.run_directory / "experiment.toml"
        if not snapshot.is_file():
            raise ExperimentRunError(f"Cannot resume without {snapshot}")

    def _execute(
        self,
        run_dir: Path,
        definition: ExperimentDefinition,
        journal: RunJournal,
    ) -> None:
        stdout_path = run_dir / "stdout.log"
        stderr_path = run_dir / "stderr.log"
        journal.update_stage(
            "execute",
            "running",
            details={
                "stdout": stdout_path.name,
                "stderr": stderr_path.name,
            },
        )
        environment = os.environ.copy()
        environment.update(
            {
                "IPPOSEREP_PROJECT_ROOT": str(self.project_root),
                "IPPOSEREP_RUN_DIR": str(run_dir),
                "IPPOSEREP_RUN_ID": str(journal.data["run_id"]),
                "IPPOSEREP_EXPERIMENT_ID": definition.experiment_id,
                "IPPOSEREP_SEED": str(definition.seed),
            }
        )
        try:
            with (
                stdout_path.open("a", encoding="utf-8", newline="\n") as stdout_handle,
                stderr_path.open("a", encoding="utf-8", newline="\n") as stderr_handle,
            ):
                result = subprocess.run(
                    list(definition.command),
                    cwd=self.project_root,
                    env=environment,
                    stdout=stdout_handle,
                    stderr=stderr_handle,
                    check=False,
                )
        except OSError as error:
            journal.update_stage(
                "execute",
                "failed",
                message=f"Command could not start: {error}",
                details={"exit_code": None},
            )
            journal.set_status("failed")
            raise ExperimentRunError(
                f"Experiment command could not start: {error}"
            ) from error
        if result.returncode != 0:
            journal.update_stage(
                "execute",
                "failed",
                message=f"Command exited with code {result.returncode}",
                details={"exit_code": result.returncode},
            )
            journal.set_status("failed")
            raise ExperimentRunError(
                f"Experiment command exited with code {result.returncode}; "
                f"see {stderr_path}"
            )
        journal.update_stage(
            "execute",
            "completed",
            message="Command completed successfully",
            details={"exit_code": 0},
        )

    def _load_manifest(
        self, definition: ExperimentDefinition
    ) -> tuple[Path, dict[str, Any]]:
        manifest_path = self._project_path(definition.dataset_manifest)
        try:
            manifest = load_json_object(manifest_path)
        except JournalError as error:
            raise ExperimentRunError(str(error)) from error
        fingerprint = manifest.get("fingerprint")
        if not isinstance(fingerprint, str) or not fingerprint.strip():
            raise ExperimentRunError(
                f"Dataset manifest has no non-empty fingerprint: {manifest_path}"
            )
        return manifest_path, manifest

    def _project_path(self, relative_path: Path) -> Path:
        candidate = (self.project_root / relative_path).resolve()
        try:
            candidate.relative_to(self.project_root)
        except ValueError as error:
            raise ExperimentRunError(
                f"Configured path escapes project root: {relative_path}"
            ) from error
        return candidate

    def _missing_dependencies(self, definition: ExperimentDefinition) -> list[str]:
        accepted: set[str] = set()
        if self.runs_root.is_dir():
            for journal_path in self.runs_root.glob("*/run.json"):
                try:
                    journal = load_json_object(journal_path)
                except JournalError:
                    continue
                acceptance = journal.get("acceptance")
                if (
                    journal.get("status") == "completed"
                    and isinstance(acceptance, dict)
                    and acceptance.get("ok") is True
                    and isinstance(journal.get("experiment_id"), str)
                ):
                    experiment_id = str(journal["experiment_id"])
                    if experiment_id not in definition.dependencies:
                        continue
                    dependency = self.registry.get(experiment_id)
                    report = verify_run(journal_path.parent, dependency)
                    if report.ok:
                        accepted.add(experiment_id)
        return [
            dependency
            for dependency in definition.dependencies
            if dependency not in accepted
        ]

    def _git_commit(self) -> str:
        result = subprocess.run(
            [
                "git",
                "-c",
                f"safe.directory={self.project_root.as_posix()}",
                "rev-parse",
                "HEAD",
            ],
            cwd=self.project_root,
            capture_output=True,
            text=True,
            check=False,
        )
        commit = result.stdout.strip()
        if result.returncode != 0 or not commit:
            detail = result.stderr.strip() or "unknown Git error"
            raise ExperimentRunError(f"Cannot resolve Git commit: {detail}")
        return commit


def _default_run_id(experiment_id: str) -> str:
    timestamp = datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ")
    return f"{experiment_id}-{timestamp}"
