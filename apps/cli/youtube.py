# -*- coding: utf-8 -*-
"""
Comandos YouTube para CLI sb.

Funcionalidades:
    - sb youtube favorite-lists       Lista playlists do usuário
    - sb youtube favorite-videos      Lista vídeos de uma playlist
    - sb youtube transcribe <url>     Transcreve vídeo YouTube
"""

import asyncio
import os
import sys
from pathlib import Path
from typing import Optional

import typer
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.text import Text

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / "src"))

from dotenv import load_dotenv

console = Console()

youtube_app = typer.Typer(
    name="youtube",
    help="Comandos YouTube - listar favoritos, transcrever vídeos",
)


@youtube_app.callback(invoke_without_command=True)
def youtube_callback(ctx: typer.Context):
    """Mostra ajuda quando nenhum subcomando é fornecido."""
    if ctx.invoked_subcommand is None:
        show_youtube_help()


def show_youtube_help():
    """Mostra menu de ajuda do YouTube quando nenhum comando é fornecido."""
    help_text = Text()
    help_text.append("Comandos disponíveis:\n\n", style="bold cyan")
    help_text.append("  sb youtube setup                 Configura State Repository SQLite\n", style="white")
    help_text.append("  sb youtube favorite-lists        Lista playlists do usuário\n", style="white")
    help_text.append("  sb youtube favorite-videos       Lista vídeos de uma playlist\n", style="white")
    help_text.append("  sb youtube transcribe <url>      Transcreve vídeo YouTube\n", style="white")
    help_text.append("\nRequisitos:\n", style="bold white")
    help_text.append("  YOUTUBE_CLIENT_ID, YOUTUBE_CLIENT_SECRET, YOUTUBE_REFRESH_TOKEN no .env\n", style="dim")
    help_text.append("\nExemplos:\n", style="bold white")
    help_text.append("  sb youtube setup                             Inicia State Repository\n", style="dim")
    help_text.append("  sb youtube favorite-lists                     Mostra todas as playlists\n", style="dim")
    help_text.append("  sb youtube favorite-videos LL                 Vídeos dos Favoritos (LL)\n", style="dim")
    help_text.append("  sb youtube transcribe https://youtube.com/...  Transcreve vídeo\n", style="dim")

    console.print()
    console.print(Panel(help_text, title="[bold cyan]YouTube Commands (sb youtube)[/bold cyan]", border_style="red"))
    console.print()


def refresh_token(client_id: str, client_secret: str, refresh_token: str) -> str:
    """Renova access token usando refresh token."""
    import requests

    token_url = "https://oauth2.googleapis.com/token"
    response = requests.post(token_url, data={
        "client_id": client_id,
        "client_secret": client_secret,
        "refresh_token": refresh_token,
        "grant_type": "refresh_token"
    })

    if response.status_code != 200:
        raise RuntimeError(f"Erro ao renovar token: {response.status_code}")

    return response.json()["access_token"]


def get_youtube_client():
    """Retorna cliente YouTube autenticado."""
    from core.youtube.infrastructure.youtube_api_client import YouTubeAPIClient

    # Carregar .env
    load_dotenv(project_root / ".env")

    client_id = os.getenv("YOUTUBE_CLIENT_ID")
    client_secret = os.getenv("YOUTUBE_CLIENT_SECRET")
    refresh_token = os.getenv("YOUTUBE_REFRESH_TOKEN")

    if not all([client_id, client_secret, refresh_token]):
        console.print("[red]❌ Erro: Credenciais não encontradas no .env[/red]")
        console.print("\nCertifique-se que .env contém:")
        console.print("  YOUTUBE_CLIENT_ID=...")
        console.print("  YOUTUBE_CLIENT_SECRET=...")
        console.print("  YOUTUBE_REFRESH_TOKEN=...")
        raise typer.Exit(1)

    console.print("[dim]🔐 Renovando access token...[/dim]")
    access_token = refresh_token(client_id, client_secret, refresh_token)
    console.print("[green]✅ Token renovado![/green]")

    return YouTubeAPIClient(access_token)


@youtube_app.command("setup")
def setup(
    db_path: str = typer.Option("data/youtube_copilot.db", "--db-path", help="Caminho para SQLite"),
    force: bool = typer.Option(False, "--force", help="Recria tabelas (PERDE DADOS)"),
    verify: bool = typer.Option(False, "--verify", help="Apenas verifica estado"),
):
    """
    Configura State Repository SQLite para persistência de estado.

    Cria as tabelas necessárias para rastrear vídeos transcritos e favoritos.
    """
    from core.youtube.infrastructure.youtube_state_setup import (
        setup_youtube_state,
        verify_youtube_state
    )

    if verify:
        console.print(f"[dim]🔍 Verificando estado: {db_path}[/dim]")
        status = verify_youtube_state(db_path)

        if not status["exists"]:
            console.print(f"[red]❌ Banco não existe: {db_path}[/red]")
            raise typer.Exit(1)

        if status.get("error"):
            console.print(f"[red]❌ Erro: {status['error']}[/red]")
            raise typer.Exit(1)

        console.print(f"[green]✅ Estado válido![/green]")
        console.print(f"   Tabelas: {', '.join(status['tables'])}")
        console.print(f"   Vídeos: {status.get('video_count', 0)}")
        console.print(f"   Playlists: {status.get('playlist_count', 0)}")
        return

    if force:
        console.print("[yellow]⚠️  Modo FORCE: tabelas serão recriadas![/yellow]")
        if not typer.confirm("Continuar?"):
            console.print("❌ Cancelado")
            raise typer.Exit(1)

    console.print(f"[dim]🔧 Configurando schema: {db_path}[/dim]")
    setup_youtube_state(db_path, force_recreate=force)

    console.print(f"[dim]🔍 Verificando...[/dim]")
    status = verify_youtube_state(db_path)

    if status.get("error"):
        console.print(f"[red]❌ Erro: {status['error']}[/red]")
        raise typer.Exit(1)

    console.print(f"[green]✅ Setup concluído![/green]")
    console.print(f"   Tabelas: {', '.join(status['tables'])}")
    console.print(f"   Vídeos: {status.get('video_count', 0)}")
    console.print(f"   Playlists: {status.get('playlist_count', 0)}")


@youtube_app.command("favorite-lists")
def favorite_lists():
    """
    Lista todas as playlists do usuário.

    Mostra ID, título, quantidade de vídeos de cada playlist.
    """
    try:
        client = get_youtube_client()

        console.print("\n[dim]📋 Buscando playlists...[/dim]")
        playlists = client.get_my_playlists(max_results=50)

        if not playlists:
            console.print("[yellow]⚠️  Nenhuma playlist encontrada[/yellow]")
            raise typer.Exit(0)

        # Tabela de playlists
        table = Table(title=f"\n[cyan]{len(playlists)} Playlists[/cyan]")
        table.add_column("#", style="dim", width=3)
        table.add_column("Título", style="white")
        table.add_column("ID", style="dim")
        table.add_column("Vídeos", justify="right")

        for i, pl in enumerate(playlists, 1):
            title = pl["title"][:30] + "..." if len(pl["title"]) > 30 else pl["title"]
            table.add_row(str(i), title, pl["id"], str(pl["item_count"]))

        console.print(table)

        console.print(f"\n[green]✅ {len(playlists)} playlists encontradas[/green]")
        console.print("\n[dim]Use 'sb youtube favorite-videos <ID>' para ver os vídeos de uma playlist[/dim]")

    except Exception as e:
        console.print(f"[red]❌ Erro: {e}[/red]")
        raise typer.Exit(1)


@youtube_app.command("favorite-videos")
def favorite_videos(
    playlist_id: str = typer.Argument(..., help="ID da playlist (LL=Favoritos, WL=Watch Later, etc.)"),
    max_results: int = typer.Option(10, "--max", "-n", help="Máximo de vídeos a mostrar (padrão: 10)"),
):
    """
    Lista vídeos de uma playlist específica.

    Use 'LL' para Favoritos (Liked Videos).
    Use 'WL' para Assistir Mais Tarde (Watch Later).
    """
    try:
        client = get_youtube_client()

        playlist_name = f"Playlist {playlist_id}"
        if playlist_id == "LL":
            playlist_name = "Favoritos (Liked Videos)"
        elif playlist_id == "WL":
            playlist_name = "Assistir Mais Tarde (Watch Later)"

        console.print(f"\n[dim]📺 Vídeos de: {playlist_name}...[/dim]\n")
        videos = client.get_playlist_items(playlist_id=playlist_id, max_results=max_results)

        if not videos:
            console.print("[yellow]⚠️  Nenhum vídeo encontrado[/yellow]")
            raise typer.Exit(0)

        # Tabela de vídeos
        vid_table = Table(title=f"\n[cyan]{len(videos)} Vídeos[/cyan]")
        vid_table.add_column("#", style="dim", width=3)
        vid_table.add_column("Título", style="white")
        vid_table.add_column("Canal", style="dim")
        vid_table.add_column("Duração", justify="right")

        def format_duration(seconds: Optional[int]) -> str:
            if seconds is None:
                return "???"
            hours = seconds // 3600
            minutes = (seconds % 3600) // 60
            secs = seconds % 60
            if hours > 0:
                return f"{hours:02d}:{minutes:02d}:{secs:02d}"
            return f"{minutes:02d}:{secs:02d}"

        for i, vid in enumerate(videos, 1):
            title = vid["title"][:40] + "..." if len(vid["title"]) > 40 else vid["title"]
            duration = format_duration(vid.get("duration_seconds"))
            vid_table.add_row(str(i), title, vid["channel"], duration)

        console.print(vid_table)

        console.print(f"\n[green]✅ {len(videos)} vídeos em '{playlist_name}'[/green]")

    except Exception as e:
        console.print(f"[red]❌ Erro: {e}[/red]")
        raise typer.Exit(1)


@youtube_app.command("transcribe")
def transcribe(
    url: str = typer.Argument(..., help="URL do vídeo YouTube"),
    output_path: Path = typer.Argument(..., help="Caminho de saída para transcrição"),
):
    """
    Transcreve vídeo YouTube usando faster-whisper.

    Baixa o áudio, transcreve localmente e salva em arquivo.

    Exemplo: sb youtube transcribe https://youtube.com/watch?v=abc123 transcricao.txt
    """
    from core.youtube.application.youtube_transcript_service import YoutubeTranscriptService

    # Carregar .env
    load_dotenv(project_root / ".env")

    console.print(f"[cyan]🎥 Transcrevendo vídeo[/cyan]")
    console.print(f"[dim]   URL: {url}[/dim]")
    console.print(f"[dim]   Saída: {output_path}[/dim]")

    async def do_transcribe():
        # Criar diretórios pai se necessário
        output_path.parent.mkdir(parents=True, exist_ok=True)

        # Diretório para download de áudio
        output_dir = output_path.parent
        service = YoutubeTranscriptService(output_path=output_dir)

        try:
            result = await service.transcribe_video(url=url, output_path=output_path)

            console.print(f"\n[green]✅ Transcrição completa![/green]")
            console.print(f"   [dim]Idioma:[/dim] {result.language}")
            console.print(f"   [dim]Confiança:[/dim] {result.confidence:.2%}")
            console.print(f"   [dim]Duração:[/dim] {result.duration_seconds:.1f}s")
            console.print(f"   [dim]Saída:[/dim] {result.output_path}")

            # Mostrar primeiros caracteres
            with open(result.output_path, 'r', encoding='utf-8') as f:
                content = f.read()
                preview = content[:300] + "..." if len(content) > 300 else content
                console.print(f"\n[dim]Preview:[/dim]")
                console.print(f"[dim]{preview}[/dim]")

        except Exception as e:
            console.print(f"\n[red]❌ Erro na transcrição: {e}[/red]")
            import traceback
            traceback.print_exc()
            raise typer.Exit(1)

    asyncio.run(do_transcribe())


# Exporta o app para registro em main.py
__all__ = ["youtube_app"]
