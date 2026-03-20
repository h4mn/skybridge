# -*- coding: utf-8 -*-
"""
Testes unitários do STTService da Voice API.

DOC: openspec/changes/voice-api-isolation/tasks.md - Fase 4, Task 4.6
Testes do STTService usando mock do modelo faster-whisper.
"""

import pytest
from unittest.mock import Mock, AsyncMock, patch, MagicMock
import numpy as np

from core.sky.voice.api.services.stt_service import (
    STTService,
    get_stt_service,
    AudioEmptyError,
    AudioTooShortError,
    InvalidAudioFormatError,
    STTModelNotReadyError,
    STTError,
    startup_state,
)


class TestSTTServiceTranscribe:
    """Testes do método transcribe com mock do modelo."""

    @pytest.fixture
    def service(self):
        """Retorna instância do STTService."""
        return STTService()

    @pytest.fixture
    def mock_model(self):
        """Retorna mock do modelo faster-whisper."""
        model = Mock()

        # Mock do segmento
        mock_segment = Mock()
        mock_segment.text = "Olá Sky"

        # Mock do info
        mock_info = Mock()
        mock_info.language = "pt"
        mock_info.language_probability = 0.95

        # Configura transcribe para retornar segmento e info
        def transcribe_side_effect(*args, **kwargs):
            return iter([mock_segment]), mock_info

        model.transcribe.side_effect = transcribe_side_effect
        return model

    @pytest.mark.asyncio
    async def test_transcribe_success(self, service, mock_model):
        """Testa transcrição bem-sucedida."""
        service._model = mock_model

        # Áudio válido (1 segundo @ 16kHz float32)
        audio_bytes = np.random.randn(16000).astype(np.float32).tobytes()

        result = await service.transcribe(audio_bytes)

        assert result == "Olá Sky"
        mock_model.transcribe.assert_called_once()

    @pytest.mark.asyncio
    async def test_transcribe_empty_audio_raises_error(self, service):
        """Testa que áudio vazio levanta AudioEmptyError."""
        with pytest.raises(AudioEmptyError) as exc_info:
            await service.transcribe(b"")

        assert "Áudio vazio" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_transcribe_too_short_audio_raises_error(self, service):
        """Testa que áudio muito curto levanta AudioTooShortError."""
        # Áudio de apenas 100 bytes (muito menor que 4800 samples mínimo)
        short_audio = b"\x00" * 100

        with pytest.raises(AudioTooShortError) as exc_info:
            await service.transcribe(short_audio)

        assert "Áudio muito curto" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_transcribe_invalid_format_raises_error(self, service):
        """Testa que formato inválido levanta InvalidAudioFormatError."""
        # Bytes que não podem ser decodificados como float32
        invalid_audio = b"\x00\x01\x02\x03" * 20  # 80 bytes - tamanho ok mas formato inválido
        # Vai falhar no frombuffer com dtype errado se não for float32 válido
        # Mas na verdade frombuffer não falha, só retorna array com valores estranhos
        # Vamos simular o erro patchando numpy

        with patch("numpy.frombuffer") as mock_frombuffer:
            mock_frombuffer.side_effect = ValueError("invalid dtype")

            with pytest.raises(InvalidAudioFormatError) as exc_info:
                await service.transcribe(b"\x00" * 100)

            assert "Não foi possível decodificar" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_transcribe_no_speech_detected_returns_empty(self, service, mock_model):
        """Testa que nenhuma fala detectada retorna string vazia."""
        # Configura modelo para retornar sem segmentos
        mock_info = Mock()
        mock_info.language = "pt"
        mock_model.transcribe.return_value = iter([]), mock_info
        service._model = mock_model

        audio_bytes = np.random.randn(16000).astype(np.float32).tobytes()

        result = await service.transcribe(audio_bytes)

        assert result == ""

    @pytest.mark.asyncio
    async def test_transcribe_multiple_segments_concatenates(self, service):
        """Testa que múltiplos segmentos são concatenados."""
        service._model = Mock()

        # Mock de 2 segmentos
        segment1 = Mock()
        segment1.text = "Olá "
        segment2 = Mock()
        segment2.text = "Sky"

        mock_info = Mock()
        mock_info.language = "pt"

        service._model.transcribe.return_value = iter([segment1, segment2]), mock_info

        audio_bytes = np.random.randn(16000).astype(np.float32).tobytes()

        result = await service.transcribe(audio_bytes)

        assert result == "Olá Sky"

    @pytest.mark.asyncio
    async def test_transcribe_model_error_wraps_in_stt_error(self, service):
        """Testa que erro do modelo é envolvido em STTError."""
        service._model = Mock()
        service._model.transcribe.side_effect = RuntimeError("Model failed")

        audio_bytes = np.random.randn(16000).astype(np.float32).tobytes()

        with pytest.raises(STTError) as exc_info:
            await service.transcribe(audio_bytes)

        assert "Erro durante transcrição" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_transcribe_loads_model_if_not_loaded(self, service, mock_model):
        """Testa que modelo é carregado se não estiver."""
        assert service._model is None

        # Patch load_model para injetar mock
        with patch.object(service, 'load_model', new_callable=AsyncMock) as mock_load:
            async def inject_model():
                service._model = mock_model

            mock_load.side_effect = inject_model

            audio_bytes = np.random.randn(16000).astype(np.float32).tobytes()
            await service.transcribe(audio_bytes)

            mock_load.assert_called_once()


class TestSTTServiceLoadModel:
    """Testes do método load_model."""

    @pytest.fixture
    def service(self):
        """Retorna instância do STTService."""
        return STTService()

    @pytest.mark.asyncio
    async def test_load_model_updates_startup_state(self, service):
        """Testa que load_model atualiza startup_state."""
        initial_progress = startup_state.progress

        with patch("src.core.sky.voice.api.services.stt_service.WhisperModel") as mock_whisper:
            mock_model_instance = Mock()
            mock_whisper.return_value = mock_model_instance

            await service.load_model()

            # Verifica que startup_state foi atualizado
            assert startup_state.stage == "stt"
            assert startup_state.status.value == "loading_models"
            assert startup_state.progress > initial_progress
            assert "STT model" in startup_state.message

    @pytest.mark.asyncio
    async def test_load_model_idempotent(self, service):
        """Testa que load_model só carrega uma vez."""
        with patch("src.core.sky.voice.api.services.stt_service.WhisperModel") as mock_whisper:
            mock_model_instance = Mock()
            mock_whisper.return_value = mock_model_instance

            # Carrega duas vezes
            await service.load_model()
            await service.load_model()

            # WhisperModel só deve ser criado uma vez
            mock_whisper.assert_called_once()

    @pytest.mark.asyncio
    async def test_load_model_thread_safe(self, service):
        """Testa que load_model é thread-safe com lock."""
        import asyncio

        with patch("src.core.sky.voice.api.services.stt_service.WhisperModel") as mock_whisper:
            mock_model_instance = Mock()
            mock_whisper.return_value = mock_model_instance

            # Carrega em paralelo
            await asyncio.gather(
                service.load_model(),
                service.load_model(),
                service.load_model()
            )

            # Deve ser criado apenas uma vez
            mock_whisper.assert_called_once()


class TestSTTServiceHealth:
    """Testes do método health."""

    @pytest.fixture
    def service(self):
        """Retorna instância do STTService."""
        return STTService()

    @pytest.mark.asyncio
    async def test_health_model_not_loaded(self, service):
        """Testa health quando modelo não carregado."""
        result = await service.health()

        assert result["model_loaded"] is False
        assert result["stage"] == "stt"

    @pytest.mark.asyncio
    async def test_health_model_loaded(self, service):
        """Testa health quando modelo carregado."""
        service._model = Mock()

        result = await service.health()

        assert result["model_loaded"] is True
        assert result["stage"] == "stt"


class TestGetSTTService:
    """Testes da função get_stt_service (singleton)."""

    def test_returns_singleton(self):
        """Testa que get_stt_service retorna singleton."""
        service1 = get_stt_service()
        service2 = get_stt_service()

        assert service1 is service2

    def test_returns_stt_service_instance(self):
        """Testa que retorna instância de STTService."""
        service = get_stt_service()

        assert isinstance(service, STTService)


class TestSTTExceptions:
    """Testes das exceções customizadas."""

    def test_audio_empty_error(self):
        """Testa AudioEmptyError."""
        error = AudioEmptyError("teste")

        assert isinstance(error, STTError)
        assert "teste" in str(error)

    def test_audio_too_short_error(self):
        """Testa AudioTooShortError."""
        error = AudioTooShortError("0.1s")

        assert isinstance(error, STTError)
        assert "0.1s" in str(error)

    def test_invalid_audio_format_error(self):
        """Testa InvalidAudioFormatError."""
        error = InvalidAudioFormatError("wav")

        assert isinstance(error, STTError)
        assert "wav" in str(error)

    def test_stt_model_not_ready_error(self):
        """Testa STTModelNotReadyError."""
        error = STTModelNotReadyError("loading")

        assert isinstance(error, STTError)
        assert "loading" in str(error)
