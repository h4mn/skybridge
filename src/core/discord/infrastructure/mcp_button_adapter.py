# -*- coding: utf-8 -*-
"""
MCPButtonAdapter

Adapter para converter interações Discord em Commands e rotear para handlers.

DOC: DDD Migration - Infrastructure Layer
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from src.core.discord.application.commands.handle_button_click import HandleButtonClickCommand
from src.core.discord.application.handlers.button_click_handler import ButtonClickHandler

if TYPE_CHECKING:
    from src.core.discord.application.services.event_publisher import EventPublisher

logger = logging.getLogger(__name__)


class MCPButtonAdapter:
    """
    Adapter para processar interações Discord (botões, menus).

    Este adapter converte interações brutas do Discord em Commands
    e as processa via handlers apropriados.

    Responsabilidade única: converter interações Discord em Commands DDD.
    Notificações MCP são enviadas pela camada Presentation (server.py).

    Fluxo:
    1. Recebe Discord Interaction
    2. Converte para HandleButtonClickCommand
    3. Processa via ButtonClickHandler
    4. Publica ButtonClickedEvent (para outros interessados)
    """

    def __init__(self, event_publisher):
        """
        Inicializa adapter.

        Args:
            event_publisher: Publicador de eventos de domínio
        """
        self._event_publisher = event_publisher
        self._handler = ButtonClickHandler(event_publisher)

    async def handle_interaction(self, interaction) -> dict:
        """
        Processa interação Discord.

        Args:
            interaction: Interação Discord (discord.Interaction)

        Returns:
            Dict com status da operação
        """
        print(f"[DEBUG MCPButtonAdapter] Interacao recebida: {interaction.type}")
        try:
            # 1. Converter para Command
            print(f"[DEBUG MCPButtonAdapter] Convertendo para command...")
            command = HandleButtonClickCommand.from_discord_interaction(interaction)
            print(f"[DEBUG MCPButtonAdapter] Command criado: {command.button_custom_id}")

            # 2. Processar via Handler
            print(f"[DEBUG MCPButtonAdapter] Processando via handler...")
            result = await self._handler.handle(command)
            print(f"[DEBUG MCPButtonAdapter] Handler result: {result.is_success}, {result.message}")

            return {
                "status": "success" if result.is_success else "error",
                "message": result.message,
                "data": result.data,
            }

        except Exception as e:
            print(f"[ERROR MCPButtonAdapter] Erro no adapter: {e}")
            import traceback
            traceback.print_exc()
            return {
                "status": "error",
                "message": str(e),
                "data": None,
            }
