# -*- coding: utf-8 -*-
"""
Tests para registry de extratores.
"""
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[4] / "src"))

from skybridge.platform.observability.snapshot.extractors.fileops_extractor import FileOpsExtractor
from skybridge.platform.observability.snapshot.models import SnapshotSubject
from skybridge.platform.observability.snapshot.registry import ExtractorRegistry


class ExtractorRegistryTests(unittest.TestCase):
    def setUp(self):
        ExtractorRegistry.clear()

    def test_register_and_get(self):
        extractor = FileOpsExtractor()
        ExtractorRegistry.register(extractor)

        stored = ExtractorRegistry.get(SnapshotSubject.FILEOPS)
        self.assertIs(stored, extractor)

    def test_list_subjects(self):
        ExtractorRegistry.register(FileOpsExtractor())
        subjects = ExtractorRegistry.list_subjects()
        self.assertIn(SnapshotSubject.FILEOPS, subjects)


if __name__ == "__main__":
    unittest.main()
