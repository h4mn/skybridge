"""Testes de integração YoutubeTranscriptService + State Repository.

DOC: src/core/youtube/application/youtube_transcript_service.py
Metodologia: TDD Estrito (RED → GREEN → REFACTOR)

Funcionalidade:
    - Verificar estado antes de transcrever
    - Marcar vídeo como transcrito após sucesso
    - Adicionar vídeo ao estado se não existir
"""

import pytest
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime


@pytest.mark.unit
class TestYoutubeTranscriptServiceState:
    """Testes de integração com State Repository."""

    def test_init_creates_state_repository(self, tmp_path):
        """Testa que cria State Repository."""
        from src.core.youtube import YoutubeTranscriptService

        service = YoutubeTranscriptService(output_path=tmp_path)

        assert service._state_repo is not None
        assert service._state_repo.db_path == "data/youtube_copilot.db"

    @pytest.mark.asyncio
    async def test_transcribe_marks_as_transcribed(self, tmp_path):
        """Testa que marca vídeo como transcrito após sucesso."""
        from src.core.youtube import YoutubeTranscriptService
        from src.core.youtube import VideoState

        service = YoutubeTranscriptService(output_path=tmp_path)

        # Mock componentes
        mock_audio_path = Path("audio.mp3")
        mock_trans_result = MagicMock()
        mock_trans_result.text = "Texto transcrito"
        mock_trans_result.language = "pt"
        mock_trans_result.confidence = 0.92
        mock_trans_result.duration_seconds = 120.0

        async def mock_download(url):
            return mock_audio_path

        async def mock_extract_id(url):
            return "abc123"

        async def mock_transcribe(path):
            return mock_trans_result

        service._yt_dlp.download_audio_only = mock_download
        service._yt_dlp.extract_video_id = mock_extract_id
        service._yt_dlp.get_metadata = Mock(return_value=MagicMock(
            title="Vídeo Teste",
            channel="Canal Teste",
            duration_seconds=120
        ))
        service._analyzer.transcribe = mock_transcribe

        output_path = tmp_path / "transcricao.txt"
        result = await service.transcribe_video(
            url="https://youtube.com/watch?v=abc123",
            output_path=output_path
        )

        # Verificar que marcamos como transcrito
        video_state = service._state_repo.get_video("abc123")
        assert video_state is not None
        assert video_state.transcribed_at is not None
        assert video_state.status == "transcribed"
        assert result.text == "Texto transcrito"

    @pytest.mark.asyncio
    async def test_transcribe_skips_if_already_transcribed(self, tmp_path):
        """Testa que pula transcrição se já foi transcrito."""
        from src.core.youtube import YoutubeTranscriptService
        from src.core.youtube import VideoState

        service = YoutubeTranscriptService(output_path=tmp_path)

        # Adicionar vídeo já transcrito ao estado
        existing_state = VideoState(
            video_id="abc123",
            title="Vídeo Existente",
            channel="Canal Teste",
            duration_seconds=120,
            playlist_id="LL",
            transcribed_at=datetime.now(),
            status="transcribed"
        )
        service._state_repo.save_video(existing_state)

        output_path = tmp_path / "transcricao.txt"
        # Criar arquivo de transcrição existente
        output_path.write_text("Transcrição existente", encoding='utf-8')

        # Mock para garantir que não é chamado
        download_called = False

        async def mock_download(url):
            nonlocal download_called
            download_called = True
            return Path("audio.mp3")

        async def mock_extract_id(url):
            return "abc123"

        service._yt_dlp.download_audio_only = mock_download
        service._yt_dlp.extract_video_id = mock_extract_id
        service._analyzer.transcribe = Mock()

        result = await service.transcribe_video(
            url="https://youtube.com/watch?v=abc123",
            output_path=output_path
        )

        # Não deve ter chamado download nem transcrição
        assert not download_called
        service._analyzer.transcribe.assert_not_called()

        # Resultado deve indicar que já estava transcrito
        assert result.transcribed_at is not None
        assert "Transcrição existente" in result.text

    @pytest.mark.asyncio
    async def test_transcribe_adds_video_to_state(self, tmp_path):
        """Testa que adiciona vídeo ao estado se não existir."""
        from src.core.youtube import YoutubeTranscriptService

        service = YoutubeTranscriptService(output_path=tmp_path)

        # Mock componentes
        mock_audio_path = Path("audio.mp3")
        mock_trans_result = MagicMock()
        mock_trans_result.text = "Texto transcrito"
        mock_trans_result.language = "pt"
        mock_trans_result.confidence = 0.92
        mock_trans_result.duration_seconds = 120.0

        # Mock metadados
        mock_metadata = MagicMock()
        mock_metadata.title = "Novo Vídeo"
        mock_metadata.channel = "Canal Novo"
        mock_metadata.duration_seconds = 180

        async def mock_download(url):
            return mock_audio_path

        async def mock_extract_id(url):
            return "new123"

        async def mock_get_metadata(url):
            return mock_metadata

        async def mock_transcribe(path):
            return mock_trans_result

        service._yt_dlp.download_audio_only = mock_download
        service._yt_dlp.extract_video_id = mock_extract_id
        service._yt_dlp.get_metadata = mock_get_metadata
        service._analyzer.transcribe = mock_transcribe

        output_path = tmp_path / "transcricao.txt"
        await service.transcribe_video(
            url="https://youtube.com/watch?v=new123",
            output_path=output_path
        )

        # Verificar que vídeo foi adicionado ao estado
        video_state = service._state_repo.get_video("new123")
        assert video_state is not None
        assert video_state.video_id == "new123"
        assert video_state.status == "transcribed"

    @pytest.mark.asyncio
    async def test_transcribe_force_overwrites_transcribed(self, tmp_path):
        """Testa que force=True transcreve mesmo se já transcrito."""
        from src.core.youtube import YoutubeTranscriptService

        service = YoutubeTranscriptService(output_path=tmp_path)

        # Adicionar vídeo já transcrito
        from src.core.youtube import VideoState
        old_date = datetime(2024, 1, 1, 12, 0, 0)
        existing_state = VideoState(
            video_id="abc123",
            title="Vídeo Antigo",
            channel="Canal",
            duration_seconds=120,
            playlist_id="LL",
            transcribed_at=old_date,
            status="transcribed"
        )
        service._state_repo.save_video(existing_state)

        # Mock para nova transcrição
        mock_audio_path = Path("audio.mp3")
        mock_trans_result = MagicMock()
        mock_trans_result.text = "Nova transcrição"
        mock_trans_result.language = "pt"
        mock_trans_result.confidence = 0.95
        mock_trans_result.duration_seconds = 120.0

        download_called = False

        async def mock_download(url):
            nonlocal download_called
            download_called = True
            return mock_audio_path

        async def mock_extract_id(url):
            return "abc123"

        async def mock_transcribe(path):
            return mock_trans_result

        service._yt_dlp.download_audio_only = mock_download
        service._yt_dlp.extract_video_id = mock_extract_id
        service._analyzer.transcribe = mock_transcribe

        output_path = tmp_path / "transcricao.txt"
        result = await service.transcribe_video(
            url="https://youtube.com/watch?v=abc123",
            output_path=output_path,
            force=True
        )

        # Deve ter transcrito novamente
        assert download_called
        assert result.text == "Nova transcrição"

        # Estado deve estar atualizado
        video_state = service._state_repo.get_video("abc123")
        assert video_state.transcribed_at > old_date
