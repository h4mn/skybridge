"""
Utilitários para o Discord MCP Server.

Funções auxiliares para:
- Chunking de mensagens longas
- Sanitização de nomes de arquivos
- Validação de paths
- Download de anexos
"""

from __future__ import annotations

import os
import re
import stat
from pathlib import Path
from typing import TYPE_CHECKING

import httpx

if TYPE_CHECKING:
    from discord import Attachment

# Constantes
MAX_CHUNK_LIMIT = 2000  # Discord hard limit
MAX_ATTACHMENT_BYTES = 25 * 1024 * 1024  # 25MB

# Diretórios
STATE_DIR = Path(
    os.environ.get("DISCORD_STATE_DIR", Path.home() / ".claude" / "channels" / "discord")
)
INBOX_DIR = STATE_DIR / "inbox"


def chunk(
    text: str, limit: int = MAX_CHUNK_LIMIT, mode: str = "length"
) -> list[str]:
    """
    Divide texto longo em chunks para envio ao Discord.

    Args:
        text: Texto a dividir
        limit: Máximo de caracteres por chunk
        mode: 'length' (hard cut) ou 'newline' (prefere quebras de parágrafo)

    Returns:
        Lista de chunks
    """
    if len(text) <= limit:
        return [text]

    chunks: list[str] = []
    rest = text

    while len(rest) > limit:
        cut = limit

        if mode == "newline":
            # Prefere último parágrafo (\n\n), depois linha (\n), depois espaço
            para = rest.rfind("\n\n", 0, limit)
            line = rest.rfind("\n", 0, limit)
            space = rest.rfind(" ", 0, limit)

            if para > limit // 2:
                cut = para
            elif line > limit // 2:
                cut = line
            elif space > 0:
                cut = space

        chunks.append(rest[:cut])
        rest = rest[cut:].lstrip("\n")

    if rest:
        chunks.append(rest)

    return chunks


def safe_attachment_name(attachment: "Attachment") -> str:
    """
    Sanitiza nome de anexo para prevenir injection.

    Args:
        attachment: Attachment do Discord

    Returns:
        Nome sanitizado
    """
    name = attachment.filename or str(attachment.id)
    # Remove caracteres perigosos
    return re.sub(r"[\[\]\r\n;]", "_", name)


def assert_sendable(file_path: str) -> None:
    """
    Valida que arquivo pode ser enviado.

    Impede envio de arquivos de estado do servidor (access.json, .env, etc.)

    Args:
        file_path: Caminho absoluto do arquivo

    Raises:
        ValueError: Se arquivo não pode ser enviado
    """
    path = Path(file_path).resolve()

    # Verifica se está tentando enviar arquivos de estado
    try:
        state_resolved = STATE_DIR.resolve()
        inbox_resolved = INBOX_DIR.resolve()
    except Exception:
        return  # Se não conseguir resolver paths, deixa passar

    # Permite inbox, bloqueia resto do state_dir
    path_str = str(path)
    state_str = str(state_resolved)
    inbox_str = str(inbox_resolved)

    if path_str.startswith(state_str) and not path_str.startswith(inbox_str):
        raise ValueError(f"Recusando enviar arquivo de estado: {file_path}")


def validate_file_size(file_path: str) -> None:
    """
    Valida tamanho do arquivo.

    Args:
        file_path: Caminho do arquivo

    Raises:
        ValueError: Se arquivo excede 25MB
    """
    path = Path(file_path)
    if not path.exists():
        raise ValueError(f"Arquivo não encontrado: {file_path}")

    size = path.stat().st_size
    if size > MAX_ATTACHMENT_BYTES:
        mb = size / (1024 * 1024)
        raise ValueError(
            f"Arquivo muito grande: {file_path} ({mb:.1f}MB, máximo 25MB)"
        )


async def download_attachment(attachment: "Attachment") -> str:
    """
    Baixa anexo para diretório inbox.

    Args:
        attachment: Attachment do Discord

    Returns:
        Caminho do arquivo baixado

    Raises:
        ValueError: Se anexo muito grande
    """
    if attachment.size > MAX_ATTACHMENT_BYTES:
        mb = attachment.size / (1024 * 1024)
        raise ValueError(f"Anexo muito grande: {mb:.1f}MB, máximo 25MB")

    # Garante diretório inbox existe
    INBOX_DIR.mkdir(parents=True, exist_ok=True)

    # Determina extensão
    name = attachment.filename or str(attachment.id)
    if "." in name:
        ext = name.rsplit(".", 1)[-1]
        ext = re.sub(r"[^a-zA-Z0-9]", "", ext) or "bin"
    else:
        ext = "bin"

    # Nome único com timestamp
    import time

    filename = f"{int(time.time() * 1000)}-{attachment.id}.{ext}"
    path = INBOX_DIR / filename

    # Download
    async with httpx.AsyncClient() as client:
        response = await client.get(attachment.url)
        response.raise_for_status()
        path.write_bytes(response.content)

    return str(path)


def format_message_for_display(
    author: str, content: str, timestamp: str, is_bot: bool = False
) -> str:
    """
    Formata mensagem para exibição no output de fetch_messages.

    Args:
        author: Nome do autor
        content: Conteúdo da mensagem
        timestamp: ISO timestamp
        is_bot: Se é mensagem do bot

    Returns:
        String formatada
    """
    who = "me" if is_bot else author
    # Sanitiza quebras de linha para não quebrar formato
    text = content.replace("\r\n", " ⏎ ").replace("\n", " ⏎ ")
    return f"[{timestamp}] {who}: {text}"


# =============================================================================
# Track de mensagens enviadas recentemente
# =============================================================================

from collections import OrderedDict

_recent_sent_ids: "OrderedDict[str, None]" = OrderedDict()
_RECENT_SENT_CAP = 200


def note_sent(message_id: str) -> None:
    """Registra ID de mensagem enviada recentemente."""
    # Remove se já existe (para mover para o final)
    if message_id in _recent_sent_ids:
        del _recent_sent_ids[message_id]

    _recent_sent_ids[message_id] = None

    # Remove mais antigo se exceder cap
    while len(_recent_sent_ids) > _RECENT_SENT_CAP:
        _recent_sent_ids.popitem(last=False)


def is_recently_sent(message_id: str) -> bool:
    """Verifica se mensagem foi enviada recentemente por nós."""
    return message_id in _recent_sent_ids
