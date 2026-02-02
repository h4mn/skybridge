# -*- coding: utf-8 -*-
"""
CLI Workspace — Gerenciamento de workspaces.

DOC: ADR024 - Comandos para gerenciar workspaces multi-instância.
DOC: PB013 - list, create, use, delete, current.

Comandos:
- sb ws list - Lista todos os workspaces
- sb ws create <id> --name <nome> - Cria novo workspace
- sb ws use <id> - Define workspace ativo
- sb ws delete <id> - Deleta workspace
- sb ws current - Mostra workspace ativo

Alias: sb workspace = sb ws
"""

import json
from pathlib import Path
from typing import Optional

import requests
import typer
from rich.console import Console
from rich.table import Table
from rich.panel import Panel

console = Console()

DEFAULT_BASE_URL = "http://127.0.0.1:8000"
ACTIVE_WORKSPACE_FILE = Path(".workspace_active")


def get_base_url(url: Optional[str] = None) -> str:
    """Retorna URL base da API."""
    return url.rstrip("/") if url else DEFAULT_BASE_URL


def show_workspace_menu():
    """Mostra menu de ajuda do workspace quando nenhum comando é fornecido."""
    from typer.main import get_command
    from rich.panel import Panel
    from rich.text import Text

    # Obter o comando workspace
    cmd = get_command(workspace_app)

    # Gerar texto de ajuda
    help_text = Text()
    help_text.append("Comandos disponíveis:\n", style="bold cyan")
    help_text.append("  sb ws list                          Lista todos os workspaces\n", style="white")
    help_text.append("  sb ws create <id> [--name]       Cria novo workspace\n", style="white")
    help_text.append("  sb ws use <id>                     Define workspace ativo\n", style="white")
    help_text.append("  sb ws delete <id>                  Deleta workspace\n", style="white")
    help_text.append("  sb ws current                       Mostra workspace ativo\n", style="white")
    help_text.append("\nExemplos:\n", style="bold yellow")
    help_text.append("  sb ws list\n", style="dim")
    help_text.append("  sb ws use trading\n", style="dim")
    help_text.append("  sb ws create dev                → Nome será 'Dev'\n", style="dim")
    help_text.append("  sb ws create trading --name 'Trader'  → Nome personalizado\n", style="dim")

    console.print(Panel(help_text, title="[bold cyan]Workspace Commands (sb ws)[/bold cyan]", border_style="bright_blue"))


workspace_app = typer.Typer(
    name="workspace",
    help="Comandos para gerenciar workspaces",
    invoke_without_command=True,
    callback=show_workspace_menu,
)


@workspace_app.command("list")
def workspace_list(
    url: Optional[str] = typer.Option(None, "--url", "-u", help="URL base da API"),
):
    """
    Lista todos os workspaces.

    DOC: ADR024 - GET /api/workspaces retorna todos.
    """
    base_url = get_base_url(url)
    response = requests.get(f"{base_url}/api/workspaces")

    if response.status_code != 200:
        console.print(f"[red]Erro:[/red] {response.status_code} - {response.text}")
        raise typer.Exit(1)

    data = response.json()
    workspaces = data.get("workspaces", [])

    # Mostrar workspace ativo
    active_workspace = get_active_workspace()

    # Tabela de workspaces
    table = Table(title=f"Workspaces ({len(workspaces)})")
    table.add_column("ID", style="cyan", no_wrap=True)
    table.add_column("Nome", style="white")
    table.add_column("Path", style="dim")
    table.add_column("Auto", style="yellow")
    table.add_column("Status", style="green")

    for ws in workspaces:
        is_active = ws["id"] == active_workspace
        status = "✓ ATIVO" if is_active else ""
        auto = "auto" if ws.get("auto") else "-"
        enabled = "enabled" if ws.get("enabled") else "disabled"

        table.add_row(
            ws["id"],
            ws["name"],
            ws["path"],
            auto,
            f"{status} {enabled}".strip(),
        )

    console.print(table)


@workspace_app.command("create")
def workspace_create(
    workspace_id: str = typer.Argument(..., help="ID do workspace (ex: trading, dev)"),
    name: str = typer.Option(None, "--name", "-n", help="Nome do workspace (padrão: ID capitalizado)"),
    path: Optional[str] = typer.Option(None, "--path", "-p", help="Caminho (padrão: workspace/<id>)"),
    description: str = typer.Option("", "--description", "-d", help="Descrição"),
    url: Optional[str] = typer.Option(None, "--url", "-u", help="URL base da API"),
):
    """
    Cria um novo workspace.

    DOC: PB013 - POST /api/workspaces cria nova instância.

    Se --name não for fornecido, usa o ID capitalizado como nome.
    """
    base_url = get_base_url(url)

    # Usar ID capitalizado como nome padrão se não fornecido
    workspace_name = name if name else workspace_id.capitalize()

    if not path:
        path = f"workspace/{workspace_id}"

    payload = {
        "id": workspace_id,
        "name": workspace_name,
        "path": path,
        "description": description,
    }

    console.print(f"[dim]Criando workspace:[/dim] {workspace_id}")
    response = requests.post(
        f"{base_url}/api/workspaces",
        json=payload,
        headers={"Content-Type": "application/json"},
    )

    if response.status_code == 201:
        result = response.json()
        console.print(f"[green]✓ Workspace criado com sucesso![/green]")
        console.print(f"  [cyan]ID:[/cyan] {result['id']}")
        console.print(f"  [cyan]Nome:[/cyan] {result['name']}")
        console.print(f"  [cyan]Path:[/cyan] {result['path']}")
    elif response.status_code == 409:
        console.print(f"[red]Erro:[/red] Workspace '{workspace_id}' já existe")
        raise typer.Exit(1)
    else:
        console.print(f"[red]Erro:[/red] {response.status_code} - {response.text}")
        raise typer.Exit(1)


@workspace_app.command("use")
def workspace_use(
    workspace_id: str = typer.Argument(..., help="ID do workspace para ativar"),
):
    """
    Define o workspace ativo.

    DOC: PB013 - Salva em .workspace_active para uso futuro.
    """
    # Verificar se workspace existe
    active_workspace = get_active_workspace()

    # Salvar no arquivo
    ACTIVE_WORKSPACE_FILE.write_text(workspace_id, encoding="utf-8")

    console.print(f"[green]✓ Workspace ativo definido para:[/green] {workspace_id}")

    if active_workspace:
        console.print(f"  [dim]Anterior:[/dim] {active_workspace}")


@workspace_app.command("delete")
def workspace_delete(
    workspace_id: str = typer.Argument(..., help="ID do workspace para deletar"),
    url: Optional[str] = typer.Option(None, "--url", "-u", help="URL base da API"),
    force: bool = typer.Option(False, "--force", "-f", help="Deletar sem confirmação"),
):
    """
    Deleta um workspace.

    DOC: PB013 - DELETE /api/workspaces/:id deleta workspace.
    """
    if workspace_id == "core":
        console.print("[red]Erro:[/red] Não é possível deletar o workspace 'core'")
        raise typer.Exit(1)

    # Confirmação
    if not force:
        console.print(f"[yellow]⚠ Deletar workspace '{workspace_id}'?[/yellow]")
        confirm = typer.confirm("Tem certeza?", default=False)
        if not confirm:
            console.print("[dim]Cancelado[/dim]")
            raise typer.Exit(0)

    base_url = get_base_url(url)
    response = requests.delete(f"{base_url}/api/workspaces/{workspace_id}")

    if response.status_code == 200:
        result = response.json()
        console.print(f"[green]✓ {result['message']}[/green]")
    elif response.status_code == 404:
        console.print(f"[red]Erro:[/red] Workspace '{workspace_id}' não encontrado")
        raise typer.Exit(1)
    else:
        console.print(f"[red]Erro:[/red] {response.status_code} - {response.text}")
        raise typer.Exit(1)


@workspace_app.command("current")
def workspace_current():
    """
    Mostra o workspace ativo.

    DOC: PB013 - Lê de .workspace_active.
    """
    active = get_active_workspace()
    if active:
        console.print(f"[cyan]Workspace ativo:[/cyan] {active}")
    else:
        console.print("[dim]Nenhum workspace ativo definido (usará 'core')[/dim]")


def get_active_workspace() -> Optional[str]:
    """
    Retorna o workspace ativo salvo.

    Lê do arquivo .workspace_active.
    """
    if ACTIVE_WORKSPACE_FILE.exists():
        return ACTIVE_WORKSPACE_FILE.read_text(encoding="utf-8").strip()
    return None
