"""
EventBus - Sistema de Publicação/Inscrição de Eventos.

Implementa padrão Observer para comunicação assíncrona entre componentes.
"""

from __future__ import annotations

import logging
from collections import defaultdict
from typing import Any, Callable, TypeVar

from .base_event import DomainEvent

logger = logging.getLogger(__name__)

# Type alias para handlers
EventHandler = Callable[[DomainEvent], None]
T = TypeVar("T", bound=DomainEvent)


class EventBus:
    """
    EventBus simples para publish/subscribe de eventos de domínio.

    Uso:
        bus = EventBus()

        # Inscrever handler
        bus.subscribe(OrdemCriada, lambda e: print(f"Ordem {e.ordem_id} criada"))

        # Publicar evento
        bus.publish(OrdemCriada(ordem_id="123", ticker="PETR4", lado="compra", quantidade=100))
    """

    def __init__(self) -> None:
        # Map: event_type -> list of handlers
        self._handlers: dict[str, list[EventHandler]] = defaultdict(list)
        # Map: event_type (string) -> event_class
        self._event_types: dict[str, type[DomainEvent]] = {}

    def subscribe(self, event_class: type[T], handler: Callable[[T], None]) -> None:
        """
        Inscreve um handler para um tipo de evento.

        Args:
            event_class: Classe do evento (ex: OrdemCriada)
            handler: Função que recebe o evento
        """
        event_type = event_class.__name__
        self._handlers[event_type].append(handler)  # type: ignore
        self._event_types[event_type] = event_class
        logger.debug(f"Handler inscrito para {event_type}")

    def unsubscribe(self, event_class: type[T], handler: Callable[[T], None]) -> None:
        """Remove um handler inscrito."""
        event_type = event_class.__name__
        if handler in self._handlers[event_type]:
            self._handlers[event_type].remove(handler)
            logger.debug(f"Handler removido de {event_type}")

    def publish(self, event: DomainEvent) -> None:
        """
        Publica um evento para todos os handlers inscritos.

        Args:
            event: Instância do evento de domínio
        """
        event_type = event.event_type
        handlers = self._handlers.get(event_type, [])

        if not handlers:
            logger.debug(f"Nenhum handler para {event_type}")
            return

        for handler in handlers:
            try:
                handler(event)
            except Exception as e:
                logger.error(f"Erro no handler de {event_type}: {e}")

    def clear(self) -> None:
        """Remove todos os handlers (útil para testes)."""
        self._handlers.clear()
        self._event_types.clear()


# Singleton global (pode ser substituído por DI container)
_global_event_bus: EventBus | None = None


def get_event_bus() -> EventBus:
    """Retorna o EventBus singleton."""
    global _global_event_bus
    if _global_event_bus is None:
        _global_event_bus = EventBus()
    return _global_event_bus


def reset_event_bus() -> None:
    """Reseta o EventBus singleton (útil para testes)."""
    global _global_event_bus
    _global_event_bus = None


__all__ = ["EventBus", "get_event_bus", "reset_event_bus"]
