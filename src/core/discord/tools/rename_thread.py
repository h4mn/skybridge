"""
Tool: rename_thread

Renomeia uma thread Discord.
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from ..models import RenameThreadInput, RenameThreadOutput
from ..access import load_access

if TYPE_CHECKING:
    from discord import Client, Thread

logger = logging.getLogger(__name__)


async def handle_rename_thread(client: "Client", args: dict) -> RenameThreadOutput:
    """
    Handler para tool rename_thread.

    Args:
        client: Cliente Discord conectado
        args: Argumentos (thread_id, name)

    Returns:
        RenameThreadOutput com confirmação

    Raises:
        ValueError: Se thread não encontrada ou não autorizada
    """
    # Valida entrada
    input_data = RenameThreadInput.model_validate(args)

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

    # Renomeia
    old_name = channel.name
    try:
        await channel.edit(name=input_data.name)
        logger.info(f"Thread renomeada: {old_name} → {input_data.name} ({channel.id})")
    except Exception as e:
        raise ValueError(f"Falha ao renomear thread: {e}")

    return RenameThreadOutput(
        thread_id=input_data.thread_id,
        old_name=old_name,
        new_name=input_data.name,
    )


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
            "thread_id": {
                "type": "string",
                "description": "Thread ID to rename",
            },
            "name": {
                "type": "string",
                "description": "New name for the thread",
            },
        },
        "required": ["thread_id", "name"],
    },
}
