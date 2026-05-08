#!/usr/bin/env python3
"""CLI para listar vídeos favoritos do YouTube organizados por playlist.

Requer:
    - pip install google-api-python-client python-dotenv requests
    - Credenciais OAuth 2.0 (refresh token)

Funcionalidades:
    - Listar playlists do usuário
    - Mostrar vídeos de uma playlist selecionada
    - Formatar duração e informações dos vídeos
"""

import sys
import os
from pathlib import Path
from typing import List, Dict, Any, Optional
from dotenv import load_dotenv

# Adicionar src ao path para imports
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root / "src"))

from core.youtube.infrastructure.youtube_api_client import YouTubeAPIClient


def refresh_access_token(
    client_id: str,
    client_secret: str,
    refresh_token: str
) -> str:
    """Obtém novo access token usando refresh token.

    Args:
        client_id: OAuth 2.0 Client ID
        client_secret: OAuth 2.0 Client Secret
        refresh_token: OAuth 2.0 Refresh Token

    Returns:
        Access token válido

    Raises:
        ValueError: Se credenciais forem inválidas
    """
    import requests

    token_url = "https://oauth2.googleapis.com/token"

    data = {
        "client_id": client_id,
        "client_secret": client_secret,
        "refresh_token": refresh_token,
        "grant_type": "refresh_token"
    }

    response = requests.post(token_url, data=data)

    if response.status_code != 200:
        raise ValueError(
            f"Erro ao renovar token: {response.status_code}\n"
            f"Response: {response.text}"
        )

    token_data = response.json()
    return token_data["access_token"]


def format_duration(seconds: Optional[int]) -> str:
    """Formata segundos para HH:MM:SS.

    Args:
        seconds: Duração em segundos (None retorna "???")

    Returns:
        String formatada (HH:MM:SS ou MM:SS)
    """
    if seconds is None:
        return "???"

    hours = seconds // 3600
    minutes = (seconds % 3600) // 60
    secs = seconds % 60

    if hours > 0:
        return f"{hours:02d}:{minutes:02d}:{secs:02d}"
    else:
        return f"{minutes:02d}:{secs:02d}"


def print_videos(videos: List[Dict[str, Any]], max_count: int = 10) -> None:
    """Imprime lista de vídeos formatada.

    Args:
        videos: Lista de vídeos com video_id, title, channel, duration_seconds
        max_count: Máximo de vídeos a imprimir
    """
    for i, video in enumerate(videos[:max_count], 1):
        duration = format_duration(video.get("duration_seconds"))

        print(f"\n  [{i}] {video['title']}")
        print(f"      Canal: {video['channel']}")
        print(f"      Duração: {duration}")
        print(f"      URL: https://youtube.com/watch?v={video['video_id']}")


def main() -> int:
    """Função principal.

    Returns:
        0 em sucesso, 1 em erro
    """
    # Carregar .env do projeto
    env_path = project_root / ".env"
    load_dotenv(env_path)

    # Ler credenciais do .env
    client_id = os.getenv("YOUTUBE_CLIENT_ID")
    client_secret = os.getenv("YOUTUBE_CLIENT_SECRET")
    refresh_token = os.getenv("YOUTUBE_REFRESH_TOKEN")

    if not all([client_id, client_secret, refresh_token]):
        print("❌ Erro: Credenciais não encontradas no .env")
        print("\nCertifique-se que .env contém:")
        print("  YOUTUBE_CLIENT_ID=...")
        print("  YOUTUBE_CLIENT_SECRET=...")
        print("  YOUTUBE_REFRESH_TOKEN=...")
        return 1

    print("🔐 Renovando access token...")
    try:
        access_token = refresh_access_token(client_id, client_secret, refresh_token)
        print("✅ Token renovado com sucesso!")
    except Exception as e:
        print(f"❌ Erro ao renovar token: {e}")
        return 1

    print("🔌 Conectando ao YouTube...")
    try:
        client = YouTubeAPIClient(access_token)
    except Exception as e:
        print(f"❌ Erro ao criar cliente: {e}")
        return 1

    # Listar playlists do usuário
    print("\n📋 Buscando suas playlists...")
    try:
        playlists = client.get_my_playlists(max_results=50)

        if not playlists:
            print("❌ Nenhuma playlist encontrada")
            return 1

        print(f"\n✅ Encontradas {len(playlists)} playlists:\n")

        # Mostrar playlists disponíveis
        for i, playlist in enumerate(playlists, 1):
            print(f"{i}. {playlist['title']}")
            print(f"   ID: {playlist['id']}")
            print(f"   Vídeos: {playlist['item_count']}")
            if playlist.get('description'):
                desc = playlist['description'][:80]
                if len(playlist['description']) > 80:
                    desc += "..."
                print(f"   Descrição: {desc}")
            print()

        # Perguntar qual playlist explorar
        try:
            choice = input("\n🔍 Digite o número da playlist para ver os últimos 10 vídeos (ou Enter para Favoritos/LL): ").strip()

            if choice == "":
                # Default: Favoritos (LL)
                playlist_id = "LL"
                playlist_name = "Favoritos (Liked Videos)"
            else:
                idx = int(choice) - 1
                if 0 <= idx < len(playlists):
                    playlist_id = playlists[idx]['id']
                    playlist_name = playlists[idx]['title']
                else:
                    print("❌ Escolha inválida")
                    return 1

        except (ValueError, KeyboardInterrupt):
            print("\n⚠️  Usando padrão: Favoritos (LL)")
            playlist_id = "LL"
            playlist_name = "Favoritos (Liked Videos)"

        # Listar vídeos da playlist escolhida
        print(f"\n📺 Buscando últimos 10 vídeos de: {playlist_name}...\n")

        videos = client.get_playlist_items(
            playlist_id=playlist_id,
            max_results=10
        )

        if not videos:
            print("❌ Nenhum vídeo encontrado nesta playlist")
            return 0

        print(f"✅ Encontrados {len(videos)} vídeos:\n")
        print_videos(videos, max_count=10)

        print(f"\n" + "="*60)
        print(f"Total: {len(videos)} vídeos em '{playlist_name}'")
        print("="*60)

        # Perguntar se quer ingerir algum vídeo
        print("\n💡 Dica: Para ingerir um vídeo no Sky Memory, copie a URL acima!")
        return 0

    except Exception as e:
        print(f"❌ Erro: {e}")
        import traceback
        traceback.print_exc()
        print("\nPossíveis causas:")
        print("  - Token expirado (gere um novo)")
        print("  - Sem permissão youtube.readonly")
        print("  - Problema de conexão")
        return 1


if __name__ == "__main__":
    sys.exit(main())
