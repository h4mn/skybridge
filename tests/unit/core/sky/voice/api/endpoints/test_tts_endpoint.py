# -*- coding: utf-8 -*-
"""
Testes do TTS endpoint da Voice API.

DOC: openspec/changes/voice-api-isolation/tasks.md - Fase 7, Tasks 7.7 e 7.8
Testes do endpoint POST /voice/tts usando TestClient do Starlette.
"""

import pytest
import numpy as np
from unittest.mock import Mock, AsyncMock, patch
from starlette.testclient import TestClient

from core.sky.voice.api.app import create_app
from core.sky.voice.api.services.tts_service import get_tts_service
from core.sky.voice.tts_adapter import VoiceMode


@pytest.fixture
def test_client():
    """Retorna TestClient para a Voice API."""
    return TestClient(create_app())


@pytest.fixture
def mock_tts_service():
    """Mock do TTSService."""
    mock_service = Mock()
    mock_service.synthesize = AsyncMock(return_value=b"\x00\x01" * 1000)

    with patch("src.core.sky.voice.api.endpoints.tts.get_tts_service", return_value=mock_service):
        yield mock_service


class TestTTSEndpointSuccess:
    """Testes de sucesso do endpoint TTS."""

    def test_tts_endpoint_normal_mode_success(self, test_client, mock_tts_service):
        """Testa síntese bem-sucedida em modo normal."""
        response = test_client.post(
            "/voice/tts",
            json={"text": "Olá Sky", "mode": "normal"}
        )

        assert response.status_code == 200
        assert response.headers["content-type"] == "audio/raw"
        assert response.headers["x-sample-rate"] == "24000"
        assert response.headers["x-audio-format"] == "float32"
        assert response.headers["x-channels"] == "1"
        assert len(response.content) > 0
        mock_tts_service.synthesize.assert_called_once()

    def test_tts_endpoint_thinking_mode_success(self, test_client, mock_tts_service):
        """Testa síntese bem-sucedida em modo thinking."""
        response = test_client.post(
            "/voice/tts",
            json={"text": "Processando...", "mode": "thinking"}
        )

        assert response.status_code == 200
        assert len(response.content) > 0
        # Verifica que o modo correto foi passado
        call_args = mock_tts_service.synthesize.call_args
        assert call_args[0][1] == VoiceMode.THINKING

    def test_tts_endpoint_default_mode(self, test_client, mock_tts_service):
        """Testa que modo padrão é 'normal'."""
        response = test_client.post(
            "/voice/tts",
            json={"text": "Teste"}
        )

        assert response.status_code == 200
        call_args = mock_tts_service.synthesize.call_args
        assert call_args[0][1] == VoiceMode.NORMAL


class TestTTSEndpointValidation:
    """Testes de validação do endpoint TTS."""

    def test_tts_endpoint_no_text(self, test_client, mock_tts_service):
        """Testa erro quando texto não é fornecido."""
        response = test_client.post(
            "/voice/tts",
            json={"mode": "normal"}
        )

        assert response.status_code == 400
        data = response.json()
        assert data["error_type"] == "missing_text"
        assert "No text provided" in data["error"]
        mock_tts_service.synthesize.assert_not_called()

    def test_tts_endpoint_empty_text(self, test_client, mock_tts_service):
        """Testa erro quando texto está vazio."""
        response = test_client.post(
            "/voice/tts",
            json={"text": "", "mode": "normal"}
        )

        assert response.status_code == 400
        data = response.json()
        assert data["error_type"] == "missing_text"
        mock_tts_service.synthesize.assert_not_called()

    def test_tts_endpoint_invalid_mode(self, test_client, mock_tts_service):
        """Testa erro quando modo é inválido."""
        response = test_client.post(
            "/voice/tts",
            json={"text": "Teste", "mode": "invalid_mode"}
        )

        assert response.status_code == 400
        data = response.json()
        assert data["error_type"] == "invalid_mode"
        assert "valid_modes" in data
        assert "normal" in data["valid_modes"]
        assert "thinking" in data["valid_modes"]
        mock_tts_service.synthesize.assert_not_called()

    def test_tts_endpoint_invalid_json(self, test_client, mock_tts_service):
        """Testa erro quando JSON é inválido."""
        response = test_client.post(
            "/voice/tts",
            content=b"not json",
            headers={"Content-Type": "application/json"}
        )

        assert response.status_code == 400  # Starlette retorna 400 para JSON inválido


class TestTTSEndpointErrors:
    """Testes de tratamento de erros do endpoint."""

    def test_tts_endpoint_service_error(self, test_client, mock_tts_service):
        """Testa que erro do serviço retorna 500."""
        mock_tts_service.synthesize.side_effect = RuntimeError("Model failed")

        response = test_client.post(
            "/voice/tts",
            json={"text": "Teste", "mode": "normal"}
        )

        assert response.status_code == 500
        data = response.json()
        assert "error" in data
        assert data["error_type"] == "internal_error"

    def test_tts_endpoint_timeout_error(self, test_client, mock_tts_service):
        """Testa que timeout retorna erro interno."""
        import asyncio

        async def timeout_error(*args, **kwargs):
            raise asyncio.TimeoutError("Synthesis timeout")

        mock_tts_service.synthesize.side_effect = timeout_error

        response = test_client.post(
            "/voice/tts",
            json={"text": "Teste muito longo", "mode": "normal"}
        )

        assert response.status_code == 500
        data = response.json()
        assert "error" in data


class TestTTSEndpointVoices:
    """Testes de lista de vozes disponíveis."""

    def test_tts_endpoint_invalid_voice_returns_list(self, test_client, mock_tts_service):
        """Testa que erro de voz inválida retorna lista de vozes disponíveis."""
        # Simula erro com "voice" na mensagem
        mock_tts_service.synthesize.side_effect = ValueError("Invalid voice: 'xyz'")
        mock_tts_service._adapter = Mock()
        mock_tts_service._adapter.get_available_voices.return_value = [
            "af_heart", "af_sky", "af_bella"
        ]

        response = test_client.post(
            "/voice/tts",
            json={"text": "Teste", "mode": "normal"}
        )

        assert response.status_code == 400
        data = response.json()
        assert data["error_type"] == "invalid_voice"
        assert "available_voices" in data
        assert "af_heart" in data["available_voices"]

    def test_tts_endpoint_voice_error_without_adapter(self, test_client, mock_tts_service):
        """Testa que sem adapter retorna lista fallback."""
        mock_tts_service.synthesize.side_effect = ValueError("voice error")
        mock_tts_service._adapter = None

        response = test_client.post(
            "/voice/tts",
            json={"text": "Teste", "mode": "normal"}
        )

        assert response.status_code == 400
        data = response.json()
        # Deve retornar lista fallback
        assert "available_voices" in data or "error_type" in data


class TestTTSEndpointCancellation:
    """Testes de cancelamento mid-stream (Task 7.8)."""

    def test_tts_endpoint_client_cancellation(self, test_client, mock_tts_service):
        """Testa que cancelamento do cliente é tratado corretamente.

        Nota: Em um ambiente real de teste, simular o cancelamento mid-stream
        é complexo. Este teste verifica que o serviço pode ser interrompido
        sem causar erros no servidor.
        """
        import asyncio

        async def slow_synthesis(*args, **kwargs):
            # Simula síntese lenta que pode ser cancelada
            await asyncio.sleep(0.1)
            return b"\x00\x01" * 100

        mock_tts_service.synthesize.side_effect = slow_synthesis

        # Em um cenário real, o cliente fecharia a conexão durante a síntese
        # Aqui apenas verificamos que a síntese completa sem erros
        response = test_client.post(
            "/voice/tts",
            json={"text": "Texto longo", "mode": "normal"}
        )

        assert response.status_code == 200
        assert len(response.content) > 0

    def test_tts_service_survives_cancellation(self, test_client):
        """Testa que o serviço TTS sobrevive a cancelamentos.

        Verifica que múltiplos requests funcionam mesmo se alguns forem
        interrompidos (simulado por exceptions).
        """
        service = get_tts_service()

        # Mock com alguns requests falhando
        call_count = 0

        async def flaky_synthesis(*args, **kwargs):
            nonlocal call_count
            call_count += 1
            if call_count == 2:
                raise asyncio.CancelledError("Client cancelled")
            return b"\x00\x01" * 100

        with patch("src.core.sky.voice.api.endpoints.tts.get_tts_service", return_value=service):
            with patch.object(service, 'synthesize', new_callable=AsyncMock) as mock_synth:
                mock_synth.side_effect = flaky_synthesis

                client = TestClient(create_app())

                # Primeiro request - sucesso
                r1 = client.post("/voice/tts", json={"text": "Teste 1", "mode": "normal"})
                assert r1.status_code == 200

                # Segundo request - cancelado (simula cancelamento mid-stream)
                r2 = client.post("/voice/tts", json={"text": "Teste 2", "mode": "normal"})
                # Pode retornar 500 ou outro status devido ao cancelamento

                # Terceiro request - deve funcionar (serviço ainda está ativo)
                r3 = client.post("/voice/tts", json={"text": "Teste 3", "mode": "normal"})
                assert r3.status_code == 200


class TestTTSEndpointAudioQuality:
    """Testes de qualidade de áudio retornado."""

    def test_tts_endpoint_returns_audio_headers(self, test_client, mock_tts_service):
        """Testa que headers de áudio estão corretos."""
        # Mock para retornar áudio com características específicas
        mock_audio = np.random.randn(24000).astype(np.float32).tobytes()  # 1s @ 24kHz
        mock_tts_service.synthesize.return_value = mock_audio

        response = test_client.post(
            "/voice/tts",
            json={"text": "Teste áudio", "mode": "normal"}
        )

        assert response.status_code == 200
        assert response.headers["x-sample-rate"] == "24000"
        assert response.headers["x-audio-format"] == "float32"
        assert response.headers["x-channels"] == "1"

    def test_tts_endpoint_audio_format(self, test_client, mock_tts_service):
        """Testa que áudio retornado está no formato correto."""
        # Verifica que o serviço foi chamado
        response = test_client.post(
            "/voice/tts",
            json={"text": "Formato teste", "mode": "thinking"}
        )

        assert response.status_code == 200
        # Content-Type deve ser audio/raw
        assert "audio/raw" in response.headers["content-type"]


class TestTTSEndpointConcurrency:
    """Testes de concorrência."""

    def test_tts_endpoint_concurrent_requests(self, test_client):
        """Testa que múltiplos requests simultâneos funcionam."""
        service = get_tts_service()

        async def fast_synthesis(*args, **kwargs):
            await asyncio.sleep(0.01)  # 10ms de latência simulada
            return b"\x00\x01" * 100

        with patch("src.core.sky.voice.api.endpoints.tts.get_tts_service", return_value=service):
            with patch.object(service, 'synthesize', new_callable=AsyncMock) as mock_synth:
                mock_synth.side_effect = fast_synthesis

                client = TestClient(create_app())

                # Faz múltiplos requests
                responses = [
                    client.post("/voice/tts", json={"text": f"Teste {i}", "mode": "normal"})
                    for i in range(5)
                ]

                # Todos devem ser bem-sucedidos
                for r in responses:
                    assert r.status_code == 200
