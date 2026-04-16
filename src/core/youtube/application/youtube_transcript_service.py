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
from ..infrastructure.youtube_state_repository import YouTubeStateRepository, VideoState


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
    transcribed_at: Optional[datetime] = None

    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.now()


class YoutubeTranscriptService:
    """
    Serviço de transcrição de vídeos YouTube.

    Orquestra:
    1. Verifica estado (SQLite)
    2. Download de áudio (yt-dlp + rate-limit)
    3. Transcrição (faster-whisper local)
    4. Salvamento em arquivo + atualização de estado

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
        analyzer: Optional[TranscriptionAdapter] = None,
        state_repo: Optional[YouTubeStateRepository] = None,
        state_db_path: str = "data/youtube_copilot.db"
    ):
        """
        Inicializa serviço.

        Args:
            output_path: Diretório padrão para transcrições
            yt_dlp: Adaptador yt-dlp (opcional)
            analyzer: Adaptador de transcrição (opcional)
            state_repo: Repositório de estado (opcional)
            state_db_path: Caminho para banco de estado (opcional)
        """
        self._output_path = output_path
        self._output_path.mkdir(parents=True, exist_ok=True)

        # Setup do State Repository se necessário
        if state_repo is None:
            from ..infrastructure.youtube_state_setup import setup_youtube_state
            setup_youtube_state(state_db_path)
            state_repo = YouTubeStateRepository(db_path=state_db_path)

        # Dependências
        self._yt_dlp = yt_dlp or YtDlpAdapter(download_path=output_path / "audio")
        self._analyzer = analyzer or TranscriptionAdapter()
        self._state_repo = state_repo

    async def transcribe_video(
        self,
        url: str,
        output_path: Optional[Path] = None,
        force: bool = False
    ) -> TranscriptResult:
        """
        Transcreve vídeo YouTube completo.

        Fluxo:
        1. Verifica estado (se já transcrito e !force, retorna resultado)
        2. Baixa áudio (yt-dlp + rate-limit)
        3. Transcreve (faster-whisper)
        4. Salva em arquivo + marca como transcrito no estado

        Args:
            url: URL do vídeo YouTube
            output_path: Caminho para salvar transcrição (opcional)
            force: Força nova transcrição mesmo se já existe (default: False)

        Returns:
            TranscriptResult com texto e metadados
        """
        # Extrair video_id
        video_id = await self._yt_dlp.extract_video_id(url)

        # 1. Verificar estado (se já transcrito e !force, retorna)
        if not force:
            existing = self._state_repo.get_video(video_id)
            if existing and existing.transcribed_at and output_path and Path(output_path).exists():
                # Já transcrito, retorna resultado existente
                with open(output_path, 'r', encoding='utf-8') as f:
                    text = f.read()

                return TranscriptResult(
                    text=text,
                    language=existing.status,
                    confidence=1.0,
                    output_path=Path(output_path),
                    duration_seconds=existing.duration_seconds,
                    transcribed_at=existing.transcribed_at
                )

        # 2. Determinar output_path
        if output_path is None:
            output_path = self._output_path / f"{video_id}.txt"

        # Criar diretórios pai
        output_path.parent.mkdir(parents=True, exist_ok=True)

        # 3. Obter metadados do vídeo
        try:
            metadata = await self._yt_dlp.get_metadata(url)
        except Exception:
            metadata = None

        # 4. Adicionar ao estado se não existe
        if not self._state_repo.get_video(video_id) and metadata:
            video_state = VideoState(
                video_id=video_id,
                title=metadata.title,
                channel=metadata.channel,
                duration_seconds=metadata.duration_seconds,
                playlist_id="manual",  # Transcrição manual
                added_at=datetime.now()
            )
            self._state_repo.save_video(video_state)

        # 5. Download áudio (com rate-limit)
        audio_path = await self._yt_dlp.download_audio_only(url)

        # 6. Transcrever
        transcription = await self._analyzer.transcribe(audio_path)

        # 7. Salvar transcrição em arquivo
        self._save_transcription(transcription, output_path)

        # 8. Marcar como transcrito no estado
        self._state_repo.mark_as_transcribed(video_id)

        return TranscriptResult(
            text=transcription.text,
            language=transcription.language,
            confidence=transcription.confidence,
            output_path=output_path,
            duration_seconds=transcription.duration_seconds,
            audio_path=audio_path,
            transcribed_at=datetime.now()
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
        from datetime import datetime

        content = f"""# Transcrição YouTube

Data: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
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
