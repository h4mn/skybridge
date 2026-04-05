# -*- coding: utf-8 -*-
"""
Inbox Skill - Captura rápida de ideias para o Linear

Uso: /inbox add <título>
"""

from __future__ import annotations

import logging
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

# Configurações
INBOX_PROJECT_ID = "02be2007-fd29-4f1c-8dc8-6b1d854a4a70"  # Inbox - Backlog de Ideias
MAX_TITLE_LENGTH = 200
EXPIRES_DAYS = 60

# Labels IDs
LABELS = {
    "fonte:claude-code": "546f52f0-f618-4f81-91bd-6bc77fde1fff",
    "domínio:geral": "01fb356c-a45f-4cb1-9a01-de5f9cbc1da5",
    "ação:implementar": "6b8cdf2d-177f-4d86-8d4d-d66f8824c7ec",
}


def calculate_expires_date() -> str:
    """Calcula data de expires (hoje + 60 dias)."""
    expires = datetime.now() + timedelta(days=EXPIRES_DAYS)
    return expires.strftime("%Y-%m-%d")


def truncate_title(title: str) -> tuple[str, bool]:
    """
    Trunca título se necessário.

    Returns:
        (título_truncado, foi_truncado)
    """
    if len(title) > MAX_TITLE_LENGTH:
        return title[:MAX_TITLE_LENGTH], True
    return title, False


def build_description(title: str, was_truncated: bool, full_title: str | None = None) -> str:
    """Constroi descrição estruturada da issue."""
    parts = ["**Fonte:** Claude Code"]

    # Preservar título completo se foi truncado
    if was_truncated and full_title:
        parts.append(f"\n**Título completo:** {full_title}")

    parts.append("\n---")
    parts.append("\n**Ação sugerida:** Implementar | Pesquisar | Arquivar | Descartar")
    parts.append(f"\n**Expires:** {calculate_expires_date()} ({EXPIRES_DAYS} dias)")

    return "\n".join(parts)


def inbox_add(title: str) -> dict:
    """
    Adiciona uma ideia ao Inbox via Linear MCP.

    Args:
        title: Título da ideia

    Returns:
        Dict com status e dados da issue criada
    """
    # Validação
    if not title or not title.strip():
        return {
            "status": "error",
            "error": "Título é obrigatório. Use: /inbox add <título>"
        }

    title = title.strip()

    # Truncar se necessário
    truncated_title, was_truncated = truncate_title(title)

    # Construir descrição
    description = build_description(
        title=truncated_title,
        was_truncated=was_truncated,
        full_title=title if was_truncated else None,
    )

    # Retornar dados para criação via Linear MCP
    return {
        "status": "ready",
        "project_id": INBOX_PROJECT_ID,
        "title": truncated_title,
        "description": description,
        "labels": [
            LABELS["fonte:claude-code"],
            LABELS["ação:implementar"],
            LABELS["domínio:geral"],
        ],
        "was_truncated": was_truncated,
    }


# Entry point para a skill
def handle_inbox_command(args: dict) -> str:
    """
    Handler principal da skill /inbox.

    Args:
        args: Dict com 'action' e 'title'

    Returns:
        Mensagem de resposta
    """
    action = args.get("action", "")

    if action != "add":
        return f"❌ Ação '{action}' não suportada. Use: /inbox add <título>"

    title = args.get("title", "")

    # Preparar dados para Linear MCP
    result = inbox_add(title)

    if result["status"] == "error":
        return f"❌ {result['error']}"

    # Nota: A criação da issue será feita pelo contexto via Linear MCP
    # Retornamos instruções para o contexto
    return (
        f"✅ **Inbox entry preparada!**\n\n"
        f"**Título:** {result['title']}\n"
        f"**Labels:** fonte:claude-code, ação:implementar, domínio:geral\n"
        f"**Expires:** {calculate_expires_date()} ({EXPIRES_DAYS} dias)\n\n"
        f"Use o Linear MCP para criar a issue com os dados acima."
    )


if __name__ == "__main__":
    # Teste local
    print(handle_inbox_command({"action": "add", "title": "Teste de ideia"}))
