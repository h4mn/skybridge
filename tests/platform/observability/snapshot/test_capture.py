# -*- coding: utf-8 -*-
"""
Tests para captura e persistencia de snapshots.
"""
import os
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[4] / "src"))

from skybridge.platform.observability.snapshot import snapshot_capture, register_default_extractors
from skybridge.platform.observability.snapshot.registry import ExtractorRegistry


class SnapshotCaptureTests(unittest.TestCase):
    def setUp(self):
        ExtractorRegistry.clear()
        register_default_extractors()

    def test_snapshot_capture_persists(self):
        with tempfile.TemporaryDirectory() as workspace_dir, tempfile.TemporaryDirectory() as target_dir:
            root = Path(target_dir)
            (root / "a.txt").write_text("abc", encoding="utf-8")

            old_workspace = os.environ.get("SKYBRIDGE_WORKSPACE")
            os.environ["SKYBRIDGE_WORKSPACE"] = workspace_dir
            try:
                result = snapshot_capture({
                    "subject": "fileops",
                    "target": target_dir,
                    "depth": 2,
                })
            finally:
                if old_workspace is None:
                    os.environ.pop("SKYBRIDGE_WORKSPACE", None)
                else:
                    os.environ["SKYBRIDGE_WORKSPACE"] = old_workspace

            self.assertTrue(result.is_ok)
            payload = result.value
            self.assertIn("snapshot_id", payload.get("metadata", {}))
            self.assertIn("storage_path", payload)
            self.assertTrue(Path(payload["storage_path"]).exists())


if __name__ == "__main__":
    unittest.main()
