# -*- coding: utf-8 -*-
"""
Tool: rename_thread

Renomeia uma thread Discord.

DOC: DDD Migration - Presentation Layer
"""

from __future__ import annotations

import logging
from typing import Any

from ...application.services.discord_service import DiscordService

logger = logging.getLogger(__name__)


async def handle_rename_thread(
    discord_service: DiscordService,
    args: dict[str, Any]
) -> dict[str, Any]:
    """
    Handler para tool rename_thread.

    Args:
        discord_service: Instância do DiscordService
        args: Argumentos do tool

    Returns:
        Dict com thread_id, old_name, new_name, status
    """
    thread_id = args.get("thread_id")
    name = args.get("name")

    if not thread_id or not name:
        return {
            "status": "error",
            "error": "thread_id e name são obrigatórios"
        }

    try:
        # Busca thread
        try:
            channel = discord_service._client.get_channel(int(thread_id))
        except Exception:
            channel = None

        if channel is None:
            channel = await discord_service._client.fetch_channel(int(thread_id))

        # Verifica se é thread
        if not hasattr(channel, "archived"):
            return {
                "status": "error",
                "error": f"Canal {thread_id} não é uma thread"
            }

        # Renomeia
        old_name = channel.name
        await channel.edit(name=name)
        logger.info(f"Thread renomeada: {old_name} → {name} ({thread_id})")

        return {
            "thread_id": thread_id,
            "old_name": old_name,
            "new_name": name,
            "status": "success"
        }
    except Exception as e:
        logger.error(f"Erro ao renomear thread: {e}")
        return {
            "status": "error",
            "error": str(e)
        }


# Tool definition para registro no MCP
TOOL_DEFINITION = {
    "name": "rename_thread",
    "description": (
        "Rename a Discord thread. "
        "Useful for organizing discussions or updating thread purpose."
    ),
    "inputSchema": {
        "type": "object",
        "properties": {
            "thread_id": {"type": "string", "description": "Thread ID to rename"},
            "name": {"type": "string", "description": "New name for the thread"},
        },
        "required": ["thread_id", "name"],
    },
}
