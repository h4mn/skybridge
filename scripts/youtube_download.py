#!/usr/bin/env python3
"""
Script para baixar e processar vídeos YouTube.

Uso:
    python scripts/youtube_download.py <url> [--tags tag1,tag2]
"""

import asyncio
import json
import sys
from datetime import datetime
from pathlib import Path

# Adiciona o projeto ao path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.core.youtube.infrastructure.yt_dlp_adapter import YtDlpAdapter
from src.core.youtube.domain import Video, VideoId, VideoMetadata


async def main():
    if len(sys.argv) < 2:
        print("Uso: python youtube_download.py <url> [--tags tag1,tag2]")
        sys.exit(1)

    url = sys.argv[1]
    tags = []

    if "--tags" in sys.argv:
        tag_idx = sys.argv.index("--tags")
        if tag_idx + 1 < len(sys.argv):
            tags = sys.argv[tag_idx + 1].split(",")

    download_path = Path("data/youtube")
    adapter = YtDlpAdapter(download_path)

    print(f"[INFO] Processando: {url}")
    print(f"[INFO] Pasta: {download_path}")

    # Extrair ID
    video_id = await adapter.extract_video_id(url)
    print(f"[INFO] Video ID: {video_id}")

    # Obter metadados
    metadata = await adapter.get_metadata(url)
    print(f"[INFO] Título: {metadata.title}")
    print(f"[INFO] Canal: {metadata.channel}")
    print(f"[INFO] Duração: {metadata.duration_seconds}s")

    # Baixar vídeo em formato adequado para MCP (menos de 8MB)
    # Tenta baixar 360p primeiro, senão 480p, senão áudio
    print(f"[INFO] Baixando vídeo...")

    video_path = download_path / f"{video_id}_360p.mp4"
    if not video_path.exists():
        # Baixar formato 396 (360p mp4)
        import subprocess
        proc = await asyncio.create_subprocess_exec(
            "yt-dlp", "-f", "396", "-o", str(video_path), url,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        await proc.communicate()

    if video_path.exists():
        file_size = video_path.stat().st_size / (1024 * 1024)  # MB
        print(f"[OK] Vídeo baixado: {video_path} ({file_size:.2f}MB)")

        if file_size > 8:
            print("[WARN] Arquivo muito grande para MCP Analyzer (>8MB)")
            print(f"   Para análise manual, use:")
            print(f"   mcp__zai-mcp-server__analyze_video {video_path}")
    else:
        print(f"[ERROR] Falha ao baixar vídeo")

    # Criar JSON com metadados
    output_data = {
        "video_id": video_id,
        "url": url,
        "title": metadata.title,
        "channel": metadata.channel,
        "duration_seconds": metadata.duration_seconds,
        "upload_date": metadata.upload_date.isoformat() if metadata.upload_date else None,
        "thumbnail_url": metadata.thumbnail_url,
        "description": metadata.description,
        "tags": tags,
        "local_path": str(video_path) if video_path.exists() else None,
        "processed_at": datetime.now().isoformat(),
    }

    output_file = download_path / f"{video_id}_metadata.json"
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(output_data, f, indent=2, ensure_ascii=False)

    print(f"[OK] Metadados salvos: {output_file}")
    print(f"[INFO] Tags: {', '.join(tags) if tags else 'nenhuma'}")
    print(f"[OK] Processamento concluído!")


if __name__ == "__main__":
    asyncio.run(main())
