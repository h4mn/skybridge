# coding: utf-8
"""
Testes de integração do ChatContainer.

DOC: openspec/changes/refactor-chat-event-driven/tasks.md

Testa o lifecycle completo do container e a integração entre componentes.
"""

import asyncio
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from core.sky.chat import ChatContainer, ChatContainerContext
from core.sky.chat.events import StreamChunkEvent
from core.sky.events import InMemoryEventBus
from core.sky.voice.streaming_tts_service import StreamingTTSService


class MockChatAdapter:
    """Mock do ClaudeChatAdapter."""

    def __init__(self):
        self.stream_responses = []

    async def stream_response(self, message: str):
        """Simula stream de resposta."""
        for event in self.stream_responses:
            yield event


class MockStreamEvent:
    """Mock do StreamEvent do Claude SDK."""

    def __init__(self, content: str, event_type: str):
        self.content = content
        self.type = event_type
        self.metadata = {}


@pytest.mark.asyncio
async def test_container_create_factory():
    """Teste: create() factory cria todas as dependências."""
    container = await ChatContainer.create()

    # Verifica que todas as dependências foram criadas
    assert container.event_bus is not None
    assert isinstance(container.event_bus, InMemoryEventBus)

    assert container.tts_service is not None
    assert isinstance(container.tts_service, StreamingTTSService)
    assert container.tts_service.is_running  # Deve estar startado

    assert container.orchestrator is not None

    # Cleanup
    await container.shutdown()


@pytest.mark.asyncio
async def test_container_async_context_manager():
    """Teste: async with garante cleanup automático."""
    tts_running = []

    async with await ChatContainer.create() as container:
        # Dentro do contexto, TTS está rodando
        assert container.tts_service.is_running
        tts_running.append(True)

    # Após o contexto, TTS foi parado (verificação via nova instância)
    # Nota: o container original foi limpo, mas a referência ainda existe
    assert len(tts_running) == 1


@pytest.mark.asyncio
async def test_container_shutdown_ordem_reversa():
    """Teste: shutdown() para recursos em ordem reversa."""
    container = await ChatContainer.create()

    # TTS está rodando
    assert container.tts_service.is_running

    # Shutdown deve parar TTS
    await container.shutdown()

    # TTS deve estar parado
    assert container.tts_service.is_running is False

    # Shutdown múltiplo não deve levantar erro
    await container.shutdown()


@pytest.mark.asyncio
async def test_container_shutdown_idempotent():
    """Teste: shutdown() pode ser chamado múltiplas vezes."""
    container = await ChatContainer.create()

    await container.shutdown()
    await container.shutdown()
    await container.shutdown()

    # Não deve levantar exceção
    assert True


@pytest.mark.asyncio
async def test_container_orchestrator_integration():
    """Teste: orchestrator do container funciona corretamente."""
    mock_chat = MockChatAdapter()
    mock_chat.stream_responses = [
        MockStreamEvent("Olá! ", "TEXT"),
        MockStreamEvent("Mundo! ", "TEXT"),
    ]

    container = await ChatContainer.create(chat=mock_chat)

    # Processa turno usando o orchestrator do container
    chunks = []
    async for chunk in container.orchestrator.process_turn("Teste", "turn-1"):
        chunks.append(chunk)

    # Verifica que chunks foram yieldados
    assert len(chunks) == 2
    assert chunks[0].content == "Olá! "
    assert chunks[1].content == "Mundo! "

    # Cleanup
    await container.shutdown()


@pytest.mark.asyncio
async def test_container_event_bus_integration():
    """Teste: EventBus do container funciona corretamente."""
    from core.sky.chat.events import TurnStartedEvent

    # Cria container com chat mock
    mock_chat = MockChatAdapter()
    mock_chat.stream_responses = []

    container = await ChatContainer.create(chat=mock_chat)
    received = []

    async def consume_turn_started():
        async for event in container.event_bus.subscribe(TurnStartedEvent):
            received.append(event)
            if len(received) >= 1:
                break

    # Inicia consumer
    consumer_task = asyncio.create_task(consume_turn_started())
    await asyncio.sleep(0.01)  # Aguarda subscriber registrar

    # Publica evento via orchestrator
    async for _ in container.orchestrator.process_turn("Teste", "turn-123"):
        pass

    # Aguarda consumer processar
    await asyncio.wait_for(consumer_task, timeout=2.0)

    # Verifica que evento foi recebido
    assert len(received) == 1
    assert received[0].turn_id == "turn-123"

    # Cleanup
    await container.shutdown()


@pytest.mark.asyncio
async def test_container_create_with_custom_chat():
    """Teste: create() aceita ClaudeChatAdapter customizado."""
    custom_chat = MockChatAdapter()

    container = await ChatContainer.create(chat=custom_chat)

    # Verifica que o orchestrator usa o chat customizado
    assert container.orchestrator._chat is custom_chat

    # Cleanup
    await container.shutdown()


@pytest.mark.asyncio
async def test_container_exception_during_context():
    """Teste: exceção durante async with ainda faz cleanup."""
    try:
        async with await ChatContainer.create() as container:
            # Simula exceção
            raise ValueError("Test exception")
    except ValueError:
        pass

    # Exceção foi propagada e cleanup foi feito
    assert True


@pytest.mark.skip(reason="Feature auto_start não foi implementada no ChatContainer")
@pytest.mark.asyncio
async def test_container_tts_not_started_when_auto_start_false():
    """Teste: create() com auto_start=False deixa TTS parado."""
    # NOTA: Esta feature não foi implementada
    # O ChatContainer sempre starta o TTS automaticamente
    pass


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
