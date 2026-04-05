# -*- coding: utf-8 -*-
"""
DTOs para Fóruns do Discord.

DOC: DDD Migration - Presentation Layer DTOs
"""

from dataclasses import dataclass
from typing import Optional
from datetime import datetime


@dataclass
class ForumTagDTO:
    """Tag de fórum Discord."""
    id: str
    name: str
    emoji: Optional[str]
    moderated: bool


@dataclass
class ForumPostDTO:
    """Post de fórum Discord."""
    id: str
    title: str
    content: str
    author_id: str
    author_name: str
    tags: list[ForumTagDTO]
    created_at: datetime
    status: str  # "open", "closed", "archived"


@dataclass
class ForumCommentDTO:
    """Comentário de post de fórum."""
    id: str
    content: str
    author_id: str
    author_name: str
    created_at: datetime


@dataclass
class ForumSettingsDTO:
    """Configurações de fórum."""
    name: str
    default_tags: list[str]  # tag_ids
    default_sort_order: str  # "latest_activity", "creation_date"
    layout: str  # "classic", "list"
