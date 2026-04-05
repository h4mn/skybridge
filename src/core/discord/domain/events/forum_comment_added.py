# -*- coding: utf-8 -*-
"""
ForumCommentAddedEvent.

Evento de domínio emitido quando um comentário é adicionado a um post de fórum Discord.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Self

from .base import DomainEvent


@dataclass(frozen=True)
class ForumCommentAddedEvent(DomainEvent):
    """
    Evento emitido quando um comentário é adicionado a um post de fórum.

    No Discord, comentários são mensagens enviadas dentro de uma Thread
    que pertence a um ForumChannel.
    """

    forum_channel_id: str = ""
    forum_post_id: str = ""
    comment_id: str = ""
    author_id: str = ""
    author_name: str = ""
    content: str = ""
    has_attachments: bool = False
    attachment_count: int = 0
    event_type: str = field(default="ForumCommentAddedEvent", init=False)

    def to_dict(self) -> dict:
        """Serializa evento."""
        data = super().to_dict()
        data.update(
            {
                "forum_channel_id": self.forum_channel_id,
                "forum_post_id": self.forum_post_id,
                "comment_id": self.comment_id,
                "author_id": self.author_id,
                "author_name": self.author_name,
                "content": self.content,
                "has_attachments": self.has_attachments,
                "attachment_count": self.attachment_count,
            }
        )
        return data

    @classmethod
    def from_dict(cls, data: dict) -> Self:
        """Deserializa evento de dicionário."""
        return cls(
            event_id=data["event_id"],
            occurred_at=datetime.fromisoformat(data["occurred_at"]),
            forum_channel_id=data["forum_channel_id"],
            forum_post_id=data["forum_post_id"],
            comment_id=data["comment_id"],
            author_id=data["author_id"],
            author_name=data["author_name"],
            content=data["content"],
            has_attachments=data.get("has_attachments", False),
            attachment_count=data.get("attachment_count", 0),
        )

    @classmethod
    def create(
        cls,
        forum_channel_id: str,
        forum_post_id: str,
        comment_id: str,
        author_id: str,
        author_name: str,
        content: str = "",
        has_attachments: bool = False,
        attachment_count: int = 0,
    ) -> Self:
        """Factory method."""
        return cls(
            forum_channel_id=forum_channel_id,
            forum_post_id=forum_post_id,
            comment_id=comment_id,
            author_id=author_id,
            author_name=author_name,
            content=content,
            has_attachments=has_attachments,
            attachment_count=attachment_count,
        )
