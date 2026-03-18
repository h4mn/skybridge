# coding: utf-8
"""
ChatOrchestrator - Coordenador de Chat + TTS.

DOC: openspec/changes/refactor-chat-event-driven/specs/chat-orchestrator/spec.md

Coordena o fluxo de chat com TTS em paralelo via EventBus.
Não conhece UI - apenas orquestra chat e TTS.

## Responsabilidades

- Consumir ClaudeChatAdapter.stream_response()
- Publicar eventos de lifecycle (TurnStartedEvent, TurnCompletedEvent)
- Enviar eventos para TTSService (non-blocking)
- Yield StreamChunkEvents para caller

## Exemplo

```python
from core.sy.chat import ChatOrchestrator, ChatContainer
from core.sy.events import InMemoryEventBus

async with ChatContainer.create() as container:
    orchestrator = container.orchestrator

    async for chunk in orchestrator.process_turn("Oi Sky", turn_id="turn-1"):
        print(f"Chunk: {chunk.content}")
```
"""

import time
from typing import AsyncIterator

from core.sky.chat.claude_chat import ClaudeChatAdapter, StreamEvent, StreamEventType
from core.sy.chat.events import (
    StreamChunkEvent,
    TurnCompletedEvent,
    TurnStartedEvent,
)
from core.sy.events import InMemoryEventBus
from core.sy.voice import TTSService


class ChatOrchestrator:
    """
    Orquestrador de Chat + TTS.

    Coordena stream de chat com TTS em paralelo, publicando
    eventos de lifecycle e enviando chunks para TTS.

    Não conhece UI - comunicação é via EventBus yielding eventos.
    """

    def __init__(
        self,
        chat: ClaudeChatAdapter,
        tts_service: TTSService,
        event_bus: InMemoryEventBus,
    ):
        """
        Inicializa o ChatOrchestrator.

        Args:
            chat: ClaudeChatAdapter para consumir stream
            tts_service: TTSService para enfileirar eventos de fala
            event_bus: EventBus para publicar eventos
        """
        self._chat = chat
        self._tts = tts_service
        self._event_bus = event_bus

    async def process_turn(self, user_message: str, turn_id: str) -> AsyncIterator[StreamChunkEvent]:
        """
        Processa um turno de chat com TTS em paralelo.

        Args:
            user_message: Mensagem do usuário
            turn_id: ID único do turno

        Yields:
            StreamChunkEvent para cada chunk do stream

        Fluxo:
        1. Publica TurnStartedEvent
        2. Consome stream_response()
        3. Publica cada chunk e envia para TTS
        4. Publica TurnCompletedEvent ao final
        """
        start_time = time.time()

        # 1. Publica TurnStartedEvent
        await self._event_bus.publish(TurnStartedEvent(
            turn_id=turn_id,
            user_message=user_message
        ))

        # 2. Consome stream e processa chunks
        async for stream_event in self._chat.stream_response(user_message):
            event_type = self._map_stream_event_type(stream_event.type)

            # Cria evento de domínio
            chunk_event = StreamChunkEvent(
                turn_id=turn_id,
                content=stream_event.content,
                event_type=event_type,
                metadata=stream_event.metadata or {}
            )

            # 3. Publica chunk (para UI consumir)
            yield chunk_event

            # 4. Envia para TTS (non-blocking)
            if self._tts.is_running:
                await self._tts.enqueue(chunk_event)

        # 5. Calcula duração e publica TurnCompletedEvent
        duration_ms = (time.time() - start_time) * 1000

        await self._event_bus.publish(TurnCompletedEvent(
            turn_id=turn_id,
            final_text="",  # TODO: capturar texto final completo
            duration_ms=duration_ms,
            metadata={}
        ))

    def _map_stream_event_type(self, stream_type: StreamEventType) -> str:
        """Mapeia StreamEventType para string de evento de domínio."""
        mapping = {
            StreamEventType.TEXT: "TEXT",
            StreamEventType.THOUGHT: "THOUGHT",
            StreamEventType.TOOL_START: "TOOL_START",
            StreamEventType.TOOL_RESULT: "TOOL_RESULT",
            StreamEventType.ERROR: "ERROR",
        }
        return mapping.get(stream_type, "TEXT")
