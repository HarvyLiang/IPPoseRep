"""Create a deterministic NTU120 skeleton manifest without modifying raw data."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from ippose_rep.data.splits import build_ntu120_manifest
from ippose_rep.experiments.journal import atomic_write_json


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Build an NTU RGB+D 120 train/test manifest from .skeleton files."
    )
    parser.add_argument("input_root", type=Path, help="Read-only NTU skeleton root")
    parser.add_argument(
        "--protocol",
        choices=("xsub", "xset"),
        default="xsub",
        help="Official NTU120 evaluation protocol (default: xsub)",
    )
    parser.add_argument(
        "--output",
        type=Path,
        help="Output JSON; defaults to data/derived/manifests/ntu120_<protocol>.json",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    input_root = args.input_root.resolve()
    if not input_root.is_dir():
        raise SystemExit(f"Input root does not exist: {input_root}")

    output = args.output or (
        PROJECT_ROOT / "data" / "derived" / "manifests" / f"ntu120_{args.protocol}.json"
    )
    output = output.resolve()
    derived_root = (PROJECT_ROOT / "data" / "derived").resolve()
    try:
        output.relative_to(derived_root)
    except ValueError as error:
        raise SystemExit(f"Output must be inside {derived_root}: {output}") from error

    paths = sorted(input_root.rglob("*.skeleton"))
    if not paths:
        raise SystemExit(f"No .skeleton files found under {input_root}")
    manifest = build_ntu120_manifest(paths, args.protocol, input_root)
    atomic_write_json(output, manifest)
    summary = {
        key: manifest[key]
        for key in (
            "dataset",
            "protocol",
            "fingerprint",
            "sample_count",
            "train_count",
            "test_count",
        )
    }
    summary["output"] = str(output)
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
