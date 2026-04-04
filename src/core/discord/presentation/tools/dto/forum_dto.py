# -*- coding: utf-8 -*-
"""
DTOs para operações de Forum Discord.

DOC: Discord Forum MCP - Data Transfer Objects
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, List


@dataclass
class ForumTagDTO:
    """DTO para Tag de Forum."""
    id: str
    name: str
    emoji: Optional[str] = None
    moderated: bool = False

    @classmethod
    def from_discord_tag(cls, tag) -> ForumTagDTO:
        """Cria DTO a partir de objeto discord.ForumTag."""
        return cls(
            id=str(tag.id),
            name=tag.name,
            emoji=tag.emoji if hasattr(tag, 'emoji') else None,
            moderated=tag.moderated if hasattr(tag, 'moderated') else False,
        )


@dataclass
class ForumSettingsDTO:
    """DTO para configurações de Forum."""
    layout: str = "classic"  # "classic" ou "list"
    default_sort_order: Optional[int] = None
    default_thread_rate_limit: Optional[int] = None
    default_reaction_emoji: Optional[str] = None


@dataclass
class ForumPostDTO:
    """DTO para Post de Forum."""
    id: str
    title: str
    content: str
    author_id: str
    author_name: str
    channel_id: str
    tags: List[ForumTagDTO] = field(default_factory=list)
    created_at: Optional[datetime] = None
    edited_at: Optional[datetime] = None
    archived: bool = False
    locked: bool = False
    pinned: bool = False
    total_messages: int = 1  # Inclui o post principal

    @classmethod
    def from_discord_thread(cls, thread) -> ForumPostDTO:
        """Cria DTO a partir de objeto discord.Thread."""
        tags = []
        if hasattr(thread, 'applied_tags'):
            tags = [ForumTagDTO.from_discord_tag(tag) for tag in thread.applied_tags]

        return cls(
            id=str(thread.id),
            title=thread.name,
            content=thread.content if hasattr(thread, 'content') else "",
            author_id=str(thread.owner_id) if hasattr(thread, 'owner_id') else "",
            author_name=thread.owner.name if hasattr(thread, 'owner') and hasattr(thread.owner, 'name') else "Unknown",
            channel_id=str(thread.parent_id) if hasattr(thread, 'parent_id') else "",
            tags=tags,
            created_at=thread.created_at,
            edited_at=thread.edited_at if hasattr(thread, 'edited_at') else None,
            archived=thread.archived,
            locked=thread.locked,
            pinned=thread.pinned if hasattr(thread, 'pinned') else False,
            total_messages=thread.message_count if hasattr(thread, 'message_count') else 1,
        )


@dataclass
class ForumCommentDTO:
    """DTO para Comentário em Post de Forum."""
    id: str
    content: str
    author_id: str
    author_name: str
    post_id: str
    created_at: Optional[datetime] = None
    edited_at: Optional[datetime] = None

    @classmethod
    def from_discord_message(cls, message, post_id: str) -> ForumCommentDTO:
        """Cria DTO a partir de objeto discord.Message."""
        return cls(
            id=str(message.id),
            content=message.content,
            author_id=str(message.author.id),
            author_name=message.author.name if hasattr(message.author, 'name') else "Unknown",
            post_id=post_id,
            created_at=message.created_at,
            edited_at=message.edited_at,
        )
