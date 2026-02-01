# -*- coding: utf-8 -*-
"""
Issue-related Domain Events.

Events emitted when GitHub issues are received, assigned, or labelled.
"""

from __future__ import annotations

from dataclasses import dataclass

from core.domain_events.domain_event import DomainEvent


@dataclass(frozen=True)
class IssueReceivedEvent(DomainEvent):
    """
    Emitted when a GitHub issue webhook is received.

    This is the initial event that triggers the entire workflow.
    """

    issue_number: int = 0
    repository: str = ""
    title: str = ""
    body: str = ""
    sender: str = ""
    action: str = ""  # e.g., "opened", "edited", "closed"
    labels: list[str] | None = None
    assignee: str | None = None

    def to_dict(self) -> dict[str, object]:
        """Convert to dictionary with issue-specific fields."""
        base = super().to_dict()
        base.update(
            {
                "issue_number": self.issue_number,
                "repository": self.repository,
                "title": self.title,
                "body": self.body,
                "sender": self.sender,
                "action": self.action,
                "labels": self.labels or [],
                "assignee": self.assignee or "",
            }
        )
        return base


@dataclass(frozen=True)
class IssueAssignedEvent(DomainEvent):
    """
    Emitted when an issue is assigned to someone.

    This can be used to trigger assignment-specific workflows,
    such as updating Trello cards with the assigned user.
    """

    issue_number: int = 0
    repository: str = ""
    assignee: str = ""
    sender: str = ""  # Who made the assignment

    def to_dict(self) -> dict[str, object]:
        """Convert to dictionary with issue-specific fields."""
        base = super().to_dict()
        base.update(
            {
                "issue_number": self.issue_number,
                "repository": self.repository,
                "assignee": self.assignee,
                "sender": self.sender,
            }
        )
        return base


@dataclass(frozen=True)
class IssueLabelledEvent(DomainEvent):
    """
    Emitted when labels are added to or removed from an issue.

    This event can be used to update Trello card categories
    or trigger label-based automation.
    """

    issue_number: int = 0
    repository: str = ""
    label: str = ""
    action: str = ""  # "added" or "removed"
    sender: str = ""

    def to_dict(self) -> dict[str, object]:
        """Convert to dictionary with issue-specific fields."""
        base = super().to_dict()
        base.update(
            {
                "issue_number": self.issue_number,
                "repository": self.repository,
                "label": self.label,
                "action": self.action,
                "sender": self.sender,
            }
        )
        return base


@dataclass(frozen=True)
class IssueClosedEvent(DomainEvent):
    """
    Emitted when an issue is closed.

    This event can be used to:
    - Archive or move Trello cards
    - Send completion notifications
    - Update metrics
    """

    issue_number: int = 0
    repository: str = ""
    sender: str = ""
    reason: str = ""  # e.g., "completed", "not planned"

    def to_dict(self) -> dict[str, object]:
        """Convert to dictionary with issue-specific fields."""
        base = super().to_dict()
        base.update(
            {
                "issue_number": self.issue_number,
                "repository": self.repository,
                "sender": self.sender,
                "reason": self.reason,
            }
        )
        return base


@dataclass(frozen=True)
class IssueCommentedEvent(DomainEvent):
    """
    Emitted when a comment is added to an issue.

    This event can be used for:
    - Syncing comments to Trello card comments
    - Triggering human-in-the-loop workflows
    - Sending notifications
    """

    issue_number: int = 0
    repository: str = ""
    comment_id: int = 0
    comment_body: str = ""
    sender: str = ""

    def to_dict(self) -> dict[str, object]:
        """Convert to dictionary with issue-specific fields."""
        base = super().to_dict()
        base.update(
            {
                "issue_number": self.issue_number,
                "repository": self.repository,
                "comment_id": self.comment_id,
                "comment_body": self.comment_body,
                "sender": self.sender,
            }
        )
        return base
