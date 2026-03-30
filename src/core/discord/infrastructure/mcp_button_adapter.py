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

    Fluxo:
    1. Recebe Discord Interaction
    2. Converte para HandleButtonClickCommand
    3. Processa via ButtonClickHandler
    4. Publica ButtonClickedEvent
    """

    def __init__(self, event_publisher, server):
        """
        Inicializa adapter.

        Args:
            event_publisher: Publicador de eventos de domínio
            server: Instância do DiscordMCPServer para enviar notificações MCP
        """
        self._event_publisher = event_publisher
        self._server = server
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

            # 3. Enviar notificação MCP para Claude Code
            if result.is_success:
                print(f"[DEBUG MCPButtonAdapter] Enviando notificacao MCP...")
                await self._send_mcp_notification(interaction, command, result)
                print(f"[DEBUG MCPButtonAdapter] Notificacao enviada!")

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

    async def _send_mcp_notification(self, interaction, command: HandleButtonClickCommand, result):
        """
        Envia notificação MCP para Claude Code.

        Args:
            interaction: Interação Discord original
            command: Command processado
            result: Resultado do processamento
        """
        notification = {
            "button_id": command.button_custom_id,
            "button_label": command.button_label,
            "user": command.user_name,
            "user_id": command.user_id,
            "channel_id": command.channel_id,
            "message_id": command.message_id,
            "event_id": result.data.get("event_id") if result.data else None,
            "ts": interaction.created_at.isoformat(),
        }

        await self._server.send_notification(
            "notifications/claude/button_clicked",
            notification,
        )

        logger.info(f"Notificação MCP enviada: {command.button_custom_id}")
