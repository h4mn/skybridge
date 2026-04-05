# -*- coding: utf-8 -*-
"""
Discord Slash Commands - Comandos nativos do Discord com autocomplete

DOC: Inbox Specification - Fase 8: Slash Command Nativo
"""

from __future__ import annotations

import logging
from datetime import datetime, timedelta
from typing import Optional

from discord import app_commands, Interaction

from ..infrastructure.linear_client import create_inbox_issue, LinearClientError

logger = logging.getLogger(__name__)

# Configurações
MAX_TITLE_LENGTH = 200
EXPIRES_DAYS = 60

# Mapeamento de canais Discord → domínios
CHANNEL_DOMAIN_MAP = {
    "paper-trading": "paper",
    "paper-dev": "paper",
    "discord-dev": "discord",
    "discord-bots": "discord",
    "autokarpa": "autokarpa",
    "autokarpa-dev": "autokarpa",
}

# Labels IDs
LABELS = {
    "fonte:discord": "e75a8d97-1064-464b-92a7-f4ad371f191d",
    "domínio:paper": "88e309d3-694a-469c-bed6-b9443cb3694e",
    "domínio:discord": "d73805a8-6b4b-4c54-8ef8-daec148fbb1f",
    "domínio:autokarpa": "b729ecd3-28d0-4320-9084-2a0264836877",
    "domínio:geral": "01fb356c-a45f-4cb1-9a01-de5f9cbc1da5",
}


def calculate_expires_date() -> str:
    """Calcula data de expires (hoje + 60 dias)."""
    expires = datetime.now() + timedelta(days=EXPIRES_DAYS)
    return expires.strftime("%Y-%m-%d")


def detect_domain_from_channel(channel_name: Optional[str]) -> str:
    """Detecta domínio baseado no nome do canal."""
    if not channel_name:
        return "geral"

    channel_lower = channel_name.lower()
    for pattern, domain_key in CHANNEL_DOMAIN_MAP.items():
        if pattern in channel_lower:
            return domain_key

    return "geral"


def build_description(
    title: str,
    channel_name: Optional[str],
    was_truncated: bool,
    full_title: Optional[str] = None,
    user_description: Optional[str] = None,
) -> str:
    """Constroi descrição estruturada da issue.

    Args:
        title: Título da ideia
        channel_name: Nome do canal Discord
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
    if channel_name:
        parts.append(f"**Fonte:** Discord #{channel_name}")
    else:
        parts.append("**Fonte:** Discord")

    # Preservar título completo se foi truncado
    if was_truncated and full_title:
        parts.append(f"\n**Título completo:** {full_title}")

    parts.append("\n**Ação sugerida:** Implementar | Pesquisar | Arquivar | Descartar")
    parts.append(f"\n**Expires:** {calculate_expires_date()} ({EXPIRES_DAYS} dias)")

    return "\n".join(parts)


async def inbox_command_handler(
    interaction: Interaction,
    titulo: str,
    descricao: Optional[str] = None,
) -> None:
    """
    Handler do comando /inbox.

    Args:
        interaction: Interação do Discord
        titulo: Título da ideia
        descricao: Descrição opcional da ideia
    """
    await interaction.response.defer()

    # Validação: pelo menos título ou descrição
    has_title = titulo and titulo.strip()
    has_description = descricao and descricao.strip()

    if not has_title and not has_description:
        await interaction.followup.send("❌ **Pelo menos título ou descrição é obrigatório!**")
        return

    # Processar título
    titulo = titulo.strip() if has_title else ""
    was_truncated = False
    truncated_title = ""

    if has_title:
        was_truncated = len(titulo) > MAX_TITLE_LENGTH
        truncated_title = titulo[:MAX_TITLE_LENGTH] if was_truncated else titulo
    else:
        # Se não há título, usar primeiras palavras da descrição
        desc_words = descricao.strip().split()[:5]
        truncated_title = "Inbox: " + " ".join(desc_words) + ("..." if len(descricao.strip().split()) > 5 else "")

    # Detectar domínio
    channel_name = interaction.channel.name if interaction.channel else None
    domain = detect_domain_from_channel(channel_name)

    # Construir descrição
    user_desc = descricao.strip() if has_description else None
    description = build_description(
        title=truncated_title,
        channel_name=channel_name,
        was_truncated=was_truncated,
        full_title=titulo if was_truncated else None,
        user_description=user_desc,
    )

    # Labels (usando IDs conhecidos do Linear)
    label_ids = [
        LABELS["fonte:discord"],
        LABELS[f"domínio:{domain}"],
    ]

    # Criar issue via Linear API
    try:
        issue_result = await create_inbox_issue(
            title=truncated_title,
            description=description,
            label_ids=label_ids,
        )

        issue_url = issue_result["url"]
        issue_identifier = issue_result["identifier"]

        response = (
            f"✅ **Inbox entry criada!**\n\n"
            f"**[{issue_identifier}]({issue_url})**\n"
            f"**Canal:** #{channel_name if channel_name else 'N/A'}\n"
            f"**Domínio:** {domain}\n"
            f"**Labels:** fonte:discord, ação:implementar\n"
            f"**Expires:** {calculate_expires_date()} ({EXPIRES_DAYS} dias)"
        )

        logger.info(f"/inbox usado por {interaction.user}: {truncated_title} -> {issue_identifier}")

    except LinearClientError as e:
        logger.error(f"Erro ao criar issue no Linear: {e}")
        response = (
            f"❌ **Erro ao criar issue no Linear**\n\n"
            f"**Título:** {truncated_title}\n"
            f"**Erro:** {str(e)}\n\n"
            f"Tente novamente ou use o MCP diretamente."
        )

    except Exception as e:
        logger.error(f"Erro ao criar issue no Linear: {e}")
        response = (
            f"❌ **Erro ao criar issue no Linear**\n\n"
            f"**Título:** {truncated_title}\n"
            f"**Erro:** {str(e)}\n\n"
            f"Tente novamente ou use o MCP diretamente."
        )

    await interaction.followup.send(response)


def setup_inbox_command(tree: app_commands.CommandTree) -> None:
    """
    Registra o comando /inbox na CommandTree.

    Args:
        tree: CommandTree do Discord bot
    """
    @tree.command(
        name="inbox",
        description="Capturar ideia no Inbox - cria issue no Linear"
    )
    @app_commands.describe(
        titulo="Título da ideia (opcional se descrição for fornecido, máximo 200 caracteres)",
        descricao="Descrição adicional da ideia (opcional, sem limite de caracteres)"
    )
    async def inbox(
        interaction: Interaction,
        titulo: str,
        descricao: Optional[str] = None,
    ):
        await inbox_command_handler(interaction, titulo, descricao)

    logger.info("Comando /inbox registrado na CommandTree")
