# -*- coding: utf-8 -*-
"""
ForumPostCreatedEvent.

Evento de domínio emitido quando um post (thread) é criado em um fórum Discord.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Self

from .base import DomainEvent


@dataclass(frozen=True)
class ForumPostCreatedEvent(DomainEvent):
    """
    Evento emitido quando um post é criado em fórum Discord.

    Um post no Discord é representado como uma Thread dentro de um ForumChannel.
    """

    forum_channel_id: str = ""
    forum_post_id: str = ""
    author_id: str = ""
    author_name: str = ""
    title: str = ""
    content: str = ""
    tags: list[str] = field(default_factory=list)
    event_type: str = field(default="ForumPostCreatedEvent", init=False)

    def to_dict(self) -> dict:
        """Serializa evento."""
        data = super().to_dict()
        data.update(
            {
                "forum_channel_id": self.forum_channel_id,
                "forum_post_id": self.forum_post_id,
                "author_id": self.author_id,
                "author_name": self.author_name,
                "title": self.title,
                "content": self.content,
                "tags": self.tags,
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
            author_id=data["author_id"],
            author_name=data["author_name"],
            title=data["title"],
            content=data["content"],
            tags=data.get("tags", []),
        )

    @classmethod
    def create(
        cls,
        forum_channel_id: str,
        forum_post_id: str,
        author_id: str,
        author_name: str,
        title: str = "",
        content: str = "",
        tags: list[str] | None = None,
    ) -> Self:
        """Factory method."""
        return cls(
            forum_channel_id=forum_channel_id,
            forum_post_id=forum_post_id,
            author_id=author_id,
            author_name=author_name,
            title=title,
            content=content,
            tags=tags or [],
        )
