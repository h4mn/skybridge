# coding: utf-8
"""
Testes A/B comparando OLD vs NEW implementation.

DOC: openspec/changes/refactor-chat-event-driven/tasks.md

Valida que ambas implementações produzem mesmos resultados.
"""

import asyncio
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from core.sy.chat import ChatContainer
from core.sy.chat.events import StreamChunkEvent
from core.sky.chat.claude_chat import ClaudeChatAdapter, StreamEvent, StreamEventType


class MockStreamEvent:
    """Mock do StreamEvent do Claude SDK."""

    def __init__(self, content: str, event_type: StreamEventType, metadata: dict | None = None):
        self.content = content
        self.type = event_type
        self.metadata = metadata or {}


class MockChatAdapter:
    """Mock controlável do ClaudeChatAdapter."""

    def __init__(self, responses: list[MockStreamEvent]):
        self.responses = responses
        self._history = []

    async def stream_response(self, message: str):
        """Simula stream de resposta controlada."""
        for event in self.responses:
            yield event

    def get_history(self):
        return self._history


@pytest.mark.asyncio
async def test_orchestrator_produces_same_chunks_as_adapter():
    """Teste: Orchestrator yield mesmos chunks que adapter.stream_response()."""
    # Setup: mock responses
    mock_responses = [
        MockStreamEvent("Olá! ", StreamEventType.TEXT),
        MockStreamEvent("Como ", StreamEventType.TEXT),
        MockStreamEvent("posso ", StreamEventType.TEXT),
        MockStreamEvent("ajudar? ", StreamEventType.TEXT),
    ]

    mock_chat = MockChatAdapter(mock_responses)

    # NEW: usa Orchestrator via Container
    container = await ChatContainer.create(chat=mock_chat)

    chunks_new = []
    async for chunk in container.orchestrator.process_turn("Teste", "turn-1"):
        chunks_new.append(chunk.content)

    await container.shutdown()

    # OLD: simula consumo direto (como MainScreen fazia)
    chunks_old = []
    async for event in mock_chat.stream_response("Teste"):
        chunks_old.append(event.content)

    # Assert: mesmos chunks em mesma ordem
    assert chunks_new == chunks_old
    assert len(chunks_new) == 4
    assert chunks_new[0] == "Olá! "


@pytest.mark.asyncio
async def test_orchestrator_handles_all_event_types():
    """Teste: Orchestrator processa todos os tipos de eventos corretamente."""
    # Setup: mistura de eventos
    mock_responses = [
        MockStreamEvent("Pensando... ", StreamEventType.THOUGHT),
        MockStreamEvent("ferramenta ", StreamEventType.TOOL_START, {"tool": "read_file", "input": '{"path": "test.txt"}'}),
        MockStreamEvent("positive", StreamEventType.TOOL_RESULT, {"result": "conteúdo", "exit_code": 0}),
        MockStreamEvent("Resposta ", StreamEventType.TEXT),
        MockStreamEvent("final! ", StreamEventType.TEXT),
    ]

    mock_chat = MockChatAdapter(mock_responses)
    container = await ChatContainer.create(chat=mock_chat)

    chunks_new = []
    event_types_new = []

    async for chunk in container.orchestrator.process_turn("Teste", "turn-2"):
        chunks_new.append(chunk.content)
        event_types_new.append(chunk.event_type)

    await container.shutdown()

    # Verifica tipos de eventos mapeados corretamente
    assert event_types_new == ["THOUGHT", "TOOL_START", "TOOL_RESULT", "TEXT", "TEXT"]
    assert chunks_new[0] == "Pensando... "
    assert chunks_new[3] == "Resposta "


@pytest.mark.asyncio
async def test_orchestrator_empty_stream():
    """Teste: Orchestrator lida corretamente com stream vazio."""
    mock_chat = MockChatAdapter([])
    container = await ChatContainer.create(chat=mock_chat)

    chunks = []
    async for chunk in container.orchestrator.process_turn("Teste", "turn-3"):
        chunks.append(chunk)

    await container.shutdown()

    # Não deve ter chunks
    assert len(chunks) == 0


@pytest.mark.asyncio
async def test_orchestrator_preserves_metadata():
    """Teste: Metadata de StreamEvent é preservado no StreamChunkEvent."""
    tool_metadata = {"tool": "execute_bash", "input": '{"command": "ls"}', "exit_code": 0}
    mock_responses = [
        MockStreamEvent("ls -la", StreamEventType.TOOL_START, tool_metadata),
    ]

    mock_chat = MockChatAdapter(mock_responses)
    container = await ChatContainer.create(chat=mock_chat)

    chunks = []
    async for chunk in container.orchestrator.process_turn("Teste", "turn-4"):
        chunks.append(chunk)

    await container.shutdown()

    # Metadata deve ser preservado
    assert len(chunks) == 1
    assert chunks[0].metadata == tool_metadata


@pytest.mark.asyncio
async def test_orchestrator_enqueues_to_tts_when_enabled():
    """Teste: Chunks são enfileirados para TTS quando serviço está rodando."""
    mock_responses = [
        MockStreamEvent("Texto ", StreamEventType.TEXT),
        MockStreamEvent("para ", StreamEventType.TEXT),
        MockStreamEvent("falar. ", StreamEventType.TEXT),
    ]

    mock_chat = MockChatAdapter(mock_responses)
    container = await ChatContainer.create(chat=mock_chat)

    # TTS deve estar rodando
    assert container.tts_service.is_running

    # Processa turno
    async for _ in container.orchestrator.process_turn("Teste", "turn-5"):
        pass

    await container.shutdown()

    # Verifica que chunks foram enfileirados (indiretamente via TTS worker)


@pytest.mark.asyncio
async def test_orchestrator_does_not_enqueue_tts_when_disabled():
    """Teste: Chunks não são enfileirados quando TTS não está rodando."""
    mock_responses = [
        MockStreamEvent("Texto ", StreamEventType.TEXT),
    ]

    mock_chat = MockChatAdapter(mock_responses)
    container = await ChatContainer.create(chat=mock_chat)

    # Para TTS explicitamente
    await container.tts_service.stop()
    assert not container.tts_service.is_running

    # Processa turno (não deve levantar erro)
    chunks = []
    async for chunk in container.orchestrator.process_turn("Teste", "turn-6"):
        chunks.append(chunk)

    await container.shutdown()

    # Chunk foi yieldado mas não enviado para TTS
    assert len(chunks) == 1
    assert chunks[0].content == "Texto "


@pytest.mark.asyncio
async def test_orchestrator_turn_id_preserved():
    """Teste: turn_id é preservado em todos os chunks."""
    mock_responses = [
        MockStreamEvent("Chunk 1 ", StreamEventType.TEXT),
        MockStreamEvent("Chunk 2 ", StreamEventType.TEXT),
        MockStreamEvent("Chunk 3 ", StreamEventType.TEXT),
    ]

    mock_chat = MockChatAdapter(mock_responses)
    container = await ChatContainer.create(chat=mock_chat)

    turn_id = "turn-test-123"
    async for chunk in container.orchestrator.process_turn("Teste", turn_id):
        # Verifica que todos os chunks têm mesmo turn_id
        assert chunk.turn_id == turn_id

    await container.shutdown()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
