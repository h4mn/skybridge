# -*- coding: utf-8 -*-
"""
Event Bus Kernel Module.

Provides singleton access to the domain event bus.
"""

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from core.domain_events.event_bus import EventBus

# Singleton instance
_event_bus: "EventBus | None" = None


def set_event_bus(event_bus: "EventBus") -> None:
    """
    Define o EventBus global (singleton).

    Args:
        event_bus: Instância do EventBus a ser usada globalmente
    """
    global _event_bus
    _event_bus = event_bus


def get_event_bus() -> "EventBus":
    """
    Retorna o EventBus global (singleton).

    Returns:
        EventBus: Instância do EventBus

    Raises:
        RuntimeError: Se o EventBus não foi inicializado
    """
    if _event_bus is None:
        raise RuntimeError(
            "EventBus not initialized. Call set_event_bus() first."
        )
    return _event_bus


def clear_event_bus() -> None:
    """Remove o EventBus global (útil para testes)."""
    global _event_bus
    _event_bus = None
