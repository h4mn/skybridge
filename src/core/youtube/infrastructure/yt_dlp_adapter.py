"""Adaptador para yt-dlp - Download de vídeos e legendas YouTube."""

import asyncio
import json
import subprocess
from pathlib import Path
from typing import Dict, Optional

from ..domain.video import VideoMetadata


class YtDlpAdapter:
    """
    Adaptador para yt-dlp (fork do youtube-dl).

    Funcionalidades:
        - Download de vídeos (MP4)
        - Extração de legendas (SRT/VTT)
        - Metadados do vídeo
    """

    def __init__(self, download_path: Path):
        self._download_path = download_path
        self._download_path.mkdir(parents=True, exist_ok=True)

    async def extract_video_id(self, url: str) -> str:
        """Extrai o ID do vídeo da URL."""
        # Formatos suportados:
        # youtube.com/watch?v=ID
        # youtu.be/ID
        # youtube.com/shorts/ID
        import re

        patterns = [
            r"youtube\.com/watch\?v=([^&]+)",
            r"youtu\.be/([^?]+)",
            r"youtube\.com/shorts/([^?]+)",
        ]

        for pattern in patterns:
            match = re.search(pattern, url)
            if match:
                return match.group(1)

        raise ValueError(f"Could not extract video ID from URL: {url}")

    async def get_metadata(self, url: str) -> VideoMetadata:
        """
        Obtém metadados do vídeo sem baixar.

        Returns:
            VideoMetadata com título, canal, duração, etc.
        """
        cmd = [
            "yt-dlp",
            "--dump-json",
            "--no-playlist",
            url,
        ]

        proc = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )

        stdout, stderr = await proc.communicate()

        if proc.returncode != 0:
            raise RuntimeError(f"yt-dlp failed: {stderr.decode()}")

        data = json.loads(stdout.decode())

        return VideoMetadata(
            title=data.get("title", "Unknown"),
            channel=data.get("channel", "Unknown"),
            duration_seconds=int(data.get("duration", 0)),
            upload_date=self._parse_upload_date(data.get("upload_date")),
            thumbnail_url=data.get("thumbnail"),
            description=data.get("description"),
        )

    async def download_video(self, url: str) -> Path:
        """
        Baixa o vídeo completo em MP4.

        Returns:
            Path para o arquivo baixado
        """
        video_id = await self.extract_video_id(url)
        output_path = self._download_path / f"{video_id}.mp4"

        cmd = [
            "yt-dlp",
            "--format", "mp4",
            "--output", str(output_path),
            "--no-playlist",
            url,
        ]

        proc = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )

        stdout, stderr = await proc.communicate()

        if proc.returncode != 0:
            raise RuntimeError(f"Download failed: {stderr.decode()}")

        return output_path

    async def download_subtitles_only(self, url: str) -> Path:
        """
        Baixa apenas as legendas (mais rápido, sem vídeo).

        Retorna o caminho para o arquivo de legendas (.srt ou .vtt)
        """
        video_id = await self.extract_video_id(url)

        # Tenta baixar legenda em português, depois inglês, depois qualquer uma
        cmd = [
            "yt-dlp",
            "--write-subs",
            "--sub-lang", "pt,en",
            "--skip-download",
            "--sub-format", "srt",
            "--output", str(self._download_path / f"{video_id}.%(ext)s"),
            "--no-playlist",
            url,
        ]

        proc = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )

        stdout, stderr = await proc.communicate()

        # Retorna o caminho do arquivo de legendas (mesmo se vazar para o vídeo)
        return self._download_path / f"{video_id}.srt"

    async def download_lightweight(self, url: str) -> Path:
        """
        Baixa vídeo em formato leve para análise (360p MP4).

        Formato 396 é ideal para MCP Analyzer (< 8MB):
        - Resolução: 640x360
        - Codec: av01 (AV1) - compacto
        - Tamanho típico: 5-8MB para 10min

        Returns:
            Path para o arquivo baixado
        """
        video_id = await self.extract_video_id(url)
        output_path = self._download_path / f"{video_id}_360p.mp4"

        # Se já existe, retorna
        if output_path.exists():
            return output_path

        # Baixar formato 396 (360p AV1)
        cmd = [
            "yt-dlp",
            "-f", "396",
            "-o", str(output_path),
            "--no-playlist",
            url,
        ]

        proc = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )

        stdout, stderr = await proc.communicate()

        if proc.returncode != 0:
            # Fallback: tentar formato 18 (360p h264)
            output_path_fallback = self._download_path / f"{video_id}_360p_h264.mp4"
            cmd_fallback = [
                "yt-dlp",
                "-f", "18",
                "-o", str(output_path_fallback),
                "--no-playlist",
                url,
            ]
            proc_fallback = await asyncio.create_subprocess_exec(
                *cmd_fallback,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            stdout_fallback, stderr_fallback = await proc_fallback.communicate()

            if proc_fallback.returncode != 0:
                raise RuntimeError(f"Download failed: {stderr.decode()}")

            return output_path_fallback

        return output_path

    def _parse_upload_date(self, date_str: Optional[str]) -> Optional[str]:
        """Converte YYYYMMDD para datetime."""
        if not date_str:
            return None
        from datetime import datetime

        try:
            return datetime.strptime(date_str, "%Y%m%d")
        except ValueError:
            return None
