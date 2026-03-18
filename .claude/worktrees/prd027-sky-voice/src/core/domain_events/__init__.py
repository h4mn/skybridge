# -*- coding: utf-8 -*-
"""
Domain Events Module.

This module implements the Domain Events pattern for decoupling components.
Events are published when something happens in the domain, and listeners
subscribe to events they care about.
"""

# Base classes
from core.domain_events.domain_event import DomainEvent
from core.domain_events.event_bus import (
    EventBus,
    EventHandler,
    EventBusError,
    EventPublishError,
    SubscriptionNotFoundError,
)

# Job events
from core.domain_events.job_events import (
    JobCreatedEvent,
    JobStartedEvent,
    JobCompletedEvent,
    JobFailedEvent,
    JobCommittedEvent,
    JobPushedEvent,
    WorktreeRemovedEvent,
)

# Issue events
from core.domain_events.issue_events import (
    IssueReceivedEvent,
    IssueAssignedEvent,
    IssueLabelledEvent,
    IssueClosedEvent,
    IssueCommentedEvent,
)

# Trello events
from core.domain_events.trello_events import (
    TrelloCardCreatedEvent,
    TrelloCardUpdatedEvent,
    TrelloCardMovedEvent,
    TrelloCardArchivedEvent,
    TrelloCommentAddedEvent,
)

__all__ = [
    # Base
    "DomainEvent",
    "EventBus",
    "EventHandler",
    "EventBusError",
    "EventPublishError",
    "SubscriptionNotFoundError",
    # Job events
    "JobCreatedEvent",
    "JobStartedEvent",
    "JobCompletedEvent",
    "JobFailedEvent",
    "JobCommittedEvent",
    "JobPushedEvent",
    "WorktreeRemovedEvent",
    # Issue events
    "IssueReceivedEvent",
    "IssueAssignedEvent",
    "IssueLabelledEvent",
    "IssueClosedEvent",
    "IssueCommentedEvent",
    # Trello events
    "TrelloCardCreatedEvent",
    "TrelloCardUpdatedEvent",
    "TrelloCardMovedEvent",
    "TrelloCardArchivedEvent",
    "TrelloCommentAddedEvent",
]
