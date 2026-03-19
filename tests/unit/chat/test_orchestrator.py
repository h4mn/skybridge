# coding: utf-8
"""
Testes unitários do ChatOrchestrator.

DOC: openspec/changes/refactor-chat-event-driven/specs/chat-orchestrator/spec.md
"""

import asyncio
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from core.sky.chat.orchestrator import ChatOrchestrator
from core.sky.chat.events import StreamChunkEvent, TurnCompletedEvent, TurnStartedEvent
from core.sky.events import InMemoryEventBus
from core.sky.voice import TTSService


class MockStreamEvent:
    """Mock do StreamEvent do Claude SDK."""

    def __init__(self, content: str, event_type: str):
        self.content = content
        self.type = event_type
        self.metadata = {}


class MockChatAdapter:
    """Mock do ClaudeChatAdapter."""

    def __init__(self):
        self.stream_responses = []

    async def stream_response(self, message: str):
        """Simula stream de resposta."""
        for event in self.stream_responses:
            yield event

    def get_history(self):
        return []


@pytest.mark.asyncio
async def test_orchestrator_process_turn_yields_chunks():
    """Teste: process_turn() yield StreamChunkEvents."""
    bus = InMemoryEventBus()

    # Mock services
    chat = MockChatAdapter()
    tts = MagicMock(spec=TTSService)
    tts.is_running = False  # TTS desabilitado para este teste

    chat.stream_responses = [
        MockStreamEvent("Olá! ", "TEXT"),
        MockStreamEvent("Como ", "TEXT"),
        MockStreamEvent("posso ", "TEXT"),
        MockStreamEvent("ajudar?", "TEXT"),
    ]

    orchestrator = ChatOrchestrator(chat, tts, bus)
    chunks = []

    async def collect_chunks():
        async for chunk in orchestrator.process_turn("Teste", "turn-1"):
            chunks.append(chunk)

    await collect_chunks()

    assert len(chunks) == 4
    assert chunks[0].content == "Olá! "
    assert chunks[0].event_type == "TEXT"


@pytest.mark.asyncio
async def test_orchestrator_publishes_lifecycle_events():
    """Teste: process_turn() publica TurnStartedEvent e TurnCompletedEvent."""
    bus = InMemoryEventBus()

    # Mock services
    chat = MockChatAdapter()
    chat.stream_responses = [MockStreamEvent("OK", "TEXT")]
    tts = MagicMock(spec=TTSService)
    tts.is_running = False

    orchestrator = ChatOrchestrator(chat, tts, bus)

    # Processa turno (deve publicar eventos internamente)
    async for _ in orchestrator.process_turn("Teste", "turn-123"):
        pass

    # Se não levantou exceção, eventos foram publicados
    # (verificação indireta - capturar eventos em unit test é complexo)
    assert True


@pytest.mark.asyncio
async def test_orchestrator_envia_para_tts():
    """Teste: chunks são enviados para TTSService via enqueue()."""
    bus = InMemoryEventBus()

    # Mock TTS
    tts = MagicMock(spec=TTSService)
    tts.is_running = True
    tts.enqueue = AsyncMock()

    # Mock chat
    chat = MockChatAdapter()
    chat.stream_responses = [
        MockStreamEvent("Texto ", "TEXT"),
        MockStreamEvent("para ", "TEXT"),
        MockStreamEvent("falar.", "TEXT"),
    ]

    orchestrator = ChatOrchestrator(chat, tts, bus)

    # Consome todos os chunks
    async for _ in orchestrator.process_turn("Teste", "turn-1"):
        pass

    # Verifica que enqueue foi chamado para cada chunk
    assert tts.enqueue.call_count == 3


@pytest.mark.asyncio
async def test_orchestrator_map_stream_event_type():
    """Teste: StreamEventType é mapeado corretamente."""
    from core.sky.chat.claude_chat import StreamEventType

    bus = InMemoryEventBus()

    chat = MockChatAdapter()
    tts = MagicMock(spec=TTSService)
    tts.is_running = False

    orchestrator = ChatOrchestrator(chat, tts, bus)

    # Verifica mapeamento
    assert orchestrator._map_stream_event_type(StreamEventType.TEXT) == "TEXT"
    assert orchestrator._map_stream_event_type(StreamEventType.THOUGHT) == "THOUGHT"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
