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

app = typer.Typer(
    name="sb",
    help="Skybridge CLI - Interface de linha de comando",
    add_completion=False,
)

rpc_app = typer.Typer(
    name="rpc",
    help="Comandos RPC (list, discover, call, reload)",
)
app.add_typer(rpc_app, name="rpc")

# Workspace commands (ADR024)
from apps.cli.workspace import workspace_app, get_active_workspace
app.add_typer(workspace_app, name="workspace")
app.add_typer(workspace_app, name="ws")  # Alias curto

console = Console()

# Configuração padrão
DEFAULT_BASE_URL = "http://127.0.0.1:8000"


def get_base_url(url: Optional[str] = None) -> str:
    """Retorna URL base da API."""
    if url:
        return url.rstrip("/")
    try:
        config = get_config()
        return f"http://{config.host}:{config.port}"
    except Exception:
        return DEFAULT_BASE_URL


def format_json(data: dict) -> str:
    """Formata JSON para exibição."""
    return json.dumps(data, indent=2, ensure_ascii=False)


@rpc_app.command("list")
def rpc_list(
    url: Optional[str] = typer.Option(None, "--url", "-u", help="URL base da API"),
    output: str = typer.Option("table", "--output", "-o", help="Formato: table, json"),
):
    """
    Lista todos os handlers RPC ativos.

    RF007: Lista handlers com metadados (method, kind, module, auth_required).
    """
    base_url = get_base_url(url)
    response = requests.get(f"{base_url}/discover")

    if response.status_code != 200:
        console.print(f"[red]Erro:[/red] {response.status_code} - {response.text}")
        raise typer.Exit(1)

    data = response.json()

    if output == "json":
        console.print_json(data=data)
        return

    # Formato tabela
    table = Table(title=f"Sky-RPC Handlers (v{data['version']})")
    table.add_column("Method", style="cyan", no_wrap=False)
    table.add_column("Kind", style="magenta")
    table.add_column("Auth", style="yellow")
    table.add_column("Module", style="dim")

    for method, handler in data.get("discovery", {}).items():
        table.add_row(
            method,
            handler.get("kind", "query"),
            "✓" if handler.get("auth_required") else "✗",
            handler.get("module", "unknown"),
        )

    console.print(table)
    console.print(f"\n[dim]Total: {data.get('total', 0)} handlers[/dim]")


@rpc_app.command("discover")
def rpc_discover(
    url: Optional[str] = typer.Option(None, "--url", "-u", help="URL base da API"),
    method: Optional[str] = typer.Option(None, "--method", "-m", help="Filtrar por método específico"),
):
    """
    Mostra introspecção completa dos handlers.

    RF009: Retorna detalhes completos incluindo schemas JSON.
    """
    base_url = get_base_url(url)

    if method:
        response = requests.get(f"{base_url}/discover/{method}")
        if response.status_code != 200:
            console.print(f"[red]Erro:[/red] Handler não encontrado: {method}")
            raise typer.Exit(1)
        data = response.json()
        console.print(Panel(JSON(data), title=f"Handler: {method}", expand=False))
    else:
        response = requests.get(f"{base_url}/discover")
        if response.status_code != 200:
            console.print(f"[red]Erro:[/red] {response.status_code} - {response.text}")
            raise typer.Exit(1)
        data = response.json()
        console.print(Panel(JSON(data), title="Discovery Completo", expand=False))


@rpc_app.command("call")
def rpc_call(
    method: str = typer.Argument(..., help="Método RPC a executar"),
    payload: Optional[str] = typer.Option(None, "--payload", "-p", help="Payload JSON"),
    url: Optional[str] = typer.Option(None, "--url", "-u", help="URL base da API"),
):
    """
    Executa um handler RPC.

    RF010: Executa método via ticket + envelope (fluxo completo Sky-RPC).
    """
    base_url = get_base_url(url)

    # 1. Obter ticket
    ticket_response = requests.get(f"{base_url}/ticket", params={"method": method})
    if ticket_response.status_code != 200:
        console.print(f"[red]Erro ao obter ticket:[/red] {ticket_response.text}")
        raise typer.Exit(1)

    ticket_data = ticket_response.json()
    if not ticket_data.get("ok"):
        console.print(f"[red]Erro ao obter ticket:[/red] {ticket_data}")
        raise typer.Exit(1)

    ticket_id = ticket_data["ticket"]["id"]
    console.print(f"[dim]Ticket obtido:[/dim] {ticket_id}")

    # 2. Preparar envelope
    envelope_payload = {}
    if payload:
        try:
            envelope_payload = json.loads(payload)
        except json.JSONDecodeError as e:
            console.print(f"[red]Erro no payload JSON:[/red] {e}")
            raise typer.Exit(1)

    envelope = {
        "ticket_id": ticket_id,
        "detail": {
            "context": method.split(".")[0] if "." in method else "rpc",
            "action": method.split(".")[-1] if "." in method else method,
            "payload": envelope_payload,
        },
    }

    # 3. Executar envelope
    env_response = requests.post(
        f"{base_url}/envelope",
        json=envelope,
        headers={"Content-Type": "application/json"},
    )

    if env_response.status_code != 200:
        console.print(f"[red]Erro na execução:[/red] {env_response.text}")
        raise typer.Exit(1)

    result = env_response.json()
    if result.get("ok"):
        console.print(Panel(JSON(result.get("result")), title=f"Resultado: {method}", expand=False))
    else:
        console.print(f"[red]Erro:[/red] {result.get('error')}")
        raise typer.Exit(1)


@rpc_app.command("reload")
def rpc_reload(
    packages: str = typer.Argument(..., help="Pacotes para reload (separados por vírgula)"),
    url: Optional[str] = typer.Option(None, "--url", "-u", help="URL base da API"),
):
    """
    Recarrega o registry com novo código.

    RF013: Reload dinâmico de handlers.
    RF014: Rollback automático em caso de erro.
    """
    base_url = get_base_url(url)
    pkg_list = [p.strip() for p in packages.split(",")]

    console.print(f"[dim]Recarregando pacotes:[/dim] {', '.join(pkg_list)}")

    response = requests.post(
        f"{base_url}/discover/reload",
        json=pkg_list,
        headers={"Content-Type": "application/json"},
    )

    if response.status_code != 200:
        console.print(f"[red]Erro no reload:[/red] {response.text}")
        raise typer.Exit(1)

    result = response.json()
    if result.get("ok"):
        console.print(f"[green]✓ Reload completo[/green]")
        console.print(f"  [dim]Adicionados:[/dim] {len(result.get('added', []))}")
        console.print(f"  [dim]Removidos:[/dim] {len(result.get('removed', []))}")
        console.print(f"  [dim]Total:[/dim] {result.get('total', 0)} handlers")

        if result.get("added"):
            console.print(f"\n[cyan]Adicionados:[/cyan] {', '.join(result['added'])}")
        if result.get("removed"):
            console.print(f"[red]Removidos:[/red] {', '.join(result['removed'])}")
    else:
        console.print(f"[red]Erro no reload:[/red] {result}")
        raise typer.Exit(1)


# Agent commands
agent_app = typer.Typer(
    name="agent",
    help="Comandos para interagir com agentes",
)
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
    ticket_response = requests.get(f"{base_url}/ticket", params={"method": "github.createissue"})
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
        f"{base_url}/envelope",
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


@app.command("version")
def version():
    """Mostra versão do Skybridge."""
    console.print(f"[cyan]Skybridge[/cyan] v{__version__}")


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


def show_interactive_menu():
    """
    Mostra menu interativo quando nenhum comando é fornecido.

    Permite acesso rápido aos comandos mais usados.
    """
    from rich.text import Text
    from rich import box

    # Banner
    banner = Text()
    banner.append("🌉 ", style="bold cyan")
    banner.append("Skybridge", style="bold cyan")
    banner.append(" CLI", style="bold white")
    banner.append(f" v{__version__}", style="dim")

    console.print()
    console.print(Panel(banner, border_style="cyan", padding=(0, 1)))

    # Menu de opções
    console.print("\n[bold cyan]Comandos Mais Usados:[/bold cyan]\n")

    options = [
        ("[1]", "Servidor", "[green]sb serve[/green]", "Inicia o servidor Skybridge"),
        ("[2]", "RPC List", "[green]sb rpc list[/green]", "Lista handlers disponíveis"),
        ("[3]", "Workspace", "[green]sb workspace list[/green]", "Lista workspaces"),
        ("[4]", "Ajuda", "[green]sb --help[/green]", "Mostra todos os comandos"),
        ("[5]", "Versão", "[green]sb version[/green]", "Mostra versão instalada"),
        ("[0]", "Sair", "", "Fecha o menu"),
    ]

    for num, nome, comando, desc in options:
        if num == "[0]":
            console.print()
        console.print(f"  {num} [bold white]{nome}[/bold white]")
        if comando:
            console.print(f"      {comando} - [dim]{desc}[/dim]")
        elif desc:
            console.print(f"      [dim]{desc}[/dim]")

    console.print()
    choice = console.input("[bold cyan]Escolha uma opção [0-5]: [/bold cyan]")

    choices = {
        "1": lambda: serve(["--reload"]),
        "2": lambda: rpc_list(url=None, output="table"),
        "3": lambda: console.print("\n[yellow]Use: [green]sb workspace list[/green] para ver workspaces[/yellow]\n"),
        "4": lambda: app(["--help"]),
        "5": lambda: version(),
        "0": lambda: None,
    }

    action = choices.get(choice.strip())
    if action:
        console.print()
        action()


def main():
    """
    Ponto de entrada.

    Se nenhum argumento for fornecido, mostra menu interativo.
    Caso contrário, executa o comando normalmente.
    """
    # Verifica se há argumentos
    if len(sys.argv) == 1:
        # Nenhum argumento = mostrar menu
        show_interactive_menu()
    else:
        # Argumentos fornecidos = executar normalmente
        app()


if __name__ == "__main__":
    main()
