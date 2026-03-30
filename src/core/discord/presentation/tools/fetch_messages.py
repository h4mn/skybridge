# -*- coding: utf-8 -*-
"""
Tool: fetch_messages

Busca histórico de mensagens do canal Discord.

DOC: DDD Migration - Presentation Layer
"""

from __future__ import annotations

import logging
from typing import Any

from ...application.services.discord_service import DiscordService
from ...domain.value_objects import ChannelId

logger = logging.getLogger(__name__)


async def handle_fetch_messages(
    discord_service: DiscordService,
    args: dict[str, Any]
) -> dict[str, Any]:
    """
    Handler para tool fetch_messages.

    Args:
        discord_service: Instância do DiscordService
        args: Argumentos do tool

    Returns:
        Dict com messages, status
    """
    chat_id = args.get("chat_id")
    limit = args.get("limit", 20)

    if not chat_id:
        return {
            "status": "error",
            "error": "chat_id é obrigatório"
        }

    channel_id = ChannelId(chat_id)

    # Busca histórico via DiscordService
    try:
        messages = await discord_service.get_history(
            channel_id=channel_id,
            limit=limit,
        )

        return {
            "messages": [
                {
                    "id": str(msg.id),
                    "content": msg.content,
                    "author": msg.author.name,
                    "author_id": str(msg.author.id),
                    "timestamp": msg.created_at.isoformat(),
                }
                for msg in messages
            ],
            "count": len(messages),
            "status": "success"
        }
    except Exception as e:
        logger.error(f"Erro ao buscar mensagens: {e}")
        return {
            "messages": [],
            "count": 0,
            "status": "error",
            "error": str(e)
        }


# Tool definition para registro no MCP
TOOL_DEFINITION = {
    "name": "fetch_messages",
    "description": (
        "Fetch message history from Discord channel. "
        "Discord's search API isn't available to bots."
    ),
    "inputSchema": {
        "type": "object",
        "properties": {
            "chat_id": {"type": "string", "description": "Channel ID"},
            "limit": {"type": "integer", "description": "Max messages (default: 20)"},
        },
        "required": ["chat_id"],
    },
}
