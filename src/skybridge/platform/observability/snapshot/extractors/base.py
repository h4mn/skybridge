# -*- coding: utf-8 -*-
"""
Interface base para extratores de estado.
"""
from __future__ import annotations

from abc import ABC, abstractmethod

from skybridge.platform.observability.snapshot.models import Snapshot, Diff, SnapshotSubject


class StateExtractor(ABC):
    """Interface base para extratores de estado."""

    @property
    @abstractmethod
    def subject(self) -> SnapshotSubject:
        """Dominio deste extrator."""

    @abstractmethod
    def capture(
        self,
        target: str,
        depth: int = 5,
        include_extensions: list[str] | None = None,
        exclude_patterns: list[str] | None = None,
        **options,
    ) -> Snapshot:
        """Captura snapshot do dominio."""

    @abstractmethod
    def compare(self, old: Snapshot, new: Snapshot) -> Diff:
        """Compara dois snapshots do mesmo dominio."""
