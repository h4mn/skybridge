"""
Tool: react

Adiciona emoji reaction a uma mensagem Discord.
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from ..models import ReactInput, ReactOutput
from ..client import fetch_allowed_channel

if TYPE_CHECKING:
    from discord import Client

logger = logging.getLogger(__name__)


async def handle_react(client: "Client", args: dict) -> ReactOutput:
    """
    Handler para tool react.

    Args:
        client: Cliente Discord conectado
        args: Argumentos (chat_id, message_id, emoji)

    Returns:
        ReactOutput com success=True

    Raises:
        ValueError: Se canal/mensagem não encontrado ou emoji inválido
    """
    # Valida entrada
    input_data = ReactInput.model_validate(args)

    # Busca canal autorizado
    channel = await fetch_allowed_channel(client, input_data.chat_id)

    # Busca mensagem
    message = await channel.fetch_message(int(input_data.message_id))
    if message is None:
        raise ValueError(f"Mensagem {input_data.message_id} não encontrada")

    # Adiciona reaction
    try:
        await message.add_reaction(input_data.emoji)
    except Exception as e:
        raise ValueError(f"Falha ao adicionar reaction: {e}")

    return ReactOutput(success=True)


# Tool definition para registro no MCP
TOOL_DEFINITION = {
    "name": "react",
    "description": (
        "Add an emoji reaction to a Discord message. "
        "Unicode emoji work directly; custom emoji need the <:name:id> form."
    ),
    "inputSchema": {
        "type": "object",
        "properties": {
            "chat_id": {"type": "string", "description": "Channel ID"},
            "message_id": {"type": "string", "description": "Message ID"},
            "emoji": {
                "type": "string",
                "description": "Emoji to react with (Unicode or <:name:id> for custom)",
            },
        },
        "required": ["chat_id", "message_id", "emoji"],
    },
}
