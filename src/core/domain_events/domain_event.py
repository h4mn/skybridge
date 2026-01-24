# -*- coding: utf-8 -*-
"""
Domain Event Base Class.

All domain events inherit from this base class. Domain Events represent
something that happened in the domain that other parts of the system
may be interested in.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any
from uuid import uuid4


@dataclass(frozen=True)
class DomainEvent:
    """
    Base class for all domain events.

    Attributes:
        event_id: Unique identifier for this event instance
        timestamp: When the event occurred (UTC)
        aggregate_id: ID of the aggregate that generated this event
        event_type: Type name of the event (e.g., "JobCreatedEvent")
        version: Event version for schema evolution (default: 1)
    """

    event_id: str = field(default_factory=lambda: str(uuid4()))
    timestamp: datetime = field(default_factory=datetime.utcnow)
    aggregate_id: str = ""
    event_type: str = ""
    version: int = 1

    def __post_init__(self) -> None:
        """Auto-set event_type from class name if not provided."""
        if not self.event_type:
            # Use object.__setattr__ because the dataclass is frozen
            object.__setattr__(self, "event_type", self.__class__.__name__)

    def to_dict(self) -> dict[str, Any]:
        """
        Convert event to dictionary for serialization.

        Returns:
            Dictionary representation of the event
        """
        return {
            "event_id": self.event_id,
            "timestamp": self.timestamp.isoformat(),
            "aggregate_id": self.aggregate_id,
            "event_type": self.event_type,
            "version": self.version,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "DomainEvent":
        """
        Create event instance from dictionary.

        Args:
            data: Dictionary containing event data

        Returns:
            DomainEvent instance
        """
        # Parse timestamp from ISO format
        timestamp_str = data.get("timestamp", "")
        timestamp = (
            datetime.fromisoformat(timestamp_str) if timestamp_str else datetime.utcnow()
        )

        return cls(
            event_id=data.get("event_id", str(uuid4())),
            timestamp=timestamp,
            aggregate_id=data.get("aggregate_id", ""),
            event_type=data.get("event_type", cls.__name__),
            version=data.get("version", 1),
        )


# Subclasses should extend this and add their own fields
@dataclass(frozen=True)
class JobCreatedEvent(DomainEvent):
    """Emitted when a new job is created."""

    job_id: str = ""
    issue_number: int = 0
    repository: str = ""

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary with job-specific fields."""
        base = super().to_dict()
        base.update(
            {
                "job_id": self.job_id,
                "issue_number": self.issue_number,
                "repository": self.repository,
            }
        )
        return base


@dataclass(frozen=True)
class IssueReceivedEvent(DomainEvent):
    """Emitted when a GitHub issue webhook is received."""

    issue_number: int = 0
    repository: str = ""
    title: str = ""
    sender: str = ""

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary with issue-specific fields."""
        base = super().to_dict()
        base.update(
            {
                "issue_number": self.issue_number,
                "repository": self.repository,
                "title": self.title,
                "sender": self.sender,
            }
        )
        return base


# Example usage in subclasses pattern:
# Subclasses should call super().to_dict() and extend it
