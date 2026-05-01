# -*- coding: utf-8 -*-
"""
Tool: send_menu

Envia menu suspenso (select) para canal Discord.
Usuário pode selecionar uma opção entre várias.

DOC: DDD Migration - Presentation Layer
"""

from __future__ import annotations

import logging
from typing import Any, TYPE_CHECKING

# Lazy imports para evitar colisao de namespace com tests/unit/core/discord/
# durante coleta do pytest. discord.py e importado apenas quando necessario.
if TYPE_CHECKING:
    import discord
    from discord.ui import View, Select

from ...application.services.discord_service import DiscordService

logger = logging.getLogger(__name__)


async def handle_send_menu(
    discord_service: DiscordService,
    args: dict[str, Any]
) -> dict[str, Any]:
    """
    Handler para tool send_menu.

    Args:
        discord_service: Instância do DiscordService
        args: Argumentos do tool

    Returns:
        Dict com message_id, status
    """
    chat_id = args.get("chat_id")
    placeholder = args.get("placeholder", "Selecione uma opção...")
    options = args.get("options", [])

    if not chat_id:
        return {
            "status": "error",
            "error": "chat_id é obrigatório"
        }

    if not options:
        return {
            "status": "error",
            "error": "Ao menos uma opção é necessária"
        }

    # Valida opções
    for opt in options:
        if "label" not in opt or "value" not in opt:
            return {
                "status": "error",
                "error": "Cada opção deve ter label e value"
            }

    try:
        # Envia menu usando o DiscordService
        message = await discord_service.send_menu(
            channel_id=chat_id,
            placeholder=placeholder,
            options=options
        )

        return {
            "message_id": str(message.id) if message else None,
            "status": "success"
        }
    except Exception as e:
        logger.error(f"Erro ao enviar menu: {e}")
        import traceback
        traceback.print_exc()
        return {
            "status": "error",
            "error": str(e)
        }


# Tool definition para registro no MCP
TOOL_DEFINITION = {
    "name": "send_menu",
    "description": (
        "Send dropdown menu (select) to Discord channel. "
        "User can select one option. Menu persists (timeout=None)."
    ),
    "inputSchema": {
        "type": "object",
        "properties": {
            "chat_id": {"type": "string", "description": "Channel ID"},
            "placeholder": {"type": "string", "description": "Placeholder text"},
            "options": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "label": {"type": "string", "description": "Display label"},
                        "value": {"type": "string", "description": "Internal value"},
                        "description": {"type": "string", "description": "Option description"},
                        "emoji": {"type": "string", "description": "Emoji (optional)"},
                    },
                    "required": ["label", "value"],
                },
                "description": "Menu options",
            },
        },
        "required": ["chat_id", "options"],
    },
}
