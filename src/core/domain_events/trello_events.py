# -*- coding: utf-8 -*-
"""
Trello-related Domain Events.

Events emitted when Trello cards are created, updated, or moved.
These events are emitted by TrelloEventListener and can be
subscribed to by other components that need to react to Trello changes.
"""

from __future__ import annotations

from dataclasses import dataclass

from core.domain_events.domain_event import DomainEvent


@dataclass(frozen=True)
class TrelloCardCreatedEvent(DomainEvent):
    """
    Emitted when a new Trello card is created.

    This typically happens when a GitHub issue webhook is received
    and a corresponding Trello card is created.
    """

    card_id: str = ""
    card_name: str = ""
    board_id: str = ""
    board_name: str = ""
    list_id: str = ""
    list_name: str = ""
    issue_number: int = 0  # Associated GitHub issue
    repository: str = ""

    def to_dict(self) -> dict[str, object]:
        """Convert to dictionary with Trello-specific fields."""
        base = super().to_dict()
        base.update(
            {
                "card_id": self.card_id,
                "card_name": self.card_name,
                "board_id": self.board_id,
                "board_name": self.board_name,
                "list_id": self.list_id,
                "list_name": self.list_name,
                "issue_number": self.issue_number,
                "repository": self.repository,
            }
        )
        return base


@dataclass(frozen=True)
class TrelloCardUpdatedEvent(DomainEvent):
    """
    Emitted when a Trello card is updated.

    Updates include:
    - Name/description changes
    - Due date changes
    - Member assignments
    - Label changes
    """

    card_id: str = ""
    card_name: str = ""
    board_id: str = ""
    list_id: str = ""
    changes: str = ""  # JSON string describing what changed

    def to_dict(self) -> dict[str, object]:
        """Convert to dictionary with Trello-specific fields."""
        base = super().to_dict()
        base.update(
            {
                "card_id": self.card_id,
                "card_name": self.card_name,
                "board_id": self.board_id,
                "list_id": self.list_id,
                "changes": self.changes,
            }
        )
        return base


@dataclass(frozen=True)
class TrelloCardMovedEvent(DomainEvent):
    """
    Emitted when a Trello card is moved to a different list.

    This is a key event for workflow automation:
    - Moving to "Done" can trigger notifications
    - Moving to "In Progress" can start timers
    - Moving to "Blocked" can alert team members
    """

    card_id: str = ""
    card_name: str = ""
    board_id: str = ""
    from_list_id: str = ""
    from_list_name: str = ""
    to_list_id: str = ""
    to_list_name: str = ""

    def to_dict(self) -> dict[str, object]:
        """Convert to dictionary with Trello-specific fields."""
        base = super().to_dict()
        base.update(
            {
                "card_id": self.card_id,
                "card_name": self.card_name,
                "board_id": self.board_id,
                "from_list_id": self.from_list_id,
                "from_list_name": self.from_list_name,
                "to_list_id": self.to_list_id,
                "to_list_name": self.to_list_name,
            }
        )
        return base


@dataclass(frozen=True)
class TrelloCardArchivedEvent(DomainEvent):
    """
    Emitted when a Trello card is archived.

    This can happen when:
    - A GitHub issue is closed
    - Manual archival
    - Card is no longer relevant
    """

    card_id: str = ""
    card_name: str = ""
    board_id: str = ""
    reason: str = ""  # e.g., "issue_closed", "manual"

    def to_dict(self) -> dict[str, object]:
        """Convert to dictionary with Trello-specific fields."""
        base = super().to_dict()
        base.update(
            {
                "card_id": self.card_id,
                "card_name": self.card_name,
                "board_id": self.board_id,
                "reason": self.reason,
            }
        )
        return base


@dataclass(frozen=True)
class TrelloCommentAddedEvent(DomainEvent):
    """
    Emitted when a comment is added to a Trello card.

    This can be used to:
    - Sync comments back to GitHub
    - Send notifications
    - Update activity logs
    """

    card_id: str = ""
    card_name: str = ""
    comment_id: str = ""
    comment_text: str = ""
    author: str = ""

    def to_dict(self) -> dict[str, object]:
        """Convert to dictionary with Trello-specific fields."""
        base = super().to_dict()
        base.update(
            {
                "card_id": self.card_id,
                "card_name": self.card_name,
                "comment_id": self.comment_id,
                "comment_text": self.comment_text,
                "author": self.author,
            }
        )
        return base
