# -*- coding: utf-8 -*-
"""
Tool: list_threads

Lista threads ativas em um canal Discord.

DOC: DDD Migration - Presentation Layer
"""

from __future__ import annotations

import logging
from typing import Any

from ...application.services.discord_service import DiscordService

logger = logging.getLogger(__name__)


async def handle_list_threads(
    discord_service: DiscordService,
    args: dict[str, Any]
) -> dict[str, Any]:
    """
    Handler para tool list_threads.

    Args:
        discord_service: Instância do DiscordService
        args: Argumentos do tool

    Returns:
        Dict com lista de threads e metadados
    """
    chat_id = args.get("chat_id") or args.get("channel_id")
    include_archived = args.get("include_archived", False)

    if not chat_id:
        return {
            "status": "error",
            "error": "chat_id é obrigatório"
        }

    try:
        channel = await discord_service._client.fetch_channel(int(chat_id))

        if not hasattr(channel, "threads"):
            return {
                "status": "error",
                "error": "Canal não suporta threads"
            }

        threads_list = []

        # Threads ativas
        for thread in channel.threads:
            threads_list.append({
                "id": str(thread.id),
                "name": thread.name,
                "message_count": thread.message_count or 0,
                "created_at": thread.created_at.isoformat() if thread.created_at else "",
                "archived": thread.archived,
                "parent_channel_id": str(channel.id),
            })

        # Threads arquivadas (se solicitado)
        if include_archived and hasattr(channel, "archived_threads"):
            async for thread in channel.archived_threads(limit=50):
                threads_list.append({
                    "id": str(thread.id),
                    "name": thread.name,
                    "message_count": thread.message_count or 0,
                    "created_at": thread.created_at.isoformat() if thread.created_at else "",
                    "archived": True,
                    "parent_channel_id": str(channel.id),
                })

        logger.info(f"Listadas {len(threads_list)} threads em {channel.id}")

        return {
            "threads": threads_list,
            "channel_id": chat_id,
            "total": len(threads_list),
            "status": "success"
        }
    except Exception as e:
        logger.error(f"Erro ao listar threads: {e}")
        return {
            "status": "error",
            "error": str(e)
        }


# Tool definition para registro no MCP
TOOL_DEFINITION = {
    "name": "list_threads",
    "description": (
        "List active threads in a Discord channel. "
        "Optionally include archived threads."
    ),
    "inputSchema": {
        "type": "object",
        "properties": {
            "chat_id": {"type": "string", "description": "Channel ID to list threads from"},
            "include_archived": {
                "type": "boolean",
                "default": False,
                "description": "Include archived threads in the list",
            },
        },
        "required": ["chat_id"],
    },
}
