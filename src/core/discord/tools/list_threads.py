"""
Tool: list_threads

Lista threads ativas em um canal Discord.
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from ..models import ListThreadsInput, ListThreadsOutput, ThreadInfo
from ..client import fetch_allowed_channel

if TYPE_CHECKING:
    from discord import Client, TextChannel

logger = logging.getLogger(__name__)


async def handle_list_threads(client: "Client", args: dict) -> ListThreadsOutput:
    """
    Handler para tool list_threads.

    Args:
        client: Cliente Discord conectado
        args: Argumentos (channel_id, include_archived?)

    Returns:
        ListThreadsOutput com lista de threads

    Raises:
        ValueError: Se canal não autorizado
    """
    # Valida entrada
    input_data = ListThreadsInput.model_validate(args)

    # Busca canal autorizado
    channel = await fetch_allowed_channel(client, input_data.channel_id)

    if not hasattr(channel, "threads"):
        raise ValueError("Canal não suporta threads")

    # Coleta threads
    threads: list[ThreadInfo] = []

    # Threads ativas
    for thread in channel.threads:
        threads.append(
            ThreadInfo(
                id=str(thread.id),
                name=thread.name,
                message_count=thread.message_count or 0,
                created_at=thread.created_at.isoformat() if thread.created_at else "",
                archived=thread.archived,
                parent_channel_id=str(channel.id),
            )
        )

    # Threads arquivadas (se solicitado)
    if input_data.include_archived and hasattr(channel, "archived_threads"):
        async for thread in channel.archived_threads(limit=50):
            threads.append(
                ThreadInfo(
                    id=str(thread.id),
                    name=thread.name,
                    message_count=thread.message_count or 0,
                    created_at=thread.created_at.isoformat() if thread.created_at else "",
                    archived=True,
                    parent_channel_id=str(channel.id),
                )
            )

    logger.info(f"Listadas {len(threads)} threads em {channel.id}")

    return ListThreadsOutput(
        threads=threads,
        channel_id=input_data.channel_id,
        total=len(threads),
    )


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
            "channel_id": {
                "type": "string",
                "description": "Channel ID to list threads from",
            },
            "include_archived": {
                "type": "boolean",
                "default": False,
                "description": "Include archived threads in the list",
            },
        },
        "required": ["channel_id"],
    },
}
