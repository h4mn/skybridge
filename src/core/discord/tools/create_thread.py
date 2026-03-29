"""
Tool: create_thread

Cria uma nova thread a partir de uma mensagem Discord.
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from ..models import CreateThreadInput, CreateThreadOutput
from ..client import fetch_allowed_channel

if TYPE_CHECKING:
    from discord import Client, Message, Thread

logger = logging.getLogger(__name__)


async def handle_create_thread(client: "Client", args: dict) -> CreateThreadOutput:
    """
    Handler para tool create_thread.

    Args:
        client: Cliente Discord conectado
        args: Argumentos (channel_id, message_id, name, auto_archive_duration?)

    Returns:
        CreateThreadOutput com thread_id e metadados

    Raises:
        ValueError: Se canal não autorizado ou thread não pode ser criada
    """
    # Valida entrada
    input_data = CreateThreadInput.model_validate(args)

    # Busca canal autorizado
    channel = await fetch_allowed_channel(client, input_data.channel_id)

    # Busca mensagem base
    try:
        message = await channel.fetch_message(int(input_data.message_id))
    except Exception as e:
        raise ValueError(f"Mensagem {input_data.message_id} não encontrada: {e}")

    if message is None:
        raise ValueError(f"Mensagem {input_data.message_id} não encontrada")

    # Cria thread
    try:
        thread = await message.create_thread(
            name=input_data.name,
            auto_archive_duration=input_data.auto_archive_duration,
        )
    except Exception as e:
        raise ValueError(f"Falha ao criar thread: {e}")

    logger.info(f"Thread criada: {thread.name} ({thread.id})")

    return CreateThreadOutput(
        thread_id=str(thread.id),
        thread_name=thread.name,
        parent_channel_id=str(channel.id),
        message_id=str(message.id),
    )


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
            "channel_id": {
                "type": "string",
                "description": "Channel ID where the message exists",
            },
            "message_id": {
                "type": "string",
                "description": "Message ID to create thread from",
            },
            "name": {
                "type": "string",
                "description": "Name for the new thread",
            },
            "auto_archive_duration": {
                "type": "number",
                "enum": [60, 1440, 4320, 10080],
                "default": 1440,
                "description": (
                    "Auto-archive duration in minutes: "
                    "60=1h, 1440=24h, 4320=3d, 10080=7d"
                ),
            },
        },
        "required": ["channel_id", "message_id", "name"],
    },
}
