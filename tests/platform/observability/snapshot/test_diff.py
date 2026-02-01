# -*- coding: utf-8 -*-
"""
Tests para comparacao de snapshots.
"""
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[4] / "src"))

from runtime.observability.snapshot.extractors.fileops_extractor import FileOpsExtractor


class SnapshotDiffTests(unittest.TestCase):
    def test_compare_fileops(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "a.txt").write_text("abc", encoding="utf-8")

            extractor = FileOpsExtractor()
            snap_old = extractor.capture(target=str(root), depth=5)

            (root / "a.txt").write_text("abcdef", encoding="utf-8")
            (root / "b.txt").write_text("new", encoding="utf-8")

            snap_new = extractor.capture(target=str(root), depth=5)
            diff = extractor.compare(snap_old, snap_new)

            self.assertEqual(diff.summary.added_files, 1)
            self.assertEqual(diff.summary.removed_files, 0)
            self.assertEqual(diff.summary.modified_files, 1)


if __name__ == "__main__":
    unittest.main()
