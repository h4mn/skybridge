# -*- coding: utf-8 -*-
"""
CLI Kanban — Comandos para gerenciar e visualizar o Kanban.

DOC: apps/cli/kanban.py
DOC: PRD024 - Kanban Cards Vivos
DOC: PRD026 - Integração Kanban com Fluxo Real

Comandos disponíveis:
- sb kanban snapshot    Estado completo: Kanban.db + Trello
- sb kanban diff        Comparação/diff: Kanban.db vs Trello
- sb kanban sync        Sincroniza Trello → kanban.db
"""

import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Optional

import typer
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.text import Text
from rich.columns import Columns

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

# Carrega .env
from dotenv import load_dotenv
load_dotenv()

from runtime.config.config import get_config

console = Console()

kanban_app = typer.Typer(
    name="kanban",
    help="Comandos para gerenciar o Kanban",
)


@kanban_app.callback(invoke_without_command=True)
def kanban_callback(ctx: typer.Context):
    """Mostra ajuda quando nenhum subcomando é fornecido."""
    if ctx.invoked_subcommand is None:
        show_kanban_menu()


def show_kanban_menu():
    """Mostra menu de ajuda do kanban quando nenhum comando é fornecido."""
    help_text = Text()
    help_text.append("Comandos disponíveis:\n\n", style="bold cyan")
    help_text.append("  sb kanban snapshot             Estado completo: Kanban.db + Trello\n", style="white")
    help_text.append("  sb kanban diff                 Comparação/diff: Kanban.db vs Trello\n", style="white")
    help_text.append("  sb kanban sync                 Sincroniza Trello → kanban.db\n", style="white")
    help_text.append("  sb kanban webhooks             Gerencia webhooks do Trello\n", style="white")
    help_text.append("\nExemplos:\n", style="bold white")
    help_text.append("  sb kanban snapshot              Ver estado completo\n", style="dim")
    help_text.append("  sb kanban diff                  Ver dessincronizações\n", style="dim")
    help_text.append("  sb kanban webhooks list         Listar webhooks\n", style="dim")
    help_text.append("  sb kanban webhooks setup --url  Configurar webhook\n", style="dim")

    console.print()
    console.print(Panel(help_text, title="[bold cyan]Kanban Commands (sb kanban)[/bold cyan]", border_style="bright_blue"))
    console.print()


@kanban_app.command("snapshot")
def kanban_snapshot(
    workspace: Optional[str] = typer.Option(None, "--workspace", "-w", help="ID do workspace (padrão: core)"),
):
    """
    Mostra estado completo: Kanban.db + Trello.

    Exibe todos os listas e cards de ambos os sistemas,
    permitindo visualizar o estado atual completo.
    """
    from runtime.observability.snapshot.extractors.trello_extractor import TrelloExtractor
    from rich.columns import Columns
    from rich.align import Align

    workspace_id = workspace or "core"
    db_path = f"workspace/{workspace_id}/data/kanban.db"
    board_id = os.getenv("TRELLO_BOARD_ID", "")

    if not board_id:
        console.print("[red]❌ TRELLO_BOARD_ID não configurado[/red]")
        raise typer.Exit(1)

    api_key = os.getenv("TRELLO_API_KEY", "")
    api_token = os.getenv("TRELLO_API_TOKEN", "")

    if not api_key or not api_token:
        console.print("[red]❌ Credenciais Trello não configuradas[/red]")
        raise typer.Exit(1)

    # Captura snapshot unificado
    extractor = TrelloExtractor(api_key, api_token)
    snapshot = extractor.capture(
        target=board_id,
        depth=3,
        kanban_db=db_path,
        tags={"workspace_id": workspace_id}
    )

    # Verifica erros
    if snapshot.metadata.tags.get("error"):
        console.print(f"[red]❌ ERRO:[/red] {snapshot.metadata.tags['error']}")
        raise typer.Exit(1)

    trello_data = snapshot.structure.get("trello", {})
    kanban_data = snapshot.structure.get("kanban", {})

    # ===== CONTEÚDO KANBAN.DB =====
    from rich.console import Group
    from rich.rule import Rule

    kanban_parts = []

    # Estatísticas
    k_stats = Table.grid(padding=(0, 1), expand=True)
    k_stats.add_column(justify="right", style="dim")
    k_stats.add_column(justify="left")
    k_stats.add_row("[cyan]Listas:[/cyan]", str(kanban_data.get('total_lists', 0)))
    k_stats.add_row("[cyan]Cards:[/cyan]", str(kanban_data.get('total_cards', 0)))
    k_stats.add_row("[cyan]Histórico:[/cyan]", f"{len(kanban_data.get('history', []))} regs")
    kanban_parts.append(k_stats)
    kanban_parts.append(Rule(style="cyan"))

    # Listas
    k_lists_table = Table(show_header=True, header_style="bold cyan", box=None, expand=True)
    k_lists_table.add_column("📋 Listas", style="white", width=15)
    k_lists_table.add_column("Pos", style="dim", width=4)
    k_lists_table.add_column("ID Trello", style="dim", width=18)

    for lst in kanban_data.get("lists", []):
        trello_id = lst.get("trello_list_id") or "[red]None[/red]"
        trello_short = str(trello_id)[:15] + "..." if len(str(trello_id)) > 15 else str(trello_id)
        k_lists_table.add_row(lst["name"], str(lst["position"]), trello_short)

    kanban_parts.append(k_lists_table)
    kanban_parts.append(Rule(style="cyan"))

    # Cards
    if kanban_data.get("cards"):
        k_cards_table = Table(show_header=True, header_style="bold cyan", box=None, expand=True)
        k_cards_table.add_column("📝 Cards", style="white", width=28)
        k_cards_table.add_column("Lista", style="cyan", width=12)
        k_cards_table.add_column("🤖", style="yellow", width=3)

        for card in kanban_data["cards"][:10]:
            vivo = "✓" if card.get("being_processed") else ""
            k_cards_table.add_row(
                card["title"][:25],
                card.get("list_name", "?")[:10],
                vivo
            )
        kanban_parts.append(k_cards_table)
        kanban_parts.append(Rule(style="cyan"))

    # Comentários/Histórico
    if kanban_data.get("history"):
        k_hist_table = Table(show_header=True, header_style="bold cyan", box=None, expand=True)
        k_hist_table.add_column("💬 Histórico", style="white", width=12)
        k_hist_table.add_column("De", style="dim", width=8)
        k_hist_table.add_column("Para", style="dim", width=8)
        k_hist_table.add_column("Data", style="dim", width=16)

        for h in kanban_data["history"][:8]:
            k_hist_table.add_row(
                h.get("event", "?")[:10],
                str(h.get("from_list_id", ""))[:6],
                str(h.get("to_list_id", ""))[:6],
                (h.get("created_at", "") or "")[:16]
            )
        kanban_parts.append(k_hist_table)

    kanban_panel = Panel(
        Group(*kanban_parts),
        title="[bold white on cyan]  📊 KANBAN.DB  [/bold white on cyan]",
        title_align="center",
        border_style="cyan",
        padding=(0, 1),
    )

    # ===== CONTEÚDO TRELLO =====
    trello_parts = []

    # Estatísticas
    t_stats = Table.grid(padding=(0, 1), expand=True)
    t_stats.add_column(justify="right", style="dim")
    t_stats.add_column(justify="left")
    t_stats.add_row("[green]Listas:[/green]", str(trello_data.get('total_lists', 0)))
    t_stats.add_row("[green]Cards:[/green]", str(trello_data.get('total_cards', 0)))
    trello_parts.append(t_stats)
    trello_parts.append(Rule(style="green"))

    # Listas
    t_lists_table = Table(show_header=True, header_style="bold green", box=None, expand=True)
    t_lists_table.add_column("📋 Listas", style="white", width=25)

    for lst in trello_data.get("lists", []):
        t_lists_table.add_row(lst["name"])

    trello_parts.append(t_lists_table)
    trello_parts.append(Rule(style="green"))

    # Cards
    if trello_data.get("cards"):
        t_cards_table = Table(show_header=True, header_style="bold green", box=None, expand=True)
        t_cards_table.add_column("📝 Cards", style="white", width=28)
        t_cards_table.add_column("Lista", style="green", width=15)
        t_cards_table.add_column("🔒", style="red", width=3)

        for card in trello_data["cards"][:10]:
            closed = "✓" if card.get("closed") else ""
            t_cards_table.add_row(
                card["name"][:25],
                card.get("list_name", "?")[:12],
                closed
            )
        trello_parts.append(t_cards_table)
        trello_parts.append(Rule(style="green"))

    # Comentários (actions do Trello)
    t_comm_table = Table(show_header=True, header_style="bold green", box=None, expand=True)
    t_comm_table.add_column("💬 Comentários", style="dim", width=40)
    t_comm_table.add_row("Requerem query adicional (/cards/{id}/actions)")
    trello_parts.append(t_comm_table)

    trello_panel = Panel(
        Group(*trello_parts),
        title="[bold white on green]  🌐 TRELLO  [/bold white on green]",
        title_align="center",
        border_style="green",
        padding=(0, 1),
    )

    # ===== HEADER =====
    console.print()
    console.print(Panel(
        f"[bold cyan]SNAPSHOT COMPLETO[/bold cyan]\n[dim]Kanban.db + Trello[/dim]\n[dim]{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}[/dim]",
        border_style="bright_blue"
    ))

    # ===== RENDERIZA LADO A LADO =====
    console.print()
    console.print(Columns([kanban_panel, trello_panel], align="center"))
    console.print()


@kanban_app.command("diff")
def kanban_diff(
    workspace: Optional[str] = typer.Option(None, "--workspace", "-w", help="ID do workspace (padrão: core)"),
):
    """
    Mostra comparação/diff: Kanban.db vs Trello.

    Compara os estados de ambos os sistemas e mostra:
    - Cards sincronizados
    - Cards dessincronizados (listas diferentes)
    - Cards só no Kanban
    - Cards só no Trello
    """
    from runtime.observability.snapshot.extractors.trello_extractor import TrelloExtractor

    workspace_id = workspace or "core"
    db_path = f"workspace/{workspace_id}/data/kanban.db"
    board_id = os.getenv("TRELLO_BOARD_ID", "")

    if not board_id:
        console.print("[red]❌ TRELLO_BOARD_ID não configurado[/red]")
        raise typer.Exit(1)

    api_key = os.getenv("TRELLO_API_KEY", "")
    api_token = os.getenv("TRELLO_API_TOKEN", "")

    if not api_key or not api_token:
        console.print("[red]❌ Credenciais Trello não configuradas[/red]")
        raise typer.Exit(1)

    console.print()
    console.print(Panel(
        f"[bold cyan]DIFF COMPARATIVO[/bold cyan]\n[dim]Kanban.db vs Trello[/dim]\n[dim]{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}[/dim]",
        border_style="cyan"
    ))
    console.print()

    # Captura snapshot unificado
    extractor = TrelloExtractor(api_key, api_token)
    snapshot = extractor.capture(
        target=board_id,
        depth=3,
        kanban_db=db_path,
        tags={"workspace_id": workspace_id}
    )

    # Verifica erros
    if snapshot.metadata.tags.get("error"):
        console.print(f"[red]❌ ERRO:[/red] {snapshot.metadata.tags['error']}")
        raise typer.Exit(1)

    trello_data = snapshot.structure.get("trello", {})
    kanban_data = snapshot.structure.get("kanban", {})

    trello_cards = trello_data.get("cards", [])
    kanban_cards = kanban_data.get("cards", [])

    # Estatísticas gerais
    stats_table = Table(show_header=False, box=None, padding=(0, 2))
    stats_table.add_row(f"[cyan]Kanban.db:[/cyan] {kanban_data.get('total_cards', 0)} cards")
    stats_table.add_row(f"[cyan]Trello:[/cyan] {trello_data.get('total_cards', 0)} cards")
    stats_table.add_row(f"[cyan]Listas Kanban:[/cyan] {kanban_data.get('total_lists', 0)}")
    stats_table.add_row(f"[cyan]Listas Trello:[/cyan] {trello_data.get('total_lists', 0)}")

    console.print(stats_table)
    console.print()

    # Cria índices por trello_card_id
    kanban_by_trello = {c["trello_card_id"]: c for c in kanban_cards if c.get("trello_card_id")}
    trello_by_id = {c["id"]: c for c in trello_cards}

    # Todos os trello_card_ids únicos
    all_trello_ids = set(kanban_by_trello.keys()) | set(trello_by_id.keys())

    # Contadores
    synced_count = 0
    desync_count = 0

    # Tabela comparativa
    table = Table(title="Comparação por Card", show_header=True, header_style="bold magenta")
    table.add_column("Card", style="white", no_wrap=True, width=45)
    table.add_column("[cyan]KANBAN.DB[/cyan]", style="cyan", width=20)
    table.add_column("[green]TRELLO API[/green]", style="green", width=20)
    table.add_column("Sync", style="bold", width=12)

    for trello_id in sorted(all_trello_ids):
        kanban_card = kanban_by_trello.get(trello_id)
        trello_card = trello_by_id.get(trello_id)

        k_list = kanban_card["list_name"] if kanban_card else "[red]❌ NÃO EXISTE[/red]"
        t_list = trello_card["list_name"] if trello_card else "[red]❌ NÃO EXISTE[/red]"

        # Verifica se está sincronizado usando trello_list_id
        k_trello_list_id = kanban_card.get("trello_list_id") if kanban_card else None
        t_list_id = trello_card.get("idList") if trello_card else None
        is_sync = k_trello_list_id and k_trello_list_id == t_list_id
        sync_marker = "[green]✅ SYNC[/green]" if is_sync else "[red]❌ DESSINC![/red]"

        if is_sync:
            synced_count += 1
        else:
            desync_count += 1

        # Formata título
        title = (kanban_card or trello_card)["title"][:40] if kanban_card else trello_card["name"][:40]

        table.add_row(title, k_list, t_list, sync_marker)

    console.print(table)

    # Resumo de sincronização
    console.print()
    sync_summary = Table(show_header=False, box=None, padding=(0, 2))
    sync_summary.add_row(f"[green]✅ Sincronizados:[/green] {synced_count}")
    sync_summary.add_row(f"[red]❌ Dessincronizados:[/red] {desync_count}")
    console.print(sync_summary)

    # Cards só no Kanban (sem trello_card_id)
    kanban_only = [c for c in kanban_cards if not c.get("trello_card_id")]
    if kanban_only:
        console.print()
        console.print(Panel(
            f"[yellow]⚠️ {len(kanban_only)} CARDS SÓ NO KANBAN[/yellow]\n[dim](sem trello_card_id - não foram sincronizados)[/dim]",
            border_style="yellow"
        ))
        for card in kanban_only:
            vivo = "[cyan]🤖 VIVO[/cyan]" if card.get("being_processed") else ""
            console.print(f"  • {card['title'][:40]} | [cyan]{card['list_name']}[/cyan]{vivo}")

    # Cards só no Trello (não existe no Kanban)
    trello_only_ids = set(trello_by_id.keys()) - set(kanban_by_trello.keys())
    if trello_only_ids:
        console.print()
        console.print(Panel(
            f"[yellow]⚠️ {len(trello_only_ids)} CARDS SÓ NO TRELLO[/yellow]\n[dim](existem no Trello mas não no kanban.db)[/dim]",
            border_style="yellow"
        ))
        for trello_id in trello_only_ids:
            card = trello_by_id[trello_id]
            console.print(f"  • {card['name'][:40]} | [green]{card['list_name']}[/green]")


@kanban_app.command("sync")
def kanban_sync(
    workspace: Optional[str] = typer.Option(None, "--workspace", "-w", help="ID do workspace (padrão: core)"),
    force: bool = typer.Option(False, "--force", "-f", help="Força sync ignorando timestamps"),
):
    """
    Sincroniza Trello → kanban.db.

    Busca todos os cards do Trello e atualiza o kanban.db
    com os dados mais recentes.
    """
    import requests
    from rich.live import Live
    from rich.spinner import Spinner

    workspace_id = workspace or "core"
    config = get_config()
    host = "127.0.0.1" if config.host == "0.0.0.0" else config.host
    base_url = f"http://{host}:{config.port}"

    with Live(Spinner("dots", text=f"[cyan]Sincronizando Trello → kanban.db (workspace={workspace_id})...[/cyan]"), console=console) as live:
        try:
            response = requests.post(
                f"{base_url}/api/kanban/sync/from-trello",
                json={"board_id": os.getenv("TRELLO_BOARD_ID", ""), "force": force},
                headers={"X-Workspace": workspace_id},
                timeout=30,
            )

            if response.status_code == 200:
                data = response.json()
                live.update(f"[green]✅ Sincronização completa![/green]\n[cyan]{data.get('synced_count', 0)} cards sincronizados[/cyan]")
            else:
                live.update(f"[red]❌ Erro na sincronização:[/red] {response.text}")

        except requests.exceptions.ConnectionError:
            live.update("[red]❌ Servidor não está rodando.[/red] [dim]Inicie com 'sb serve'[/dim]")
        except Exception as e:
            live.update(f"[red]❌ Erro:[/red] {e}")

    console.print()


@kanban_app.command("webhooks")
def kanban_webhooks(
    action: str = typer.Argument(..., help="Ação: setup, list, delete"),
    webhook_id: Optional[str] = typer.Option(None, "--id", "-i", help="ID do webhook (para delete)"),
    callback_url: Optional[str] = typer.Option(None, "--url", "-u", help="Callback URL (para setup)"),
):
    """
    Gerencia webhooks do Trello.

    Ações disponíveis:
    - setup: Configura webhook automaticamente
    - list: Lista webhooks existentes
    - delete: Deleta um webhook específico

    Exemplos:
        sb kanban webhooks setup --url https://seu-dominio.com/api/webhooks/trello
        sb kanban webhooks list
        sb kanban webhooks delete --id 123456789
    """
    import asyncio
    from rich.table import Table
    from rich.panel import Panel

    board_id = os.getenv("TRELLO_BOARD_ID", "")
    if not board_id:
        console.print("[red]❌ TRELLO_BOARD_ID não configurado[/red]")
        raise typer.Exit(1)

    api_key = os.getenv("TRELLO_API_KEY", "")
    api_token = os.getenv("TRELLO_API_TOKEN", "")

    if not api_key or not api_token:
        console.print("[red]❌ Credenciais Trello não configuradas[/red]")
        raise typer.Exit(1)

    # Cria adapter
    from infra.kanban.adapters.trello_adapter import TrelloAdapter
    from core.kanban.application.trello_service import TrelloService

    adapter = TrelloAdapter(api_key, api_token, board_id)
    service = TrelloService(adapter)

    if action == "list":
        # Lista webhooks existentes
        result = asyncio.run(service.adapter.list_webhooks())
        if result.is_err:
            console.print(f"[red]❌ Erro ao listar webhooks:[/red] {result.error}")
            raise typer.Exit(1)

        webhooks = result.unwrap()

        table = Table(show_header=True, header_style="bold magenta")
        table.add_column("ID", style="dim")
        table.add_column("Descrição")
        table.add_column("Callback URL")
        table.add_column("Model ID")

        for wh in webhooks:
            table.add_row(
                wh.get("id", "")[:8],
                wh.get("description", ""),
                wh.get("callbackURL", ""),
                wh.get("idModel", ""),
            )

        console.print()
        console.print(Panel(table, title=f"[bold cyan]Webhooks Trello ({len(webhooks)})[/bold cyan]"))
        console.print()

    elif action == "delete":
        if not webhook_id:
            console.print("[red]❌ --id é obrigatório para delete[/red]")
            raise typer.Exit(1)

        # Confirmação
        console.print(f"[yellow]Deletando webhook {webhook_id}...[/yellow]")
        result = asyncio.run(service.adapter.delete_webhook(webhook_id))
        if result.is_err:
            console.print(f"[red]❌ Erro ao deletar webhook:[/red] {result.error}")
            raise typer.Exit(1)

        console.print(f"[green]✅ Webhook {webhook_id} deletado[/green]")

    elif action == "setup":
        # Setup automático
        default_url = callback_url or os.getenv("TRELLO_WEBHOOK_CALLBACK_URL", "")

        if not default_url:
            console.print("[yellow]⚠️  Nenhuma callback URL fornecida[/yellow]")
            console.print("[dim]Use --url https://seu-dominio.com/api/webhooks/trello[/dim]")
            console.print("[dim]Ou configure TRELLO_WEBHOOK_CALLBACK_URL no .env[/dim]")
            raise typer.Exit(1)

        # Verifica se a URL está correta
        if not default_url.startswith("http"):
            console.print(f"[red]❌ Callback URL inválida: {default_url}[/red]")
            console.print("[dim]Deve começar com http:// ou https://[/dim]")
            raise typer.Exit(1)

        # Verifica se está usando o endpoint correto
        if "/api/webhooks/trello" not in default_url:
            console.print(f"[yellow]⚠️  Aviso: URL não parece seguir o padrão /api/webhooks/trello[/yellow]")
            console.print(f"[dim]URL fornecida: {default_url}[/dim]")
            console.print("[dim]Esperado: https://seu-dominio.com/api/webhooks/trello[/dim]")

        from rich.live import Live
        from rich.spinner import Spinner

        with Live(Spinner("dots", text=f"[cyan]Configurando webhook Trello...[/cyan]"), console=console) as live:
            result = asyncio.run(service.setup_webhook(
                callback_url=default_url,
                description="Skybridge Trello Webhook (auto-configured)"
            ))

            if result.is_ok:
                webhook = result.unwrap()
                live.update(f"[green]✅ Webhook configurado com sucesso![/green]\n[cyan]ID: {webhook.get('id')}[/cyan]")
            else:
                live.update(f"[red]❌ Erro ao configurar webhook:[/red] {result.error}")

    else:
        console.print(f"[red]❌ Ação desconhecida: {action}[/red]")
        console.print("[dim]Ações disponíveis: setup, list, delete[/dim]")
        raise typer.Exit(1)
