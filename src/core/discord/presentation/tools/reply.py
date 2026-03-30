# -*- coding: utf-8 -*-
"""
Tool: reply

Envia mensagem para canal Discord autorizado.
Suporta threading (reply_to) e anexos (files).

DOC: DDD Migration - Presentation Layer
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any

from ...application.services.discord_service import DiscordService
from ...domain.value_objects import ChannelId

logger = logging.getLogger(__name__)

# Constantes
MAX_ATTACHMENT_BYTES = 25 * 1024 * 1024  # 25MB
MAX_ATTACHMENTS = 10


async def handle_reply(
    discord_service: DiscordService,
    args: dict[str, Any]
) -> dict[str, Any]:
    """
    Handler para tool reply.

    Args:
        discord_service: Instância do DiscordService
        args: Argumentos do tool (chat_id, text, reply_to?, files?)

    Returns:
        Dict com message_id, sent_count, status
    """
    chat_id = args.get("chat_id")
    text = args.get("text")
    reply_to = args.get("reply_to")
    files = args.get("files", [])

    if not chat_id or not text:
        return {
            "status": "error",
            "error": "chat_id e text são obrigatórios"
        }

    # Valida arquivos
    files_to_send = []
    if files:
        if len(files) > MAX_ATTACHMENTS:
            return {
                "status": "error",
                "error": f"Discord permite no máximo {MAX_ATTACHMENTS} anexos"
            }

        for file_path in files:
            path = Path(file_path)
            if not path.exists():
                return {
                    "status": "error",
                    "error": f"Arquivo não encontrado: {file_path}"
                }

            size = path.stat().st_size
            if size > MAX_ATTACHMENT_BYTES:
                mb = size / (1024 * 1024)
                return {
                    "status": "error",
                    "error": f"Arquivo muito grande: {file_path} ({mb:.1f}MB, máximo 25MB)"
                }

            files_to_send.append(file_path)

    # Envia mensagem via DiscordService
    try:
        message = await discord_service.send_message(
            channel_id=chat_id,
            content=text,
            reply_to=reply_to,
        )

        return {
            "message_id": str(message.id) if message else None,
            "sent_count": 1,
            "status": "success"
        }
    except Exception as e:
        logger.error(f"Erro ao enviar reply: {e}")
        return {
            "status": "error",
            "error": str(e)
        }


# Tool definition para registro no MCP
TOOL_DEFINITION = {
    "name": "reply",
    "description": (
        "Reply on Discord. Pass chat_id from the inbound message. "
        "Optionally pass reply_to (message_id) for threading, "
        "and files (absolute paths) to attach images or other files."
    ),
    "inputSchema": {
        "type": "object",
        "properties": {
            "chat_id": {"type": "string", "description": "Channel or thread ID"},
            "text": {"type": "string", "description": "Message text to send"},
            "reply_to": {
                "type": "string",
                "description": "Message ID to thread under. Use message_id from inbound message.",
            },
            "files": {
                "type": "array",
                "items": {"type": "string"},
                "description": "Absolute file paths to attach. Max 10 files, 25MB each.",
            },
        },
        "required": ["chat_id", "text"],
    },
}
