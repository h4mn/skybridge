# -*- coding: utf-8 -*-
"""
ReactCommand.

Comando CQRS para adicionar reação a mensagem.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Self

from ...domain.value_objects import ChannelId, MessageId


@dataclass(frozen=True)
class ReactCommand:
    """
    Command para adicionar reação emoji a mensagem.
    """

    channel_id: ChannelId
    message_id: MessageId
    emoji: str

    @classmethod
    def create(
        cls,
        channel_id: str,
        message_id: str,
        emoji: str,
    ) -> Self:
        """
        Factory method.

        Args:
            channel_id: ID do canal
            message_id: ID da mensagem
            emoji: Emoji para reagir (unicode ou <:name:id>)

        Returns:
            Nova instância do comando
        """
        return cls(
            channel_id=ChannelId(channel_id),
            message_id=MessageId(message_id),
            emoji=emoji,
        )
