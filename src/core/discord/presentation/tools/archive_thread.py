# -*- coding: utf-8 -*-
"""
Tool: archive_thread

Arquiva uma thread Discord.

DOC: DDD Migration - Presentation Layer
"""

from __future__ import annotations

import logging
from typing import Any

from ...application.services.discord_service import DiscordService

logger = logging.getLogger(__name__)


async def handle_archive_thread(
    discord_service: DiscordService,
    args: dict[str, Any]
) -> dict[str, Any]:
    """
    Handler para tool archive_thread.

    Args:
        discord_service: Instância do DiscordService
        args: Argumentos do tool

    Returns:
        Dict com thread_id, archived, status
    """
    thread_id = args.get("thread_id")

    if not thread_id:
        return {
            "status": "error",
            "error": "thread_id é obrigatório"
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

        # Arquiva
        await channel.edit(archived=True)
        logger.info(f"Thread arquivada: {channel.name} ({thread_id})")

        return {
            "thread_id": thread_id,
            "thread_name": channel.name,
            "archived": True,
            "status": "success"
        }
    except Exception as e:
        logger.error(f"Erro ao arquivar thread: {e}")
        return {
            "status": "error",
            "error": str(e)
        }


# Tool definition para registro no MCP
TOOL_DEFINITION = {
    "name": "archive_thread",
    "description": (
        "Archive a Discord thread. "
        "Archived threads are hidden but can be unarchived later."
    ),
    "inputSchema": {
        "type": "object",
        "properties": {
            "thread_id": {"type": "string", "description": "Thread ID to archive"},
        },
        "required": ["thread_id"],
    },
}
