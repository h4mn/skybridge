# -*- coding: utf-8 -*-
"""
Tests para extratores do Snapshot Service.
"""
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[4] / "src"))

from skybridge.platform.observability.snapshot.extractors.fileops_extractor import FileOpsExtractor
from skybridge.platform.observability.snapshot.extractors.health_extractor import HealthExtractor
from skybridge.platform.observability.snapshot.extractors.tasks_extractor import TasksExtractor
from skybridge.platform.observability.snapshot.models import SnapshotSubject


class ExtractorsTests(unittest.TestCase):
    def test_fileops_capture_basic(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "sub").mkdir()
            (root / "a.txt").write_text("abc", encoding="utf-8")
            (root / "sub" / "b.py").write_text("print('x')", encoding="utf-8")

            extractor = FileOpsExtractor()
            snapshot = extractor.capture(target=str(root), depth=5)

            self.assertEqual(snapshot.metadata.subject, SnapshotSubject.FILEOPS)
            self.assertEqual(snapshot.stats.total_files, 2)
            self.assertGreaterEqual(snapshot.stats.total_dirs, 1)
            paths = {item["path"] for item in snapshot.files}
            self.assertIn("a.txt", paths)
            self.assertIn("sub/b.py", paths)

    def test_fileops_capture_with_filters(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "sub").mkdir()
            (root / "a.txt").write_text("abc", encoding="utf-8")
            (root / "sub" / "b.py").write_text("print('x')", encoding="utf-8")

            extractor = FileOpsExtractor()
            snapshot = extractor.capture(
                target=str(root),
                depth=5,
                include_extensions=[".py"],
            )
            paths = {item["path"] for item in snapshot.files}
            self.assertNotIn("a.txt", paths)
            self.assertIn("sub/b.py", paths)

            snapshot = extractor.capture(
                target=str(root),
                depth=5,
                exclude_patterns=["sub/*"],
            )
            paths = {item["path"] for item in snapshot.files}
            self.assertIn("a.txt", paths)
            self.assertNotIn("sub/b.py", paths)

    def test_health_extractor(self):
        extractor = HealthExtractor()
        snapshot = extractor.capture(target="system")
        self.assertEqual(snapshot.metadata.subject, SnapshotSubject.HEALTH)
        self.assertIn("health", snapshot.structure)

    def test_tasks_extractor(self):
        extractor = TasksExtractor()
        snapshot = extractor.capture(target="queue")
        self.assertEqual(snapshot.metadata.subject, SnapshotSubject.TASKS)
        self.assertIn("tasks", snapshot.structure)


if __name__ == "__main__":
    unittest.main()
