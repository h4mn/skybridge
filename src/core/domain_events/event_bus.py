# -*- coding: utf-8 -*-
"""
Event Bus Interface.

Defines the contract for event bus implementations. The event bus is
responsible for publishing events to subscribed listeners.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Awaitable, Callable, TypeVar

from core.domain_events.domain_event import DomainEvent

# Type alias for event handlers
# An event handler is a callable that takes a DomainEvent and returns None
EventHandler = Callable[[DomainEvent], None | Awaitable[None]]

# Generic type for event subclasses
E = TypeVar("E", bound=DomainEvent)


class EventBus(ABC):
    """
    Abstract base class for event bus implementations.

    The event bus implements the Observer pattern, allowing components
    to publish events without knowing who is listening.
    """

    @abstractmethod
    async def publish(self, event: DomainEvent) -> None:
        """
        Publish an event to all subscribed listeners.

        Args:
            event: The domain event to publish
        """
        pass

    @abstractmethod
    async def publish_batch(self, events: list[DomainEvent]) -> None:
        """
        Publish multiple events atomically.

        Args:
            events: List of domain events to publish
        """
        pass

    @abstractmethod
    def subscribe(
        self,
        event_type: type[DomainEvent],
        handler: EventHandler,
    ) -> str:
        """
        Subscribe to events of a specific type.

        Args:
            event_type: The DomainEvent subclass to listen for
            handler: Callable that will be invoked when events occur

        Returns:
            subscription_id: Unique ID for this subscription (can be used to unsubscribe)
        """
        pass

    @abstractmethod
    def unsubscribe(self, subscription_id: str) -> bool:
        """
        Unsubscribe from events using the subscription ID.

        Args:
            subscription_id: The ID returned by subscribe()

        Returns:
            True if subscription was removed, False if not found
        """
        pass

    @abstractmethod
    def unsubscribe_all(self, handler: EventHandler) -> int:
        """
        Unsubscribe all subscriptions for a given handler.

        Args:
            handler: The handler to unsubscribe

        Returns:
            Number of subscriptions removed
        """
        pass

    @abstractmethod
    async def close(self) -> None:
        """
        Close the event bus and release resources.

        Should be called when shutting down the application.
        """
        pass


class EventBusError(Exception):
    """Base exception for event bus errors."""

    pass


class EventPublishError(EventBusError):
    """Raised when publishing an event fails."""

    pass


class SubscriptionNotFoundError(EventBusError):
    """Raised when trying to unsubscribe a non-existent subscription."""

    pass
