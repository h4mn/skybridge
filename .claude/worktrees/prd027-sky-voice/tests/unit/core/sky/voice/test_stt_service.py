"""
Tests for STTService and WhisperAdapter.

DOC: src/core/sky/voice/stt_service.py - STT deve transcrever áudio para texto

Este teste valida:
1. Inicialização correta do WhisperAdapter
2. Transcrição de áudio vazio retorna texto vazio
3. Transcrição de áudio com texto detecta idioma corretamente
4. Interface STTService é implementada corretamente
"""

import pytest
from unittest.mock import Mock, AsyncMock, patch
from src.core.sky.voice.stt_service import (
    STTService,
    WhisperAdapter,
    STTModel,
    TranscriptionConfig,
    TranscriptionResult,
)
from src.core.sky.voice.audio_capture import AudioData


class TestWhisperAdapterInit:
    """Testa inicialização do WhisperAdapter."""

    def test_whisper_adapter_init_default_params(self):
        """Testa inicialização com parâmetros padrão."""
        adapter = WhisperAdapter()

        assert adapter.model == STTModel.WHISPER_LOCAL
        assert adapter.model_size == "base"
        assert adapter.device == "cpu"
        assert adapter._model is None  # Lazy load

    def test_whisper_adapter_init_custom_params(self):
        """Testa inicialização com parâmetros customizados."""
        adapter = WhisperAdapter(model_size="small", device="cuda")

        assert adapter.model_size == "small"
        assert adapter.device == "cuda"


class TestWhisperAdapterTranscribe:
    """Testa método transcribe do WhisperAdapter."""

    @pytest.mark.asyncio
    async def test_transcribe_empty_audio(self):
        """Testa transcrição de áudio vazio retorna texto vazio."""
        adapter = WhisperAdapter()

        # Áudio vazio (0 bytes)
        empty_audio = AudioData(
            samples=b"",
            sample_rate=16000,
            channels=1,
            duration=0.0,
        )

        # Mock do modelo para não precisar instalar faster-whisper no teste
        with patch.object(adapter, "_load_model"):
            mock_model = Mock()
            # faster-whisper retorna (segments_iterator, info)
            mock_info = Mock()
            mock_info.language = "pt"
            mock_info.language_probability = 0.0

            mock_model.transcribe.return_value = (iter([]), mock_info)
            adapter._model = mock_model

        result = await adapter.transcribe(empty_audio)

        assert result.text == ""
        assert result.language == "pt"  # padrão
        assert result.duration == 0.0

    @pytest.mark.asyncio
    async def test_transcribe_with_text_portuguese(self):
        """Testa transcrição de áudio com texto em português."""
        adapter = WhisperAdapter()

        # Áudio simulado com "Olá Sky"
        audio_data = AudioData(
            samples=b"\x00\x01" * 100,  # 200 bytes de áudio simulado
            sample_rate=16000,
            channels=1,
            duration=0.1,
        )

        # Mock do modelo
        with patch.object(adapter, "_load_model"):
            mock_model = Mock()
            mock_segment = Mock()
            mock_segment.text = "Olá Sky"
            mock_model.transcribe.return_value = iter([mock_segment])

            mock_info = Mock()
            mock_info.language = "pt"
            mock_info.language_probability = 0.95
            mock_model.transcribe.return_value = iter([mock_segment]), mock_info

            adapter._model = mock_model

        result = await adapter.transcribe(
            audio_data,
            config=TranscriptionConfig(language="pt"),
        )

        assert result.text == "Olá Sky"
        assert result.language == "pt"
        assert result.confidence == 0.95
        assert result.duration == 0.1

    @pytest.mark.asyncio
    async def test_transcribe_language_detection(self):
        """Testa detecção automática de idioma."""
        adapter = WhisperAdapter()

        audio_data = AudioData(
            samples=b"\x00\x01" * 100,
            sample_rate=16000,
            channels=1,
            duration=0.1,
        )

        with patch.object(adapter, "_load_model"):
            mock_model = Mock()
            mock_segment = Mock()
            mock_segment.text = "Hello Sky"
            mock_model.transcribe.return_value = iter([mock_segment])

            mock_info = Mock()
            mock_info.language = "en"
            mock_info.language_probability = 0.92
            mock_model.transcribe.return_value = iter([mock_segment]), mock_info

            adapter._model = mock_model

        # Config com detecção automática
        result = await adapter.transcribe(
            audio_data,
            config=TranscriptionConfig(detect_language=True),
        )

        assert result.text == "Hello Sky"
        assert result.language == "en"
        assert result.confidence == 0.92

    @pytest.mark.asyncio
    async def test_transcribe_multiple_segments(self):
        """Testa transcrição com múltiplos segmentos."""
        adapter = WhisperAdapter()

        audio_data = AudioData(
            samples=b"\x00\x01" * 200,
            sample_rate=16000,
            channels=1,
            duration=0.2,
        )

        with patch.object(adapter, "_load_model"):
            mock_model = Mock()
            segment1 = Mock()
            segment1.text = "Olá "
            segment2 = Mock()
            segment2.text = "Sky"

            mock_info = Mock()
            mock_info.language = "pt"
            mock_info.language_probability = 0.95

            mock_model.transcribe.return_value = iter([segment1, segment2]), mock_info
            adapter._model = mock_model

        result = await adapter.transcribe(audio_data)

        # Segmentos são concatenados
        assert result.text == "Olá Sky"
        assert result.language == "pt"


class TestSTTServiceInterface:
    """Testa interface abstrata STTService."""

    def test_whisper_adapter_is_stt_service(self):
        """Testa que WhisperAdapter implementa STTService."""
        adapter = WhisperAdapter()

        assert isinstance(adapter, STTService)
        assert hasattr(adapter, "transcribe")
        assert hasattr(adapter, "listen")

    @pytest.mark.asyncio
    async def test_stt_transcribe_signature(self):
        """Testa assinatura do método transcribe."""
        adapter = WhisperAdapter()

        # Verifica que o método é async
        import inspect

        assert inspect.iscoroutinefunction(adapter.transcribe)

        # Verifica parâmetros
        sig = inspect.signature(adapter.transcribe)
        params = list(sig.parameters.keys())
        assert "audio" in params
        assert "config" in params


class TestTranscriptionResult:
    """Testa TranscriptionResult dataclass."""

    def test_transcription_result_creation(self):
        """Testa criação de TranscriptionResult."""
        result = TranscriptionResult(
            text="Olá Sky",
            language="pt",
            confidence=0.95,
            duration=1.5,
        )

        assert result.text == "Olá Sky"
        assert result.language == "pt"
        assert result.confidence == 0.95
        assert result.duration == 1.5

    def test_transcription_result_defaults(self):
        """Testa valores padrão de TranscriptionResult."""
        result = TranscriptionResult(
            text="Teste",
            language="en",
        )

        assert result.confidence == 0.0
        assert result.duration == 0.0


class TestTranscriptionConfig:
    """Testa TranscriptionConfig dataclass."""

    def test_config_defaults(self):
        """Testa valores padrão da configuração."""
        config = TranscriptionConfig()

        assert config.language == "pt"
        assert config.model == "base"
        assert config.detect_language is False

    def test_config_custom_values(self):
        """Testa configuração com valores customizados."""
        config = TranscriptionConfig(
            language="en",
            model="small",
            detect_language=True,
        )

        assert config.language == "en"
        assert config.model == "small"
        assert config.detect_language is True
