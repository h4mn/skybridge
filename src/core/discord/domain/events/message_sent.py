# -*- coding: utf-8 -*-
"""
MessageSentEvent.

Evento de domínio emitido quando mensagem é enviada com sucesso.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Self

from .base import DomainEvent


@dataclass(frozen=True)
class MessageSentEvent(DomainEvent):
    """
    Evento emitido quando mensagem é enviada com sucesso.

    Confirma entrega de mensagem ao Discord.
    """

    message_id: str = ""
    channel_id: str = ""
    content_length: int = 0
    chunk_count: int = 1
    had_attachments: bool = False
    reply_to: str | None = None
    event_type: str = field(default="MessageSentEvent", init=False)

    def to_dict(self) -> dict:
        """Serializa evento."""
        data = super().to_dict()
        data.update(
            {
                "message_id": self.message_id,
                "channel_id": self.channel_id,
                "content_length": self.content_length,
                "chunk_count": self.chunk_count,
                "had_attachments": self.had_attachments,
                "reply_to": self.reply_to,
            }
        )
        return data

    @classmethod
    def from_dict(cls, data: dict) -> Self:
        """Deserializa evento de dicionário."""
        return cls(
            event_id=data["event_id"],
            occurred_at=datetime.fromisoformat(data["occurred_at"]),
            message_id=data["message_id"],
            channel_id=data["channel_id"],
            content_length=data.get("content_length", 0),
            chunk_count=data.get("chunk_count", 1),
            had_attachments=data.get("had_attachments", False),
            reply_to=data.get("reply_to"),
        )

    @classmethod
    def create(
        cls,
        message_id: str,
        channel_id: str,
        content_length: int = 0,
        chunk_count: int = 1,
        had_attachments: bool = False,
        reply_to: str | None = None,
    ) -> Self:
        """Factory method."""
        return cls(
            message_id=message_id,
            channel_id=channel_id,
            content_length=content_length,
            chunk_count=chunk_count,
            had_attachments=had_attachments,
            reply_to=reply_to,
        )
