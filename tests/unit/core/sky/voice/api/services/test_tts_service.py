# -*- coding: utf-8 -*-
"""
Testes unitários do TTSService da Voice API.

DOC: openspec/changes/voice-api-isolation/tasks.md - Fase 6, Task 6.8
Testes do TTSService usando mock do KokoroAdapter.
"""

import pytest
from unittest.mock import Mock, AsyncMock, patch
import numpy as np

from core.sky.voice.api.services.tts_service import (
    TTSService,
    get_tts_service,
    TTSRequest,
)
from core.sky.voice.tts_adapter import VoiceMode


class TestTTSServiceSynthesize:
    """Testes do método synthesize."""

    @pytest.fixture
    def service(self):
        """Retorna instância do TTSService."""
        return TTSService()

    @pytest.fixture
    def mock_adapter(self):
        """Retorna mock do KokoroAdapter."""
        adapter = Mock()

        # Mock do AudioData retornado
        mock_audio_data = Mock()
        mock_audio_data.samples = np.random.randn(24000).astype(np.float32).tobytes()  # 1 segundo @ 24kHz
        mock_audio_data.sample_rate = 24000
        mock_audio_data.duration = 1.0

        adapter.synthesize = AsyncMock(return_value=mock_audio_data)
        return adapter

    @pytest.mark.asyncio
    async def test_synthesize_success_normal_mode(self, service, mock_adapter):
        """Testa síntese bem-sucedida em modo NORMAL."""
        service._adapter = mock_adapter

        text = "Olá Sky"
        audio_bytes = await service.synthesize(text, VoiceMode.NORMAL)

        assert len(audio_bytes) > 0
        mock_adapter.synthesize.assert_called_once_with(text, VoiceMode.NORMAL)

    @pytest.mark.asyncio
    async def test_synthesize_success_thinking_mode(self, service, mock_adapter):
        """Testa síntese bem-sucedida em modo THINKING."""
        service._adapter = mock_adapter

        text = "Processando..."
        audio_bytes = await service.synthesize(text, VoiceMode.THINKING)

        assert len(audio_bytes) > 0
        mock_adapter.synthesize.assert_called_once_with(text, VoiceMode.THINKING)

    @pytest.mark.asyncio
    async def test_synthesize_default_mode(self, service, mock_adapter):
        """Testa síntese com modo padrão (NORMAL)."""
        service._adapter = mock_adapter

        text = "Teste"
        audio_bytes = await service.synthesize(text)

        assert len(audio_bytes) > 0
        # Verifica que o modo padrão é NORMAL
        mock_adapter.synthesize.assert_called_once()
        call_args = mock_adapter.synthesize.call_args
        assert call_args[0][1] == VoiceMode.NORMAL

    @pytest.mark.asyncio
    async def test_synthesize_engine_not_initialized_raises_error(self, service):
        """Testa que engine não inicializado levanta RuntimeError."""
        service._adapter = None

        with pytest.raises(RuntimeError) as exc_info:
            await service.synthesize("Teste")

        assert "not initialized" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_synthesize_returns_raw_bytes(self, service, mock_adapter):
        """Testa que synthesize retorna bytes brutos de áudio."""
        # Mock para retornar bytes específicos
        test_bytes = b"\x00\x01" * 100
        mock_audio_data = Mock()
        mock_audio_data.samples = test_bytes
        mock_audio_data.sample_rate = 24000
        mock_audio_data.duration = 1.0

        mock_adapter.synthesize = AsyncMock(return_value=mock_audio_data)
        service._adapter = mock_adapter

        result = await service.synthesize("Teste")

        assert result == test_bytes


class TestTTSServiceInitialize:
    """Testes do método initialize."""

    @pytest.fixture
    def service(self):
        """Retorna instância do TTSService."""
        return TTSService()

    @pytest.mark.asyncio
    async def test_initialize_loads_adapter(self, service):
        """Testa que initialize carrega o KokoroAdapter."""
        with patch("src.core.sky.voice.api.services.tts_service.KokoroAdapter") as mock_klass:
            mock_adapter = Mock()
            mock_adapter._load_model = AsyncMock()
            mock_klass.return_value = mock_adapter

            await service.initialize()

            # Verifica que KokoroAdapter foi criado
            mock_klass.assert_called_once()
            assert service._adapter == mock_adapter

    @pytest.mark.asyncio
    async def test_initialize_updates_startup_state(self, service):
        """Testa que initialize atualiza startup_state."""
        from core.sky.voice.api.services.stt_service import startup_state

        initial_progress = getattr(startup_state, 'progress', 0.0)

        with patch("src.core.sky.voice.api.services.tts_service.KokoroAdapter") as mock_klass:
            mock_adapter = Mock()
            mock_adapter._load_model = AsyncMock()
            mock_klass.return_value = mock_adapter

            await service.initialize()

            # Verifica que startup_state foi atualizado
            assert startup_state.stage == "tts"
            assert startup_state.progress >= initial_progress
            assert "TTS" in startup_state.message

    @pytest.mark.asyncio
    async def test_initialize_idempotent(self, service):
        """Testa que initialize só carrega uma vez."""
        with patch("src.core.sky.voice.api.services.tts_service.KokoroAdapter") as mock_klass:
            mock_adapter = Mock()
            mock_adapter._load_model = AsyncMock()
            mock_klass.return_value = mock_adapter

            # Inicializa duas vezes
            await service.initialize()
            await service.initialize()

            # Deve ser criado apenas uma vez
            mock_klass.assert_called_once()

    @pytest.mark.asyncio
    async def test_initialize_thread_safe(self, service):
        """Testa que initialize é thread-safe com lock."""
        import asyncio

        with patch("src.core.sky.voice.api.services.tts_service.KokoroAdapter") as mock_klass:
            mock_adapter = Mock()
            mock_adapter._load_model = AsyncMock()
            mock_klass.return_value = mock_adapter

            # Inicializa em paralelo
            await asyncio.gather(
                service.initialize(),
                service.initialize(),
                service.initialize()
            )

            # Deve ser criado apenas uma vez
            mock_klass.assert_called_once()


class TestTTSServiceHealth:
    """Testes do método health."""

    @pytest.fixture
    def service(self):
        """Retorna instância do TTSService."""
        return TTSService()

    @pytest.mark.asyncio
    async def test_health_engine_not_loaded(self, service):
        """Testa health quando engine não carregado."""
        result = await service.health()

        assert result["engine_loaded"] is False
        assert result["stage"] == "tts"
        assert "queue_size" in result
        assert "queue_limit" in result

    @pytest.mark.asyncio
    async def test_health_engine_loaded(self, service):
        """Testa health quando engine carregado."""
        # Mock adapter com pipeline carregado
        service._adapter = Mock()
        service._adapter._pipeline = Mock()

        result = await service.health()

        assert result["engine_loaded"] is True
        assert result["stage"] == "tts"


class TestTTSServiceShutdown:
    """Testes do método shutdown."""

    @pytest.fixture
    def service(self):
        """Retorna instância do TTSService."""
        return TTSService()

    @pytest.mark.asyncio
    async def test_shutdown_no_errors(self, service):
        """Testa que shutdown não levanta erros."""
        # Não deve levantar exceção
        await service.shutdown()


class TestGetTTSService:
    """Testes da função get_tts_service (singleton)."""

    def test_returns_singleton(self):
        """Testa que get_tts_service retorna singleton."""
        service1 = get_tts_service()
        service2 = get_tts_service()

        assert service1 is service2

    def test_returns_tts_service_instance(self):
        """Testa que retorna instância de TTSService."""
        service = get_tts_service()

        assert isinstance(service, TTSService)


class TestTTSRequest:
    """Testes da classe TTSRequest."""

    def test_tts_request_creation(self):
        """Testa criação de TTSRequest."""
        request = TTSRequest("Olá Sky", VoiceMode.NORMAL)

        assert request.text == "Olá Sky"
        assert request.mode == VoiceMode.NORMAL

    def test_tts_request_default_mode(self):
        """Testa TTSRequest com modo padrão."""
        request = TTSRequest("Teste")

        assert request.text == "Teste"
        assert request.mode == VoiceMode.NORMAL

    def test_tts_request_thinking_mode(self):
        """Testa TTSRequest com modo THINKING."""
        request = TTSRequest("Processando", VoiceMode.THINKING)

        assert request.text == "Processando"
        assert request.mode == VoiceMode.THINKING
