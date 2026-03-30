# -*- coding: utf-8 -*-
"""
DiscordAdapter - Implementa ports do domínio usando discord.py.

Adapter que conecta o Domain Layer à biblioteca discord.py,
traduzindo entidades do domínio para objetos Discord e vice-versa.

DOC: openspec/changes/discord-ddd-migration/specs/discord-infrastructure/spec.md
"""

from __future__ import annotations

from typing import Any, Optional, Self

import discord
from discord import Embed

from ...domain.entities import Message, Channel
from ...domain.repositories import (
    MessageRepository,
    ChannelRepository,
)
from ...domain.value_objects import (
    ChannelId,
    MessageId,
    UserId,
    MessageContent,
)


class DiscordAdapter(MessageRepository, ChannelRepository):
    """
    Adapter para a biblioteca discord.py.

    Encapsula a API do Discord para enviar mensagens, embeds e botões.

    Args:
        client: Instância de discord.Client ou discord.Bot
    """

    def __init__(self, client: discord.Client | discord.Bot) -> None:
        """
        Inicializa adapter.

        Args:
            client: Cliente discord.py configurado
        """
        self._client = client

    async def send_message(
        self,
        channel_id: str,
        content: str,
        reply_to: str | None = None,
    ) -> str:
        """
        Envia mensagem de texto para um canal.

        Args:
            channel_id: ID do canal
            content: Conteúdo da mensagem
            reply_to: ID da mensagem para responder (opcional)

        Returns:
            ID da mensagem enviada

        Raises:
            DiscordException: Se erro na API do Discord
        """
        channel = await self._client.fetch_channel(channel_id)

        kwargs = {"content": content}
        if reply_to:
            kwargs["reference"] = await channel.fetch_message(reply_to)

        message = await channel.send(**kwargs)
        return str(message.id)

    async def send_embed(
        self,
        channel_id: str,
        title: str,
        description: str | None = None,
        color: int = 0,
        fields: list[dict] | None = None,
        footer: str | None = None,
    ) -> str:
        """
        Envia embed para um canal.

        Args:
            channel_id: ID do canal
            title: Título do embed
            description: Descrição (opcional)
            color: Cor do embed (decimal)
            fields: Lista de campos {name, value, inline}
            footer: Texto do rodapé (opcional)

        Returns:
            ID da mensagem enviada
        """
        channel = await self._client.fetch_channel(channel_id)

        # Criar embed Discord
        embed = Embed(
            title=title,
            description=description,
            color=color,
        )

        if fields:
            for field in fields:
                embed.add_field(
                    name=field["name"],
                    value=field["value"],
                    inline=field.get("inline", False),
                )

        if footer:
            embed.set_footer(text=footer)

        message = await channel.send(embed=embed)
        return str(message.id)

    async def send_buttons(
        self,
        channel_id: str,
        text: str,
        buttons: list[dict],
    ) -> str:
        """
        Envia mensagem com botões interativos.

        Args:
            channel_id: ID do canal
            text: Texto da mensagem
            buttons: Lista de {id, label, style, emoji, disabled}

        Returns:
            ID da mensagem enviada
        """
        from discord.ui import Button, View

        channel = await self._client.fetch_channel(channel_id)

        # Criar View
        view = View()

        for btn_data in buttons:
            # Mapear estilo para ButtonStyle
            style_map = {
                "primary": discord.ButtonStyle.primary,
                "secondary": discord.ButtonStyle.secondary,
                "success": discord.ButtonStyle.success,
                "danger": discord.ButtonStyle.danger,
                "link": discord.ButtonStyle.link,
            }

            style = style_map.get(
                btn_data.get("style", "primary"),
                discord.ButtonStyle.primary,
            )

            button = Button(
                label=btn_data["label"],
                style=style,
                custom_id=btn_data["id"],
                disabled=btn_data.get("disabled", False),
                emoji=btn_data.get("emoji"),
            )

            view.add_item(button)

        message = await channel.send(text, view=view)
        return str(message.id)

    async def fetch_messages(
        self,
        channel_id: str,
        limit: int = 20,
    ) -> list[Any]:
        """
        Busca histórico de mensagens do canal.

        Args:
            channel_id: ID do canal
            limit: Máximo de mensagens

        Returns:
            Lista de mensagens (objetos discord.py)
        """
        channel = await self._client.fetch_channel(channel_id)

        messages = []
        async for msg in channel.history(limit=limit):
            messages.append(msg)

        return messages

    # =========================================================================
    # MessageRepository Implementation (Ports do Domínio)
    # =========================================================================

    async def get_by_id(self, message_id: MessageId) -> Optional[Message]:
        """Busca mensagem por ID no Discord."""
        try:
            # Discord API não permite buscar mensagem diretamente sem canal
            # Precisamos buscar nos canais acessíveis
            for channel in self._client.get_all_channels():
                if not isinstance(channel, discord.abc.Messageable):
                    continue
                try:
                    msg = await channel.fetch_message(int(message_id.value))
                    return self._to_domain_message(msg)
                except discord.NotFound:
                    continue
            return None
        except Exception:
            return None

    async def save(self, message: Message) -> None:
        """
        Salva mensagem (envia para o Discord).

        Nota: Mensagens do domínio são imutáveis.
        Para enviar, use os métodos públicos (send_message, etc).
        """
        raise NotImplementedError(
            "Use DiscordService.send_message() para enviar mensagens"
        )

    async def get_history(
        self,
        channel_id: ChannelId,
        limit: int = 20,
    ) -> list[Message]:
        """Busca histórico de mensagens do canal."""
        try:
            channel = await self._client.fetch_channel(int(channel_id.value))
            if not isinstance(channel, discord.abc.Messageable):
                return []

            messages = []
            async for msg in channel.history(limit=limit):
                messages.append(self._to_domain_message(msg))
            return messages
        except Exception:
            return []

    async def delete(self, message_id: MessageId) -> bool:
        """Remove mensagem do Discord."""
        try:
            for channel in self._client.get_all_channels():
                if not isinstance(channel, discord.abc.Messageable):
                    continue
                try:
                    msg = await channel.fetch_message(int(message_id.value))
                    await msg.delete()
                    return True
                except discord.NotFound:
                    continue
            return False
        except Exception:
            return False

    # =========================================================================
    # ChannelRepository Implementation (Ports do Domínio)
    # =========================================================================

    async def get_by_id(self, channel_id: ChannelId) -> Optional[Channel]:
        """Busca canal por ID no Discord."""
        try:
            discord_channel = await self._client.fetch_channel(
                int(channel_id.value)
            )
            return self._to_domain_channel(discord_channel)
        except Exception:
            return None

    async def is_authorized(self, channel_id: ChannelId) -> bool:
        """
        Verifica se canal está autorizado.

        Nota: Verifica apenas se o canal existe.
        A autorização real é feita via AccessRepository.
        """
        channel = await self.get_by_id(channel_id)
        return channel is not None

    async def save(self, channel: Channel) -> None:
        """Salva canal (cache - não implementado)."""
        # Canais Discord não são "salvos", eles existem no Discord
        pass

    # =========================================================================
    # Métodos Auxiliares de Tradução (Discord → Domínio)
    # =========================================================================

    def _to_domain_message(self, discord_msg: discord.Message) -> Message:
        """Traduz discord.Message para Message (entidade do domínio)."""
        return Message(
            message_id=MessageId(str(discord_msg.id)),
            channel_id=ChannelId(str(discord_msg.channel.id)),
            author_id=UserId(str(discord_msg.author.id)),
            author_name=discord_msg.author.name,
            content=MessageContent(discord_msg.content or ""),
            has_attachments=len(discord_msg.attachments) > 0,
            attachment_count=len(discord_msg.attachments),
            is_dm=discord_msg.guild is None,
        )

    def _to_domain_channel(self, discord_channel: discord.abc.GuildChannel) -> Channel:
        """Traduz discord.Channel para Channel (entidade do domínio)."""
        return Channel(
            channel_id=ChannelId(str(discord_channel.id)),
            name=discord_channel.name,
            is_dm=False,
            guild_id=ChannelId(str(discord_channel.guild.id)) if discord_channel.guild else None,
        )

    def _to_domain_dm_channel(self, discord_channel: discord.DMChannel) -> Channel:
        """Traduz discord.DMChannel para Channel (entidade do domínio)."""
        return Channel(
            channel_id=ChannelId(str(discord_channel.id)),
            name=f"DM-{discord_channel.recipient.name}",
            is_dm=True,
            guild_id=None,
        )

    # =========================================================================
    # Factory
    # =========================================================================

    @classmethod
    def create(cls, client: discord.Client | discord.Bot) -> Self:
        """Factory method."""
        return cls(client)


def create_discord_adapter(client: discord.Client | discord.Bot) -> DiscordAdapter:
    """Cria instância de DiscordAdapter."""
    return DiscordAdapter.create(client)
