"""Testes para TranscriptionAdapter.

DOC: src/core/youtube/infrastructure/transcription_adapter.py
Metodologia: TDD Estrito (RED → GREEN → REFACTOR)

Arquitetura:
- faster-whisper (principal, local, rápido)
- zai-analyze-video (fallback, análise completa)
"""

import pytest
from pathlib import Path
from unittest.mock import Mock, patch, AsyncMock, MagicMock


@pytest.mark.unit
class TestTranscriptionAdapter:
    """Testes do adaptador de transcrição."""

    def test_init_creates_model_dir(self, tmp_path):
        """Testa que cria diretório para modelos."""
        from src.core.youtube.infrastructure.transcription_adapter import TranscriptionAdapter

        model_dir = tmp_path / "models"
        adapter = TranscriptionAdapter(model_dir=model_dir)

        assert model_dir.exists()

    @pytest.mark.asyncio
    async def test_transcribe_audio_with_faster_whisper(self):
        """Testa transcrição com faster-whisper (principal)."""
        from src.core.youtube.infrastructure.transcription_adapter import TranscriptionAdapter

        adapter = TranscriptionAdapter()

        # Mock faster-whisper
        with patch('src.core.youtube.infrastructure.transcription_adapter.WhisperModel') as mock_model:
            mock_instance = MagicMock()
            mock_model.return_value = mock_instance

            # Mock segments da transcrição
            mock_segment = MagicMock()
            mock_segment.text = "Este é um teste de transcrição."
            mock_instance.transcribe.return_value = ([mock_segment], MagicMock(language="pt", language_probability=0.92))

            # Arquivo de áudio mock
            audio_path = Path("data/youtube/test.mp3")

            result = await adapter.transcribe(audio_path)

            assert result.text == "Este é um teste de transcrição."
            assert result.language == "pt"
            assert result.method == "faster-whisper"
            assert result.confidence == 0.92

    @pytest.mark.asyncio
    async def test_transcribe_fallback_to_zai_on_error(self):
        """Testa fallback para zai-analyze-video quando faster-whisper falha."""
        from src.core.youtube.infrastructure.transcription_adapter import TranscriptionAdapter

        adapter = TranscriptionAdapter()

        # Mock faster-whisper falhando
        with patch('src.core.youtube.infrastructure.transcription_adapter.WhisperModel') as mock_model:
            mock_instance = MagicMock()
            mock_instance.side_effect = Exception("faster-whisper failed")
            mock_model.return_value = mock_instance

            audio_path = Path("data/youtube/test.mp3")
            result = await adapter.transcribe(audio_path)

            # Fallback atual retorna vazio (zai não implementado ainda)
            assert result.method == "zai-mcp"
            assert result.text == ""
            assert result.language == "unknown"

    @pytest.mark.asyncio
    async def test_transcribe_with_language_detection(self):
        """Testa detecção automática de idioma."""
        from src.core.youtube.infrastructure.transcription_adapter import TranscriptionAdapter

        adapter = TranscriptionAdapter()

        with patch('src.core.youtube.infrastructure.transcription_adapter.WhisperModel') as mock_model:
            mock_instance = MagicMock()
            mock_model.return_value = mock_instance

            # Mock com detectado como inglês
            mock_segment = MagicMock()
            mock_segment.text = "This is an English test."
            mock_info = MagicMock()
            mock_info.language = "en"
            mock_info.language_probability = 0.95
            mock_instance.transcribe.return_value = ([mock_segment], mock_info)

            audio_path = Path("data/youtube/test.mp3")
            result = await adapter.transcribe(audio_path)

            assert result.language == "en"
            assert result.confidence > 0.9


@pytest.mark.unit
class TestTranscriptionResult:
    """Testes do Value Object TranscriptionResult."""

    def test_create_transcription_result(self):
        """Testa criação de resultado de transcrição."""
        from src.core.youtube.infrastructure.transcription_adapter import TranscriptionResult

        result = TranscriptionResult(
            text="Texto da transcrição",
            language="pt",
            confidence=0.95,
            method="faster-whisper",
            duration_seconds=120
        )

        assert result.text == "Texto da transcrição"
        assert result.language == "pt"
        assert result.confidence == 0.95
        assert result.method == "faster-whisper"
        assert result.duration_seconds == 120

    def test_transcription_result_defaults(self):
        """Testa valores padrão."""
        from src.core.youtube.infrastructure.transcription_adapter import TranscriptionResult

        result = TranscriptionResult(
            text="Texto",
            language="unknown"
        )

        assert result.confidence == 0.0
        assert result.method == "unknown"
        assert result.duration_seconds == 0


@pytest.mark.integration
class TestTranscriptionAdapterIntegration:
    """Testes de integração (requer faster-whisper instalado)."""

    @pytest.mark.skipif(
        True,  # Só rodar se tiver modelo baixado
        reason="Requer faster-whisper instalado e modelo baixado"
    )
    @pytest.mark.asyncio
    async def test_real_transcription_with_audio_file(self, tmp_path):
        """Teste real com arquivo de áudio (se existir)."""
        from src.core.youtube.infrastructure.transcription_adapter import TranscriptionAdapter

        adapter = TranscriptionAdapter(model_size="tiny")  # Modelo menor

        # Criar áudio de teste (ou usar existente)
        audio_path = tmp_path / "test.mp3"

        if not audio_path.exists():
            pytest.skip("Arquivo de áudio de teste não encontrado")

        result = await adapter.transcribe(audio_path)

        assert result.text
        assert len(result.text) > 0
        assert result.method == "faster-whisper"
