import json
import sys
import tempfile
import unittest
from pathlib import Path

from ippose_rep.experiments.registry import ExperimentRegistry
from ippose_rep.experiments.runner import ExperimentRunError, ExperimentRunner


def toml_string(value: str) -> str:
    return json.dumps(value)


def write_definition(
    path: Path,
    *,
    experiment_id: str,
    command: list[str],
    dependencies: tuple[str, ...] = (),
) -> None:
    dependency_text = ", ".join(toml_string(item) for item in dependencies)
    command_text = ", ".join(toml_string(item) for item in command)
    path.write_text(
        f'''id = "{experiment_id}"
description = "runner test"
dependencies = [{dependency_text}]
seed = 13
dataset_manifest = "data/derived/manifests/manifest.json"
command = [{command_text}]

[acceptance]
metrics_file = "metrics.json"
required_artifacts = ["metrics.json", "environment.json", "confusion_matrix.png"]
required_metrics = ["top1", "macro_f1"]
''',
        encoding="utf-8",
    )


def create_project(root: Path, command: list[str]) -> ExperimentRunner:
    config_root = root / "configs" / "experiments"
    config_root.mkdir(parents=True)
    write_definition(
        config_root / "m0.toml",
        experiment_id="m0",
        command=command,
    )
    manifest = root / "data" / "derived" / "manifests" / "manifest.json"
    manifest.parent.mkdir(parents=True)
    manifest.write_text('{"fingerprint": "dataset123"}', encoding="utf-8")
    registry = ExperimentRegistry.load(config_root)
    runner = ExperimentRunner(
        root,
        registry,
        root / "data" / "derived" / "experiment_runs",
    )
    runner._git_commit = lambda: "abc123"  # type: ignore[method-assign]
    return runner


class RunnerTests(unittest.TestCase):
    def test_dry_run_reports_empty_command_without_writing_run_state(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            runner = create_project(root, [])

            result = runner.dry_run("m0")

            self.assertFalse(result["ready"])
            self.assertIn("command is not configured", result["issues"])
            self.assertFalse(runner.runs_root.exists())
            with self.assertRaisesRegex(ExperimentRunError, "no command"):
                runner.run("m0", run_id="run-1")

    def test_executes_and_accepts_a_run_then_returns_it_on_resume(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            worker = root / "worker.py"
            worker.write_text(
                """import json
import os
from pathlib import Path

run_dir = Path(os.environ["IPPOSEREP_RUN_DIR"])
(run_dir / "metrics.json").write_text(
    json.dumps({"top1": 0.91, "macro_f1": 0.87}), encoding="utf-8"
)
(run_dir / "environment.json").write_text("{}", encoding="utf-8")
(run_dir / "confusion_matrix.png").write_bytes(b"test-image")
""",
                encoding="utf-8",
            )
            runner = create_project(root, [sys.executable, str(worker)])

            result = runner.run("m0", run_id="run-1")
            resumed = runner.run("m0", run_id="run-1", resume=True)

            self.assertEqual(result["status"], "completed")
            self.assertTrue(result["acceptance"]["ok"])
            self.assertEqual(resumed["status"], "completed")
            run_dir = runner.runs_root / "run-1"
            self.assertTrue((run_dir / "stdout.log").is_file())
            self.assertTrue((run_dir / "experiment.toml").is_file())
            self.assertFalse((run_dir / ".run.lock").exists())

            (run_dir / "metrics.json").unlink()
            with self.assertRaisesRegex(
                ExperimentRunError, "no longer passes acceptance"
            ):
                runner.run("m0", run_id="run-1", resume=True)

    def test_records_a_command_start_failure(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            runner = create_project(root, [str(root / "missing-executable")])

            with self.assertRaisesRegex(ExperimentRunError, "could not start"):
                runner.run("m0", run_id="run-1")

            journal = json.loads(
                (runner.runs_root / "run-1" / "run.json").read_text(encoding="utf-8")
            )
            self.assertEqual(journal["status"], "failed")
            self.assertEqual(journal["stages"]["execute"]["status"], "failed")

    def test_dependency_requires_an_accepted_completed_run(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            config_root = root / "configs" / "experiments"
            config_root.mkdir(parents=True)
            write_definition(config_root / "m0.toml", experiment_id="m0", command=[])
            write_definition(
                config_root / "m1.toml",
                experiment_id="m1",
                command=[],
                dependencies=("m0",),
            )
            manifest = root / "data" / "derived" / "manifests" / "manifest.json"
            manifest.parent.mkdir(parents=True)
            manifest.write_text('{"fingerprint": "dataset123"}', encoding="utf-8")
            runner = ExperimentRunner(
                root,
                ExperimentRegistry.load(config_root),
                root / "data" / "derived" / "experiment_runs",
            )

            result = runner.dry_run("m1")

            self.assertIn(
                "dependencies have no accepted completed run: m0",
                result["issues"],
            )


if __name__ == "__main__":
    unittest.main()
