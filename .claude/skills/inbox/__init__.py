# -*- coding: utf-8 -*-
"""
Inbox Skill - Captura rápida de ideias para o Linear

Uso: /inbox add <título> ou /inbox add description:<texto>
"""

from __future__ import annotations

import logging
from datetime import datetime, timedelta
import sys
from pathlib import Path

logger = logging.getLogger(__name__)

# Adicionar src ao path para importar módulos do projeto
src_path = Path(__file__).parent.parent.parent.parent / "src"
if str(src_path) not in sys.path:
    sys.path.insert(0, str(src_path))

from core.discord.infrastructure.linear_labels import LinearLabels

# Configurações
INBOX_PROJECT_ID = "02be2007-fd29-4f1c-8dc8-6b1d854a4a70"  # Inbox - Backlog de Ideias
MAX_TITLE_LENGTH = 200
EXPIRES_DAYS = 60


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


def build_description(title: str, was_truncated: bool, full_title: str | None = None, user_description: str | None = None) -> str:
    """Constroi descrição estruturada da issue.

    Args:
        title: Título da ideia
        was_truncated: Se o título foi truncado
        full_title: Título completo (se foi truncado)
        user_description: Descrição opcional fornecida pelo usuário

    Returns:
        Descrição estruturada em Markdown
    """
    parts = []

    # Descrição do usuário (se fornecida)
    if user_description:
        parts.append(user_description.strip())
        parts.append("\n---")

    # Fonte
    parts.append("**Fonte:** Claude Code")

    # Preservar título completo se foi truncado
    if was_truncated and full_title:
        parts.append(f"\n**Título completo:** {full_title}")

    parts.append("\n**Ação sugerida:** Implementar | Pesquisar | Arquivar | Descartar")
    parts.append(f"\n**Expires:** {calculate_expires_date()} ({EXPIRES_DAYS} dias)")

    return "\n".join(parts)


def inbox_add(title: str | None = None, description: str | None = None) -> dict:
    """
    Adiciona uma ideia ao Inbox via Linear MCP.

    Args:
        title: Título da ideia (opcional se description for fornecido)
        description: Descrição adicional da ideia (opcional, sem limite de caracteres)

    Returns:
        Dict com status e dados da issue criada
    """
    # Validação: pelo menos título ou descrição
    has_title = title and title.strip()
    has_description = description and description.strip()

    if not has_title and not has_description:
        return {
            "status": "error",
            "error": "Pelo menos título ou descrição é obrigatório. Use: /inbox add <título> ou /inbox add description:<texto>"
        }

    # Processar título
    title = title.strip() if has_title else ""
    truncated_title = ""
    was_truncated = False

    if has_title:
        truncated_title, was_truncated = truncate_title(title)
    else:
        # Se não há título, usar primeiras palavras da descrição
        desc_words = description.strip().split()[:5]
        truncated_title = "Inbox: " + " ".join(desc_words) + ("..." if len(description.strip().split()) > 5 else "")

    # Construir descrição
    user_desc = description.strip() if has_description else None
    structured_description = build_description(
        title=truncated_title,
        was_truncated=was_truncated,
        full_title=title if was_truncated else None,
        user_description=user_desc,
    )

    # Retornar dados para criação via Linear MCP
    return {
        "status": "ready",
        "project_id": INBOX_PROJECT_ID,
        "title": truncated_title,
        "description": structured_description,
        "labels": [
            LinearLabels.FONTE_CLAUDE_CODE,
            LinearLabels.ACAO_IMPLEMENTAR,
            LinearLabels.DOMINIO_GERAL,
        ],
        "was_truncated": was_truncated,
    }


# Entry point para a skill
def handle_inbox_command(args: dict) -> str:
    """
    Handler principal da skill /inbox.

    Args:
        args: Dict com 'action', 'title' e 'description'

    Returns:
        Mensagem de resposta
    """
    action = args.get("action", "")

    if action != "add":
        return f"❌ Ação '{action}' não suportada. Use: /inbox add <título> ou /inbox add description:<texto>"

    title = args.get("title")
    description = args.get("description")

    # Preparar dados para Linear MCP
    result = inbox_add(title=title, description=description)

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
    print(handle_inbox_command({"action": "add", "description": "Ideia completa sem título"}))
