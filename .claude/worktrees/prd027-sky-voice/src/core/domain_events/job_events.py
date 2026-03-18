# -*- coding: utf-8 -*-
"""
Job-related Domain Events.

Events emitted during job lifecycle: creation, start, completion, and failure.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from core.domain_events.domain_event import DomainEvent


@dataclass(frozen=True)
class JobCreatedEvent(DomainEvent):
    """
    Emitted when a new job is created and enqueued.

    This event signals that a job has been accepted into the system
    but has not yet started processing.
    """

    job_id: str = ""
    issue_number: int = 0
    repository: str = ""
    worktree_path: str = ""

    def to_dict(self) -> dict[str, object]:
        """Convert to dictionary with job-specific fields."""
        base = super().to_dict()
        base.update(
            {
                "job_id": self.job_id,
                "issue_number": self.issue_number,
                "repository": self.repository,
                "worktree_path": self.worktree_path,
            }
        )
        return base


@dataclass(frozen=True)
class JobStartedEvent(DomainEvent):
    """
    Emitted when a job starts processing.

    This event indicates that an agent has begun working on the job.
    """

    job_id: str = ""
    issue_number: int = 0
    repository: str = ""
    agent_type: str = ""  # e.g., "claude", "roo", "copilot"

    def to_dict(self) -> dict[str, object]:
        """Convert to dictionary with job-specific fields."""
        base = super().to_dict()
        base.update(
            {
                "job_id": self.job_id,
                "issue_number": self.issue_number,
                "repository": self.repository,
                "agent_type": self.agent_type,
            }
        )
        return base


@dataclass(frozen=True)
class JobCompletedEvent(DomainEvent):
    """
    Emitted when a job completes successfully.

    This event signals that the agent has finished processing
    and the worktree contains the generated changes.
    """

    job_id: str = ""
    issue_number: int = 0
    repository: str = ""
    files_modified: int = 0
    duration_seconds: float = 0.0
    worktree_path: str = ""

    def to_dict(self) -> dict[str, object]:
        """Convert to dictionary with job-specific fields."""
        base = super().to_dict()
        base.update(
            {
                "job_id": self.job_id,
                "issue_number": self.issue_number,
                "repository": self.repository,
                "files_modified": self.files_modified,
                "duration_seconds": self.duration_seconds,
                "worktree_path": self.worktree_path,
            }
        )
        return base


@dataclass(frozen=True)
class JobFailedEvent(DomainEvent):
    """
    Emitted when a job fails.

    This event indicates that the job encountered an error
    and could not complete successfully.
    """

    job_id: str = ""
    issue_number: int = 0
    repository: str = ""
    error_message: str = ""
    error_type: str = ""  # e.g., "TimeoutError", "ValueError"
    duration_seconds: float = 0.0
    retry_count: int = 0

    def to_dict(self) -> dict[str, object]:
        """Convert to dictionary with job-specific fields."""
        base = super().to_dict()
        base.update(
            {
                "job_id": self.job_id,
                "issue_number": self.issue_number,
                "repository": self.repository,
                "error_message": self.error_message,
                "error_type": self.error_type,
                "duration_seconds": self.duration_seconds,
                "retry_count": self.retry_count,
            }
        )
        return base


@dataclass(frozen=True)
class JobCommittedEvent(DomainEvent):
    """
    Emitted when changes from a job are committed to git.

    This event occurs after a successful job completion,
    when the generated changes are committed.
    """

    job_id: str = ""
    issue_number: int = 0
    repository: str = ""
    commit_hash: str = ""
    commit_message: str = ""

    def to_dict(self) -> dict[str, object]:
        """Convert to dictionary with job-specific fields."""
        base = super().to_dict()
        base.update(
            {
                "job_id": self.job_id,
                "issue_number": self.issue_number,
                "repository": self.repository,
                "commit_hash": self.commit_hash,
                "commit_message": self.commit_message,
            }
        )
        return base


@dataclass(frozen=True)
class JobPushedEvent(DomainEvent):
    """
    Emitted when committed changes are pushed to remote.

    This event occurs after git push, making the changes
    available on the remote repository.
    """

    job_id: str = ""
    issue_number: int = 0
    repository: str = ""
    branch_name: str = ""
    commit_hash: str = ""

    def to_dict(self) -> dict[str, object]:
        """Convert to dictionary with job-specific fields."""
        base = super().to_dict()
        base.update(
            {
                "job_id": self.job_id,
                "issue_number": self.issue_number,
                "repository": self.repository,
                "branch_name": self.branch_name,
                "commit_hash": self.commit_hash,
            }
        )
        return base


@dataclass(frozen=True)
class WorktreeRemovedEvent(DomainEvent):
    """
    Emitted when a worktree is cleaned up after job completion.

    This event signals that the temporary worktree has been removed
    and resources have been freed.
    """

    job_id: str = ""
    issue_number: int = 0
    worktree_path: str = ""

    def to_dict(self) -> dict[str, object]:
        """Convert to dictionary with job-specific fields."""
        base = super().to_dict()
        base.update(
            {
                "job_id": self.job_id,
                "issue_number": self.issue_number,
                "worktree_path": self.worktree_path,
            }
        )
        return base


@dataclass(frozen=True)
class PRCreatedEvent(DomainEvent):
    """
    Emitted when a Pull Request is created.

    PRD018 Fase 3: Evento emitido após criar PR via GitHub API.

    This event signals that a PR has been created for the job changes
    and is ready for review and merge.
    """

    pr_number: int = 0
    issue_number: int = 0
    repository: str = ""
    pr_url: str = ""
    pr_title: str = ""
    branch_name: str = ""

    def to_dict(self) -> dict[str, object]:
        """Convert to dictionary with PR-specific fields."""
        base = super().to_dict()
        base.update(
            {
                "pr_number": self.pr_number,
                "issue_number": self.issue_number,
                "repository": self.repository,
                "pr_url": self.pr_url,
                "pr_title": self.pr_title,
                "branch_name": self.branch_name,
            }
        )
        return base
