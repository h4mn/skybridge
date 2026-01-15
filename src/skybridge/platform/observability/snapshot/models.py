# -*- coding: utf-8 -*-
"""
Modelos Pydantic do Snapshot Service.
"""
from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Any, Dict, Optional

from pydantic import BaseModel, Field


class SnapshotSubject(str, Enum):
    """Dominios observaveis."""

    FILEOPS = "fileops"
    TASKS = "tasks"
    HEALTH = "health"
    CUSTOM = "custom"


class SnapshotMetadata(BaseModel):
    """Metadados do snapshot."""

    snapshot_id: str = Field(..., description="ID unico do snapshot")
    timestamp: datetime = Field(..., description="Momento da captura")
    subject: SnapshotSubject = Field(..., description="Dominio observado")
    target: str = Field(..., description="Alvo observado")
    depth: int = Field(default=5, description="Profundidade da captura")
    git_hash: Optional[str] = Field(None, description="Hash do commit Git")
    git_branch: Optional[str] = Field(None, description="Branch Git")
    tags: Dict[str, str] = Field(default_factory=dict, description="Tags customizadas")


class SnapshotStats(BaseModel):
    """Estatisticas agregadas."""

    total_files: int
    total_dirs: int
    total_size: int
    file_types: Dict[str, int] = Field(default_factory=dict)


class Snapshot(BaseModel):
    """Snapshot completo."""

    metadata: SnapshotMetadata
    stats: SnapshotStats
    structure: Dict[str, Any] = Field(default_factory=dict)
    files: list[Dict[str, Any]] = Field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return self.model_dump(mode="json")


class DiffChange(str, Enum):
    """Tipos de mudanca."""

    ADDED = "added"
    REMOVED = "removed"
    MODIFIED = "modified"
    MOVED = "moved"


class DiffItem(BaseModel):
    """Item individual do diff."""

    type: DiffChange
    path: str
    old_path: Optional[str] = None
    size_delta: Optional[int] = None


class DiffSummary(BaseModel):
    """Resumo do diff."""

    added_files: int
    removed_files: int
    modified_files: int
    moved_files: int
    added_dirs: int
    removed_dirs: int
    size_delta: int


class Diff(BaseModel):
    """Diff completo entre dois snapshots."""

    diff_id: str
    timestamp: datetime
    old_snapshot_id: str
    new_snapshot_id: str
    subject: SnapshotSubject
    summary: DiffSummary
    changes: list[DiffItem]

    def to_dict(self) -> dict[str, Any]:
        return self.model_dump(mode="json")
