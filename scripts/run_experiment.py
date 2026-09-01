"""Preflight, execute, resume, and verify a versioned experiment."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from ippose_rep.experiments.registry import (
    ExperimentRegistry,
    RegistryError,
)
from ippose_rep.experiments.runner import (
    ExperimentRunError,
    ExperimentRunner,
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("experiment_id", help="Experiment id from configs/experiments")
    parser.add_argument(
        "--run-id", help="Stable run id; generated from UTC time if omitted"
    )
    parser.add_argument(
        "--resume",
        action="store_true",
        help="Continue an existing run after validating persisted provenance",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Report readiness without writing files or executing a command",
    )
    parser.add_argument("--project-root", type=Path, default=PROJECT_ROOT)
    parser.add_argument("--config-root", type=Path)
    parser.add_argument("--runs-root", type=Path)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    project_root = args.project_root.resolve()
    config_root = (
        args.config_root or project_root / "configs" / "experiments"
    ).resolve()
    runs_root = (
        args.runs_root or project_root / "data" / "derived" / "experiment_runs"
    ).resolve()
    try:
        registry = ExperimentRegistry.load(config_root)
        runner = ExperimentRunner(project_root, registry, runs_root)
        result = (
            runner.dry_run(args.experiment_id)
            if args.dry_run
            else runner.run(
                args.experiment_id,
                run_id=args.run_id,
                resume=args.resume,
            )
        )
    except (ExperimentRunError, RegistryError) as error:
        print(f"error: {error}", file=sys.stderr)
        return 2
    print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))
    if args.dry_run and result.get("ready") is not True:
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
