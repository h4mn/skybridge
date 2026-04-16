"""YoutubeTranscriptService - Serviço de transcrição YouTube.

Fluxo completo:
    URL → yt-dlp (áudio) → faster-whisper (transcrição) → Arquivo

Metodologia: TDD Estrito
"""

import asyncio
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Optional

from ..infrastructure.yt_dlp_adapter import YtDlpAdapter
from ..infrastructure.transcription_adapter import TranscriptionAdapter, TranscriptionResult


@dataclass
class TranscriptResult:
    """Resultado do serviço de transcrição."""
    text: str
    language: str
    confidence: float
    output_path: Path
    duration_seconds: float = 0.0
    audio_path: Optional[Path] = None
    created_at: datetime = None

    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.now()


class YoutubeTranscriptService:
    """
    Serviço de transcrição de vídeos YouTube.

    Orquestra:
    1. Download de áudio (yt-dlp + rate-limit)
    2. Transcrição (faster-whisper local)
    3. Salvamento em arquivo

    Uso:
        service = YoutubeTranscriptService()
        result = await service.transcribe_video(
            url="https://youtube.com/watch?v=abc123",
            output_path=Path("transcricoes/video.txt")
        )
    """

    def __init__(
        self,
        output_path: Path = Path("data/transcricoes"),
        yt_dlp: Optional[YtDlpAdapter] = None,
        analyzer: Optional[TranscriptionAdapter] = None
    ):
        """
        Inicializa serviço.

        Args:
            output_path: Diretório padrão para transcrições
            yt_dlp: Adaptador yt-dlp (opcional)
            analyzer: Adaptador de transcrição (opcional)
        """
        self._output_path = output_path
        self._output_path.mkdir(parents=True, exist_ok=True)

        # Dependências
        self._yt_dlp = yt_dlp or YtDlpAdapter(download_path=output_path / "audio")
        self._analyzer = analyzer or TranscriptionAdapter()

    async def transcribe_video(
        self,
        url: str,
        output_path: Optional[Path] = None
    ) -> TranscriptResult:
        """
        Transcreve vídeo YouTube completo.

        Fluxo:
        1. Baixa áudio (yt-dlp + rate-limit)
        2. Transcreve (faster-whisper)
        3. Salva em arquivo

        Args:
            url: URL do vídeo YouTube
            output_path: Caminho para salvar transcrição (opcional)

        Returns:
            TranscriptResult com texto e metadados
        """
        # 1. Determinar output_path
        if output_path is None:
            video_id = await self._yt_dlp.extract_video_id(url)
            output_path = self._output_path / f"{video_id}.txt"

        # Criar diretórios pai
        output_path.parent.mkdir(parents=True, exist_ok=True)

        # 2. Download áudio (com rate-limit)
        audio_path = await self._yt_dlp.download_audio_only(url)

        # 3. Transcrever
        transcription = await self._analyzer.transcribe(audio_path)

        # 4. Salvar transcrição em arquivo
        self._save_transcription(transcription, output_path)

        return TranscriptResult(
            text=transcription.text,
            language=transcription.language,
            confidence=transcription.confidence,
            output_path=output_path,
            duration_seconds=transcription.duration_seconds,
            audio_path=audio_path
        )

    def _save_transcription(
        self,
        transcription: TranscriptionResult,
        output_path: Path
    ) -> None:
        """
        Salva transcrição em arquivo.

        Args:
            transcription: Resultado da transcrição
            output_path: Caminho para salvar
        """
        content = f"""# Transcrição YouTube

Data: {transcription.created_at.strftime('%Y-%m-%d %H:%M:%S')}
Idioma: {transcription.language}
Confiança: {transcription.confidence:.2%}

{transcription.text}
"""

        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(content)

    async def transcribe_batch(
        self,
        urls: list[str],
        output_dir: Optional[Path] = None
    ) -> list[TranscriptResult]:
        """
        Transcreve múltiplos vídeos em lote.

        Args:
            urls: Lista de URLs YouTube
            output_dir: Diretório para salvar (opcional)

        Returns:
            Lista de TranscriptResult
        """
        if output_dir is None:
            output_dir = self._output_path / "batch"

        results = []
        for url in urls:
            try:
                result = await self.transcribe_video(url)
                results.append(result)
            except Exception as e:
                print(f"⚠️  Erro ao transcrever {url}: {e}")
                continue

        return results
