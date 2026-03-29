"""
Tool: edit_message

Edita mensagem previamente enviada pelo bot.
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from ..models import EditMessageInput, EditMessageOutput
from ..client import fetch_allowed_channel

if TYPE_CHECKING:
    from discord import Client

logger = logging.getLogger(__name__)


async def handle_edit_message(client: "Client", args: dict) -> EditMessageOutput:
    """
    Handler para tool edit_message.

    Args:
        client: Cliente Discord conectado
        args: Argumentos (chat_id, message_id, text)

    Returns:
        EditMessageOutput com message_id

    Raises:
        ValueError: Se canal/mensagem não autorizado ou não é do bot
    """
    # Valida entrada
    input_data = EditMessageInput.model_validate(args)

    # Busca canal autorizado
    channel = await fetch_allowed_channel(client, input_data.chat_id)

    # Busca mensagem
    message = await channel.fetch_message(int(input_data.message_id))
    if message is None:
        raise ValueError(f"Mensagem {input_data.message_id} não encontrada")

    # Verifica se é mensagem do bot
    if client.user and message.author.id != client.user.id:
        raise ValueError("Só é possível editar mensagens do próprio bot")

    # Edita
    try:
        edited = await message.edit(content=input_data.text)
        return EditMessageOutput(message_id=str(edited.id), edited=True)
    except Exception as e:
        raise ValueError(f"Falha ao editar mensagem: {e}")


# Tool definition para registro no MCP
TOOL_DEFINITION = {
    "name": "edit_message",
    "description": (
        "Edit a message the bot previously sent. "
        "Useful for interim progress updates. "
        "Edits don't trigger push notifications — send a new reply "
        "when a long task completes so the user's device pings."
    ),
    "inputSchema": {
        "type": "object",
        "properties": {
            "chat_id": {"type": "string", "description": "Channel ID"},
            "message_id": {"type": "string", "description": "Message ID to edit"},
            "text": {"type": "string", "description": "New message text"},
        },
        "required": ["chat_id", "message_id", "text"],
    },
}
