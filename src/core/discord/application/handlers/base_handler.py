# -*- coding: utf-8 -*-
"""
BaseHandler.

Classe base para handlers CQRS do Discord.

Fornece funcionalidade comum para todos os handlers:
- Validação de acesso
- Publicação de eventos
- Constantes compartilhadas
"""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

from ...domain.entities import Message
from ...domain.events import MessageSentEvent
from ...domain.repositories import ChannelRepository


# IDs temporários para mensagens antes de serem enviadas ao Discord API
# Serão substituídos pelos IDs reais retornados pelo Discord
TEMP_MESSAGE_ID = "0"
TEMP_AUTHOR_ID = "0"


class BaseHandler:
    """
    Classe base para handlers CQRS do Discord.

    Fornece métodos comuns para validação e publicação de eventos.
    """

    def __init__(
        self,
        channel_repository: ChannelRepository,
        event_publisher: Callable[[Any], Any],
    ) -> None:
        """
        Inicializa handler base.

        Args:
            channel_repository: Repositório de canais para validação
            event_publisher: Publicador de eventos de domínio
        """
        self._channel_repo = channel_repository
        self._event_publisher = event_publisher

    async def _validate_access(self, channel_id) -> None:
        """
        Valida se o canal está autorizado.

        Args:
            channel_id: ChannelId a validar

        Raises:
            PermissionError: Se canal não está autorizado
        """
        if not await self._channel_repo.is_authorized(channel_id):
            raise PermissionError(f"Canal {channel_id} não está autorizado")

    async def _publish_event(self, message: Message) -> None:
        """
        Publica evento de domínio MessageSentEvent.

        Args:
            message: Message que foi enviada
        """
        event = MessageSentEvent.create(
            message_id=str(message.id),
            channel_id=str(message.channel_id),
            content_length=len(message.content),
            chunk_count=len(message.content.chunk()),
        )
        await self._event_publisher(event)
