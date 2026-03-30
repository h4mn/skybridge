# -*- coding: utf-8 -*-
"""
EventPublisher

Publicador de eventos de domínio.

DOC: DDD Migration - Application Layer
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from src.core.discord.domain.events.base import DomainEvent

logger = logging.getLogger(__name__)


class EventPublisher:
    """
    Publicador de eventos de domínio.

    Responsável por publicar eventos para os interessados.
    Em implementação futura, pode usar um message broker (RabbitMQ, Kafka).

    Uso:
        publisher = EventPublisher()
        await publisher.publish(ButtonClickedEvent.create(...))
    """

    async def publish(self, event: DomainEvent) -> None:
        """
        Publica evento de domínio.

        Args:
            event: Evento a ser publicado
        """
        # Por enquanto, apenas log
        # Em implementação futura, enviar para message broker
        logger.info(
            f"Event published: {event.__class__.__name__} "
            f"(id={event.event_id}, occurred_at={event.occurred_at})"
        )

        # Aqui seria o ponto para:
        # - Enviar para RabbitMQ/Kafka
        # - Invocar subscribers via EventBus
        # - Persistir em EventStore

    async def publish_batch(self, events: list[DomainEvent]) -> None:
        """
        Publica lote de eventos.

        Args:
            events: Lista de eventos a serem publicados
        """
        for event in events:
            await self.publish(event)
