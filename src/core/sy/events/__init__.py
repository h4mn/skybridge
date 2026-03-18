# coding: utf-8
"""
Sistema de Eventos - Arquitetura Event-Driven para Chat + TTS.

Este módulo fornece infraestrutura de pub/sub assíncrono para comunicação
loose-coupled entre componentes do chat.

DOC: openspec/changes/refactor-chat-event-driven/specs/event-bus/spec.md

## Componentes

- EventBus: Protocolo para sistemas de pub/sub
- InMemoryEventBus: Implementação em memória com asyncio.Queue
- BaseEvent: Classe base para todos os eventos de domínio

## Eventos de Domínio

Eventos específicos do chat estão em `core.sy.chat.events`:
- StreamChunkEvent
- TurnStartedEvent
- TurnCompletedEvent
- TTSStartedEvent
- TTSCompletedEvent

## Exemplo de Uso

```python
from core.sy.events import InMemoryEventBus, BaseEvent
from core.sy.chat.events import StreamChunkEvent

async def main():
    bus = InMemoryEventBus()

    # Subscriber recebe eventos
    async for event in bus.subscribe(StreamChunkEvent):
        print(f"Received: {event.content}")

    # Publisher envia eventos
    await bus.publish(StreamChunkEvent(content="Hello"))
```

## Exports

EventBus: Protocolo para sistemas de pub/sub
InMemoryEventBus: Implementação em memória
BaseEvent: Classe base para eventos
"""

from core.sy.events.event_bus import EventBus, InMemoryEventBus, BaseEvent

__all__ = [
    "EventBus",
    "InMemoryEventBus",
    "BaseEvent",
]
