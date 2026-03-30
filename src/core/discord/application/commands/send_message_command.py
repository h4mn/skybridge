# -*- coding: utf-8 -*-
"""
SendMessageCommand.

Comando CQRS para enviar mensagem de texto.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Self

from ...domain.value_objects import ChannelId, MessageContent


@dataclass(frozen=True)
class SendMessageCommand:
    """
    Command para enviar mensagem de texto.

    Usa ChannelId e MessageContent do domínio.
    """

    channel_id: ChannelId
    content: MessageContent
    reply_to: str | None = None  # Message ID para thread/resposta
    files: list[str] = field(default_factory=list)  # Paths absolutos

    @classmethod
    def create(
        cls,
        channel_id: str,
        text: str,
        reply_to: str | None = None,
        files: list[str] | None = None,
    ) -> Self:
        """
        Factory method.

        Args:
            channel_id: ID do canal (string numérica)
            text: Texto da mensagem
            reply_to: Message ID para resposta (opcional)
            files: Lista de paths de arquivos (opcional)

        Returns:
            Nova instância do comando
        """
        return cls(
            channel_id=ChannelId(channel_id),
            content=MessageContent(text),
            reply_to=reply_to,
            files=files or [],
        )
