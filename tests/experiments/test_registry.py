import tempfile
import unittest
from pathlib import Path

from ippose_rep.experiments.registry import ExperimentRegistry, RegistryError


def write_config(
    path: Path,
    experiment_id: str,
    dependencies: tuple[str, ...] = (),
    *,
    dataset_manifest: str = "data/derived/manifest.json",
) -> None:
    dependency_text = ", ".join(f'"{item}"' for item in dependencies)
    path.write_text(
        f'''id = "{experiment_id}"
description = "test experiment"
dependencies = [{dependency_text}]
seed = 7
dataset_manifest = "{dataset_manifest}"
command = []

[acceptance]
metrics_file = "metrics.json"
required_artifacts = ["metrics.json"]
required_metrics = ["top1"]
''',
        encoding="utf-8",
    )


class RegistryTests(unittest.TestCase):
    def test_loads_dependency_graph_in_topological_order(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            write_config(root / "m1.toml", "m1", ("m0",))
            write_config(root / "m0.toml", "m0")

            registry = ExperimentRegistry.load(root)

            self.assertEqual(registry.topological_order(), ("m0", "m1"))
            self.assertEqual(registry.get("m0").command, ())

    def test_rejects_missing_dependency(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            write_config(root / "m1.toml", "m1", ("missing",))

            with self.assertRaisesRegex(RegistryError, "missing dependencies"):
                ExperimentRegistry.load(root)

    def test_rejects_dependency_cycle(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            write_config(root / "a.toml", "a", ("b",))
            write_config(root / "b.toml", "b", ("a",))

            with self.assertRaisesRegex(RegistryError, "cycle"):
                ExperimentRegistry.load(root)

    def test_rejects_unsafe_relative_path(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            write_config(
                root / "unsafe.toml",
                "unsafe",
                dataset_manifest="../private.json",
            )

            with self.assertRaisesRegex(RegistryError, "safe relative path"):
                ExperimentRegistry.load(root)


if __name__ == "__main__":
    unittest.main()
