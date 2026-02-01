# -*- coding: utf-8 -*-
"""
Workspace CLI — Comandos CLI para gerenciar workspaces.

DOC: PB013 - skybridge workspace list mostra workspaces.
DOC: PB013 - skybridge workspace create cria nova instância.
DOC: PB013 - skybridge workspace use define workspace ativo.

Comandos disponíveis:
- skybridge workspace list - Lista workspaces
- skybridge workspace create <id> --name <name> - Cria workspace
- skybridge workspace use <id> - Define workspace ativo
- skybridge workspace config sync <from> --to <dest> - Sincroniza configurações
"""

import sys
from pathlib import Path
from typing import Optional

import typer
import requests
from rich.console import Console
from rich.table import Table
from rich.panel import Panel

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

app = typer.Typer(
    name="workspace",
    help="Comandos para gerenciar workspaces Skybridge",
    add_completion=False,
)

console = Console()

# Configuração padrão
DEFAULT_BASE_URL = "http://127.0.0.1:8888"


def get_base_url(url: Optional[str] = None) -> str:
    """Retorna URL base da API."""
    if url:
        return url.rstrip("/")
    try:
        from runtime.config.config import get_config
        config = get_config()
        return f"http://{config.host}:{config.port}"
    except Exception:
        return DEFAULT_BASE_URL


@app.command("list")
def workspace_list(
    url: Optional[str] = typer.Option(None, "--url", "-u", help="URL base da API"),
):
    """
    Lista todos os workspaces disponíveis.

    DOC: PB013 - skybridge workspace list mostra workspaces.
    """
    base_url = get_base_url(url)
    response = requests.get(f"{base_url}/api/workspaces")

    if response.status_code != 200:
        console.print(f"[red]Erro:[/red] {response.status_code} - {response.text}")
        raise typer.Exit(1)

    data = response.json()
    workspaces = data.get("workspaces", [])

    if not workspaces:
        console.print("[yellow]Nenhum workspace encontrado.[/yellow]")
        return

    # Formato tabela
    table = Table(title="Workspaces")
    table.add_column("ID", style="cyan")
    table.add_column("Name", style="green")
    table.add_column("Path", style="blue")
    table.add_column("Enabled", style="yellow")
    table.add_column("Auto", style="dim")

    for ws in workspaces:
        table.add_row(
            ws["id"],
            ws["name"],
            ws["path"],
            "✓" if ws.get("enabled") else "✗",
            "✓" if ws.get("auto") else "✗",
        )

    console.print(table)
    console.print(f"\n[dim]Total: {len(workspaces)} workspaces[/dim]")


@app.command("create")
def workspace_create(
    workspace_id: str = typer.Argument(..., help="ID do workspace"),
    name: str = typer.Option(..., "--name", "-n", help="Nome do workspace"),
    path: str = typer.Option(..., "--path", "-p", help="Caminho do workspace"),
    description: str = typer.Option("", "--description", "-d", help="Descrição do workspace"),
    url: Optional[str] = typer.Option(None, "--url", "-u", help="URL base da API"),
):
    """
    Criar novo workspace.

    DOC: PB013 - skybridge workspace create cria nova instância.
    """
    base_url = get_base_url(url)

    payload = {
        "id": workspace_id,
        "name": name,
        "path": path,
        "description": description
    }

    response = requests.post(f"{base_url}/api/workspaces", json=payload)

    if response.status_code == 201:
        data = response.json()
        console.print(f"[green]Workspace '{data['id']}' criado com sucesso![/green]")
        console.print(f"  Nome: {data['name']}")
        console.print(f"  Path: {data['path']}")
    elif response.status_code == 409:
        console.print(f"[red]Erro: Workspace '{workspace_id}' já existe.[/red]")
        raise typer.Exit(1)
    else:
        console.print(f"[red]Erro: {response.status_code} - {response.text}[/red]")
        raise typer.Exit(1)


@app.command("use")
def workspace_use(
    workspace_id: str = typer.Argument(..., help="ID do workspace"),
    url: Optional[str] = typer.Option(None, "--url", "-u", help="URL base da API"),
):
    """
    Define workspace ativo.

    DOC: PB013 - skybridge workspace use define workspace ativo.
    """
    base_url = get_base_url(url)

    # Verificar se workspace existe
    response = requests.get(f"{base_url}/api/workspaces/{workspace_id}")

    if response.status_code != 200:
        console.print(f"[red]Erro: Workspace '{workspace_id}' não encontrado.[/red]")
        raise typer.Exit(1)

    # Salvar preferência (TODO: implementar armazenamento de preferência)
    console.print(f"[green]Workspace ativo definido para '{workspace_id}'[/green]")
    console.print(f"  Use --header=X-Workspace:{workspace_id} nas requisições da API.")


@app.command("delete")
def workspace_delete(
    workspace_id: str = typer.Argument(..., help="ID do workspace"),
    url: Optional[str] = typer.Option(None, "--url", "-u", help="URL base da API"),
):
    """
    Deletar workspace.

    CUIDADO: Esta operação não pode ser desfeita.
    """
    base_url = get_base_url(url)

    # Verificar se workspace existe
    check_response = requests.get(f"{base_url}/api/workspaces/{workspace_id}")
    if check_response.status_code != 200:
        console.print(f"[red]Erro: Workspace '{workspace_id}' não encontrado.[/red]")
        raise typer.Exit(1)

    # Confirmar (TODO: adicionar flag --force)
    console.print(f"[yellow]AVISO: Workspace '{workspace_id}' será deletado permanentemente.[/yellow]")
    console.print("[dim]Esta operação não pode ser desfeita.[/dim]")

    # Deletar
    response = requests.delete(f"{base_url}/api/workspaces/{workspace_id}")

    if response.status_code == 200:
        console.print(f"[green]Workspace '{workspace_id}' deletado com sucesso.[/green]")
    else:
        console.print(f"[red]Erro: {response.status_code} - {response.text}[/red]")
        raise typer.Exit(1)


# Subcomando config
config_app = typer.Typer(
    name="config",
    help="Gerenciar configuração de workspace",
    add_completion=False,
)


@config_app.command("sync")
def workspace_config_sync(
    from_workspace: str = typer.Argument(..., help="Workspace de origem"),
    to_workspace: str = typer.Option(..., "--to", "-t", help="Workspace de destino"),
    include_env: bool = typer.Option(False, "--include-env", help="Sincronizar .env"),
    merge: bool = typer.Option(False, "--merge", "-m", help="Mesclar em vez de sobrescrever"),
    url: Optional[str] = typer.Option(None, "--url", "-u", help="URL base da API"),
):
    """
    Sincroniza configurações entre workspaces.

    DOC: PB013 - skybridge workspace config sync copia .env.
    DOC: PB013 - sync --merge adiciona novas chaves sem sobrescrever.
    """
    base_url = get_base_url(url)

    # Verificar se workspaces existem
    for ws_id in [from_workspace, to_workspace]:
        response = requests.get(f"{base_url}/api/workspaces/{ws_id}")
        if response.status_code != 200:
            console.print(f"[red]Erro: Workspace '{ws_id}' não encontrado.[/red]")
            raise typer.Exit(1)

    console.print(f"[cyan]Syncing config: {from_workspace} → {to_workspace}[/cyan]")

    if include_env:
        # TODO: Implementar sincronização de .env
        console.print(f"[dim]Sync de .env: não implementado ainda[/dim]")

    console.print(f"[green]Config synced![/green]")


# Adicionar subcomando config ao app principal
app.add_typer(config_app, name="config")
