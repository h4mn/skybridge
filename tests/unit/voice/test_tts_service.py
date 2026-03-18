# coding: utf-8
"""
Testes unitários do TTSService.

DOC: openspec/changes/refactor-chat-event-driven/specs/tts-service/spec.md
"""

import asyncio
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from core.sy.chat.events import (
    StreamChunkEvent,
    TTSCompletedEvent,
    TTSStartedEvent,
)
from core.sy.events import InMemoryEventBus
from core.sy.voice import TTSService
from core.sky.voice.tts_adapter import VoiceMode


class MockTTSAdapter:
    """Mock do TTS adapter para testes."""

    def __init__(self):
        self.calls = []

    async def speak(self, text: str, mode: VoiceMode = VoiceMode.NORMAL) -> None:
        self.calls.append((text, mode))
        await asyncio.sleep(0.01)  # Simula latência


@pytest.fixture
def mock_tts():
    """Fixture que retorna mock do TTS."""
    return MockTTSAdapter()


@pytest.mark.asyncio
async def test_tts_service_start_stop(mock_tts):
    """Teste: start() inicializa worker, stop() para graciosamente."""
    bus = InMemoryEventBus()

    with patch("core.sy.voice.tts_service.get_tts_adapter", return_value=mock_tts):
        tts = TTSService(event_bus=bus)

        assert not tts.is_running

        await tts.start()
        assert tts.is_running

        await tts.stop()
        assert not tts.is_running


@pytest.mark.asyncio
async def test_tts_service_enqueue_fala_texto(mock_tts):
    """Teste: enqueue() coloca evento na fila e worker fala."""
    bus = InMemoryEventBus()

    with patch("core.sy.voice.tts_service.get_tts_adapter", return_value=mock_tts):
        tts = TTSService(event_bus=bus)
        await tts.start()

        # Aguarda worker iniciar
        await asyncio.sleep(0.01)

        # Enfileira evento com texto longo que deve falar
        await tts.enqueue(StreamChunkEvent(
            turn_id="turn-1",
            content="Este é um teste com mais de cinquenta caracteres para falar.",
            event_type="TEXT"
        ))

        # Aguarda processar
        await asyncio.sleep(0.15)

        # Para worker
        await tts.stop()

    # Verifica que TTS foi chamado
    assert len(mock_tts.calls) > 0
    assert "teste com mais de cinquenta caracteres" in mock_tts.calls[0][0]


@pytest.mark.asyncio
async def test_tts_service_buffer_acumula(mock_tts):
    """Teste: buffer acumula até pontuação final."""
    bus = InMemoryEventBus()

    with patch("core.sy.voice.tts_service.get_tts_adapter", return_value=mock_tts):
        tts = TTSService(event_bus=bus)
        await tts.start()

        # Envia texto curto (não deve falar imediatamente)
        await tts.enqueue(StreamChunkEvent(
            turn_id="turn-1",
            content="Texto curto ",
            event_type="TEXT"
        ))

        await asyncio.sleep(0.05)
        assert len(mock_tts.calls) == 0  # Ainda não falou

        # Completa com pontuação
        await tts.enqueue(StreamChunkEvent(
            turn_id="turn-1",
            content="agora tem pontuação.",
            event_type="TEXT"
        ))

        await asyncio.sleep(0.1)

        await tts.stop()

    # Deve ter falado agora
    assert len(mock_tts.calls) > 0
    assert "pontuação" in mock_tts.calls[0][0]


@pytest.mark.asyncio
async def test_tts_service_transicao_tool_result_thought(mock_tts):
    """Teste: TOOL_RESULT → THOUGHT fala buffer e inicia novo ciclo."""
    bus = InMemoryEventBus()

    with patch("core.sy.voice.tts_service.get_tts_adapter", return_value=mock_tts):
        tts = TTSService(event_bus=bus)
        await tts.start()

        # Acumula buffer
        await tts.enqueue(StreamChunkEvent(
            turn_id="turn-1",
            content="Pensamento anterior ",
            event_type="THOUGHT"
        ))

        # TOOL_RESULT deve falar buffer e iniciar novo ciclo
        await tts.enqueue(StreamChunkEvent(
            turn_id="turn-1",
            content="positive",
            event_type="TOOL_RESULT"
        ))

        await tts.enqueue(StreamChunkEvent(
            turn_id="turn-1",
            content="Novo pensamento",
            event_type="THOUGHT"
        ))

        await asyncio.sleep(0.15)
        await tts.stop()

    # Deve ter falado pelo menos 2 vezes (buffer antigo + novo)
    assert len(mock_tts.calls) >= 2


@pytest.mark.asyncio
async def test_tts_service_cancelled_error_silencioso(mock_tts):
    """Teste: CancelledError no worker é tratado silenciosamente."""
    bus = InMemoryEventBus()

    with patch("core.sy.voice.tts_service.get_tts_adapter", return_value=mock_tts):
        tts = TTSService(event_bus=bus)
        await tts.start()

        # Coloca algum trabalho na fila
        await tts.enqueue(StreamChunkEvent(
            turn_id="turn-1",
            content="Trabalho ",
            event_type="TEXT"
        ))

        # Cancela worker externamente
        if tts._worker_task:
            tts._worker_task.cancel()

        # stop() deve completar sem propagar CancelledError
        await tts.stop()

        # Worker deve estar parado
        assert not tts.is_running


@pytest.mark.asyncio
async def test_tts_service_enqueue_sem_start(mock_tts):
    """Teste: enqueue() sem start() levanta erro."""
    bus = InMemoryEventBus()

    with patch("core.sy.voice.tts_service.get_tts_adapter", return_value=mock_tts):
        tts = TTSService(event_bus=bus)

        # Não chamou start()
        with pytest.raises(RuntimeError, match="não está rodando"):
            await tts.enqueue(StreamChunkEvent(
                turn_id="turn-1",
                content="teste",
                event_type="TEXT"
            ))


@pytest.mark.asyncio
async def test_tts_service_start_duplo(mock_tts):
    """Teste: start() duas vezes levanta erro."""
    bus = InMemoryEventBus()

    with patch("core.sy.voice.tts_service.get_tts_adapter", return_value=mock_tts):
        tts = TTSService(event_bus=bus)
        await tts.start()

        with pytest.raises(RuntimeError, match="já está rodando"):
            await tts.start()

        await tts.stop()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
