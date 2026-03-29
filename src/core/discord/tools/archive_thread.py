"""
Tool: archive_thread

Arquiva uma thread Discord.
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from ..models import ArchiveThreadInput, ArchiveThreadOutput
from ..access import load_access

if TYPE_CHECKING:
    from discord import Client, Thread

logger = logging.getLogger(__name__)


async def handle_archive_thread(client: "Client", args: dict) -> ArchiveThreadOutput:
    """
    Handler para tool archive_thread.

    Args:
        client: Cliente Discord conectado
        args: Argumentos (thread_id)

    Returns:
        ArchiveThreadOutput com confirmação

    Raises:
        ValueError: Se thread não encontrada ou não autorizada
    """
    # Valida entrada
    input_data = ArchiveThreadInput.model_validate(args)

    # Busca thread
    try:
        channel = client.get_channel(int(input_data.thread_id))
    except Exception:
        channel = None

    if channel is None:
        # Tenta fetch da API
        try:
            channel = await client.fetch_channel(int(input_data.thread_id))
        except Exception:
            raise ValueError(f"Thread {input_data.thread_id} não encontrada")

    # Verifica se é thread
    if not hasattr(channel, "archived"):
        raise ValueError(f"Canal {input_data.thread_id} não é uma thread")

    # Verifica autorização (usa parent channel para lookup)
    access = load_access()
    parent_id = str(channel.parent_id) if hasattr(channel, "parent_id") else str(channel.id)

    if parent_id not in access.groups:
        raise ValueError(
            f"Thread em canal não autorizado — adicione via /discord:access"
        )

    # Arquiva
    try:
        await channel.edit(archived=True)
        logger.info(f"Thread arquivada: {channel.name} ({channel.id})")
    except Exception as e:
        raise ValueError(f"Falha ao arquivar thread: {e}")

    return ArchiveThreadOutput(
        thread_id=input_data.thread_id,
        archived=True,
    )


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
            "thread_id": {
                "type": "string",
                "description": "Thread ID to archive",
            },
        },
        "required": ["thread_id"],
    },
}
