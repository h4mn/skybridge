# -*- coding: utf-8 -*-
"""
UpdateComponentHandler.

Handler para comando de atualização de componente.
Atualiza progresso, botões ou menu de mensagem existente.
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from ..commands.update_component_command import UpdateComponentCommand

if TYPE_CHECKING:
    from discord import Client, Message

logger = logging.getLogger(__name__)


class UpdateComponentHandler:
    """Handler para UpdateComponentCommand."""

    def __init__(self, client: Client):
        """
        Inicializa handler.

        Args:
            client: Cliente Discord
        """
        self._client = client

    async def handle(self, command: UpdateComponentCommand) -> Message:
        """
        Executa atualização de componente.

        Args:
            command: Comando de atualização

        Returns:
            Mensagem atualizada

        Raises:
            ValueError: Se mensagem não encontrada
        """
        # Busca canal
        channel = await self._client.fetch_channel(command.channel_id.to_int())

        # Busca mensagem
        try:
            message = await channel.fetch_message(command.message_id.to_int())
        except Exception as e:
            raise ValueError(f"Mensagem {command.message_id} não encontrada: {e}")

        # Atualiza conforme comando
        kwargs = {}

        if command.new_text is not None:
            kwargs["content"] = command.new_text

        # Desabilitar botões (remove view)
        if command.disable_buttons:
            kwargs["view"] = None

        # Atualizar progresso
        # NOTA: Atualização de embed de progresso requerida infraestrutura Discord
        # e causa conflito de namespace em testes. Implementação futura pode
        # mover esta lógica para uma camada de adapter específica.
        if command.new_progress_percentage is not None or command.new_progress_status is not None:
            logger.info(
                f"Progress update requested: {command.new_progress_percentage}% "
                f"status={command.new_progress_status} "
                f"(embed update not implemented due to namespace conflict)"
            )
            # TODO: Implementar atualização de embed quando resolver conflito namespace
            pass

        # Edita mensagem
        try:
            updated_msg = await message.edit(**kwargs)
            logger.info(f"Componente atualizado: mensagem {command.message_id}")
            return updated_msg
        except Exception as e:
            raise ValueError(f"Falha ao atualizar componente: {e}")
