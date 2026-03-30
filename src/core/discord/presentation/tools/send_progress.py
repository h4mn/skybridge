# -*- coding: utf-8 -*-
"""
Tool: send_progress

Envia indicador de progresso para canal Discord.
Mostra barra de progresso visual com status.

DOC: DDD Migration - Presentation Layer
"""

from __future__ import annotations

import logging
from typing import Any

from ...application.services.discord_service import DiscordService

logger = logging.getLogger(__name__)


async def handle_send_progress(
    discord_service: DiscordService,
    args: dict[str, Any]
) -> dict[str, Any]:
    """
    Handler para tool send_progress.

    Args:
        discord_service: Instância do DiscordService
        args: Argumentos do tool

    Returns:
        Dict com message_id, status
    """
    chat_id = args.get("chat_id")
    title = args.get("title", "Processando")
    current = args.get("current", 0)
    total = args.get("total", 100)
    status = args.get("status")
    tracking_id = args.get("tracking_id")  # ID para rastrear e atualizar mesma mensagem

    if not chat_id:
        return {
            "status": "error",
            "error": "chat_id é obrigatório"
        }

    # Valida números
    try:
        current = int(current)
        total = int(total)
    except (ValueError, TypeError):
        return {
            "status": "error",
            "error": "current e total devem ser números"
        }

    # Envia progress indicator via DiscordService
    try:
        message = await discord_service.send_progress(
            channel_id=chat_id,
            title=title,
            current=current,
            total=total,
            status=status,
            tracking_id=tracking_id,
        )

        return {
            "message_id": str(message.id) if message else None,
            "percentage": int((current / total) * 100) if total > 0 else 0,
            "status": "success"
        }
    except Exception as e:
        logger.error(f"Erro ao enviar progresso: {e}")
        return {
            "status": "error",
            "error": str(e)
        }


# Tool definition para registro no MCP
TOOL_DEFINITION = {
    "name": "send_progress",
    "description": (
        "Send visual progress indicator to Discord channel. "
        "Shows progress bar with percentage and status message. "
        "Use tracking_id to update the same message instead of sending multiple."
    ),
    "inputSchema": {
        "type": "object",
        "properties": {
            "chat_id": {"type": "string", "description": "Channel ID"},
            "title": {"type": "string", "description": "Progress title"},
            "current": {"type": "integer", "description": "Current progress value"},
            "total": {"type": "integer", "description": "Total value (100%)"},
            "status": {"type": "string", "description": "Status message (optional)"},
            "tracking_id": {
                "type": "string",
                "description": "Unique ID to track and update same message. First call creates, subsequent calls update."
            },
        },
        "required": ["chat_id"],
    },
}
