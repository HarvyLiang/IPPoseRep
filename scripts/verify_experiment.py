"""Re-run acceptance checks for a persisted experiment directory."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from ippose_rep.evaluation.acceptance import verify_run
from ippose_rep.experiments.registry import (
    ExperimentDefinition,
    RegistryError,
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("run_directory", type=Path)
    parser.add_argument(
        "--config",
        type=Path,
        help="Config to verify against; defaults to <run_directory>/experiment.toml",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    run_directory = args.run_directory.resolve()
    config_path = (args.config or run_directory / "experiment.toml").resolve()
    try:
        definition = ExperimentDefinition.from_toml(config_path)
        report = verify_run(run_directory, definition)
    except RegistryError as error:
        print(f"error: {error}", file=sys.stderr)
        return 2
    print(json.dumps(report.to_dict(), ensure_ascii=False, indent=2, sort_keys=True))
    return 0 if report.ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
