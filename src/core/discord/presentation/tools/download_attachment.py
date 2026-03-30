# -*- coding: utf-8 -*-
"""
Tool: download_attachment

Baixa anexos de mensagem Discord para inbox local.

DOC: DDD Migration - Presentation Layer
"""

from __future__ import annotations

import logging
import re
import time
from pathlib import Path
from typing import Any

from ...application.services.discord_service import DiscordService

logger = logging.getLogger(__name__)

# Constantes
MAX_ATTACHMENT_BYTES = 25 * 1024 * 1024  # 25MB
STATE_DIR = Path.home() / ".claude" / "channels" / "discord"
INBOX_DIR = STATE_DIR / "inbox"


def safe_attachment_name(attachment: Any) -> str:
    """Sanitiza nome de anexo."""
    name = attachment.filename or str(attachment.id)
    return re.sub(r"[\[\]\r\n;]", "_", name)


async def handle_download_attachment(
    discord_service: DiscordService,
    args: dict[str, Any]
) -> dict[str, Any]:
    """
    Handler para tool download_attachment.

    Args:
        discord_service: Instância do DiscordService
        args: Argumentos do tool

    Returns:
        Dict com files, count, status
    """
    chat_id = args.get("chat_id")
    message_id = args.get("message_id")

    if not chat_id or not message_id:
        return {
            "status": "error",
            "error": "chat_id e message_id são obrigatórios"
        }

    try:
        channel = await discord_service._client.fetch_channel(int(chat_id))
        message = await channel.fetch_message(int(message_id))

        if not message.attachments:
            return {
                "files": [],
                "count": 0,
                "status": "success"
            }

        # Garante diretório inbox existe
        INBOX_DIR.mkdir(parents=True, exist_ok=True)

        downloaded = []
        for att in message.attachments:
            if att.size > MAX_ATTACHMENT_BYTES:
                mb = att.size / (1024 * 1024)
                logger.warning(f"Anexo muito grande: {att.filename} ({mb:.1f}MB)")
                continue

            try:
                # Determina extensão
                name = att.filename or str(att.id)
                if "." in name:
                    ext = name.rsplit(".", 1)[-1]
                    ext = re.sub(r"[^a-zA-Z0-9]", "", ext) or "bin"
                else:
                    ext = "bin"

                # Nome único
                filename = f"{int(time.time() * 1000)}-{att.id}.{ext}"
                path = INBOX_DIR / filename

                # Baixa
                await att.save(str(path))

                downloaded.append({
                    "path": str(path),
                    "name": safe_attachment_name(att),
                    "content_type": att.content_type,
                    "size_kb": att.size // 1024,
                })

                logger.info(f"Anexo baixado: {att.filename} -> {path}")
            except Exception as e:
                logger.error(f"Falha ao baixar {att.filename}: {e}")

        return {
            "files": downloaded,
            "count": len(downloaded),
            "status": "success"
        }
    except Exception as e:
        logger.error(f"Erro ao baixar anexos: {e}")
        return {
            "status": "error",
            "error": str(e)
        }


# Tool definition para registro no MCP
TOOL_DEFINITION = {
    "name": "download_attachment",
    "description": (
        "Download attachments from Discord message to local inbox. "
        "Use after fetch_messages shows attachments (+Natt). Returns file paths."
    ),
    "inputSchema": {
        "type": "object",
        "properties": {
            "chat_id": {"type": "string", "description": "Channel ID"},
            "message_id": {"type": "string", "description": "Message ID with attachments"},
        },
        "required": ["chat_id", "message_id"],
    },
}
