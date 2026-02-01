# -*- coding: utf-8 -*-
"""
Logica de comparacao e renderizacao de diffs.
"""
from __future__ import annotations

from datetime import datetime
import html

from runtime.observability.snapshot.models import Diff, DiffItem, DiffSummary, Snapshot
from runtime.observability.snapshot.registry import ExtractorRegistry


def compare_snapshots(old: Snapshot, new: Snapshot) -> Diff:
    """Compara snapshots usando o extrator do dominio."""
    extractor = ExtractorRegistry.get(old.metadata.subject)
    return extractor.compare(old, new)


def render_diff(diff: Diff, format: str) -> str:
    """Renderiza diff em markdown ou html."""
    format_lower = format.lower()
    if format_lower == "markdown":
        return _render_markdown(diff)
    if format_lower == "html":
        return _render_html(diff)
    raise ValueError(f"Unsupported diff format: {format}")


def _render_markdown(diff: Diff) -> str:
    lines: list[str] = []
    lines.append(f"# Diff {diff.diff_id}")
    lines.append("")
    lines.append(f"**Gerado em:** {diff.timestamp.isoformat()}")
    lines.append("")
    summary = diff.summary
    lines.append("## Resumo")
    lines.append("")
    lines.append(f"- Arquivos adicionados: {summary.added_files}")
    lines.append(f"- Arquivos removidos: {summary.removed_files}")
    lines.append(f"- Arquivos modificados: {summary.modified_files}")
    lines.append(f"- Arquivos movidos: {summary.moved_files}")
    lines.append(f"- Diretorios adicionados: {summary.added_dirs}")
    lines.append(f"- Diretorios removidos: {summary.removed_dirs}")
    lines.append(f"- Delta de tamanho: {summary.size_delta}")
    lines.append("")
    lines.append("## Mudancas")
    lines.append("")
    for change in diff.changes:
        if change.type.value == "moved" and change.old_path:
            lines.append(f"- {change.type.value}: {change.old_path} -> {change.path}")
        else:
            lines.append(f"- {change.type.value}: {change.path}")
    lines.append("")
    return "\n".join(lines)


def _render_html(diff: Diff) -> str:
    summary = diff.summary
    rows = "".join(
        f"<li>{html.escape(change.type.value)}: {html.escape(change.old_path or '')} {html.escape(change.path)}</li>"
        for change in diff.changes
    )
    return f"""<!DOCTYPE html>
<html lang=\"pt-br\">
<head>
  <meta charset=\"utf-8\">
  <title>Diff {html.escape(diff.diff_id)}</title>
</head>
<body>
  <h1>Diff {html.escape(diff.diff_id)}</h1>
  <p><strong>Gerado em:</strong> {html.escape(diff.timestamp.isoformat())}</p>
  <h2>Resumo</h2>
  <ul>
    <li>Arquivos adicionados: {summary.added_files}</li>
    <li>Arquivos removidos: {summary.removed_files}</li>
    <li>Arquivos modificados: {summary.modified_files}</li>
    <li>Arquivos movidos: {summary.moved_files}</li>
    <li>Diretorios adicionados: {summary.added_dirs}</li>
    <li>Diretorios removidos: {summary.removed_dirs}</li>
    <li>Delta de tamanho: {summary.size_delta}</li>
  </ul>
  <h2>Mudancas</h2>
  <ul>
    {rows}
  </ul>
</body>
</html>"""
