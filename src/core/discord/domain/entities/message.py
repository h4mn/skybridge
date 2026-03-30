# -*- coding: utf-8 -*-
"""
Message Aggregate Root.

Entidade raiz de agregado para mensagens Discord.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Self

from ..value_objects import ChannelId, MessageId, UserId, MessageContent


class MessageEditError(Exception):
    """Erro ao editar mensagem."""

    def __init__(self, reason: str):
        self.reason = reason
        super().__init__(f"Não foi possível editar mensagem: {reason}")


@dataclass
class Message:
    """
    Aggregate Root para mensagem Discord.

    Contém ID, channel_id, author_id, content, timestamp, attachments e reactions.
    """

    id: MessageId
    channel_id: ChannelId
    author_id: UserId
    content: MessageContent
    created_at: datetime
    edited_at: datetime | None = None
    attachments: list[Attachment] = field(default_factory=list)
    reactions: list[Reaction] = field(default_factory=list)
    is_bot: bool = False

    # Constantes de negócio
    EDIT_DEADLINE_HOURS: int = 24

    def edit(self, new_content: MessageContent) -> None:
        """
        Edita conteúdo da mensagem.

        Args:
            new_content: Novo conteúdo

        Raises:
            MessageEditError: Se mensagem expirou (mais de 24h)
        """
        deadline = self.created_at + timedelta(hours=self.EDIT_DEADLINE_HOURS)
        if datetime.now() > deadline:
            raise MessageEditError(
                f"Mensagem expirou (mais de {self.EDIT_DEADLINE_HOURS}h)"
            )

        self.content = new_content
        self.edited_at = datetime.now()

    def add_reaction(self, emoji: str) -> None:
        """Adiciona reação à mensagem."""
        # Verifica se já existe
        for reaction in self.reactions:
            if reaction.emoji == emoji:
                reaction.count += 1
                return

        self.reactions.append(Reaction(emoji=emoji, count=1))

    def has_attachment(self) -> bool:
        """Verifica se mensagem tem anexos."""
        return len(self.attachments) > 0

    def is_edited(self) -> bool:
        """Verifica se mensagem foi editada."""
        return self.edited_at is not None

    def age_hours(self) -> float:
        """Retorna idade da mensagem em horas."""
        delta = datetime.now() - self.created_at
        return delta.total_seconds() / 3600

    @classmethod
    def create(
        cls,
        message_id: str,
        channel_id: str,
        author_id: str,
        content: str,
        is_bot: bool = False,
    ) -> Self:
        """
        Factory method para criar mensagem.

        Args:
            message_id: ID da mensagem (string numérica)
            channel_id: ID do canal
            author_id: ID do autor
            content: Texto da mensagem
            is_bot: Se mensagem é de bot

        Returns:
            Nova instância de Message
        """
        return cls(
            id=MessageId(message_id),
            channel_id=ChannelId(channel_id),
            author_id=UserId(author_id),
            content=MessageContent(content),
            created_at=datetime.now(),
            is_bot=is_bot,
        )


@dataclass
class Attachment:
    """Anexo de mensagem."""

    id: str
    filename: str
    content_type: str | None
    size_bytes: int
    url: str

    def size_kb(self) -> int:
        """Retorna tamanho em KB."""
        return self.size_bytes // 1024

    def is_image(self) -> bool:
        """Verifica se anexo é imagem."""
        if not self.content_type:
            return False
        return self.content_type.startswith("image/")


@dataclass
class Reaction:
    """Reação em mensagem."""

    emoji: str
    count: int = 1
