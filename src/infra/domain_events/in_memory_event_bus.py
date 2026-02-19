# -*- coding: utf-8 -*-
"""
In-Memory Event Bus Implementation.

A simple, synchronous event bus implementation that stores subscriptions
in memory. Thread-safe using threading.Lock.

This is suitable for development and single-instance deployments.
For multi-instance deployments, consider a Redis-backed event bus.
"""

from __future__ import annotations

import asyncio
import logging
import threading
from collections import defaultdict
from typing import Any
from uuid import uuid4

from core.domain_events.domain_event import DomainEvent
from core.domain_events.event_bus import (
    EventBus,
    EventHandler,
    EventPublishError,
    SubscriptionNotFoundError,
)

logger = logging.getLogger(__name__)


class InMemoryEventBus(EventBus):
    """
    In-memory implementation of the event bus.

    This implementation:
    - Stores subscriptions in memory (lost on restart)
    - Delivers events synchronously
    - Is thread-safe using threading.Lock (works across event loops)
    - Supports both sync and async handlers
    """

    def __init__(self, history_size: int = 100) -> None:
        """
        Initialize the in-memory event bus.

        Args:
            history_size: Maximum number of events to keep in history (default: 100)
        """
        self._subscriptions: dict[
            type[DomainEvent], dict[str, tuple[EventHandler, bool]]
        ] = defaultdict(dict)
        # threading.Lock works across different event loops (unlike asyncio.Lock)
        self._lock = threading.Lock()
        self._closed = False
        self._history: list[dict[str, Any]] = []
        self._history_size = history_size

    async def publish(self, event: DomainEvent) -> None:
        """
        Publish an event to all subscribed listeners.

        Args:
            event: The domain event to publish

        Raises:
            EventPublishError: If the event bus is closed or publishing fails
        """
        if self._closed:
            raise EventPublishError("Cannot publish to closed event bus")

        event_type = type(event)

        # Get handlers for this event type (with lock)
        handlers_copy: dict[str, tuple[EventHandler, bool]] = self._get_handlers(event_type)

        # Store event in history FIRST (before checking handlers)
        self._add_to_history(event.to_dict())

        if not handlers_copy:
            logger.debug(f"No handlers subscribed for event type: {event_type.__name__} (event still recorded in history)")
            return

        # Notify all handlers (without lock - allows handlers to publish)
        logger.info(
            f"Publishing {event_type.__name__} (id={event.event_id}) to {len(handlers_copy)} handler(s)"
        )

        for subscription_id, (handler, is_async) in handlers_copy.items():
            try:
                if is_async:
                    # Async handler
                    result = handler(event)
                    if asyncio.iscoroutine(result):
                        await result
                else:
                    # Sync handler - run in executor to avoid blocking
                    loop = asyncio.get_event_loop()
                    await loop.run_in_executor(None, handler, event)

            except Exception as e:
                logger.exception(
                    f"Handler {subscription_id} failed for event {event_type.__name__}: {e}"
                )
                # Continue notifying other handlers even if one fails

    def _get_handlers(self, event_type: type[DomainEvent]) -> dict[str, tuple[EventHandler, bool]]:
        """Get handlers for an event type (thread-safe)."""
        with self._lock:
            return self._subscriptions.get(event_type, {}).copy()

    def _add_to_history(self, event_dict: dict[str, Any]) -> None:
        """Add event to history (thread-safe)."""
        with self._lock:
            self._history.append(event_dict)
            # Keep only the most recent events
            if len(self._history) > self._history_size:
                self._history = self._history[-self._history_size:]

    async def publish_batch(self, events: list[DomainEvent]) -> None:
        """
        Publish multiple events in sequence.

        Args:
            events: List of domain events to publish

        Raises:
            EventPublishError: If the event bus is closed
        """
        for event in events:
            await self.publish(event)

    async def subscribe(
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
            subscription_id: Unique ID for this subscription

        Raises:
            EventPublishError: If the event bus is closed
        """
        if self._closed:
            raise EventPublishError("Cannot subscribe to closed event bus")

        subscription_id = str(uuid4())

        # Detect if handler is async or sync
        is_async = asyncio.iscoroutinefunction(handler)

        with self._lock:
            self._subscriptions[event_type][subscription_id] = (handler, is_async)

        logger.info(
            f"Subscribed {subscription_id} to {event_type.__name__} "
            f"({'async' if is_async else 'sync'} handler)"
        )

        return subscription_id

    def unsubscribe(self, subscription_id: str) -> bool:
        """
        Unsubscribe from events using the subscription ID.

        Args:
            subscription_id: The ID returned by subscribe()

        Returns:
            True if subscription was removed, False if not found
        """
        # Search through all event types
        with self._lock:
            for event_type, handlers in self._subscriptions.items():
                if subscription_id in handlers:
                    del handlers[subscription_id]
                    logger.info(f"Unsubscribed {subscription_id} from {event_type.__name__}")
                    return True

        raise SubscriptionNotFoundError(f"Subscription {subscription_id} not found")

    def unsubscribe_all(self, handler: EventHandler) -> int:
        """
        Unsubscribe all subscriptions for a given handler.

        Args:
            handler: The handler to unsubscribe

        Returns:
            Number of subscriptions removed
        """
        count = 0

        with self._lock:
            for event_type, handlers in self._subscriptions.items():
                to_remove = [
                    sub_id for sub_id, (h, _) in handlers.items() if h == handler
                ]

                for sub_id in to_remove:
                    del handlers[sub_id]
                    count += 1

        if count > 0:
            logger.info(f"Unsubscribed {count} subscription(s) for handler {handler}")

        return count

    async def close(self) -> None:
        """
        Close the event bus and clear all subscriptions.

        After closing, no new subscriptions or publications are allowed.
        """
        with self._lock:
            self._subscriptions.clear()
            self._closed = True

        logger.info("InMemoryEventBus closed")

    @property
    def is_closed(self) -> bool:
        """Check if the event bus is closed."""
        return self._closed

    def get_subscription_count(self, event_type: type[DomainEvent] | None = None) -> int:
        """
        Get the number of active subscriptions.

        Args:
            event_type: If specified, count only for this event type.
                       If None, count all subscriptions.

        Returns:
            Number of active subscriptions
        """
        with self._lock:
            if event_type:
                return len(self._subscriptions.get(event_type, {}))

            return sum(len(handlers) for handlers in self._subscriptions.values())

    def get_history(self, limit: int | None = None) -> list[dict[str, Any]]:
        """
        Get event history.

        Args:
            limit: Maximum number of events to return (most recent first).
                   If None, returns all events in history.

        Returns:
            List of event dictionaries in reverse chronological order
        """
        with self._lock:
            if limit:
                return self._history[-limit:][::-1]
            return self._history[::-1]

    def clear_history(self) -> None:
        """
        Clear all events from history.

        Useful for testing or resetting the event stream.
        """
        with self._lock:
            self._history.clear()
