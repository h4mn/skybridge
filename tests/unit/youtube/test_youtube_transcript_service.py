"""Testes para YoutubeTranscriptService.

DOC: src/core/youtube/application/youtube_transcript_service.py
Metodologia: TDD Estrito (RED → GREEN → REFACTOR)

Fluxo:
    URL → yt-dlp (áudio) → faster-whisper (transcrição) → Arquivo
"""

import pytest
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock


@pytest.mark.unit
class TestYoutubeTranscriptService:
    """Testes do serviço de transcrição YouTube."""

    def test_init_creates_dependencies(self, tmp_path):
        """Testa que cria dependências."""
        from src.core.youtube import YoutubeTranscriptService

        service = YoutubeTranscriptService(output_path=tmp_path)

        assert service._yt_dlp is not None
        assert service._analyzer is not None
        assert service._output_path == tmp_path

    @pytest.mark.asyncio
    async def test_transcribe_video_complete_flow(self, tmp_path):
        """Testa fluxo completo: download áudio + transcrição."""
        from src.core.youtube import YoutubeTranscriptService

        service = YoutubeTranscriptService(output_path=tmp_path)

        # Mock completo
        mock_audio_path = Path("audio.mp3")
        mock_trans_result = MagicMock()
        mock_trans_result.text = "Texto transcrito"
        mock_trans_result.language = "pt"
        mock_trans_result.confidence = 0.92
        mock_trans_result.duration_seconds = 120.0

        async def mock_download(url):
            return mock_audio_path

        async def mock_transcribe(path):
            return mock_trans_result

        service._yt_dlp.download_audio_only = mock_download
        service._analyzer.transcribe = mock_transcribe

        output_path = tmp_path / "transcricao.txt"
        result = await service.transcribe_video(
            url="https://youtube.com/watch?v=abc123",
            output_path=output_path
        )

        assert output_path.exists()
        content = output_path.read_text(encoding="utf-8")
        assert "Texto transcrito" in content
        assert result.text == "Texto transcrito"

    @pytest.mark.asyncio
    async def test_transcribe_video_uses_output_path(self, tmp_path):
        """Testa que usa o output_path fornecido."""
        from src.core.youtube import YoutubeTranscriptService

        service = YoutubeTranscriptService(output_path=tmp_path)

        async def mock_download(url):
            return Path("audio.mp3")

        async def mock_transcribe(path):
            m = MagicMock()
            m.text = "Transcrição teste"
            m.language = "pt"
            m.confidence = 0.88
            m.duration_seconds = 60.0
            return m

        service._yt_dlp.download_audio_only = mock_download
        service._analyzer.transcribe = mock_transcribe

        custom_output = tmp_path / "custom" / "saida.txt"
        result = await service.transcribe_video(
            url="https://youtube.com/watch?v=xyz789",
            output_path=custom_output
        )

        assert custom_output.parent.exists()
        assert custom_output.exists()
        assert result.output_path == custom_output

    @pytest.mark.asyncio
    async def test_transcribe_video_creates_parent_dirs(self, tmp_path):
        """Testa que cria diretórios pai se não existirem."""
        from src.core.youtube import YoutubeTranscriptService

        service = YoutubeTranscriptService(output_path=tmp_path)

        async def mock_download(url):
            return Path("audio.mp3")

        async def mock_transcribe(path):
            m = MagicMock()
            m.text = "Diretório criado"
            m.language = "pt"
            m.confidence = 0.90
            m.duration_seconds = 90.0
            return m

        service._yt_dlp.download_audio_only = mock_download
        service._analyzer.transcribe = mock_transcribe

        nested_output = tmp_path / "nivel1" / "nivel2" / "saida.txt"
        result = await service.transcribe_video(
            url="https://youtube.com/watch?v=nested",
            output_path=nested_output
        )

        assert nested_output.parent.exists()
        assert nested_output.exists()


@pytest.mark.unit
class TestTranscriptResult:
    """Testes do resultado de transcrição."""

    def test_create_result(self):
        """Testa criação de resultado."""
        from src.core.youtube import TranscriptResult

        result = TranscriptResult(
            text="Texto da transcrição",
            language="pt",
            confidence=0.92,
            output_path=Path("output.txt"),
            duration_seconds=120
        )

        assert result.text == "Texto da transcrição"
        assert result.language == "pt"
        assert result.confidence == 0.92
        assert result.output_path == Path("output.txt")
        assert result.duration_seconds == 120
