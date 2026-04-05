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
) -> str:
    """Constroi descrição estruturada da issue."""
    parts = [f"**Fonte:** Discord #{channel_name}" if channel_name else "**Fonte:** Discord"]

    if was_truncated and full_title:
        parts.append(f"\n**Título completo:** {full_title}")

    parts.extend([
        "\n---",
        "\n**Ação sugerida:** Implementar | Pesquisar | Arquivar | Descartar",
        f"\n**Expires:** {calculate_expires_date()} ({EXPIRES_DAYS} dias)",
    ])

    return "\n".join(parts)


async def inbox_command_handler(
    interaction: Interaction,
    titulo: str,
    linear_mcp_func=None,
) -> None:
    """
    Handler do comando /inbox.

    Args:
        interaction: Interação do Discord
        titulo: Título da ideia
        linear_mcp_func: Função para criar issue no Linear (opcional, para teste)
    """
    await interaction.response.defer()

    # Validação
    if not titulo or not titulo.strip():
        await interaction.followup.send("❌ **Título é obrigatório!**")
        return

    titulo = titulo.strip()
    was_truncated = len(titulo) > MAX_TITLE_LENGTH
    truncated_title = titulo[:MAX_TITLE_LENGTH] if was_truncated else titulo

    # Detectar domínio
    channel_name = interaction.channel.name if interaction.channel else None
    domain = detect_domain_from_channel(channel_name)

    # Construir descrição
    description = build_description(
        title=truncated_title,
        channel_name=channel_name,
        was_truncated=was_truncated,
        full_title=titulo if was_truncated else None,
    )

    # TODO: Criar issue via Linear MCP
    # Por enquanto, retorna mensagem formatada
    response = (
        f"✅ **Inbox entry criada!**\n\n"
        f"**Título:** {truncated_title}\n"
        f"**Canal:** #{channel_name if channel_name else 'N/A'}\n"
        f"**Domínio:** {domain}\n"
        f"**Labels:** fonte:discord, ação:implementar\n"
        f"**Expires:** {calculate_expires_date()} ({EXPIRES_DAYS} dias)"
    )

    await interaction.followup.send(response)
    logger.info(f"/inbox usado por {interaction.user}: {truncated_title}")


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
        titulo="Título da ideia (obrigatório, máximo 200 caracteres)"
    )
    async def inbox(
        interaction: Interaction,
        titulo: str,
    ):
        await inbox_command_handler(interaction, titulo)

    logger.info("Comando /inbox registrado na CommandTree")
