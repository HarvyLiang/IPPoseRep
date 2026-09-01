import json
import tempfile
import unittest
from pathlib import Path

from ippose_rep.experiments.journal import (
    JournalError,
    RunJournal,
    RunLock,
    RunLockedError,
    atomic_write_json,
    resolve_run_directory,
)
from ippose_rep.experiments.registry import ExperimentDefinition


def definition(root: Path) -> ExperimentDefinition:
    config = root / "experiment.toml"
    config.write_text(
        """id = "m0"
description = "journal test"
dependencies = []
seed = 7
dataset_manifest = "data/derived/manifest.json"
command = []

[acceptance]
metrics_file = "metrics.json"
required_artifacts = ["metrics.json"]
required_metrics = ["top1"]
""",
        encoding="utf-8",
    )
    return ExperimentDefinition.from_toml(config)


class JournalTests(unittest.TestCase):
    def test_atomic_write_and_journal_round_trip(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            output = root / "atomic.json"
            atomic_write_json(output, {"value": 3})
            self.assertEqual(
                json.loads(output.read_text(encoding="utf-8")), {"value": 3}
            )

            run_dir = root / "run"
            journal = RunJournal.create(
                run_dir,
                "run-1",
                definition(root),
                git_commit="abc123",
                dataset_fingerprint="dataset123",
                dataset_manifest="data/derived/manifest.json",
            )
            journal.update_stage("preflight", "completed")

            loaded = RunJournal.load(run_dir)
            self.assertEqual(loaded.data["stages"]["preflight"]["status"], "completed")

    def test_lock_rejects_a_second_owner(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            run_dir = Path(temporary) / "run"
            with RunLock(run_dir), self.assertRaises(RunLockedError):
                RunLock(run_dir).acquire()
            self.assertFalse((run_dir / ".run.lock").exists())

    def test_run_id_cannot_escape_root(self) -> None:
        with (
            tempfile.TemporaryDirectory() as temporary,
            self.assertRaises(JournalError),
        ):
            resolve_run_directory(temporary, "../escape")

    def test_run_id_cannot_alias_the_runs_root(self) -> None:
        with (
            tempfile.TemporaryDirectory() as temporary,
            self.assertRaises(JournalError),
        ):
            resolve_run_directory(temporary, ".")


if __name__ == "__main__":
    unittest.main()
