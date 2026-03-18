# -*- coding: utf-8 -*-
"""
Extrator simples para dominio de tarefas.
"""
from __future__ import annotations

from datetime import datetime

from runtime.observability.snapshot.capture import generate_snapshot_id
from runtime.observability.snapshot.extractors.base import StateExtractor
from runtime.observability.snapshot.models import Snapshot, SnapshotMetadata, SnapshotStats, SnapshotSubject, Diff, DiffItem, DiffSummary, DiffChange


class TasksExtractor(StateExtractor):
    """Extrator basico para dominio de tarefas."""

    @property
    def subject(self) -> SnapshotSubject:
        return SnapshotSubject.TASKS

    def capture(
        self,
        target: str,
        depth: int = 1,
        include_extensions: list[str] | None = None,
        exclude_patterns: list[str] | None = None,
        **options,
    ) -> Snapshot:
        tags = options.get("tags", {})
        snapshot_id = generate_snapshot_id(self.subject, target)
        timestamp = datetime.utcnow()

        metadata = SnapshotMetadata(
            snapshot_id=snapshot_id,
            timestamp=timestamp,
            subject=self.subject,
            target=target,
            depth=depth,
            tags=tags,
        )
        stats = SnapshotStats(total_files=0, total_dirs=0, total_size=0)
        structure = {"tasks": []}
        return Snapshot(metadata=metadata, stats=stats, structure=structure, files=[])

    def compare(self, old: Snapshot, new: Snapshot) -> Diff:
        changed = old.structure != new.structure
        summary = DiffSummary(
            added_files=0,
            removed_files=0,
            modified_files=1 if changed else 0,
            moved_files=0,
            added_dirs=0,
            removed_dirs=0,
            size_delta=0,
        )
        changes: list[DiffItem] = []
        if changed:
            changes.append(DiffItem(type=DiffChange.MODIFIED, path="tasks"))

        diff_id = generate_snapshot_id(self.subject, f"{old.metadata.snapshot_id}:{new.metadata.snapshot_id}").replace("snap_", "diff_")
        return Diff(
            diff_id=diff_id,
            timestamp=datetime.utcnow(),
            old_snapshot_id=old.metadata.snapshot_id,
            new_snapshot_id=new.metadata.snapshot_id,
            subject=self.subject,
            summary=summary,
            changes=changes,
        )
