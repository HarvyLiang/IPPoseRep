"""NTU RGB+D skeleton filename parsing and official NTU120 splits."""

from __future__ import annotations

import re
from collections.abc import Iterable
from dataclasses import asdict, dataclass
from hashlib import sha256
from pathlib import Path
from typing import Literal

NTU120_XSUB_TRAIN_SUBJECTS = frozenset(
    {
        1,
        2,
        4,
        5,
        8,
        9,
        13,
        14,
        15,
        16,
        17,
        18,
        19,
        25,
        27,
        28,
        31,
        34,
        35,
        38,
        45,
        46,
        47,
        49,
        50,
        52,
        53,
        54,
        55,
        56,
        57,
        58,
        59,
        70,
        74,
        78,
        80,
        81,
        82,
        83,
        84,
        85,
        86,
        89,
        91,
        92,
        93,
        94,
        95,
        97,
        98,
        100,
        103,
    }
)

_NTU_NAME = re.compile(
    r"^S(?P<setup>\d{3})"
    r"C(?P<camera>\d{3})"
    r"P(?P<subject>\d{3})"
    r"R(?P<repetition>\d{3})"
    r"A(?P<action>\d{3})\.skeleton$",
    re.IGNORECASE,
)

Protocol = Literal["xsub", "xset"]
Partition = Literal["train", "test"]


@dataclass(frozen=True, slots=True)
class NTUSample:
    """Metadata encoded in one NTU skeleton filename."""

    filename: str
    setup: int
    camera: int
    subject: int
    repetition: int
    action: int

    @property
    def action_index(self) -> int:
        """Return the zero-based class index used by classifiers."""

        return self.action - 1

    @property
    def capture_group(self) -> str:
        """Identify a capture while deliberately excluding the camera field."""

        return (
            f"S{self.setup:03d}P{self.subject:03d}"
            f"R{self.repetition:03d}A{self.action:03d}"
        )


def parse_ntu_skeleton_name(path: str | Path) -> NTUSample:
    """Parse and validate an NTU RGB+D 120 skeleton filename.

    Only the basename is interpreted, so callers may pass a full path. The
    accepted ranges correspond to NTU120 metadata, not the number of files
    currently present on disk.
    """

    filename = Path(path).name
    match = _NTU_NAME.fullmatch(filename)
    if match is None:
        raise ValueError(f"Invalid NTU skeleton filename: {filename!r}")

    fields = {name: int(value) for name, value in match.groupdict().items()}
    _require_range("setup", fields["setup"], 1, 32, filename)
    _require_range("camera", fields["camera"], 1, 3, filename)
    _require_range("subject", fields["subject"], 1, 106, filename)
    _require_range("repetition", fields["repetition"], 1, 2, filename)
    _require_range("action", fields["action"], 1, 120, filename)
    return NTUSample(filename=filename, **fields)


def _require_range(
    field: str, value: int, minimum: int, maximum: int, filename: str
) -> None:
    if not minimum <= value <= maximum:
        raise ValueError(
            f"{field}={value} is outside {minimum}..{maximum} in {filename!r}"
        )


def normalize_protocol(protocol: str) -> Protocol:
    normalized = protocol.strip().lower()
    if normalized not in {"xsub", "xset"}:
        raise ValueError(f"Unsupported NTU120 protocol: {protocol!r}")
    return normalized  # type: ignore[return-value]


def split_ntu120(sample: NTUSample, protocol: str) -> Partition:
    """Assign a parsed NTU120 sample to the official train or test split."""

    normalized = normalize_protocol(protocol)
    if normalized == "xsub":
        return "train" if sample.subject in NTU120_XSUB_TRAIN_SUBJECTS else "test"
    return "train" if sample.setup % 2 == 0 else "test"


def build_ntu120_manifest(
    paths: Iterable[str | Path], protocol: str, source_root: str | Path
) -> dict[str, object]:
    """Build deterministic manifest data from skeleton paths.

    The fingerprint covers sorted relative paths and split assignments. File
    contents are intentionally not read because raw NTU skeleton archives can
    be large and must remain read-only.
    """

    normalized = normalize_protocol(protocol)
    root = Path(source_root).resolve()
    records: list[dict[str, object]] = []
    seen: set[str] = set()

    for raw_path in paths:
        path = Path(raw_path).resolve()
        try:
            relative = path.relative_to(root).as_posix()
        except ValueError as error:
            raise ValueError(f"Sample is outside source root: {path}") from error
        if relative in seen:
            raise ValueError(f"Duplicate sample path: {relative}")
        seen.add(relative)
        sample = parse_ntu_skeleton_name(path)
        record = asdict(sample)
        record.update(
            {
                "path": relative,
                "action_index": sample.action_index,
                "capture_group": sample.capture_group,
                "partition": split_ntu120(sample, normalized),
            }
        )
        records.append(record)

    records.sort(key=lambda item: str(item["path"]))
    digest = sha256()
    for record in records:
        digest.update(str(record["path"]).encode("utf-8"))
        digest.update(b"\0")
        digest.update(str(record["partition"]).encode("ascii"))
        digest.update(b"\n")

    train_count = sum(record["partition"] == "train" for record in records)
    return {
        "schema_version": 1,
        "dataset": "NTU RGB+D 120",
        "protocol": normalized,
        "source_root": str(root),
        "fingerprint": digest.hexdigest(),
        "sample_count": len(records),
        "train_count": train_count,
        "test_count": len(records) - train_count,
        "samples": records,
    }
