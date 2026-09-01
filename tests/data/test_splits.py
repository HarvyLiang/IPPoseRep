import tempfile
import unittest
from pathlib import Path

from ippose_rep.data.splits import (
    build_ntu120_manifest,
    parse_ntu_skeleton_name,
    split_ntu120,
)


class NTU120SplitTests(unittest.TestCase):
    def test_parser_exposes_zero_based_action_and_capture_group(self) -> None:
        sample = parse_ntu_skeleton_name("S002C003P001R002A120.skeleton")

        self.assertEqual(sample.action_index, 119)
        self.assertEqual(sample.capture_group, "S002P001R002A120")

    def test_parser_rejects_invalid_metadata_range(self) -> None:
        with self.assertRaisesRegex(ValueError, "camera=4"):
            parse_ntu_skeleton_name("S001C004P001R001A001.skeleton")

    def test_official_xsub_and_xset_assignments(self) -> None:
        train_subject = parse_ntu_skeleton_name("S001C001P001R001A001.skeleton")
        test_subject = parse_ntu_skeleton_name("S001C001P003R001A001.skeleton")
        even_setup = parse_ntu_skeleton_name("S002C001P003R001A001.skeleton")

        self.assertEqual(split_ntu120(train_subject, "xsub"), "train")
        self.assertEqual(split_ntu120(test_subject, "xsub"), "test")
        self.assertEqual(split_ntu120(even_setup, "xset"), "train")
        self.assertEqual(split_ntu120(test_subject, "xset"), "test")

    def test_manifest_is_deterministic_and_counts_partitions(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            first = root / "S001C001P003R001A001.skeleton"
            second = root / "S002C001P001R001A002.skeleton"
            first.touch()
            second.touch()

            manifest_a = build_ntu120_manifest([first, second], "xsub", root)
            manifest_b = build_ntu120_manifest([second, first], "XSUB", root)

            self.assertEqual(manifest_a, manifest_b)
            self.assertEqual(manifest_a["train_count"], 1)
            self.assertEqual(manifest_a["test_count"], 1)

    def test_manifest_rejects_duplicate_and_outside_paths(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            parent = Path(temporary)
            root = parent / "root"
            root.mkdir()
            sample = root / "S001C001P001R001A001.skeleton"
            outside = parent / "S001C001P001R001A002.skeleton"
            sample.touch()
            outside.touch()

            with self.assertRaisesRegex(ValueError, "Duplicate"):
                build_ntu120_manifest([sample, sample], "xsub", root)
            with self.assertRaisesRegex(ValueError, "outside source root"):
                build_ntu120_manifest([outside], "xsub", root)


if __name__ == "__main__":
    unittest.main()
