# -*- coding: utf-8 -*-
"""
Tool: send_buttons

Envia embed com botões interativos para canal Discord.

DOC: DDD Migration - Presentation Layer
"""

from __future__ import annotations

import logging
from typing import Any

from ...application.services.discord_service import DiscordService, ButtonConfig

logger = logging.getLogger(__name__)


async def handle_send_buttons(
    discord_service: DiscordService,
    args: dict[str, Any]
) -> dict[str, Any]:
    """
    Handler para tool send_buttons.

    Args:
        discord_service: Instância do DiscordService
        args: Argumentos do tool

    Returns:
        Dict com message_id, status
    """
    chat_id = args.get("chat_id")
    title = args.get("title")
    description = args.get("description")
    buttons = args.get("buttons", [])

    if not chat_id or not title:
        return {
            "status": "error",
            "error": "chat_id e title são obrigatórios"
        }

    if not buttons:
        return {
            "status": "error",
            "error": "Ao menos um botão é necessário"
        }

    # Converte botões para ButtonConfig
    button_configs = [
        ButtonConfig(
            label=b["label"],
            style=b.get("style", "primary"),
            custom_id=b["id"],
            disabled=b.get("disabled", False),
        )
        for b in buttons
    ]

    # Envia via DiscordService
    try:
        message = await discord_service.send_buttons(
            channel_id=chat_id,
            title=title,
            description=description,
            buttons=button_configs,
        )

        return {
            "message_id": str(message.id) if message else None,
            "status": "success"
        }
    except Exception as e:
        logger.error(f"Erro ao enviar botões: {e}")
        return {
            "status": "error",
            "error": str(e)
        }


# Tool definition para registro no MCP
TOOL_DEFINITION = {
    "name": "send_buttons",
    "description": (
        "Send interactive buttons to Discord channel. "
        "Buttons use discord.ui.View with timeout=None (never expire)."
    ),
    "inputSchema": {
        "type": "object",
        "properties": {
            "chat_id": {"type": "string", "description": "Channel ID"},
            "title": {"type": "string", "description": "Embed title"},
            "description": {"type": "string", "description": "Embed description"},
            "buttons": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "id": {"type": "string", "description": "Button custom_id"},
                        "label": {"type": "string", "description": "Button label"},
                        "style": {"type": "string", "enum": ["primary", "success", "danger", "secondary"]},
                        "disabled": {"type": "boolean", "description": "Disable button"},
                    },
                    "required": ["id", "label"],
                },
                "description": "List of buttons",
            },
        },
        "required": ["chat_id", "title", "buttons"],
    },
}
