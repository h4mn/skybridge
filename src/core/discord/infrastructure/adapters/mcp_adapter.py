# -*- coding: utf-8 -*-
"""
MCPAdapter - Fachada para expor ferramentas MCP.

Este adapter organiza os MCP Tools existentes, conectando
as chamadas do Claude Code aos Commands/Handlers do domínio.
"""

from __future__ import annotations

from typing import Any, Optional

from ...application.services.discord_service import DiscordService
from ...application.commands import (
    SendMessageCommand,
    SendEmbedCommand,
    SendButtonsCommand,
    EditMessageCommand,
    ReactCommand,
)
from ...domain.value_objects import ChannelId
from ...application.services.discord_service import ButtonConfig, EmbedField


class MCPAdapter:
    """
    Adapter para MCP (Model Context Protocol).

    Expose uma fachada organizada para as ferramentas MCP que
    Claude Code pode chamar, delegando para DiscordService.
    """

    def __init__(self, discord_service: DiscordService):
        """
        Inicializa o adapter.

        Args:
            discord_service: Instância do DiscordService
        """
        self._discord_service = discord_service

    # =========================================================================
    # MCP Tools - Reply (Mensagem simples)
    # =========================================================================

    async def reply(
        self,
        chat_id: str,
        text: str,
        reply_to: Optional[str] = None,
    ) -> dict[str, Any]:
        """
        Envia mensagem de texto para canal Discord.

        Args:
            chat_id: ID do canal Discord
            text: Conteúdo da mensagem
            reply_to: ID da mensagem para responder (opcional)

        Returns:
            Dict com {message_id, status}
        """
        try:
            message = await self._discord_service.send_message(
                channel_id=chat_id,
                content=text,
            )
            return {
                "message_id": str(message.id) if message else None,
                "status": "success",
            }
        except Exception as e:
            return {
                "message_id": None,
                "status": "error",
                "error": str(e),
            }

    # =========================================================================
    # MCP Tools - Send Embed
    # =========================================================================

    async def send_embed(
        self,
        chat_id: str,
        title: str,
        description: Optional[str] = None,
        color: int = 3447003,
        fields: Optional[list[dict]] = None,
        footer: Optional[str] = None,
    ) -> dict[str, Any]:
        """
        Envia embed para canal Discord.

        Args:
            chat_id: ID do canal Discord
            title: Título do embed
            description: Descrição do embed
            color: Cor do embed (decimal)
            fields: Lista de campos {name, value, inline}
            footer: Texto do rodapé

        Returns:
            Dict com {message_id, status}
        """
        try:
            embed_fields = None
            if fields:
                embed_fields = [
                    EmbedField(
                        name=f["name"],
                        value=f["value"],
                        inline=f.get("inline", False),
                    )
                    for f in fields
                ]

            message = await self._discord_service.send_embed(
                channel_id=chat_id,
                title=title,
                description=description,
                color=color,
                fields=embed_fields,
                footer=footer,
            )
            return {
                "message_id": str(message.id) if message else None,
                "status": "success",
            }
        except Exception as e:
            return {
                "message_id": None,
                "status": "error",
                "error": str(e),
            }

    # =========================================================================
    # MCP Tools - Send Buttons
    # =========================================================================

    async def send_buttons(
        self,
        chat_id: str,
        title: str,
        description: Optional[str] = None,
        buttons: Optional[list[dict]] = None,
    ) -> dict[str, Any]:
        """
        Envia embed com botões interativos.

        Args:
            chat_id: ID do canal Discord
            title: Título do embed
            description: Descrição
            buttons: Lista de {label, style, custom_id, disabled}

        Returns:
            Dict com {message_id, status}
        """
        try:
            button_configs = None
            if buttons:
                button_configs = [
                    ButtonConfig(
                        label=b["label"],
                        style=b.get("style", "primary"),
                        custom_id=b["id"],
                        disabled=b.get("disabled", False),
                    )
                    for b in buttons
                ]

            message = await self._discord_service.send_buttons(
                channel_id=chat_id,
                title=title,
                description=description,
                buttons=button_configs,
            )
            return {
                "message_id": str(message.id) if message else None,
                "status": "success",
            }
        except Exception as e:
            return {
                "message_id": None,
                "status": "error",
                "error": str(e),
            }

    # =========================================================================
    # MCP Tools - Fetch Messages
    # =========================================================================

    async def fetch_messages(
        self,
        chat_id: str,
        limit: int = 20,
    ) -> dict[str, Any]:
        """
        Busca histórico de mensagens do canal.

        Args:
            chat_id: ID do canal Discord
            limit: Máximo de mensagens

        Returns:
            Dict com {messages, status}
        """
        try:
            channel_id = ChannelId(chat_id)
            messages = await self._discord_service.get_history(
                channel_id=channel_id,
                limit=limit,
            )
            return {
                "messages": [
                    {
                        "id": str(msg.message_id),
                        "content": str(msg.content),
                        "author": msg.author_name,
                        "author_id": str(msg.author_id),
                        "timestamp": msg.occurred_at.isoformat(),
                    }
                    for msg in messages
                ],
                "status": "success",
            }
        except Exception as e:
            return {
                "messages": [],
                "status": "error",
                "error": str(e),
            }

    # =========================================================================
    # MCP Tools - React
    # =========================================================================

    async def react(
        self,
        chat_id: str,
        message_id: str,
        emoji: str,
    ) -> dict[str, Any]:
        """
        Adiciona reação a mensagem.

        Args:
            chat_id: ID do canal Discord
            message_id: ID da mensagem
            emoji: Emoji a adicionar

        Returns:
            Dict com {status}
        """
        try:
            success = await self._discord_service.add_reaction(
                channel_id=chat_id,
                message_id=message_id,
                emoji=emoji,
            )
            return {"status": "success" if success else "failed"}
        except Exception as e:
            return {
                "status": "error",
                "error": str(e),
            }

    # =========================================================================
    # MCP Tools - Edit Message
    # =========================================================================

    async def edit_message(
        self,
        chat_id: str,
        message_id: str,
        content: Optional[str] = None,
        embed: Optional[dict] = None,
    ) -> dict[str, Any]:
        """
        Edita mensagem existente.

        Args:
            chat_id: ID do canal Discord
            message_id: ID da mensagem
            content: Novo conteúdo
            embed: Novo embed (dict)

        Returns:
            Dict com {message_id, status}
        """
        try:
            message = await self._discord_service.edit_message(
                channel_id=chat_id,
                message_id=message_id,
                content=content,
                embed=embed,
            )
            return {
                "message_id": str(message.id) if message else None,
                "status": "success",
            }
        except Exception as e:
            return {
                "message_id": None,
                "status": "error",
                "error": str(e),
            }

    # =========================================================================
    # Factory
    # =========================================================================

    @classmethod
    def create(cls, discord_service: DiscordService) -> "MCPAdapter":
        """Factory method."""
        return cls(discord_service)


def create_mcp_adapter(discord_service: DiscordService) -> MCPAdapter:
    """
    Cria instância de MCPAdapter.

    Args:
        discord_service: Instância do DiscordService

    Returns:
        Instância de MCPAdapter
    """
    return MCPAdapter.create(discord_service)
