# -*- coding: utf-8 -*-
"""
Tool: create_thread

Cria uma nova thread a partir de uma mensagem Discord.

DOC: DDD Migration - Presentation Layer
"""

from __future__ import annotations

import logging
from typing import Any

from ...application.services.discord_service import DiscordService

logger = logging.getLogger(__name__)


async def handle_create_thread(
    discord_service: DiscordService,
    args: dict[str, Any]
) -> dict[str, Any]:
    """
    Handler para tool create_thread.

    Args:
        discord_service: Instância do DiscordService
        args: Argumentos do tool

    Returns:
        Dict com thread_id, thread_name, status
    """
    chat_id = args.get("chat_id") or args.get("channel_id")
    message_id = args.get("message_id")
    name = args.get("name")
    auto_archive_duration = args.get("auto_archive_duration", 1440)

    if not chat_id or not message_id or not name:
        return {
            "status": "error",
            "error": "chat_id, message_id e name são obrigatórios"
        }

    # Valida auto_archive_duration
    if auto_archive_duration not in [60, 1440, 4320, 10080]:
        auto_archive_duration = 1440

    try:
        channel = await discord_service._client.fetch_channel(int(chat_id))
        message = await channel.fetch_message(int(message_id))

        thread = await message.create_thread(
            name=name,
            auto_archive_duration=auto_archive_duration,
        )

        logger.info(f"Thread criada: {thread.name} ({thread.id})")

        return {
            "thread_id": str(thread.id),
            "thread_name": thread.name,
            "parent_channel_id": str(channel.id),
            "message_id": str(message.id),
            "status": "success"
        }
    except Exception as e:
        logger.error(f"Erro ao criar thread: {e}")
        return {
            "status": "error",
            "error": str(e)
        }


# Tool definition para registro no MCP
TOOL_DEFINITION = {
    "name": "create_thread",
    "description": (
        "Create a new thread from a message in a Discord channel. "
        "Threads allow organized discussions branching from a specific message."
    ),
    "inputSchema": {
        "type": "object",
        "properties": {
            "chat_id": {"type": "string", "description": "Channel ID where the message exists"},
            "message_id": {"type": "string", "description": "Message ID to create thread from"},
            "name": {"type": "string", "description": "Name for the new thread"},
            "auto_archive_duration": {
                "type": "number",
                "enum": [60, 1440, 4320, 10080],
                "default": 1440,
                "description": "Auto-archive duration in minutes: 60=1h, 1440=24h, 4320=3d, 10080=7d",
            },
        },
        "required": ["chat_id", "message_id", "name"],
    },
}
