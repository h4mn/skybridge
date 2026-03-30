# -*- coding: utf-8 -*-
"""
Channel Entity.

Entidade para canais Discord.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Self

from ..value_objects import ChannelId


class ChannelType(str, Enum):
    """Tipo de canal Discord."""

    TEXT = "text"  # Canal de texto
    VOICE = "voice"  # Canal de voz
    DM = "dm"  # Mensagem direta
    GROUP_DM = "group_dm"  # DM em grupo
    THREAD = "thread"  # Thread
    CATEGORY = "category"  # Categoria
    ANNOUNCEMENT = "announcement"  # Canal de anúncios
    STAGE = "stage"  # Canal de palco


@dataclass
class Channel:
    """
    Entity para canal Discord.

    Representa qualquer tipo de canal: texto, DM, thread, etc.
    """

    id: ChannelId
    type: ChannelType
    name: str
    guild_id: str | None = None  # None para DMs
    parent_id: str | None = None  # Para threads
    topic: str | None = None

    def is_dm(self) -> bool:
        """Verifica se canal é DM."""
        return self.type == ChannelType.DM

    def is_thread(self) -> bool:
        """Verifica se canal é thread."""
        return self.type == ChannelType.THREAD

    def is_group(self) -> bool:
        """Verifica se canal é de grupo (servidor)."""
        return self.type in (
            ChannelType.TEXT,
            ChannelType.VOICE,
            ChannelType.ANNOUNCEMENT,
        )

    def is_guild_channel(self) -> bool:
        """Verifica se canal pertence a um servidor."""
        return self.guild_id is not None

    def display_name(self) -> str:
        """Retorna nome de exibição."""
        if self.is_dm():
            return f"DM com {self.name}"
        if self.is_thread():
            return f"Thread: {self.name}"
        return f"#{self.name}"

    @classmethod
    def create_dm(cls, channel_id: str, user_name: str) -> Self:
        """Cria canal DM."""
        return cls(
            id=ChannelId(channel_id),
            type=ChannelType.DM,
            name=user_name,
        )

    @classmethod
    def create_text(
        cls, channel_id: str, name: str, guild_id: str, topic: str | None = None
    ) -> Self:
        """Cria canal de texto."""
        return cls(
            id=ChannelId(channel_id),
            type=ChannelType.TEXT,
            name=name,
            guild_id=guild_id,
            topic=topic,
        )

    @classmethod
    def create_thread(
        cls,
        thread_id: str,
        name: str,
        parent_channel_id: str,
        guild_id: str,
    ) -> Self:
        """Cria thread."""
        return cls(
            id=ChannelId(thread_id),
            type=ChannelType.THREAD,
            name=name,
            guild_id=guild_id,
            parent_id=parent_channel_id,
        )
