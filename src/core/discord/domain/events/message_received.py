# -*- coding: utf-8 -*-
"""
MessageReceivedEvent.

Evento de domínio emitido quando mensagem é recebida do Discord.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Self

from .base import DomainEvent


@dataclass(frozen=True)
class MessageReceivedEvent(DomainEvent):
    """
    Evento emitido quando mensagem é recebida do Discord.

    Contém dados completos da mensagem para processamento.
    """

    message_id: str = ""
    channel_id: str = ""
    author_id: str = ""
    author_name: str = ""
    content: str = ""
    has_attachments: bool = False
    attachment_count: int = 0
    is_dm: bool = False
    event_type: str = field(default="MessageReceivedEvent", init=False)

    def to_dict(self) -> dict:
        """Serializa evento."""
        data = super().to_dict()
        data.update(
            {
                "message_id": self.message_id,
                "channel_id": self.channel_id,
                "author_id": self.author_id,
                "author_name": self.author_name,
                "content": self.content,
                "has_attachments": self.has_attachments,
                "attachment_count": self.attachment_count,
                "is_dm": self.is_dm,
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
            author_id=data["author_id"],
            author_name=data["author_name"],
            content=data["content"],
            has_attachments=data.get("has_attachments", False),
            attachment_count=data.get("attachment_count", 0),
            is_dm=data.get("is_dm", False),
        )

    @classmethod
    def create(
        cls,
        message_id: str,
        channel_id: str,
        author_id: str,
        author_name: str,
        content: str,
        has_attachments: bool = False,
        attachment_count: int = 0,
        is_dm: bool = False,
    ) -> Self:
        """Factory method."""
        return cls(
            message_id=message_id,
            channel_id=channel_id,
            author_id=author_id,
            author_name=author_name,
            content=content,
            has_attachments=has_attachments,
            attachment_count=attachment_count,
            is_dm=is_dm,
        )
