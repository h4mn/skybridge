# -*- coding: utf-8 -*-
"""
ButtonClickHandler

Handler para processar cliques de botão Discord.
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from src.core.discord.application.commands.handle_button_click import HandleButtonClickCommand
from src.core.discord.application.handlers.base_handler import BaseHandler
from src.core.discord.application.handlers.handler_result import HandlerResult
from src.core.discord.domain.events.button_clicked import ButtonClickedEvent

if TYPE_CHECKING:
    from src.core.discord.application.services.event_publisher import EventPublisher

logger = logging.getLogger(__name__)


class ButtonClickHandler(BaseHandler):
    """
    Handler para processar cliques de botão Discord.

    Fluxo:
    1. Recebe HandleButtonClickCommand
    2. Valida dados
    3. Publica ButtonClickedEvent
    4. Retorna HandlerResult com sucesso
    """

    def __init__(self, event_publisher):
        """
        Inicializa handler.

        Args:
            event_publisher: Publicador de eventos de domínio
        """
        self._event_publisher = event_publisher

    async def handle(self, command: HandleButtonClickCommand) -> HandlerResult:
        """
        Processa clique de botão.

        Args:
            command: Command com dados do clique

        Returns:
            HandlerResult com status e dados do evento
        """
        try:
            # 1. Validar dados
            if not command.button_custom_id:
                return HandlerResult.failure("button_custom_id é obrigatório")

            if not command.channel_id:
                return HandlerResult.failure("channel_id é obrigatório")

            # 2. Converter para Domain Event
            event = command.to_event()

            # 3. Publicar evento
            await self._event_publisher.publish(event)

            # 4. Log para debug
            logger.info(
                f"ButtonClickedEvent publicado: "
                f"botão={command.button_label} "
                f"usuário={command.user_name} "
                f"canal={command.channel_id}"
            )

            # 5. Retornar sucesso (usa success com message_id como event_id)
            return HandlerResult(
                success=True,
                message_id=event.event_id,
            )

        except Exception as e:
            logger.error(f"Erro ao processar clique de botão: {e}")
            return HandlerResult.failure(f"Erro ao processar clique: {str(e)}")
