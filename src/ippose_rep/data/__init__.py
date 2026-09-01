"""Dataset metadata and split utilities."""

from .splits import (
    NTU120_XSUB_TRAIN_SUBJECTS,
    NTUSample,
    build_ntu120_manifest,
    parse_ntu_skeleton_name,
    split_ntu120,
)

__all__ = [
    "NTU120_XSUB_TRAIN_SUBJECTS",
    "NTUSample",
    "build_ntu120_manifest",
    "parse_ntu_skeleton_name",
    "split_ntu120",
]
