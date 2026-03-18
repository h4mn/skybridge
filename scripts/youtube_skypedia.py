#!/usr/bin/env python3
"""
CLI para Skypedia - Enciclopédia de Vídeos da Sky

Uso:
    python scripts/youtube_skypedia.py add <url> --tag tag1,tag2
    python scripts/youtube_skypedia.py search "texto para buscar"
    python scripts/youtube_skypedia.py stats
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
        print("  youtube_skypedia.py add <url> [--tag TAG1,TAG2]")
        print("  youtube_skypedia.py search <query>")
        print("  youtube_skypedia.py stats")
        sys.exit(1)

    command = sys.argv[1]
    service = YouTubeVideoService()

    if command == "add":
        if len(sys.argv) < 3:
            print("Erro: URL do video é obrigatória")
            sys.exit(1)

        url = sys.argv[2]
        tags = []

        if "--tag" in sys.argv:
            tag_idx = sys.argv.index("--tag")
            if tag_idx + 1 < len(sys.argv):
                tags = sys.argv[tag_idx + 1].split(",")

        print(f"[INFO] Processando vídeo: {url}")
        print(f"[INFO] Tags: {tags if tags else 'nenhuma'}")

        result = await service.process_and_index(url, tags)

        print(f"\n[OK] Vídeo processado e indexado!")
        print(f"   Título: {result['video'].metadata.title}")
        print(f"   Canal: {result['video'].metadata.channel}")
        print(f"   Memory ID: {result['memory_id']}")

        # Mostrar topics se disponíveis
        if result['analysis'].get('topics'):
            print(f"   Tópicos: {', '.join(result['analysis']['topics'][:5])}")

        # Mostrar summary se disponível
        if result['analysis'].get('summary'):
            summary = result['analysis']['summary']
            if len(summary) > 200:
                summary = summary[:200] + "..."
            print(f"\n   Resumo: {summary}")

    elif command == "search":
        if len(sys.argv) < 3:
            print("Erro: Query de busca é obrigatória")
            sys.exit(1)

        query = sys.argv[2]
        print(f"[INFO] Buscando na Skypedia: {query}")

        results = await service.search_skypedia(query, limit=5)

        if not results:
            print("[INFO] Nenhum resultado encontrado")
        else:
            print(f"\n[OK] Encontrados {len(results)} resultados:\n")
            for i, r in enumerate(results, 1):
                print(f"{i}. [distância: {r['distance']:.3f}]")
                # Extrair título do conteúdo (primeira linha após #)
                lines = r['content'].split('\n')
                title = lines[0] if lines else "Sem título"
                print(f"   {title}")

                # Mostrar preview do conteúdo
                content_lines = r['content'].split('\n')[2:]  # Pular título
                preview = ' '.join(content_lines[:3])
                if len(preview) > 150:
                    preview = preview[:150] + "..."
                print(f"   {preview}\n")

    elif command == "stats":
        stats = await service.get_skypedia_stats()
        print(f"[INFO] Estatísticas da Skypedia:")
        print(f"   Total de vídeos: {stats.get('count', 0)}")

    else:
        print(f"Comando desconhecido: {command}")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
