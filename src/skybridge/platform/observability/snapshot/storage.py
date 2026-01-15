# -*- coding: utf-8 -*-
"""
Persistencia e retencao de snapshots e diffs.
"""
from __future__ import annotations

from datetime import datetime, timedelta
from pathlib import Path
from typing import Iterable

from skybridge.platform.observability.snapshot.models import Snapshot, Diff, SnapshotSubject
from skybridge.platform.observability.snapshot.workspace import ensure_workspace


def _snapshot_dir(subject: SnapshotSubject) -> Path:
    paths = ensure_workspace()
    subject_dir = paths["snapshots"] / subject.value
    subject_dir.mkdir(parents=True, exist_ok=True)
    return subject_dir


def _diff_dir(subject: SnapshotSubject) -> Path:
    paths = ensure_workspace()
    subject_dir = paths["diffs"] / subject.value
    subject_dir.mkdir(parents=True, exist_ok=True)
    return subject_dir


def save_snapshot(snapshot: Snapshot) -> Path:
    """Persiste snapshot em JSON no workspace."""
    path = _snapshot_dir(snapshot.metadata.subject) / f"{snapshot.metadata.snapshot_id}.json"
    path.write_text(snapshot.model_dump_json(indent=2, ensure_ascii=False), encoding="utf-8")
    return path


def load_snapshot(snapshot_id: str, subject: SnapshotSubject | None = None) -> Snapshot:
    """Carrega snapshot por id (e subject opcional)."""
    if subject is not None:
        path = _snapshot_dir(subject) / f"{snapshot_id}.json"
        if not path.exists():
            raise FileNotFoundError(f"Snapshot not found: {snapshot_id}")
        data = path.read_text(encoding="utf-8")
        return Snapshot.model_validate_json(data)

    paths = ensure_workspace()
    for subject_dir in paths["snapshots"].iterdir():
        if not subject_dir.is_dir():
            continue
        candidate = subject_dir / f"{snapshot_id}.json"
        if candidate.exists():
            data = candidate.read_text(encoding="utf-8")
            return Snapshot.model_validate_json(data)

    raise FileNotFoundError(f"Snapshot not found: {snapshot_id}")


def list_snapshots(subject: SnapshotSubject) -> list[Path]:
    """Lista snapshots para um subject."""
    subject_dir = _snapshot_dir(subject)
    return sorted(subject_dir.glob("*.json"))


def save_diff(diff: Diff, format: str = "json", report: str | None = None) -> Path:
    """Persiste diff em JSON ou relatorio em Markdown/HTML."""
    diff_dir = _diff_dir(diff.subject)
    format_lower = format.lower()

    if format_lower == "json":
        path = diff_dir / f"{diff.diff_id}.json"
        path.write_text(diff.model_dump_json(indent=2, ensure_ascii=False), encoding="utf-8")
        return path

    if report is None:
        raise ValueError("Report content required for non-json formats")

    suffix = ".md" if format_lower == "markdown" else ".html"
    path = diff_dir / f"{diff.diff_id}{suffix}"
    path.write_text(report, encoding="utf-8")
    return path


def _iter_snapshot_files(subjects: Iterable[SnapshotSubject]) -> Iterable[Path]:
    for subject in subjects:
        for path in _snapshot_dir(subject).glob("*.json"):
            yield path


def prune_snapshots(
    *,
    subjects: list[SnapshotSubject],
    retention_days: int = 90,
    retention_tagged_days: int = 365,
) -> list[Path]:
    """Remove snapshots antigos conforme politica de retencao."""
    removed: list[Path] = []
    now = datetime.utcnow()

    for path in _iter_snapshot_files(subjects):
        try:
            data = path.read_text(encoding="utf-8")
            snapshot = Snapshot.model_validate_json(data)
        except Exception:
            continue

        tagged = bool(snapshot.metadata.tags)
        max_age = retention_tagged_days if tagged else retention_days
        cutoff = now - timedelta(days=max_age)
        mtime = datetime.utcfromtimestamp(path.stat().st_mtime)
        if mtime < cutoff:
            path.unlink(missing_ok=True)
            removed.append(path)

    return removed


def prune_diffs(
    *,
    subjects: list[SnapshotSubject],
    retention_days: int = 90,
) -> list[Path]:
    """Remove diffs antigos conforme politica de retencao."""
    removed: list[Path] = []
    now = datetime.utcnow()
    cutoff = now - timedelta(days=retention_days)

    for subject in subjects:
        for path in _diff_dir(subject).glob("*.*"):
            mtime = datetime.utcfromtimestamp(path.stat().st_mtime)
            if mtime < cutoff:
                path.unlink(missing_ok=True)
                removed.append(path)

    return removed
