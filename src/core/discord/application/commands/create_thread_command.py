# -*- coding: utf-8 -*-
"""
CreateThreadCommand.

Comando CQRS para criar thread a partir de mensagem.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal, Self

from ...domain.value_objects import ChannelId, MessageId


@dataclass(frozen=True)
class CreateThreadCommand:
    """
    Command para criar thread Discord.

    Thread é criada a partir de uma mensagem existente.
    """

    channel_id: ChannelId
    message_id: MessageId
    name: str
    auto_archive_duration: Literal[60, 1440, 4320, 10080] = 1440  # minutos

    @classmethod
    def create(
        cls,
        channel_id: str,
        message_id: str,
        name: str,
        auto_archive_duration: int = 1440,
    ) -> Self:
        """
        Factory method.

        Args:
            channel_id: ID do canal onde criar thread
            message_id: ID da mensagem base
            name: Nome da thread
            auto_archive_duration: Duração antes de auto-arquivar (minutos)
                60 = 1h, 1440 = 24h, 4320 = 3d, 10080 = 7d

        Returns:
            Nova instância do comando
        """
        return cls(
            channel_id=ChannelId(channel_id),
            message_id=MessageId(message_id),
            name=name,
            auto_archive_duration=auto_archive_duration,
        )
