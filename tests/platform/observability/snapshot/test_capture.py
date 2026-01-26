# -*- coding: utf-8 -*-
"""
Tests para captura de snapshots.
"""
import os
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[4] / "src"))

from runtime.observability.snapshot.capture import capture_snapshot
from runtime.observability.snapshot import register_default_extractors
from runtime.observability.snapshot.registry import ExtractorRegistry
from runtime.observability.snapshot.models import SnapshotSubject


class SnapshotCaptureTests(unittest.TestCase):
    def setUp(self):
        ExtractorRegistry.clear()
        register_default_extractors()

    def test_snapshot_capture_works(self):
        """Testa que capture_snapshot retorna um snapshot válido."""
        with tempfile.TemporaryDirectory() as workspace_dir, tempfile.TemporaryDirectory() as target_dir:
            root = Path(target_dir)
            (root / "a.txt").write_text("abc", encoding="utf-8")

            old_workspace = os.environ.get("SKYBRIDGE_WORKSPACE")
            os.environ["SKYBRIDGE_WORKSPACE"] = workspace_dir
            try:
                snapshot = capture_snapshot(
                    subject=SnapshotSubject.FILEOPS,
                    target=target_dir,
                    depth=2,
                )
            finally:
                if old_workspace is None:
                    os.environ.pop("SKYBRIDGE_WORKSPACE", None)
                else:
                    os.environ["SKYBRIDGE_WORKSPACE"] = old_workspace

            # Verifica que o snapshot foi criado corretamente
            self.assertIsNotNone(snapshot.metadata.snapshot_id)
            self.assertEqual(snapshot.stats.total_files, 1)
            self.assertEqual(snapshot.metadata.subject, SnapshotSubject.FILEOPS)


if __name__ == "__main__":
    unittest.main()
