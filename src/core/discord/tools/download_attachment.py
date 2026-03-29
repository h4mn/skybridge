"""
Tool: download_attachment

Baixa anexos de uma mensagem Discord para o diretório inbox.
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from ..models import (
    DownloadAttachmentInput,
    DownloadAttachmentOutput,
    DownloadedFile,
)
from ..utils import safe_attachment_name, download_attachment, MAX_ATTACHMENT_BYTES

if TYPE_CHECKING:
    from discord import Client

logger = logging.getLogger(__name__)


async def handle_download_attachment(
    client: "Client", args: dict
) -> DownloadAttachmentOutput:
    """
    Handler para tool download_attachment.

    Args:
        client: Cliente Discord conectado
        args: Argumentos (chat_id, message_id)

    Returns:
        DownloadAttachmentOutput com lista de arquivos baixados

    Raises:
        ValueError: Se canal/mensagem não autorizado ou sem anexos
    """
    # Valida entrada
    input_data = DownloadAttachmentInput.model_validate(args)

    # Busca canal autorizado
    from ..client import fetch_allowed_channel

    channel = await fetch_allowed_channel(client, input_data.chat_id)

    # Busca mensagem
    message = await channel.fetch_message(int(input_data.message_id))
    if message is None:
        raise ValueError(f"Mensagem {input_data.message_id} não encontrada")

    # Verifica anexos
    if not message.attachments:
        return DownloadAttachmentOutput(files=[], count=0)

    # Baixa cada anexo
    downloaded: list[DownloadedFile] = []
    for att in message.attachments:
        # Verifica tamanho
        if att.size > MAX_ATTACHMENT_BYTES:
            mb = att.size / (1024 * 1024)
            logger.warning(f"Anexo muito grande ignorado: {att.filename} ({mb:.1f}MB)")
            continue

        try:
            path = await download_attachment(att)
            downloaded.append(
                DownloadedFile(
                    path=path,
                    name=safe_attachment_name(att),
                    content_type=att.content_type,
                    size_kb=att.size // 1024,
                )
            )
        except Exception as e:
            logger.error(f"Falha ao baixar anexo {att.filename}: {e}")

    return DownloadAttachmentOutput(
        files=downloaded,
        count=len(downloaded),
    )


# Tool definition para registro no MCP
TOOL_DEFINITION = {
    "name": "download_attachment",
    "description": (
        "Download attachments from a specific Discord message to the local inbox. "
        "Use after fetch_messages shows a message has attachments (marked with +Natt). "
        "Returns file paths ready to Read."
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
