# -*- coding: utf-8 -*-
"""
Registro de extratores por dominio.
"""
from __future__ import annotations

from typing import Dict

from skybridge.platform.observability.snapshot.extractors.base import StateExtractor
from skybridge.platform.observability.snapshot.models import SnapshotSubject


class ExtractorRegistry:
    """Registro global de extratores por dominio."""

    _extractors: Dict[SnapshotSubject, StateExtractor] = {}

    @classmethod
    def register(cls, extractor: StateExtractor) -> None:
        """Registra um extrator."""
        cls._extractors[extractor.subject] = extractor

    @classmethod
    def get(cls, subject: SnapshotSubject) -> StateExtractor:
        """Retorna extrator para o dominio."""
        if subject not in cls._extractors:
            raise ValueError(f"No extractor for subject: {subject}")
        return cls._extractors[subject]

    @classmethod
    def list_subjects(cls) -> list[SnapshotSubject]:
        """Lista dominios observaveis."""
        return list(cls._extractors.keys())

    @classmethod
    def clear(cls) -> None:
        """Limpa registro (uso em testes)."""
        cls._extractors.clear()
