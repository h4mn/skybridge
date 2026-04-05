"""
Testes unitários para EventBus.

Testa:
- subscribe/unsubscribe
- publish para handlers inscritos
- múltiplos handlers para mesmo evento
- clear
"""

import pytest

from src.core.paper.domain.events import (
    EventBus,
    get_event_bus,
    reset_event_bus,
    OrdemCriada,
    Lado,
)


class TestEventBus:
    """Testes para EventBus."""

    def test_subscribe_e_publish(self):
        """Handler inscrito deve receber evento publicado."""
        bus = EventBus()
        received = []

        def handler(event: OrdemCriada):
            received.append(event)

        bus.subscribe(OrdemCriada, handler)

        event = OrdemCriada(
            ordem_id="123",
            ticker="PETR4",
            lado=Lado.COMPRA,
            quantidade=100
        )
        bus.publish(event)

        assert len(received) == 1
        assert received[0].ordem_id == "123"

    def test_subscribe_multiplos_handlers(self):
        """Múltiplos handlers devem ser notificados."""
        bus = EventBus()
        results = []

        bus.subscribe(OrdemCriada, lambda e: results.append("handler1"))
        bus.subscribe(OrdemCriada, lambda e: results.append("handler2"))

        event = OrdemCriada(
            ordem_id="123",
            ticker="PETR4",
            lado=Lado.COMPRA,
            quantidade=100
        )
        bus.publish(event)

        assert results == ["handler1", "handler2"]

    def testunsubscribe_remove_handler(self):
        """Unsubscribe deve remover handler."""
        bus = EventBus()
        received = []

        def handler(event: OrdemCriada):
            received.append(event)

        bus.subscribe(OrdemCriada, handler)
        bus.unsubscribe(OrdemCriada, handler)

        event = OrdemCriada(
            ordem_id="123",
            ticker="PETR4",
            lado=Lado.COMPRA,
            quantidade=100
        )
        bus.publish(event)

        assert len(received) == 0

    def test_publish_sem_handlers(self):
        """Publish sem handlers não deve levantar erro."""
        bus = EventBus()

        event = OrdemCriada(
            ordem_id="123",
            ticker="PETR4",
            lado=Lado.COMPRA,
            quantidade=100
        )

        # Não deve levantar exceção
        bus.publish(event)

    def test_clear_remove_todos_handlers(self):
        """Clear deve remover todos os handlers."""
        bus = EventBus()
        received = []

        bus.subscribe(OrdemCriada, lambda e: received.append("x"))
        bus.clear()

        event = OrdemCriada(
            ordem_id="123",
            ticker="PETR4",
            lado=Lado.COMPRA,
            quantidade=100
        )
        bus.publish(event)

        assert len(received) == 0


class TestEventBusSingleton:
    """Testes para EventBus singleton."""

    def test_get_event_bus_retorna_mesma_instancia(self):
        """get_event_bus deve retornar mesma instância."""
        bus1 = get_event_bus()
        bus2 = get_event_bus()

        assert bus1 is bus2

    def test_reset_event_bus_cria_nova_instancia(self):
        """reset_event_bus deve criar nova instância."""
        bus1 = get_event_bus()
        reset_event_bus()
        bus2 = get_event_bus()

        assert bus1 is not bus2
