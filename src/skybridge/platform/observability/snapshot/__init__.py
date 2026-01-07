# -*- coding: utf-8 -*-
"""
Snapshot Service - handlers e registro de extratores.
"""
from __future__ import annotations

from typing import Any

from skybridge.kernel import Result
from skybridge.kernel.registry.decorators import query
from skybridge.platform.observability.snapshot.capture import capture_snapshot
from skybridge.platform.observability.snapshot.diff import compare_snapshots, render_diff
from skybridge.platform.observability.snapshot.extractors.fileops_extractor import FileOpsExtractor
from skybridge.platform.observability.snapshot.extractors.health_extractor import HealthExtractor
from skybridge.platform.observability.snapshot.extractors.tasks_extractor import TasksExtractor
from skybridge.platform.observability.snapshot.models import SnapshotSubject
from skybridge.platform.observability.snapshot.registry import ExtractorRegistry
from skybridge.platform.observability.snapshot.storage import list_snapshots, load_snapshot, save_diff, save_snapshot


def register_default_extractors() -> None:
    """Registra extratores padrao do Snapshot Service."""
    ExtractorRegistry.register(FileOpsExtractor())
    ExtractorRegistry.register(TasksExtractor())
    ExtractorRegistry.register(HealthExtractor())


register_default_extractors()


def _normalize_tags(metadata: dict[str, Any] | None, tags: dict[str, Any] | None) -> dict[str, str]:
    result: dict[str, str] = {}
    if isinstance(metadata, dict):
        meta_tags = metadata.get("tags")
        if isinstance(meta_tags, dict):
            result.update({str(k): str(v) for k, v in meta_tags.items()})
        if metadata.get("tag"):
            result["tag"] = str(metadata.get("tag"))
        if metadata.get("description"):
            result["description"] = str(metadata.get("description"))
    if isinstance(tags, dict):
        result.update({str(k): str(v) for k, v in tags.items()})
    return result


@query(
    name="snapshot.capture",
    description="Captura snapshot estrutural de um dominio",
    tags=["snapshot", "observability"],
    input_schema={
        "type": "object",
        "properties": {
            "subject": {"type": "string"},
            "target": {"type": "string"},
            "depth": {"type": "integer"},
            "include_extensions": {"type": "array", "items": {"type": "string"}},
            "exclude_patterns": {"type": "array", "items": {"type": "string"}},
            "metadata": {"type": "object"},
            "tags": {"type": "object"},
        },
        "required": ["subject"],
    },
    output_schema={
        "type": "object",
        "properties": {
            "snapshot_id": {"type": "string"},
            "timestamp": {"type": "string"},
            "subject": {"type": "string"},
            "metadata": {"type": "object"},
            "stats": {"type": "object"},
            "structure": {"type": "object"},
            "storage_path": {"type": "string"},
        },
    },
)
def snapshot_capture(request: dict[str, Any]) -> Result[dict[str, Any], str]:
    """Handler RPC para captura de snapshot."""
    if not request:
        return Result.err("Request vazio")

    subject_value = request.get("subject") or request.get("detalhe")
    if not subject_value:
        return Result.err("subject is required")

    try:
        subject = SnapshotSubject(subject_value)
    except ValueError:
        return Result.err(f"Unsupported subject: {subject_value}")

    target = request.get("target") or request.get("path") or ""
    if subject == SnapshotSubject.FILEOPS and not target:
        return Result.err("target is required for fileops")
    if not target:
        target = "system"

    depth = int(request.get("depth") or 5)
    include_extensions = request.get("include_extensions")
    if isinstance(include_extensions, str):
        include_extensions = [include_extensions]
    exclude_patterns = request.get("exclude_patterns")
    if isinstance(exclude_patterns, str):
        exclude_patterns = [exclude_patterns]
    tags = _normalize_tags(request.get("metadata"), request.get("tags"))

    try:
        snapshot = capture_snapshot(
            subject=subject,
            target=str(target),
            depth=depth,
            include_extensions=include_extensions,
            exclude_patterns=exclude_patterns,
            tags=tags,
        )
        storage_path = save_snapshot(snapshot)
        result = snapshot.to_dict()
        result["snapshot_id"] = snapshot.metadata.snapshot_id
        result["timestamp"] = snapshot.metadata.timestamp.isoformat()
        result["subject"] = snapshot.metadata.subject.value
        result["storage_path"] = str(storage_path)
        return Result.ok(result)
    except Exception as exc:
        return Result.err(str(exc))


@query(
    name="snapshot.compare",
    description="Compara dois snapshots e retorna diff",
    tags=["snapshot", "observability"],
    input_schema={
        "type": "object",
        "properties": {
            "old_snapshot_id": {"type": "string"},
            "new_snapshot_id": {"type": "string"},
            "format": {"type": "string", "enum": ["json", "markdown", "html"]},
        },
        "required": ["old_snapshot_id", "new_snapshot_id"],
    },
    output_schema={
        "type": "object",
        "properties": {
            "diff_id": {"type": "string"},
            "timestamp": {"type": "string"},
            "summary": {"type": "object"},
            "changes": {"type": "array"},
            "report_path": {"type": "string"},
        },
    },
)
def snapshot_compare(request: dict[str, Any]) -> Result[dict[str, Any], str]:
    """Handler RPC para comparacao de snapshots."""
    if not request:
        return Result.err("Request vazio")

    old_id = request.get("old_snapshot_id")
    new_id = request.get("new_snapshot_id")
    if not old_id or not new_id:
        return Result.err("old_snapshot_id e new_snapshot_id sao obrigatorios")

    format_value = str(request.get("format") or "json").lower()
    if format_value not in {"json", "markdown", "html"}:
        return Result.err("format deve ser json, markdown ou html")

    try:
        old_snapshot = load_snapshot(old_id)
        new_snapshot = load_snapshot(new_id)
        if old_snapshot.metadata.subject != new_snapshot.metadata.subject:
            return Result.err("Snapshots precisam ser do mesmo subject")

        diff = compare_snapshots(old_snapshot, new_snapshot)
        report_content = render_diff(diff, format_value) if format_value != "json" else None
        report_path = save_diff(diff, format=format_value, report=report_content)

        result = diff.to_dict()
        result["report_path"] = str(report_path)
        return Result.ok(result)
    except Exception as exc:
        return Result.err(str(exc))


@query(
    name="snapshot.list",
    description="Lista snapshots disponiveis para um subject",
    tags=["snapshot", "observability"],
    input_schema={
        "type": "object",
        "properties": {
            "subject": {"type": "string", "enum": ["fileops", "tasks", "health"]},
        },
        "required": ["subject"],
    },
    output_schema={
        "type": "object",
        "properties": {
            "subject": {"type": "string"},
            "total": {"type": "integer"},
            "snapshots": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "snapshot_id": {"type": "string"},
                        "timestamp": {"type": "string"},
                        "target": {"type": "string"},
                        "tag": {"type": "string"},
                    },
                },
            },
        },
    },
)
def snapshot_list(request: dict[str, Any]) -> Result[dict[str, Any], str]:
    """Handler RPC para listar snapshots."""
    if not request:
        return Result.err("Request vazio")

    subject_value = request.get("subject") or request.get("detalhe")
    if not subject_value:
        return Result.err("subject is required")

    try:
        subject = SnapshotSubject(subject_value)
    except ValueError:
        return Result.err(f"Unsupported subject: {subject_value}")

    try:
        snapshot_paths = list_snapshots(subject)
        snapshots = []
        for path in snapshot_paths:
            try:
                data = path.read_text(encoding="utf-8")
                snapshot_obj = Snapshot.model_validate_json(data)
                snapshots.append({
                    "snapshot_id": snapshot_obj.metadata.snapshot_id,
                    "timestamp": snapshot_obj.metadata.timestamp.isoformat(),
                    "target": snapshot_obj.metadata.target,
                    "tag": snapshot_obj.metadata.tags.get("tag", ""),
                })
            except Exception:
                # Skip invalid snapshots
                continue

        # Sort by timestamp descending (newest first)
        snapshots.sort(key=lambda s: s["timestamp"], reverse=True)

        return Result.ok({
            "subject": subject_value,
            "total": len(snapshots),
            "snapshots": snapshots,
        })
    except Exception as exc:
        return Result.err(str(exc))
