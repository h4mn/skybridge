# coding: utf-8
"""
Core SY - Chat Module.

Este módulo contém componentes refatorados de chat com arquitetura event-driven.

## Componentes Principais

- **ChatContainer**: Container DI com lifecycle management
- **ChatOrchestrator**: Coordenador de chat + TTS
- **EventBus**: Barramento de eventos para comunicação loose-coupled
- **TTSService**: Serviço TTS isolado com lifecycle próprio

## Exemplo de Uso

```python
from core.sy.chat import ChatContainer

async with ChatContainer.create() as container:
    orchestrator = container.orchestrator
    async for chunk in orchestrator.process_turn("Oi Sky", turn_id="turn-1"):
        print(f"Chunk: {chunk.content}")
# Cleanup automático
```

DOC: openspec/changes/refactor-chat-event-driven
"""

from core.sy.chat.container import ChatContainer, ChatContainerContext
from core.sy.chat.events import (
    StreamChunkEvent,
    TTSCompletedEvent,
    TTSStartedEvent,
    TurnCompletedEvent,
    TurnStartedEvent,
)
from core.sy.chat.orchestrator import ChatOrchestrator

__all__ = [
    # Container
    "ChatContainer",
    "ChatContainerContext",
    # Orchestrator
    "ChatOrchestrator",
    # Events
    "StreamChunkEvent",
    "TTSStartedEvent",
    "TTSCompletedEvent",
    "TurnStartedEvent",
    "TurnCompletedEvent",
]
