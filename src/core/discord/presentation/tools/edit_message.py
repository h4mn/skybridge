# -*- coding: utf-8 -*-
"""
Tool: edit_message

Edita mensagem existente no Discord.

DOC: DDD Migration - Presentation Layer
"""

from __future__ import annotations

import logging
from typing import Any

from ...application.services.discord_service import DiscordService

logger = logging.getLogger(__name__)


async def handle_edit_message(
    discord_service: DiscordService,
    args: dict[str, Any]
) -> dict[str, Any]:
    """
    Handler para tool edit_message.

    Args:
        discord_service: Instância do DiscordService
        args: Argumentos do tool

    Returns:
        Dict com message_id, status
    """
    chat_id = args.get("chat_id")
    message_id = args.get("message_id")
    content = args.get("content")
    embed = args.get("embed")

    if not all([chat_id, message_id]):
        return {
            "status": "error",
            "error": "chat_id e message_id são obrigatórios"
        }

    if not content and not embed:
        return {
            "status": "error",
            "error": "Especifique content ou embed para editar"
        }

    # Edita mensagem via DiscordService
    try:
        message = await discord_service.edit_message(
            channel_id=chat_id,
            message_id=message_id,
            content=content,
            embed=embed,
        )

        return {
            "message_id": str(message.id) if message else None,
            "status": "success"
        }
    except Exception as e:
        logger.error(f"Erro ao editar mensagem: {e}")
        return {
            "status": "error",
            "error": str(e)
        }


# Tool definition para registro no MCP
TOOL_DEFINITION = {
    "name": "edit_message",
    "description": (
        "Edit existing Discord message. "
        "Use for interim progress updates - doesn't trigger push notifications."
    ),
    "inputSchema": {
        "type": "object",
        "properties": {
            "chat_id": {"type": "string", "description": "Channel ID"},
            "message_id": {"type": "string", "description": "Message ID to edit"},
            "content": {"type": "string", "description": "New message content"},
            "embed": {"type": "object", "description": "New embed (dict format)"},
        },
        "required": ["chat_id", "message_id"],
    },
}
