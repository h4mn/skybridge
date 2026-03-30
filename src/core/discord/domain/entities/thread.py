# -*- coding: utf-8 -*-
"""
Thread Entity.

Entidade para threads Discord.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Self

from ..value_objects import ChannelId, MessageId


@dataclass
class Thread:
    """
    Entity para thread Discord.

    Threads são canais temporários criados a partir de mensagens.
    """

    id: ChannelId
    name: str
    parent_channel_id: ChannelId
    root_message_id: MessageId
    guild_id: str
    created_at: datetime
    archived: bool = False
    locked: bool = False
    auto_archive_duration: int = 1440  # minutos (24h padrão)
    message_count: int = 0

    def is_active(self) -> bool:
        """Verifica se thread está ativa (não arquivada nem travada)."""
        return not self.archived and not self.locked

    def archive(self) -> None:
        """Arquiva a thread."""
        self.archived = True

    def unarchive(self) -> None:
        """Desarquiva a thread."""
        self.archived = False

    def lock(self) -> None:
        """Trava a thread (apenas mods podem postar)."""
        self.locked = True

    def unlock(self) -> None:
        """Destrava a thread."""
        self.locked = False

    def rename(self, new_name: str) -> None:
        """Renomeia a thread."""
        if not new_name.strip():
            raise ValueError("Nome da thread não pode ser vazio")
        self.name = new_name.strip()

    def increment_message_count(self) -> None:
        """Incrementa contador de mensagens."""
        self.message_count += 1

    @classmethod
    def create(
        cls,
        thread_id: str,
        name: str,
        parent_channel_id: str,
        root_message_id: str,
        guild_id: str,
        auto_archive_duration: int = 1440,
    ) -> Self:
        """
        Factory method para criar thread.

        Args:
            thread_id: ID da thread
            name: Nome da thread
            parent_channel_id: ID do canal pai
            root_message_id: ID da mensagem raiz
            guild_id: ID do servidor
            auto_archive_duration: Duração antes de auto-arquivar (minutos)

        Returns:
            Nova instância de Thread
        """
        return cls(
            id=ChannelId(thread_id),
            name=name,
            parent_channel_id=ChannelId(parent_channel_id),
            root_message_id=MessageId(root_message_id),
            guild_id=guild_id,
            created_at=datetime.now(),
            auto_archive_duration=auto_archive_duration,
        )
