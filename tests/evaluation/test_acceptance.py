import json
import shutil
import tempfile
import unittest
from pathlib import Path

from ippose_rep.evaluation.acceptance import verify_run
from ippose_rep.experiments.journal import RunJournal
from ippose_rep.experiments.registry import ExperimentDefinition


def make_definition(root: Path) -> ExperimentDefinition:
    config = root / "source.toml"
    config.write_text(
        """id = "m0"
description = "acceptance test"
dependencies = []
seed = 11
dataset_manifest = "data/derived/manifest.json"
command = ["python", "train.py"]

[acceptance]
metrics_file = "metrics.json"
required_artifacts = ["metrics.json", "environment.json"]
required_metrics = ["top1", "macro_f1"]
""",
        encoding="utf-8",
    )
    return ExperimentDefinition.from_toml(config)


class AcceptanceTests(unittest.TestCase):
    def test_accepts_complete_run_with_provenance_artifacts_and_metrics(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            definition = make_definition(root)
            run_dir = root / "run"
            run_dir.mkdir()
            shutil.copy2(definition.source_path, run_dir / "experiment.toml")
            journal = RunJournal.create(
                run_dir,
                "run-1",
                definition,
                git_commit="abc123",
                dataset_fingerprint="data123",
                dataset_manifest="data/derived/manifest.json",
            )
            journal.update_stage("preflight", "completed")
            journal.update_stage("execute", "completed", details={"exit_code": 0})
            (run_dir / "metrics.json").write_text(
                json.dumps({"top1": 0.9, "macro_f1": 0.8}), encoding="utf-8"
            )
            (run_dir / "environment.json").write_text("{}", encoding="utf-8")
            journal.update_stage("verify", "completed")
            journal.set_status("completed")

            report = verify_run(run_dir, definition)

            self.assertTrue(report.ok, report.issues)
            self.assertEqual(report.metrics, {"top1": 0.9, "macro_f1": 0.8})

    def test_rejects_missing_or_non_finite_metric(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            definition = make_definition(root)
            run_dir = root / "run"
            run_dir.mkdir()
            shutil.copy2(definition.source_path, run_dir / "experiment.toml")
            journal = RunJournal.create(
                run_dir,
                "run-1",
                definition,
                git_commit="abc123",
                dataset_fingerprint="data123",
                dataset_manifest="data/derived/manifest.json",
            )
            journal.update_stage("execute", "completed", details={"exit_code": 0})
            journal.update_stage("verify", "completed")
            journal.set_status("completed")
            (run_dir / "metrics.json").write_text('{"top1": NaN}', encoding="utf-8")

            report = verify_run(run_dir, definition)

            codes = {issue.code for issue in report.issues}
            self.assertFalse(report.ok)
            self.assertIn("metric_missing_or_invalid", codes)
            self.assertIn("artifact_missing", codes)


if __name__ == "__main__":
    unittest.main()
