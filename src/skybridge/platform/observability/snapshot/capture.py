# -*- coding: utf-8 -*-
"""
Logica de captura de snapshots.
"""
from __future__ import annotations

from datetime import datetime
import hashlib

from skybridge.platform.observability.snapshot.models import Snapshot, SnapshotSubject
from skybridge.platform.observability.snapshot.registry import ExtractorRegistry


def generate_snapshot_id(subject: SnapshotSubject, target: str) -> str:
    """Gera id unico do snapshot com timestamp e hash curto."""
    timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S_%f")
    digest = hashlib.md5(f"{subject.value}:{target}".encode("utf-8")).hexdigest()[:8]
    return f"snap_{timestamp}_{digest}"


def capture_snapshot(
    *,
    subject: SnapshotSubject,
    target: str,
    depth: int = 5,
    include_extensions: list[str] | None = None,
    exclude_patterns: list[str] | None = None,
    tags: dict[str, str] | None = None,
) -> Snapshot:
    """Captura snapshot usando o extrator registrado."""
    extractor = ExtractorRegistry.get(subject)
    snapshot = extractor.capture(
        target=target,
        depth=depth,
        include_extensions=include_extensions,
        exclude_patterns=exclude_patterns,
        tags=tags or {},
    )
    return snapshot
