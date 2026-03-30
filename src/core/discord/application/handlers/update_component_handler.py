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
        channel = await self._client.fetch_channel(int(command.channel_id))

        # Busca mensagem
        try:
            message = await channel.fetch_message(int(command.message_id))
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
        if command.new_progress_percentage is not None or command.new_progress_status is not None:
            # Precisa editar embed de progresso
            if message.embeds:
                embed = message.embeds[0]
                if command.new_progress_percentage is not None:
                    # Recalcula barra de progresso
                    total = 100  # Assume 100 como base
                    current = command.new_progress_percentage
                    bar_length = 20
                    filled = int((current / total) * bar_length)
                    bar = "█" * filled + "░" * (bar_length - filled)

                    description = f"```\n{bar} {current}%\n```"

                    # Adiciona status se fornecido
                    if command.new_progress_status:
                        status_map = {
                            "running": "🔄 Em andamento",
                            "success": "✅ Concluído",
                            "error": "❌ Erro",
                        }
                        description += f"\n{status_map.get(command.new_progress_status, command.new_progress_status)}"

                    # Atualiza descrição do embed
                    # Discord.py não permite editar embed diretamente, precisa criar novo
                    from discord import Embed
                    new_embed = Embed.from_dict(embed.to_dict())
                    new_embed.description = description
                    kwargs["embed"] = new_embed

        # Edita mensagem
        try:
            updated_msg = await message.edit(**kwargs)
            logger.info(f"Componente atualizado: mensagem {command.message_id}")
            return updated_msg
        except Exception as e:
            raise ValueError(f"Falha ao atualizar componente: {e}")
