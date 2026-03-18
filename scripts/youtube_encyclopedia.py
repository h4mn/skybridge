#!/usr/bin/env python3
"""
CLI para Enciclopédia YouTube

Uso:
    python scripts/youtube_encyclopedia.py process <url> --tag arquitetura
    python scripts/youtube_encyclopedia.py search "circuit breaker"
"""

import asyncio
import sys
from pathlib import Path

# Adiciona o projeto ao path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.core.youtube.application import YouTubeVideoService


async def main():
    if len(sys.argv) < 2:
        print("Uso:")
        print("  python youtube_encyclopedia.py process <url> [--tag TAG1,TAG2]")
        print("  python youtube_encyclopedia.py search <query>")
        sys.exit(1)

    command = sys.argv[1]
    service = YouTubeVideoService()

    if command == "process":
        if len(sys.argv) < 3:
            print("Erro: URL do vídeo é obrigatória")
            sys.exit(1)

        url = sys.argv[2]
        tags = []

        if "--tag" in sys.argv:
            tag_idx = sys.argv.index("--tag")
            if tag_idx + 1 < len(sys.argv):
                tags = sys.argv[tag_idx + 1].split(",")

        print(f"🎬 Processando vídeo: {url}")
        print(f"🏷️  Tags: {tags if tags else 'nenhuma'}")

        video = await service.process_and_index(url, tags=tags)

        print(f"✅ Vídeo processado:")
        print(f"   Título: {video.metadata.title}")
        print(f"   Canal: {video.metadata.channel}")
        print(f"   Duração: {video.metadata.duration_seconds}s")
        print(f"   Indexado: {video.is_indexed}")

    elif command == "search":
        if len(sys.argv) < 3:
            print("Erro: Query de busca é obrigatória")
            sys.exit(1)

        query = sys.argv[2]
        print(f"🔍 Buscando: {query}")

        results = await service.search_encyclopedia(query)

        if not results:
            print("Nenhum resultado encontrado")
        else:
            print(f"✅ Encontrados {len(results)} vídeos:")
            for video in results:
                print(f"   - {video.metadata.title}")
                print(f"     {video.metadata.channel}")
                print(f"     Tags: {', '.join(video.tags)}")

    else:
        print(f"Comando desconhecido: {command}")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
