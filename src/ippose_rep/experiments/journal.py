"""Atomic experiment run journals and exclusive run locks."""

from __future__ import annotations

import json
import os
import re
import tempfile
from copy import deepcopy
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Self

from .registry import ExperimentDefinition

_RUN_ID = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.-]{0,95}$")
_STAGE_NAMES = ("preflight", "execute", "verify")
_STAGE_STATUSES = {"pending", "running", "completed", "failed", "skipped"}


class JournalError(RuntimeError):
    """Raised when persisted run state is invalid or cannot be updated."""


class RunLockedError(JournalError):
    """Raised when another process owns a run lock."""


def utc_now() -> str:
    return datetime.now(UTC).isoformat()


def resolve_run_directory(runs_root: str | Path, run_id: str) -> Path:
    if _RUN_ID.fullmatch(run_id) is None:
        raise JournalError(
            "run_id must be 1-96 characters using letters, numbers, '.', '_' or '-'"
        )
    root = Path(runs_root).resolve()
    candidate = (root / run_id).resolve()
    if candidate == root:
        raise JournalError("run_id must identify a child directory, not the runs root")
    try:
        candidate.relative_to(root)
    except ValueError as error:
        raise JournalError(f"Run directory escapes runs root: {candidate}") from error
    return candidate


def atomic_write_json(path: str | Path, value: object) -> None:
    destination = Path(path)
    destination.parent.mkdir(parents=True, exist_ok=True)
    temporary_name: str | None = None
    try:
        with tempfile.NamedTemporaryFile(
            "w",
            encoding="utf-8",
            newline="\n",
            dir=destination.parent,
            prefix=f".{destination.name}.",
            suffix=".tmp",
            delete=False,
        ) as handle:
            temporary_name = handle.name
            json.dump(value, handle, ensure_ascii=False, indent=2, sort_keys=True)
            handle.write("\n")
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary_name, destination)
    except Exception:
        if temporary_name is not None:
            Path(temporary_name).unlink(missing_ok=True)
        raise


def load_json_object(path: str | Path) -> dict[str, Any]:
    source = Path(path)
    try:
        value = json.loads(source.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        raise JournalError(f"Cannot load JSON object {source}: {error}") from error
    if not isinstance(value, dict):
        raise JournalError(f"Expected a JSON object in {source}")
    return value


class RunLock:
    """An exclusive lock represented by a file created with O_EXCL."""

    def __init__(self, run_directory: str | Path) -> None:
        self.run_directory = Path(run_directory)
        self.path = self.run_directory / ".run.lock"
        self._owned = False

    def acquire(self) -> Self:
        self.run_directory.mkdir(parents=True, exist_ok=True)
        try:
            descriptor = os.open(
                self.path,
                os.O_CREAT | os.O_EXCL | os.O_WRONLY,
                0o600,
            )
        except FileExistsError as error:
            owner = "unknown"
            try:
                owner = self.path.read_text(encoding="utf-8").strip() or owner
            except OSError:
                pass
            raise RunLockedError(f"Run is locked by {owner}: {self.path}") from error
        with os.fdopen(descriptor, "w", encoding="utf-8", newline="\n") as handle:
            handle.write(f"pid={os.getpid()} acquired_at={utc_now()}\n")
        self._owned = True
        return self

    def release(self) -> None:
        if self._owned:
            self.path.unlink(missing_ok=True)
            self._owned = False

    def __enter__(self) -> Self:
        return self.acquire()

    def __exit__(self, exc_type: object, exc: object, traceback: object) -> None:
        self.release()


class RunJournal:
    """Mutable in-memory view backed by an atomically replaced JSON file."""

    def __init__(self, run_directory: str | Path, data: dict[str, Any]) -> None:
        self.run_directory = Path(run_directory).resolve()
        self.path = self.run_directory / "run.json"
        self._data = data
        self._validate()

    @classmethod
    def create(
        cls,
        run_directory: str | Path,
        run_id: str,
        definition: ExperimentDefinition,
        *,
        git_commit: str,
        dataset_fingerprint: str,
        dataset_manifest: str,
    ) -> RunJournal:
        now = utc_now()
        stages = {
            name: {
                "status": "pending",
                "started_at": None,
                "finished_at": None,
                "message": None,
            }
            for name in _STAGE_NAMES
        }
        data: dict[str, Any] = {
            "schema_version": 1,
            "run_id": run_id,
            "experiment_id": definition.experiment_id,
            "status": "running",
            "created_at": now,
            "updated_at": now,
            "provenance": {
                "git_commit": git_commit,
                "config_sha256": definition.config_sha256,
                "dataset_manifest": dataset_manifest,
                "dataset_fingerprint": dataset_fingerprint,
                "seed": definition.seed,
                "command": list(definition.command),
            },
            "stages": stages,
            "acceptance": None,
        }
        journal = cls(run_directory, data)
        journal.save()
        return journal

    @classmethod
    def load(cls, run_directory: str | Path) -> RunJournal:
        directory = Path(run_directory).resolve()
        return cls(directory, load_json_object(directory / "run.json"))

    @property
    def data(self) -> dict[str, Any]:
        return deepcopy(self._data)

    def save(self) -> None:
        self._data["updated_at"] = utc_now()
        self._validate()
        atomic_write_json(self.path, self._data)

    def update_stage(
        self,
        stage: str,
        status: str,
        *,
        message: str | None = None,
        details: dict[str, Any] | None = None,
    ) -> None:
        if stage not in _STAGE_NAMES:
            raise JournalError(f"Unknown run stage: {stage}")
        if status not in _STAGE_STATUSES:
            raise JournalError(f"Unknown stage status: {status}")
        record = self._data["stages"][stage]
        if status == "running":
            record["started_at"] = utc_now()
            record["finished_at"] = None
        elif status in {"completed", "failed", "skipped"}:
            if record.get("started_at") is None:
                record["started_at"] = utc_now()
            record["finished_at"] = utc_now()
        record["status"] = status
        record["message"] = message
        if details:
            record.update(details)
        self.save()

    def set_acceptance(self, result: dict[str, Any]) -> None:
        self._data["acceptance"] = result
        self.save()

    def set_status(self, status: str) -> None:
        if status not in {"running", "completed", "failed"}:
            raise JournalError(f"Unknown run status: {status}")
        self._data["status"] = status
        self.save()

    def _validate(self) -> None:
        required = {
            "schema_version",
            "run_id",
            "experiment_id",
            "status",
            "created_at",
            "updated_at",
            "provenance",
            "stages",
            "acceptance",
        }
        missing = sorted(required.difference(self._data))
        if missing:
            raise JournalError(f"Run journal is missing fields: {', '.join(missing)}")
        if self._data["schema_version"] != 1:
            raise JournalError("Unsupported run journal schema_version")
        if self._data["status"] not in {"running", "completed", "failed"}:
            raise JournalError(f"Invalid run status: {self._data['status']!r}")
        stages = self._data["stages"]
        if not isinstance(stages, dict) or set(stages) != set(_STAGE_NAMES):
            raise JournalError("Run journal has invalid stages")
        for name, record in stages.items():
            if (
                not isinstance(record, dict)
                or record.get("status") not in _STAGE_STATUSES
            ):
                raise JournalError(f"Run stage {name!r} has invalid state")
