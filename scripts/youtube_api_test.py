#!/usr/bin/env python3
"""Script de teste manual para YouTube API Client.

Uso:
    # Com token OAuth
    GOOGLE_OAUTH_TOKEN=seu_token_aqui python scripts/youtube_api_test.py

    # Ou via variável de ambiente
    export GOOGLE_OAUTH_TOKEN=seu_token_aqui
    python scripts/youtube_api_test.py
"""

import os
import sys
import json
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.core.youtube.infrastructure.youtube_api_client import (
    YouTubeAPIClient,
    get_favorites,
    get_watch_later,
    get_my_playlists
)


def print_section(title: str):
    """Imprime separador de seção."""
    print(f"\n{'='*60}")
    print(f"  {title}")
    print(f"{'='*60}\n")


def print_video(video: dict, index: int = None):
    """Imprime informações de um vídeo."""
    prefix = f"{index}. " if index is not None else ""
    title = video.get("title", "Sem título")
    channel = video.get("channel", "Canal desconhecido")
    duration = video.get("duration_seconds")

    if duration:
        hours = duration // 3600
        minutes = (duration % 3600) // 60
        seconds = duration % 60

        if hours > 0:
            dur_str = f"{hours}h {minutes}min {seconds}s"
        else:
            dur_str = f"{minutes}min {seconds}s"
    else:
        dur_str = "???"

    print(f"{prefix}{title}")
    print(f"    Canal: {channel}")
    print(f"    Duração: {dur_str}")
    print(f"    ID: {video.get('video_id')}")
    print()


def print_playlist(playlist: dict, index: int = None):
    """Imprime informações de uma playlist."""
    prefix = f"{index}. " if index is not None else ""
    title = playlist.get("title", "Sem título")
    count = playlist.get("item_count", 0)

    print(f"{prefix}{title}")
    print(f"    Vídeos: {count}")
    print(f"    ID: {playlist.get('id')}")
    print()


def test_favorites(client: YouTubeAPIClient):
    """Testa listar favoritos."""
    print_section("FAVORITOS (Liked Videos)")

    try:
        favorites = client.get_playlist_items(
            playlist_id="LL",
            max_results=10
        )

        if not favorites:
            print("Nenhum vídeo favorito encontrado.")
            return

        print(f"Total: {len(favorites)} vídeos (mostrando primeiros 10)\n")

        for i, video in enumerate(favorites, 1):
            print_video(video, i)

    except Exception as e:
        print(f"❌ Erro: {e}")


def test_watch_later(client: YouTubeAPIClient):
    """Testa lista Assistir Mais Tarde."""
    print_section("ASSISTIR MAIS TARDE (Watch Later)")

    try:
        watch_later = client.get_playlist_items(
            playlist_id="WL",
            max_results=10
        )

        if not watch_later:
            print("Nenhum vídeo na lista Assistir Mais Tarde.")
            return

        print(f"Total: {len(watch_later)} vídeos (mostrando primeiros 10)\n")

        for i, video in enumerate(watch_later, 1):
            print_video(video, i)

    except Exception as e:
        print(f"❌ Erro: {e}")


def test_my_playlists(client: YouTubeAPIClient):
    """Testa listar playlists do usuário."""
    print_section("MINHAS PLAYLISTS")

    try:
        playlists = client.get_my_playlists(max_results=20)

        if not playlists:
            print("Nenhuma playlist encontrada.")
            return

        print(f"Total: {len(playlists)} playlists\n")

        for i, playlist in enumerate(playlists, 1):
            print_playlist(playlist, i)

    except Exception as e:
        print(f"❌ Erro: {e}")


def test_video_details(client: YouTubeAPIClient):
    """Testa buscar detalhes de um vídeo."""
    print_section("DETALHES DE VÍDEO")

    # Rick Roll como exemplo
    video_id = "dQw4w9WgXcQ"

    try:
        details = client.get_video_details(video_id)

        if details:
            print(f"Vídeo: {details.get('title')}")
            print(f"Canal: {details.get('channel')}")
            print(f"Duração: {details.get('duration_formatted')}")
            print(f"Publicado: {details.get('published_at')}")
            print(f"Thumbnail: {details.get('thumbnail')}")

            # Primeiras 200 chars da descrição
            desc = details.get('description', '')[:200]
            print(f"Descrição: {desc}...")
        else:
            print(f"Vídeo {video_id} não encontrado.")

    except Exception as e:
        print(f"❌ Erro: {e}")


def main():
    """Função principal."""
    # Get OAuth token from environment
    token = os.getenv("GOOGLE_OAUTH_TOKEN")

    if not token:
        print("❌ GOOGLE_OAUTH_TOKEN não encontrado!")
        print("\nPara usar:")
        print("  export GOOGLE_OAUTH_TOKEN=seu_token_aqui")
        print("  python scripts/youtube_api_test.py")
        return 1

    # Initialize client
    try:
        client = YouTubeAPIClient(access_token=token)
        print("✅ Cliente YouTube inicializado com sucesso!\n")
    except Exception as e:
        print(f"❌ Erro ao inicializar cliente: {e}")
        return 1

    # Run tests
    test_video_details(client)
    test_my_playlists(client)
    test_favorites(client)
    test_watch_later(client)

    print_section("✅ TESTES CONCLUÍDOS")
    print("Se tudo funcionou, a integração está pronta!")

    return 0


if __name__ == "__main__":
    sys.exit(main())
