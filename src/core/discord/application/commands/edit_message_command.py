# -*- coding: utf-8 -*-
"""
EditMessageCommand.

Comando CQRS para editar mensagem existente.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Self

from ...domain.value_objects import ChannelId, MessageId, MessageContent


@dataclass(frozen=True)
class EditMessageCommand:
    """
    Command para editar mensagem do bot.

    Só pode editar mensagens do próprio bot.
    """

    channel_id: ChannelId
    message_id: MessageId
    new_content: MessageContent

    @classmethod
    def create(
        cls,
        channel_id: str,
        message_id: str,
        new_text: str,
    ) -> Self:
        """
        Factory method.

        Args:
            channel_id: ID do canal
            message_id: ID da mensagem
            new_text: Novo texto da mensagem

        Returns:
            Nova instância do comando
        """
        return cls(
            channel_id=ChannelId(channel_id),
            message_id=MessageId(message_id),
            new_content=MessageContent(new_text),
        )
