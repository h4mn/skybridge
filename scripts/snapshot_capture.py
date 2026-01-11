#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Skybridge Snapshot Capture - Script reutilizável para capturar snapshots.

Uso:
    python scripts/snapshot_capture.py --target <path> --tag <tag>
    python scripts/snapshot_capture.py --compare <id1> <id2> --format markdown

Exemplos:
    # Capturar snapshot do diretório atual
    python scripts/snapshot_capture.py --target . --tag "worktree-atual"

    # Capturar snapshot de outro diretório
    python scripts/snapshot_capture.py --target ../skybridge --tag "main-branch"

    # Comparar dois snapshots
    python scripts/snapshot_capture.py --compare snap1 snap2 --format markdown

    # Listar snapshots disponíveis
    python scripts/snapshot_capture.py --list fileops
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from skybridge.platform.observability.snapshot import capture_snapshot
from skybridge.platform.observability.snapshot.storage import (
    save_snapshot,
    load_snapshot,
    list_snapshots,
)
from skybridge.platform.observability.snapshot.models import SnapshotSubject
from skybridge.platform.observability.snapshot.diff import compare_snapshots, render_diff
from skybridge.platform.observability.snapshot.storage import save_diff


def capture(target: str, tag: str = "", description: str = "", depth: int = 5) -> None:
    """Captura snapshot de um diretório."""
    tags = {}
    if tag:
        tags["tag"] = tag
    if description:
        tags["description"] = description

    snapshot = capture_snapshot(
        subject=SnapshotSubject.FILEOPS,
        target=target,
        depth=depth,
        tags=tags,
    )
    path = save_snapshot(snapshot)

    print(f"✅ Snapshot capturado com sucesso!")
    print(f"   ID:       {snapshot.metadata.snapshot_id}")
    print(f"   Tag:      {tag}")
    print(f"   Target:   {snapshot.metadata.target}")
    print(f"   Arquivo:  {path}")
    print(f"   Files:    {snapshot.stats.total_files}")
    print(f"   Size:     {snapshot.stats.total_size:,} bytes")
    print()
    print(f"Para comparar use: --compare <old_id> {snapshot.metadata.snapshot_id}")


def compare(old_id: str, new_id: str, format: str = "json") -> None:
    """Compara dois snapshots e gera relatório."""
    old_snapshot = load_snapshot(old_id)
    new_snapshot = load_snapshot(new_id)

    if old_snapshot.metadata.subject != new_snapshot.metadata.subject:
        print(f"❌ Erro: Snapshots de subjects diferentes")
        sys.exit(1)

    diff = compare_snapshots(old_snapshot, new_snapshot)
    report_content = render_diff(diff, format) if format != "json" else None
    report_path = save_diff(diff, format=format, report=report_content)

    print(f"✅ Comparação concluída!")
    print(f"   Diff ID:  {diff.diff_id}")
    print(f"   Old:      {old_snapshot.metadata.snapshot_id[:8]} ({old_snapshot.metadata.tags.get('tag', 'no-tag')})")
    print(f"   New:      {new_snapshot.metadata.snapshot_id[:8]} ({new_snapshot.metadata.tags.get('tag', 'no-tag')})")
    print(f"   Format:   {format}")
    print(f"   Relatório: {report_path}")
    print()
    print(f"📊 Resumo:")
    print(f"   Adicionados:  {diff.stats.added}")
    print(f"   Removidos:    {diff.stats.removed}")
    print(f"   Modificados:  {diff.stats.modified}")
    print(f"   Movidos:      {diff.stats.moved}")


def list_snap(subject: str) -> None:
    """Lista snapshots disponíveis."""
    try:
        subj = SnapshotSubject(subject)
    except ValueError:
        print(f"❌ Erro: Subject inválido: {subject}")
        print(f"   Subjects disponíveis: fileops, tasks, health")
        sys.exit(1)

    snapshot_paths = list_snapshots(subj)
    snapshots = []

    for path in snapshot_paths:
        try:
            data = path.read_text(encoding="utf-8")
            from skybridge.platform.observability.snapshot.models import Snapshot
            snapshot_obj = Snapshot.model_validate_json(data)
            snapshots.append({
                "id": snapshot_obj.metadata.snapshot_id[:8],
                "full_id": snapshot_obj.metadata.snapshot_id,
                "timestamp": snapshot_obj.metadata.timestamp.isoformat(),
                "target": snapshot_obj.metadata.target,
                "tag": snapshot_obj.metadata.tags.get("tag", ""),
                "files": snapshot_obj.stats.total_files,
                "size": snapshot_obj.stats.total_size,
            })
        except Exception:
            continue

    # Sort by timestamp descending (newest first)
    snapshots.sort(key=lambda s: s["timestamp"], reverse=True)

    print(f"📋 Snapshots disponíveis para '{subject}': {len(snapshots)}")
    print()
    if snapshots:
        print(f"{'ID':<10} {'Tag':<20} {'Target':<30} {'Files':<8} {'Size':<12} {'Timestamp'}")
        print("-" * 100)
        for s in snapshots:
            tag = s["tag"][:20] if s["tag"] else "-"
            target = s["target"][:30] if s["target"] else "-"
            print(f"{s['id']:<10} {tag:<20} {target:<30} {s['files']:<8} {s['size']:<12,} {s['timestamp']}")
    else:
        print("   Nenhum snapshot encontrado.")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Skybridge Snapshot Capture - Script reutilizável",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("--capture", action="store_true", help="Capturar snapshot")
    parser.add_argument("--target", type=str, help="Diretório alvo (padrão: .)")
    parser.add_argument("--tag", type=str, default="", help="Tag para identificar o snapshot")
    parser.add_argument("--description", type=str, default="", help="Descrição do snapshot")
    parser.add_argument("--depth", type=int, default=5, help="Profundidade de扫描 (padrão: 5)")
    parser.add_argument("--compare", nargs=2, metavar=("OLD", "NEW"), help="Comparar dois snapshots")
    parser.add_argument("--format", type=str, default="json", choices=["json", "markdown", "html"],
                        help="Formato do relatório de comparação")
    parser.add_argument("--list", type=str, metavar="SUBJECT", help="Listar snapshots disponíveis")

    args = parser.parse_args()

    # List snapshots
    if args.list:
        list_snap(args.list)
        return

    # Compare snapshots
    if args.compare:
        compare(args.compare[0], args.compare[1], args.format)
        return

    # Capture snapshot (default or explicit)
    target = args.target or "."
    capture(target, args.tag, args.description, args.depth)


if __name__ == "__main__":
    main()
