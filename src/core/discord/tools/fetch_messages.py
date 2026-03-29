"""
Tool: fetch_messages

Busca histórico de mensagens de um canal Discord.
"""

from __future__ import annotations

import logging
from datetime import datetime
from typing import TYPE_CHECKING

from ..models import (
    FetchMessagesInput,
    FetchMessagesOutput,
    FetchedMessage,
    MessageAttachment,
)
from ..utils import safe_attachment_name
from ..client import fetch_allowed_channel

if TYPE_CHECKING:
    from discord import Client, Message

logger = logging.getLogger(__name__)


async def handle_fetch_messages(client: "Client", args: dict) -> FetchMessagesOutput:
    """
    Handler para tool fetch_messages.

    Args:
        client: Cliente Discord conectado
        args: Argumentos (channel, limit?)

    Returns:
        FetchMessagesOutput com lista de mensagens

    Raises:
        ValueError: Se canal não autorizado
    """
    # Valida entrada
    input_data = FetchMessagesInput.model_validate(args)

    # Busca canal autorizado
    channel = await fetch_allowed_channel(client, input_data.channel)

    # Busca mensagens
    limit = min(input_data.limit, 100)  # Discord cap
    messages = [msg async for msg in channel.history(limit=limit)]

    # Meu ID para identificar minhas mensagens
    my_id = str(client.user.id) if client.user else None

    # Formata output (mais antigas primeiro)
    formatted: list[FetchedMessage] = []
    for msg in reversed(messages):
        # Sanitiza conteúdo
        content = msg.content or ""
        if msg.attachments:
            content = content or "(attachment)"

        # Anexos
        attachments_list: list[MessageAttachment] = []
        if msg.attachments:
            for att in msg.attachments:
                attachments_list.append(
                    MessageAttachment(
                        name=safe_attachment_name(att),
                        content_type=att.content_type,
                        size_kb=att.size // 1024,
                    )
                )

        formatted.append(
            FetchedMessage(
                id=str(msg.id),
                author=msg.author.name,
                content=content,
                timestamp=msg.created_at.isoformat(),
                attachments=attachments_list,
                is_bot=(str(msg.author.id) == my_id),
            )
        )

    return FetchMessagesOutput(messages=formatted, channel_id=input_data.channel)


# Tool definition para registro no MCP
TOOL_DEFINITION = {
    "name": "fetch_messages",
    "description": (
        "Fetch recent messages from a Discord channel. "
        "Returns oldest-first with message IDs. "
        "Discord's search API isn't exposed to bots, so this is the only way to look back."
    ),
    "inputSchema": {
        "type": "object",
        "properties": {
            "channel": {"type": "string", "description": "Channel ID"},
            "limit": {
                "type": "number",
                "description": "Max messages (default 20, Discord caps at 100)",
            },
        },
        "required": ["channel"],
    },
}
