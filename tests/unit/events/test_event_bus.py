# coding: utf-8
"""
Testes unitários do EventBus.

DOC: openspec/changes/refactor-chat-event-driven/specs/event-bus/spec.md
"""

import asyncio
import pytest

from core.sy.events.event_bus import InMemoryEventBus, BaseEvent


class DummyEvent(BaseEvent):
    """Evento de teste simples."""

    def __init__(self, value: str):
        super().__init__()
        self.value = value


class AnotherEvent(BaseEvent):
    """Outro evento de teste."""

    def __init__(self, number: int):
        super().__init__()
        self.number = number


@pytest.mark.asyncio
async def test_event_bus_publish_subscribe():
    """Teste básico: publicar e receber evento."""
    bus = InMemoryEventBus()
    received = []

    # Consumer task
    async def consume():
        async for event in bus.subscribe(DummyEvent):
            received.append(event)
            if len(received) >= 2:
                break  # Para após 2 eventos

    consumer = asyncio.create_task(consume())

    # Aguarda subscriber registrar
    await asyncio.sleep(0.01)

    # Publica 2 eventos
    await bus.publish(DummyEvent("first"))
    await bus.publish(DummyEvent("second"))

    # Aguarda consumer terminar
    await asyncio.wait_for(consumer, timeout=2.0)

    assert len(received) == 2
    assert received[0].value == "first"
    assert received[1].value == "second"


@pytest.mark.asyncio
async def test_event_bus_type_filtering():
    """Subscriber recebe apenas o tipo inscrito."""
    bus = InMemoryEventBus()
    received = []

    async def consume():
        async for event in bus.subscribe(DummyEvent):
            received.append(event)
            if len(received) >= 1:
                break

    consumer = asyncio.create_task(consume())

    # Aguarda subscriber registrar
    await asyncio.sleep(0.01)

    # Publica diferentes tipos
    await bus.publish(AnotherEvent(42))  # Não deve receber
    await bus.publish(DummyEvent("yes"))  # Deve receber

    await asyncio.wait_for(consumer, timeout=2.0)

    assert len(received) == 1
    assert isinstance(received[0], DummyEvent)
    assert received[0].value == "yes"


@pytest.mark.asyncio
async def test_event_bus_no_subscribers():
    """Publish sem subscribers não causa erro."""
    bus = InMemoryEventBus()

    # Não deve causar erro
    await bus.publish(DummyEvent("orphan"))


@pytest.mark.asyncio
async def test_event_bus_shutdown():
    """Shutdown encerra subscribers."""
    bus = InMemoryEventBus()
    received = []

    async def consume():
        async for event in bus.subscribe(DummyEvent):
            received.append(event)

    consumer = asyncio.create_task(consume())

    # Aguarda subscriber registrar
    await asyncio.sleep(0.01)

    await bus.publish(DummyEvent("before"))
    await asyncio.sleep(0.05)  # Deixa tempo para processar
    await bus.shutdown()

    # Após shutdown, consumer deve terminar
    await asyncio.wait_for(consumer, timeout=1.0)

    assert len(received) == 1
    assert received[0].value == "before"


@pytest.mark.asyncio
async def test_event_bus_multiple_subscribers():
    """Múltiplos subscribers recebem o mesmo evento."""
    bus = InMemoryEventBus()
    received_1 = []
    received_2 = []

    async def consume1():
        async for event in bus.subscribe(DummyEvent):
            received_1.append(event)
            if len(received_1) >= 1:
                break

    async def consume2():
        async for event in bus.subscribe(DummyEvent):
            received_2.append(event)
            if len(received_2) >= 1:
                break

    c1 = asyncio.create_task(consume1())
    c2 = asyncio.create_task(consume2())

    # Aguarda subscribers registrar
    await asyncio.sleep(0.01)

    await bus.publish(DummyEvent("event1"))

    await asyncio.gather(
        asyncio.wait_for(c1, timeout=2.0),
        asyncio.wait_for(c2, timeout=2.0),
    )

    assert len(received_1) == 1
    assert len(received_2) == 1
    assert received_1[0].value == received_2[0].value == "event1"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
