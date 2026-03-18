"""Serviço de transcrição placeholder."""

from pathlib import Path


class TranscriptionService:
    """Serviço para transcrição de vídeos."""

    async def transcribe(self, video_path: str | Path) -> str:
        """Transcreve o áudio do vídeo."""
        return "Transcrição placeholder"
