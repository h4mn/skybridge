# -*- coding: utf-8 -*-
"""
Tool: send_embed

Envia embed rico para canal Discord.

DOC: DDD Migration - Presentation Layer
"""

from __future__ import annotations

import logging
from typing import Any

from ...application.services.discord_service import DiscordService, EmbedField

logger = logging.getLogger(__name__)


async def handle_send_embed(
    discord_service: DiscordService,
    args: dict[str, Any]
) -> dict[str, Any]:
    """
    Handler para tool send_embed.

    Args:
        discord_service: Instância do DiscordService
        args: Argumentos do tool

    Returns:
        Dict com message_id, status
    """
    chat_id = args.get("chat_id")
    title = args.get("title")
    description = args.get("description")
    color = args.get("color", 3447003)  # Azul padrão
    fields = args.get("fields", [])
    footer = args.get("footer")

    if not chat_id or not title:
        return {
            "status": "error",
            "error": "chat_id e title são obrigatórios"
        }

    # Converte campos para EmbedField
    embed_fields = None
    if fields:
        embed_fields = [
            EmbedField(
                name=f["name"],
                value=f["value"],
                inline=f.get("inline", False),
            )
            for f in fields
        ]

    # Envia embed via DiscordService
    try:
        message = await discord_service.send_embed(
            channel_id=chat_id,
            title=title,
            description=description,
            color=color,
            fields=embed_fields,
            footer=footer,
        )

        return {
            "message_id": str(message.id) if message else None,
            "status": "success"
        }
    except Exception as e:
        logger.error(f"Erro ao enviar embed: {e}")
        return {
            "status": "error",
            "error": str(e)
        }


# Tool definition para registro no MCP
TOOL_DEFINITION = {
    "name": "send_embed",
    "description": (
        "Send rich embed to Discord channel. "
        "Use for structured messages with fields, colors, and footers."
    ),
    "inputSchema": {
        "type": "object",
        "properties": {
            "chat_id": {"type": "string", "description": "Channel ID"},
            "title": {"type": "string", "description": "Embed title"},
            "description": {"type": "string", "description": "Embed description"},
            "color": {"type": "integer", "description": "Embed color (decimal)"},
            "fields": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "name": {"type": "string"},
                        "value": {"type": "string"},
                        "inline": {"type": "boolean"},
                    },
                },
                "description": "Embed fields",
            },
            "footer": {"type": "string", "description": "Footer text"},
        },
        "required": ["chat_id", "title"],
    },
}
