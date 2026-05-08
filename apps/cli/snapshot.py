# -*- coding: utf-8 -*-
"""
CLI Snapshot — Comandos para o Snapshot Service.

DOC: docs/spec/SPEC007-Snapshot-Service.md
DOC: docs/adr/ADR015-adotar-snapshot-como-serviço-plataforma.md

Comandos disponíveis:
- sb snapshot capture     Captura snapshot estrutural
- sb snapshot compare     Compara dois snapshots
- sb snapshot list        Lista snapshots disponíveis
- sb snapshot show        Mostra detalhes de um snapshot
- sb snapshot prune       Remove snapshots antigos
"""

import asyncio
import sys
from datetime import datetime
from pathlib import Path
from typing import Optional

import typer
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.text import Text
from rich.json import JSON
from rich.tree import Tree

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

# Carrega .env
from dotenv import load_dotenv
load_dotenv()

from runtime.observability.snapshot.capture import capture_snapshot
from runtime.observability.snapshot.diff import compare_snapshots, render_diff
from runtime.observability.snapshot.models import SnapshotSubject
from runtime.observability.snapshot.storage import (
    load_snapshot,
    list_snapshots,
    prune_snapshots,
    prune_diffs,
)
from kernel import Result

console = Console()

snapshot_app = typer.Typer(
    name="snapshot",
    help="Comandos para o Snapshot Service",
)


@snapshot_app.callback(invoke_without_command=True)
def snapshot_callback(ctx: typer.Context):
    """Mostra ajuda quando nenhum subcomando é fornecido."""
    if ctx.invoked_subcommand is None:
        show_snapshot_menu()


def show_snapshot_menu():
    """Mostra menu de ajuda do snapshot quando nenhum comando é fornecido."""
    help_text = Text()
    help_text.append("Comandos disponíveis:\n\n", style="bold cyan")
    help_text.append("  sb snapshot capture <subject>      Captura snapshot estrutural\n", style="white")
    help_text.append("  sb snapshot compare <old> <new>    Compara dois snapshots\n", style="white")
    help_text.append("  sb snapshot list <subject>         Lista snapshots disponíveis\n", style="white")
    help_text.append("  sb snapshot show <id>              Mostra detalhes de um snapshot\n", style="white")
    help_text.append("  sb snapshot prune <subject>        Remove snapshots antigos\n", style="white")
    help_text.append("\nSubjects disponíveis:\n", style="bold white")
    help_text.append("  fileops                           Estruturas de arquivos\n", style="dim")
    help_text.append("  trello                            Estado do Trello\n", style="dim")
    help_text.append("  kanban                            Kanban.db\n", style="dim")
    help_text.append("  health                            Health checks\n", style="dim")
    help_text.append("  tasks                             Tasks do sistema\n", style="dim")
    help_text.append("\nExemplos:\n", style="bold white")
    help_text.append("  sb snapshot capture fileops --target . --depth 5\n", style="dim")
    help_text.append("  sb snapshot compare snap_old snap_new --format markdown\n", style="dim")
    help_text.append("  sb snapshot list fileops\n", style="dim")
    help_text.append("  sb snapshot prune fileops --retention 30\n", style="dim")

    console.print()
    console.print(Panel(help_text, title="[bold cyan]Snapshot Commands (sb snapshot)[/bold cyan]", border_style="bright_blue"))
    console.print()


@snapshot_app.command("capture")
def snapshot_capture(
    subject: str = typer.Argument(..., help="Subject: fileops, trello, kanban, health, tasks"),
    target: str = typer.Option(".", "--target", "-t", help="Alvo a ser capturado (padrão: .)"),
    depth: int = typer.Option(5, "--depth", "-d", help="Profundidade da captura (padrão: 5)"),
    include_extensions: Optional[str] = typer.Option(None, "--include", "-i", help="Extensões para incluir (sep. por vírgula)"),
    exclude_patterns: Optional[str] = typer.Option(None, "--exclude", "-e", help="Padrões para excluir (sep. por vírgula)"),
    tag: Optional[str] = typer.Option(None, "--tag", help="Tag para identificar o snapshot"),
    save: bool = typer.Option(True, "--save/--no-save", help="Persistir snapshot no workspace"),
):
    """
    Captura snapshot estrutural de um domínio.

    Exemplos:
        sb snapshot capture fileops --target . --depth 5
        sb snapshot capture fileops --target src --include .py,.md
        sb snapshot capture trello --tag "baseline"
    """
    try:
        subject_value = SnapshotSubject(subject)
    except ValueError:
        console.print(f"[red]❌ Subject inválido: {subject}[/red]")
        console.print("[dim]Subjects disponíveis: fileops, trello, kanban, health, tasks[/dim]")
        raise typer.Exit(1)

    # Processa extensões
    include_exts = None
    if include_extensions:
        include_exts = [ext.strip() for ext in include_extensions.split(",")]

    # Processa padrões de exclusão
    exclude_pats = None
    if exclude_patterns:
        exclude_pats = [pat.strip() for pat in exclude_patterns.split(",")]

    # Prepara tags
    tags = {}
    if tag:
        tags["tag"] = tag

    console.print(f"[dim]Capturando snapshot {subject_value.value}...[/dim]")
    console.print(f"[dim]Target:[/dim] {target}")
    console.print(f"[dim]Depth:[/dim] {depth}")

    try:
        snapshot = capture_snapshot(
            subject=subject_value,
            target=target,
            depth=depth,
            include_extensions=include_exts,
            exclude_patterns=exclude_pats,
            tags=tags,
        )

        # Salva se solicitado
        if save:
            from runtime.observability.snapshot.storage import save_snapshot
            path = save_snapshot(snapshot)
            console.print(f"[green]✓ Snapshot salvo:[/green] {path}")

        # Exibe resumo
        console.print()
        console.print(f"[cyan]Snapshot ID:[/cyan] {snapshot.metadata.snapshot_id}")
        console.print(f"[cyan]Timestamp:[/cyan] {snapshot.metadata.timestamp.isoformat()}")
        console.print(f"[cyan]Subject:[/cyan] {snapshot.metadata.subject.value}")
        console.print(f"[cyan]Target:[/cyan] {snapshot.metadata.target}")
        console.print()
        console.print("[bold]Estatísticas:[/bold]")
        console.print(f"  Files: {snapshot.stats.total_files}")
        console.print(f"  Dirs: {snapshot.stats.total_dirs}")
        console.print(f"  Size: {snapshot.stats.total_size:,} bytes")
        if snapshot.stats.file_types:
            console.print(f"  Types: {', '.join(f'{k}:{v}' for k, v in snapshot.stats.file_types.items())}")

    except Exception as e:
        console.print(f"[red]❌ Erro ao capturar snapshot:[/red] {e}")
        raise typer.Exit(1)


@snapshot_app.command("compare")
def snapshot_compare(
    old_id: str = typer.Argument(..., help="ID do snapshot antigo"),
    new_id: str = typer.Argument(..., help="ID do snapshot novo"),
    format: str = typer.Option("json", "--format", "-f", help="Formato: json, markdown, html"),
):
    """
    Compara dois snapshots e gera diff.

    Exemplos:
        sb snapshot compare snap_old snap_new
        sb snapshot compare snap_old snap_new --format markdown
    """
    if format not in ("json", "markdown", "html"):
        console.print(f"[red]❌ Formato inválido: {format}[/red]")
        console.print("[dim]Formatos disponíveis: json, markdown, html[/dim]")
        raise typer.Exit(1)

    console.print(f"[dim]Comparando snapshots...[/dim]")
    console.print(f"[dim]Old:[/dim] {old_id}")
    console.print(f"[dim]New:[/dim] {new_id}")

    try:
        old_snapshot = load_snapshot(old_id)
        new_snapshot = load_snapshot(new_id)

        if old_snapshot.metadata.subject != new_snapshot.metadata.subject:
            console.print(f"[red]❌ Snapshots de subjects diferentes:[/red]")
            console.print(f"  Old: {old_snapshot.metadata.subject.value}")
            console.print(f"  New: {new_snapshot.metadata.subject.value}")
            raise typer.Exit(1)

        diff = compare_snapshots(old_snapshot, new_snapshot)

        # Salva diff
        from runtime.observability.snapshot.storage import save_diff
        report_content = None
        if format != "json":
            report_content = render_diff(diff, format)

        path = save_diff(diff, format=format, report=report_content)
        console.print(f"[green]✓ Diff salvo:[/green] {path}")

        # Exibe resumo
        console.print()
        console.print(f"[cyan]Diff ID:[/cyan] {diff.diff_id}")
        console.print(f"[cyan]Subject:[/cyan] {diff.subject.value}")
        console.print()
        console.print("[bold]Resumo:[/bold]")
        console.print(f"  Added: +{diff.summary.added_files} files, +{diff.summary.added_dirs} dirs")
        console.print(f"  Removed: -{diff.summary.removed_files} files, -{diff.summary.removed_dirs} dirs")
        console.print(f"  Modified: ~{diff.summary.modified_files} files")
        console.print(f"  Moved: ↝{diff.summary.moved_files} files")
        console.print(f"  Size delta: {diff.summary.size_delta:+,} bytes")

        if format == "json":
            console.print()
            import json
            console.print(Panel(JSON(json.dumps(diff.to_dict(), indent=2, ensure_ascii=False)), title="[bold cyan]Changes[/bold cyan]", border_style="bright_blue"))

    except FileNotFoundError as e:
        console.print(f"[red]❌ Snapshot não encontrado:[/red] {e}")
        raise typer.Exit(1)
    except Exception as e:
        console.print(f"[red]❌ Erro ao comparar snapshots:[/red] {e}")
        raise typer.Exit(1)


@snapshot_app.command("list")
def snapshot_list(
    subject: str = typer.Argument(..., help="Subject: fileops, trello, kanban, health, tasks"),
    limit: int = typer.Option(20, "--limit", "-l", help="Número máximo de snapshots (padrão: 20)"),
):
    """
    Lista snapshots disponíveis para um subject.

    Exemplos:
        sb snapshot list fileops
        sb snapshot list trello --limit 10
    """
    try:
        subject_value = SnapshotSubject(subject)
    except ValueError:
        console.print(f"[red]❌ Subject inválido: {subject}[/red]")
        console.print("[dim]Subjects disponíveis: fileops, trello, kanban, health, tasks[/dim]")
        raise typer.Exit(1)

    try:
        snapshot_paths = list_snapshots(subject_value)

        if not snapshot_paths:
            console.print(f"[dim]Nenhum snapshot encontrado para subject: {subject}[/dim]")
            return

        # Carrega snapshots
        from runtime.observability.snapshot.models import Snapshot
        snapshots = []
        for path in snapshot_paths[:limit]:
            try:
                data = path.read_text(encoding="utf-8")
                snapshot = Snapshot.model_validate_json(data)
                snapshots.append(snapshot)
            except Exception:
                continue

        # Ordena por timestamp (mais recente primeiro)
        snapshots.sort(key=lambda s: s.metadata.timestamp, reverse=True)

        # Cria tabela
        table = Table(title=f"Snapshots: {subject_value.value}")
        table.add_column("ID", style="cyan")
        table.add_column("Timestamp", style="green")
        table.add_column("Target", style="white")
        table.add_column("Tag", style="yellow")
        table.add_column("Files", style="dim")
        table.add_column("Size", style="dim")

        for snap in snapshots:
            tag = snap.metadata.tags.get("tag", "")
            table.add_row(
                snap.metadata.snapshot_id[:40] + "...",
                snap.metadata.timestamp.strftime("%Y-%m-%d %H:%M:%S"),
                snap.metadata.target[:30],
                tag,
                str(snap.stats.total_files),
                f"{snap.stats.total_size:,}",
            )

        console.print()
        console.print(table)
        console.print(f"\n[dim]Total: {len(snapshots)} snapshots[/dim]")

    except Exception as e:
        console.print(f"[red]❌ Erro ao listar snapshots:[/red] {e}")
        raise typer.Exit(1)


@snapshot_app.command("show")
def snapshot_show(
    snapshot_id: str = typer.Argument(..., help="ID do snapshot"),
    subject: Optional[str] = typer.Option(None, "--subject", "-s", help="Subject do snapshot (opcional)"),
):
    """
    Mostra detalhes de um snapshot específico.

    Exemplos:
        sb snapshot show snap_20260406_032524_a3f9b1e2
        sb snapshot show snap_20260406_032524_a3f9b1e2 --subject fileops
    """
    try:
        snapshot = load_snapshot(snapshot_id)

        # Cria árvore de estrutura
        console.print()
        console.print(f"[cyan]Snapshot ID:[/cyan] {snapshot.metadata.snapshot_id}")
        console.print(f"[cyan]Timestamp:[/cyan] {snapshot.metadata.timestamp.isoformat()}")
        console.print(f"[cyan]Subject:[/cyan] {snapshot.metadata.subject.value}")
        console.print(f"[cyan]Target:[/cyan] {snapshot.metadata.target}")
        console.print(f"[cyan]Depth:[/cyan] {snapshot.metadata.depth}")
        console.print()

        # Git info
        if snapshot.metadata.git_hash:
            console.print(f"[dim]Git:[/dim] {snapshot.metadata.git_hash} ({snapshot.metadata.git_branch or 'unknown'})")
            console.print()

        # Tags
        if snapshot.metadata.tags:
            console.print("[bold]Tags:[/bold]")
            for k, v in snapshot.metadata.tags.items():
                console.print(f"  {k}: {v}")
            console.print()

        # Estatísticas
        console.print("[bold]Estatísticas:[/bold]")
        console.print(f"  Files: {snapshot.stats.total_files}")
        console.print(f"  Dirs: {snapshot.stats.total_dirs}")
        console.print(f"  Size: {snapshot.stats.total_size:,} bytes ({snapshot.stats.total_size / 1024 / 1024:.2f} MB)")
        if snapshot.stats.file_types:
            console.print(f"  Types:")
            for ext, count in sorted(snapshot.stats.file_types.items(), key=lambda x: -x[1])[:10]:
                console.print(f"    {ext}: {count}")
        console.print()

        # Estrutura em árvore (apenas para fileops)
        if snapshot.metadata.subject == SnapshotSubject.FILEOPS and snapshot.structure:
            tree = Tree(f"[bold]{snapshot.metadata.target}[/bold]")
            _build_tree(tree, snapshot.structure)
            console.print(tree)

    except FileNotFoundError:
        console.print(f"[red]❌ Snapshot não encontrado: {snapshot_id}[/red]")
        raise typer.Exit(1)
    except Exception as e:
        console.print(f"[red]❌ Erro ao mostrar snapshot:[/red] {e}")
        raise typer.Exit(1)


def _build_tree(tree: Tree, node: dict, max_depth: int = 3, current_depth: int = 0) -> None:
    """Constrói árvore Rich para exibição."""
    if current_depth >= max_depth:
        return

    for child in node.get("children", []):
        if child.get("type") == "dir":
            branch = tree.add(f"[cyan]📁 {child['name']}[/cyan]")
            _build_tree(branch, child, max_depth, current_depth + 1)
        else:
            icon = _get_file_icon(child.get("file_type", "file"))
            size = child.get("size", 0)
            size_str = f" ({size:,} B)" if size > 0 else ""
            branch = tree.add(f"[dim]{icon} {child['name']}{size_str}[/dim]")


def _get_file_icon(file_type: str) -> str:
    icons = {
        "code": "🐍",
        "text": "📄",
        "config": "⚙️",
        "image": "🖼️",
        "file": "📎",
    }
    return icons.get(file_type, "📎")


@snapshot_app.command("prune")
def snapshot_prune(
    subject: str = typer.Argument(..., help="Subject: fileops, trello, kanban, health, tasks"),
    retention: int = typer.Option(90, "--retention", "-r", help="Dias de retenção (padrão: 90)"),
    retention_tagged: int = typer.Option(365, "--retention-tagged", help="Dias para tagged (padrão: 365)"),
    diffs: bool = typer.Option(True, "--diffs/--no-diffs", help="Remover diffs também"),
    dry_run: bool = typer.Option(False, "--dry-run", help="Apenas simular, não remover"),
):
    """
    Remove snapshots antigos conforme política de retenção.

    Snapshots com tags têm retenção mais longa.

    Exemplos:
        sb snapshot prune fileops --retention 30
        sb snapshot prune fileops --dry-run
        sb snapshot prune trello --retention 30 --no-diffs
    """
    try:
        subject_value = SnapshotSubject(subject)
    except ValueError:
        console.print(f"[red]❌ Subject inválido: {subject}[/red]")
        console.print("[dim]Subjects disponíveis: fileops, trello, kanban, health, tasks[/dim]")
        raise typer.Exit(1)

    console.print(f"[dim]Pruning snapshots de {subject_value.value}...[/dim]")
    console.print(f"[dim]Retenção:[/dim] {retention} dias (tagged: {retention_tagged} dias)")

    if dry_run:
        console.print("[yellow]⚠️  DRY RUN - nenhum arquivo será removido[/yellow]")

    try:
        removed_snapshots = prune_snapshots(
            subjects=[subject_value],
            retention_days=retention,
            retention_tagged_days=retention_tagged,
        )

        removed_diffs_files = []
        if diffs:
            removed_diffs_files = prune_diffs(
                subjects=[subject_value],
                retention_days=retention,
            )

        if dry_run:
            console.print(f"\n[cyan]Snapshots que seriam removidos:[/cyan] {len(removed_snapshots)}")
            if diffs:
                console.print(f"[cyan]Diffs que seriam removidos:[/cyan] {len(removed_diffs_files)}")
        else:
            console.print(f"\n[green]✓ Snapshots removidos:[/green] {len(removed_snapshots)}")
            if diffs:
                console.print(f"[green]✓ Diffs removidos:[/green] {len(removed_diffs_files)}")

        if not dry_run and removed_snapshots:
            console.print()
            console.print("[dim]Arquivos removidos:[/dim]")
            for path in removed_snapshots[:10]:
                console.print(f"  {path}")
            if len(removed_snapshots) > 10:
                console.print(f"  ... e mais {len(removed_snapshots) - 10}")

    except Exception as e:
        console.print(f"[red]❌ Erro ao fazer prune:[/red] {e}")
        raise typer.Exit(1)
