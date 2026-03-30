# -*- coding: utf-8 -*-
"""
Tool: update_component

Atualiza componente de mensagem existente (progresso, botões, menu).
Útil para progress bars ou desabilitar botões após clique.

DOC: DDD Migration - Presentation Layer
"""

from __future__ import annotations

import logging
from typing import Any

from ...application.handlers.update_component_handler import UpdateComponentHandler
from ...application.services.discord_service import DiscordService

logger = logging.getLogger(__name__)


async def handle_update_component(
    discord_service: DiscordService,
    args: dict[str, Any]
) -> dict[str, Any]:
    """
    Handler para tool update_component.

    Args:
        discord_service: Instância do DiscordService
        args: Argumentos do tool

    Returns:
        Dict com message_id, status
    """
    chat_id = args.get("chat_id")
    message_id = args.get("message_id")
    new_text = args.get("new_text")
    disable_buttons = args.get("disable_buttons", False)
    new_progress_percentage = args.get("new_progress_percentage")
    new_progress_status = args.get("new_progress_status")

    if not chat_id or not message_id:
        return {
            "status": "error",
            "error": "chat_id e message_id são obrigatórios"
        }

    try:
        # Cria handler e executa
        handler = UpdateComponentHandler(client=discord_service._client)

        from ...application.commands.update_component_command import UpdateComponentCommand

        command = UpdateComponentCommand(
            channel_id=chat_id,
            message_id=message_id,
            new_text=new_text,
            disable_buttons=disable_buttons,
            new_progress_percentage=new_progress_percentage,
            new_progress_status=new_progress_status,
        )

        message = await handler.handle(command)

        return {
            "message_id": str(message.id),
            "status": "success"
        }
    except Exception as e:
        logger.error(f"Erro ao atualizar componente: {e}")
        return {
            "status": "error",
            "error": str(e)
        }


# Tool definition para registro no MCP
TOOL_DEFINITION = {
    "name": "update_component",
    "description": (
        "Update existing message component (progress bar, buttons, menu). "
        "Use to update progress indicators or disable buttons after interaction. "
        "For progress updates with tracking_id, use send_progress instead."
    ),
    "inputSchema": {
        "type": "object",
        "properties": {
            "chat_id": {"type": "string", "description": "Channel ID"},
            "message_id": {"type": "string", "description": "Message ID to update"},
            "new_text": {"type": "string", "description": "New message content (optional)"},
            "disable_buttons": {
                "type": "boolean",
                "default": False,
                "description": "Disable/remove buttons from message"
            },
            "new_progress_percentage": {
                "type": "integer",
                "description": "Update progress bar to this percentage (0-100)",
                "minimum": 0,
                "maximum": 100,
            },
            "new_progress_status": {
                "type": "string",
                "enum": ["running", "success", "error"],
                "description": "Progress status for visual indicator",
            },
        },
        "required": ["chat_id", "message_id"],
    },
}
