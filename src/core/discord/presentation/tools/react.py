# -*- coding: utf-8 -*-
"""
Tool: react

Adiciona reação emoji a mensagem Discord.

DOC: DDD Migration - Presentation Layer
"""

from __future__ import annotations

import logging
from typing import Any

from ...application.services.discord_service import DiscordService

logger = logging.getLogger(__name__)


async def handle_react(
    discord_service: DiscordService,
    args: dict[str, Any]
) -> dict[str, Any]:
    """
    Handler para tool react.

    Args:
        discord_service: Instância do DiscordService
        args: Argumentos do tool

    Returns:
        Dict com status
    """
    chat_id = args.get("chat_id")
    message_id = args.get("message_id")
    emoji = args.get("emoji")

    if not all([chat_id, message_id, emoji]):
        return {
            "status": "error",
            "error": "chat_id, message_id e emoji são obrigatórios"
        }

    # Adiciona reação via DiscordService
    try:
        success = await discord_service.add_reaction(
            channel_id=chat_id,
            message_id=message_id,
            emoji=emoji,
        )

        return {
            "status": "success" if success else "failed"
        }
    except Exception as e:
        logger.error(f"Erro ao adicionar reação: {e}")
        return {
            "status": "error",
            "error": str(e)
        }


# Tool definition para registro no MCP
TOOL_DEFINITION = {
    "name": "react",
    "description": (
        "Add emoji reaction to Discord message. "
        "Use for quick acknowledgment or feedback."
    ),
    "inputSchema": {
        "type": "object",
        "properties": {
            "chat_id": {"type": "string", "description": "Channel ID"},
            "message_id": {"type": "string", "description": "Message ID"},
            "emoji": {"type": "string", "description": "Emoji to add (e.g., ✅, 👍, 🔥)"},
        },
        "required": ["chat_id", "message_id", "emoji"],
    },
}
