# -*- coding: utf-8 -*-
"""
CLI sb — Interface de linha de comando Skybridge.

Conforme PRD009-RF15: CLI sb com subcomandos rpc (list, discover, call, reload).
"""

import sys
import json
import subprocess
from pathlib import Path
from typing import Optional

import typer
import requests
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.json import JSON

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

from runtime.config.config import get_config
from version import __version__

# Rich console (deve ser criado antes do app para uso no callback)
console = Console()

app = typer.Typer(
    name="sb",
    help="Skybridge CLI - Interface de linha de comando",
    add_completion=False,
)


@app.callback(invoke_without_command=True)
def main(
    version: bool = typer.Option(False, "--version", "-v", help="Mostra versão e sai"),
    ctx: typer.Context = typer.Context,
):
    """Skybridge CLI - Interface de linha de comando."""
    if version:
        console.print(f"[cyan]Skybridge[/cyan] v{__version__}")
        raise typer.Exit()

    # Se nenhum comando foi fornecido, mostra help
    if ctx.invoked_subcommand is None:
        show_help()

# Workspace commands (ADR024)
from apps.cli.workspace import workspace_app, get_active_workspace
app.add_typer(workspace_app, name="workspace")
app.add_typer(workspace_app, name="ws")  # Alias curto

# Configuração padrão
DEFAULT_BASE_URL = "http://127.0.0.1:8000"


def get_base_url(url: Optional[str] = None) -> str:
    """Retorna URL base da API."""
    if url:
        return url.rstrip("/")
    try:
        config = get_config()
        # 0.0.0.0 não funciona como endereço de destino no Windows
        # Usa 127.0.0.1 quando config.host é 0.0.0.0
        host = "127.0.0.1" if config.host == "0.0.0.0" else config.host
        return f"http://{host}:{config.port}"
    except Exception:
        return DEFAULT_BASE_URL


def format_json(data: dict) -> str:
    """Formata JSON para exibição."""
    return json.dumps(data, indent=2, ensure_ascii=False)



# Agent commands
agent_app = typer.Typer(
    name="agent",
    help="Comandos para interagir com agentes",
)


@agent_app.callback(invoke_without_command=True)
def agent_callback(ctx: typer.Context):
    """Mostra ajuda quando nenhum subcomando é fornecido."""
    if ctx.invoked_subcommand is None:
        show_agent_menu()


def show_agent_menu():
    """Mostra menu de ajuda do agent quando nenhum comando é fornecido."""
    from rich.text import Text

    help_text = Text()
    help_text.append("Comandos disponíveis:\n\n", style="bold cyan")
    help_text.append("  sb agent issue                  Cria issue no GitHub\n", style="white")
    help_text.append("\nOpções:\n", style="bold white")
    help_text.append("  --titulo, -t                  Título da issue\n", style="dim")
    help_text.append("  --desc, -d                    Descrição da issue\n", style="dim")
    help_text.append("  --labels, -l                  Labels separadas por vírgula\n", style="dim")

    console.print()
    console.print(Panel(help_text, title="[bold cyan]Agent Commands (sb agent)[/bold cyan]", border_style="bright_blue"))
    console.print()


app.add_typer(agent_app, name="agent")


@agent_app.command("issue")
def agent_issue(
    titulo: str = typer.Option(..., "--titulo", "-t", help="Título da issue"),
    desc: str = typer.Option(..., "--desc", "-d", help="Descrição da issue"),
    labels: str = typer.Option("automated", "--labels", "-l", help="Labels separadas por vírgula"),
    url: Optional[str] = typer.Option(None, "--url", "-u", help="URL base da API"),
):
    """
    Cria uma nova issue no GitHub configurado.

    A issue será criada no repositório configurado (GITHUB_REPO).
    Usa o token GITHUB_TOKEN para autenticação.
    """
    base_url = get_base_url(url)

    # Prepara labels
    label_list = [l.strip() for l in labels.split(",")]

    # Prepara payload
    payload = {
        "title": titulo,
        "body": desc,
        "labels": label_list,
    }

    console.print(f"[dim]Criando issue no GitHub...[/dim]")
    console.print(f"[dim]Título:[/dim] {titulo}")
    console.print(f"[dim]Labels:[/dim] {', '.join(label_list)}")

    # 1. Obter ticket
    ticket_response = requests.get(f"{base_url}/api/ticket", params={"method": "github.createissue"})
    if ticket_response.status_code != 200:
        console.print(f"[red]Erro ao obter ticket:[/red] {ticket_response.text}")
        raise typer.Exit(1)

    ticket_data = ticket_response.json()
    if not ticket_data.get("ok"):
        console.print(f"[red]Erro ao obter ticket:[/red] {ticket_data}")
        raise typer.Exit(1)

    ticket_id = ticket_data["ticket"]["id"]

    # 2. Preparar envelope
    envelope = {
        "ticket_id": ticket_id,
        "detail": {
            "context": "github",
            "action": "create_issue",
            "payload": payload,
        },
    }

    # 3. Executar envelope
    env_response = requests.post(
        f"{base_url}/api/envelope",
        json=envelope,
        headers={"Content-Type": "application/json"},
    )

    if env_response.status_code != 200:
        console.print(f"[red]Erro na execução:[/red] {env_response.text}")
        raise typer.Exit(1)

    result = env_response.json()
    if result.get("ok"):
        issue_data = result.get("result")
        console.print(f"[green]✓ Issue criada com sucesso![/green]")
        console.print(f"  [cyan]Número:[/cyan] #{issue_data.get('issue_number')}")
        console.print(f"  [cyan]URL:[/cyan] {issue_data.get('issue_url')}")
        console.print(f"  [dim]Labels:[/dim] {', '.join(issue_data.get('labels', []))}")
    else:
        console.print(f"[red]Erro:[/red] {result.get('error')}")
        raise typer.Exit(1)


@app.command("serve")
def serve(
    args: Optional[list[str]] = typer.Argument(None, help="Argumentos adicionais para o servidor"),
):
    """
    Inicia o servidor Skybridge.

    Executa apps.server.main com os argumentos fornecidos.
    """
    cmd = [sys.executable, "-m", "apps.server.main"]
    if args:
        cmd.extend(args)

    console.print(f"[dim]Iniciando servidor...[/dim]")
    console.print(f"[dim]Comando:[/dim] {' '.join(cmd)}")

    subprocess.run(cmd)


def show_help():
    """Mostra ajuda do sb quando nenhum comando é fornecido."""
    from rich.text import Text

    help_text = Text()
    help_text.append("Comandos disponíveis:\n\n", style="bold cyan")
    help_text.append("Servidor:\n", style="bold white")
    help_text.append("  sb serve [--reload]            Inicia o servidor Skybridge\n", style="white")
    help_text.append("\nWorkspace:\n", style="bold white")
    help_text.append("  sb workspace list               Lista todos os workspaces\n", style="white")
    help_text.append("  sb ws create <id>               Cria novo workspace\n", style="white")
    help_text.append("  sb ws use <id>                  Define workspace ativo\n", style="white")
    help_text.append("\nAgent:\n", style="bold white")
    help_text.append("  sb agent issue                  Cria issue no GitHub\n", style="white")
    help_text.append("\nOutros:\n", style="bold white")
    help_text.append("  sb --version, -v               Mostra versão instalada\n", style="white")
    help_text.append("  sb --help                       Mostra esta ajuda\n", style="white")

    console.print()
    console.print(Panel(help_text, title=f"[bold cyan]Skybridge CLI v{__version__}[/bold cyan]", border_style="bright_blue"))
    console.print()


def main():
    """
    Ponto de entrada.

    O callback do app trata automaticamente:
    - Sem argumentos → mostra menu interativo
    - Com argumentos → executa comando normalmente
    """
    app()


if __name__ == "__main__":
    main()
