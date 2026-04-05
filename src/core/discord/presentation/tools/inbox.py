# -*- coding: utf-8 -*-
"""
Tool: inbox

Captura ideias via Discord slash command /inbox e cria issue no Linear.

DOC: Inbox Specification - inbox-discord-slash
"""

from __future__ import annotations

import logging
from datetime import datetime, timedelta
from typing import Any

from ...application.services.discord_service import DiscordService

logger = logging.getLogger(__name__)

# Configurações
INBOX_PROJECT_ID = "02be2007-fd29-4f1c-8dc8-6b1d854a4a70"  # Inbox - Backlog de Ideias
MAX_TITLE_LENGTH = 200
EXPIRES_DAYS = 60

# Mapeamento de canais Discord → domínios
CHANNEL_DOMAIN_MAP = {
    # Paper Trading
    "paper-trading": "paper",
    "paper-dev": "paper",
    "paper-announcements": "paper",

    # Discord
    "discord-dev": "discord",
    "discord-bots": "discord",
    "discord-mcp": "discord",

    # AutoKarpa
    "autokarpa": "autokarpa",
    "autokarpa-dev": "autokarpa",
}

# Labels IDs (obtidos via criação)
LABELS = {
    "fonte:discord": "e75a8d97-1064-464b-92a7-f4ad371f191d",
    "domínio:paper": "88e309d3-694a-469c-bed6-b9443cb3694e",
    "domínio:discord": "d73805a8-6b4b-4c54-8ef8-daec148fbb1f",
    "domínio:autokarpa": "b729ecd3-28d0-4320-9084-2a0264836877",
    "domínio:geral": "01fb356c-a45f-4cb1-9a01-de5f9cbc1da5",
    "ação:implementar": "6b8cdf2d-177f-4d86-8d4d-d66f8824c7ec",
}


def _calculate_expires_date() -> str:
    """Calcula data de expires (hoje + 60 dias)."""
    expires = datetime.now() + timedelta(days=EXPIRES_DAYS)
    return expires.strftime("%Y-%m-%d")


def _detect_domain_from_channel(channel_name: str | None) -> str:
    """Detecta domínio baseado no nome do canal."""
    if not channel_name:
        return LABELS["domínio:geral"]

    channel_lower = channel_name.lower()
    for pattern, domain_label in CHANNEL_DOMAIN_MAP.items():
        if pattern in channel_lower:
            return LABELS[f"domínio:{domain_label}"]

    return LABELS["domínio:geral"]


def _truncate_title(title: str) -> tuple[str, bool]:
    """
    Trunca título se necessário.

    Returns:
        (título_truncado, foi_truncado)
    """
    if len(title) > MAX_TITLE_LENGTH:
        return title[:MAX_TITLE_LENGTH], True
    return title, False


def _build_description(
    title: str,
    channel_name: str | None,
    was_truncated: bool,
    full_title: str | None = None,
) -> str:
    """Constroi descrição estruturada da issue."""
    parts = []

    # Fonte
    if channel_name:
        parts.append(f"**Fonte:** Discord #{channel_name}")
    else:
        parts.append("**Fonte:** Discord")

    # Preservar título completo se foi truncado
    if was_truncated and full_title:
        parts.append(f"\n**Título completo:** {full_title}")

    parts.append("\n---")
    parts.append("\n**Ação sugerida:** Implementar | Pesquisar | Arquivar | Descartar")
    parts.append(f"\n**Expires:** {_calculate_expires_date()} ({EXPIRES_DAYS} dias)")

    return "\n".join(parts)


# Nota: A criação da issue será feita via Linear MCP chamado pelo contexto
# Esta função retorna os dados estruturados para serem usados pelo MCP
async def handle_inbox_add(
    discord_service: DiscordService,
    args: dict[str, Any]
) -> dict[str, Any]:
    """
    Handler para tool inbox_add.

    Args:
        discord_service: Instância do DiscordService
        args: Argumentos do tool (title, channel_id)

    Returns:
        Dict com dados estruturados para criação da issue Linear
    """
    title = args.get("title", "").strip()
    channel_id = args.get("channel_id")

    # Validação: título é obrigatório
    if not title:
        return {
            "status": "error",
            "error": "Título é obrigatório. Use: /inbox add <título>"
        }

    # Truncar título se necessário
    truncated_title, was_truncated = _truncate_title(title)

    # Obter nome do canal
    channel_name = None
    if channel_id:
        try:
            channel = await discord_service._client.fetch_channel(int(channel_id))
            channel_name = channel.name
        except Exception:
            logger.warning(f"Não foi possível obter nome do canal {channel_id}")
            channel_name = None

    # Detectar domínio
    domain_label = _detect_domain_from_channel(channel_name)

    # Construir descrição
    description = _build_description(
        title=truncated_title,
        channel_name=channel_name,
        was_truncated=was_truncated,
        full_title=title if was_truncated else None,
    )

    # Retornar dados estruturados para criação via Linear MCP
    return {
        "status": "ready",
        "project_id": INBOX_PROJECT_ID,
        "title": truncated_title,
        "description": description,
        "labels": [
            LABELS["fonte:discord"],
            LABELS["ação:implementar"],
            domain_label,
        ],
        "was_truncated": was_truncated,
        "channel_name": channel_name,
    }


# Tool definition para registro no MCP
TOOL_DEFINITION = {
    "name": "inbox_add",
    "description": (
        "Captura uma ideia rápida e cria uma issue no projeto Inbox do Linear. "
        "Use para registrar inspirações, oportunidades de melhoria ou tarefas futuras "
        "que surgirem durante conversas no Discord. Cada entrada expira em 60 dias."
    ),
    "inputSchema": {
        "type": "object",
        "properties": {
            "title": {
                "type": "string",
                "description": "Título da ideia (obrigatório, máximo 200 caracteres)"
            },
            "channel_id": {
                "type": "string",
                "description": "ID do canal (opcional, usado para detectar domínio automaticamente)"
            },
        },
        "required": ["title"],
    },
}
