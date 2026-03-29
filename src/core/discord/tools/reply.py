"""
Tool: reply

Envia mensagem para canal Discord autorizado.
Suporta threading (reply_to) e anexos (files).
"""

from __future__ import annotations

import logging
import os
from pathlib import Path
from typing import TYPE_CHECKING

from ..models import ReplyInput, ReplyOutput
from ..utils import chunk, assert_sendable, note_sent
from ..client import fetch_allowed_channel
from ..access import load_access

if TYPE_CHECKING:
    from discord import Client, TextChannel, DMChannel, Thread

logger = logging.getLogger(__name__)

# Constantes
MAX_ATTACHMENT_BYTES = 25 * 1024 * 1024  # 25MB
MAX_ATTACHMENTS = 10


async def handle_reply(client: "Client", args: dict) -> ReplyOutput:
    """
    Handler para tool reply.

    Args:
        client: Cliente Discord conectado
        args: Argumentos do tool (chat_id, text, reply_to?, files?)

    Returns:
        ReplyOutput com message_id(s)

    Raises:
        ValueError: Se canal não autorizado ou argumentos inválidos
    """
    # Valida entrada
    input_data = ReplyInput.model_validate(args)

    # Busca canal autorizado
    channel = await fetch_allowed_channel(client, input_data.chat_id)

    if not hasattr(channel, "send"):
        raise ValueError("Canal não suporta envio de mensagens")

    # Valida arquivos
    files_to_send = []
    if input_data.files:
        if len(input_data.files) > MAX_ATTACHMENTS:
            raise ValueError("Discord permite no máximo 10 anexos por mensagem")

        for file_path in input_data.files:
            assert_sendable(file_path)

            path = Path(file_path)
            if not path.exists():
                raise ValueError(f"Arquivo não encontrado: {file_path}")

            size = path.stat().st_size
            if size > MAX_ATTACHMENT_BYTES:
                mb = size / (1024 * 1024)
                raise ValueError(f"Arquivo muito grande: {file_path} ({mb:.1f}MB, máximo 25MB)")

            files_to_send.append(file_path)

    # Carrega configuração de chunking
    access = load_access()
    chunk_limit = min(access.text_chunk_limit or 2000, 2000)
    chunk_mode = access.chunk_mode or "length"
    reply_mode = access.reply_to_mode or "first"

    # Divide em chunks
    chunks_list = chunk(input_data.text, chunk_limit, chunk_mode)
    sent_ids: list[str] = []

    # Envia chunks
    for i, chunk_text in enumerate(chunks_list):
        # Determina se deve usar reply_to
        should_reply = (
            input_data.reply_to is not None
            and reply_mode != "off"
            and (reply_mode == "all" or i == 0)
        )

        # Prepara kwargs
        kwargs = {"content": chunk_text}

        # Anexos apenas no primeiro chunk
        if i == 0 and files_to_send:
            kwargs["files"] = files_to_send

        # Reply/thread
        if should_reply:
            kwargs["reference"] = {"message_id": int(input_data.reply_to)}
            # failIfNotExists=False para não falhar se mensagem foi deletada

        try:
            sent = await channel.send(**kwargs)
            note_sent(str(sent.id))
            sent_ids.append(str(sent.id))
        except Exception as e:
            msg = str(e)
            raise ValueError(
                f"reply falhou após {len(sent_ids)} de {len(chunks_list)} chunk(s): {msg}"
            )

    # Retorna resultado
    if len(sent_ids) == 1:
        return ReplyOutput(message_id=sent_ids[0], sent_count=1)
    else:
        return ReplyOutput(
            message_id=sent_ids[0],  # Primeiro ID como referência
            sent_count=len(sent_ids),
        )


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
