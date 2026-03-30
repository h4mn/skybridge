# -*- coding: utf-8 -*-
"""
Tool: send_menu

Envia menu suspenso (select) para canal Discord.
Usuário pode selecionar uma opção entre várias.

DOC: DDD Migration - Presentation Layer
"""

from __future__ import annotations

import logging
from typing import Any

import discord
from discord.ui import View, Select

from ...application.services.discord_service import DiscordService

logger = logging.getLogger(__name__)


class MenuView(View):
    """View com menu suspenso que persiste."""

    def __init__(self, options: list[dict], callback_name: str):
        """
        Inicializa View com menu.

        Args:
            options: Lista de {label, value, description, emoji}
            callback_name: Nome do callback para debug
        """
        super().__init__(timeout=None)  # Nunca expira
        self._options = options
        self._callback_name = callback_name

    @discord.ui.select(
        placeholder="Selecione uma opção...",
        min_values=1,
        max_values=1,
    )
    async def select_callback(self, interaction: discord.Interaction, select: Select):
        """Callback quando seleção é feita."""
        # Pega valor selecionado
        selected_value = select.values[0]
        selected_label = select.options[select.index].label

        # Busca opção completa
        option = next((o for o in self._options if o["value"] == selected_value), None)

        # Responde
        if option:
            emoji = option.get("emoji", "")
            desc = option.get("description", "")

            response = f"✅ **{selected_label}** selecionado"
            if emoji:
                response = f"{emoji} **{selected_label}** selecionado"
            if desc:
                response += f"\n{desc}"

            await interaction.response.send_message(response)
        else:
            await interaction.response.send_message(f"Seleção: {selected_label}")

        logger.info(
            f"Menu {self._callback_name}: {selected_label} "
            f"por {interaction.user.name}"
        )


async def handle_send_menu(
    discord_service: DiscordService,
    args: dict[str, Any]
) -> dict[str, Any]:
    """
    Handler para tool send_menu.

    Args:
        discord_service: Instância do DiscordService
        args: Argumentos do tool

    Returns:
        Dict com message_id, status
    """
    chat_id = args.get("chat_id")
    placeholder = args.get("placeholder", "Selecione uma opção...")
    options = args.get("options", [])

    if not chat_id:
        return {
            "status": "error",
            "error": "chat_id é obrigatório"
        }

    if not options:
        return {
            "status": "error",
            "error": "Ao menos uma opção é necessária"
        }

    # Valida opções
    for opt in options:
        if "label" not in opt or "value" not in opt:
            return {
                "status": "error",
                "error": "Cada opção deve ter label e value"
            }

    try:
        # Envia menu com View customizada
        channel = await discord_service._client.fetch_channel(int(chat_id))

        view = MenuView(options, callback_name="send_menu")

        # Adiciona Select à View
        select = Select(
            placeholder=placeholder,
            min_values=1,
            max_values=1,
            options=[
            discord.SelectOption(
                label=opt["label"],
                value=opt["value"],
                description=opt.get("description"),
                emoji=opt.get("emoji"),
            )
            for opt in options
        ])

        view.add_item(select)

        # Envia mensagem com o menu
        message = await channel.send("Escolha uma opção:", view=view)

        # Guarda referência da view
        discord_service._views_by_message[message.id] = view

        return {
            "message_id": str(message.id),
            "status": "success"
        }
    except Exception as e:
        logger.error(f"Erro ao enviar menu: {e}")
        return {
            "status": "error",
            "error": str(e)
        }


# Tool definition para registro no MCP
TOOL_DEFINITION = {
    "name": "send_menu",
    "description": (
        "Send dropdown menu (select) to Discord channel. "
        "User can select one option. Menu persists (timeout=None)."
    ),
    "inputSchema": {
        "type": "object",
        "properties": {
            "chat_id": {"type": "string", "description": "Channel ID"},
            "placeholder": {"type": "string", "description": "Placeholder text"},
            "options": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "label": {"type": "string", "description": "Display label"},
                        "value": {"type": "string", "description": "Internal value"},
                        "description": {"type": "string", "description": "Option description"},
                        "emoji": {"type": "string", "description": "Emoji (optional)"},
                    },
                    "required": ["label", "value"],
                },
                "description": "Menu options",
            },
        },
        "required": ["chat_id", "options"],
    },
}
