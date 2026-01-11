# -*- coding: utf-8 -*-
"""
Unit tests for Webhook Domain Layer.

Testa entidades de domínio: WebhookEvent, WebhookJob, JobStatus, WebhookSource.
"""
from datetime import datetime

import pytest

from skybridge.core.contexts.webhooks.domain import (
    WebhookEvent,
    WebhookJob,
    WebhookSource,
    JobStatus,
    generate_worktree_name,
    generate_branch_name,
)


class TestWebhookSource:
    """Testa enum WebhookSource."""

    def test_github_source_exists(self):
        """GitHub source deve existir."""
        assert WebhookSource.GITHUB.value == "github"

    def test_source_values(self):
        """Todas as fontes devem ter valores corretos."""
        assert WebhookSource.GITHUB.value == "github"


class TestJobStatus:
    """Testa enum JobStatus."""

    def test_all_statuses_defined(self):
        """Todos os status devem estar definidos."""
        assert JobStatus.PENDING.value == "pending"
        assert JobStatus.PROCESSING.value == "processing"
        assert JobStatus.COMPLETED.value == "completed"
        assert JobStatus.FAILED.value == "failed"


class TestWebhookEvent:
    """Testa entidade WebhookEvent."""

    def test_create_github_event(self):
        """Deve criar evento de webhook do GitHub."""
        event = WebhookEvent(
            source=WebhookSource.GITHUB,
            event_type="issues.opened",
            event_id="12345",
            payload={"issue": {"number": 225}},
            received_at=datetime.utcnow(),
            signature="sha256=abc123",
        )

        assert event.source == WebhookSource.GITHUB
        assert event.event_type == "issues.opened"
        assert event.event_id == "12345"

    def test_get_issue_number_from_github_issue(self):
        """Deve extrair número da issue de evento do GitHub."""
        event = WebhookEvent(
            source=WebhookSource.GITHUB,
            event_type="issues.opened",
            event_id="12345",
            payload={"issue": {"number": 225}},
            received_at=datetime.utcnow(),
        )

        assert event.get_issue_number() == 225

    def test_get_issue_number_returns_none_for_non_issue(self):
        """Deve retornar None para eventos não relacionados a issue."""
        event = WebhookEvent(
            source=WebhookSource.GITHUB,
            event_type="push",
            event_id="12345",
            payload={},
            received_at=datetime.utcnow(),
        )

        assert event.get_issue_number() is None

    def test_get_repository(self):
        """Deve extrair informações do repositório."""
        event = WebhookEvent(
            source=WebhookSource.GITHUB,
            event_type="issues.opened",
            event_id="12345",
            payload={
                "repository": {
                    "owner": {"login": "h4mn"},
                    "name": "skybridge"
                }
            },
            received_at=datetime.utcnow(),
        )

        owner, name = event.get_repository()
        assert owner == "h4mn"
        assert name == "skybridge"

    def test_get_repository_returns_none_when_missing(self):
        """Deve retornar None quando repository não está no payload."""
        event = WebhookEvent(
            source=WebhookSource.GITHUB,
            event_type="issues.opened",
            event_id="12345",
            payload={},
            received_at=datetime.utcnow(),
        )

        assert event.get_repository() is None


class TestWebhookJob:
    """Testa entidade WebhookJob."""

    def test_create_job_from_event(self):
        """Deve criar job a partir de evento."""
        event = WebhookEvent(
            source=WebhookSource.GITHUB,
            event_type="issues.opened",
            event_id="12345",
            payload={"issue": {"number": 225}},
            received_at=datetime.utcnow(),
        )

        job = WebhookJob.create(event)

        assert job.event == event
        assert job.status == JobStatus.PENDING
        assert job.issue_number == 225
        assert job.worktree_path is None

    def test_job_can_cleanup_when_completed(self):
        """Job pode ser limpo quando completado."""
        job = WebhookJob(
            job_id="test-123",
            event=None,  # type: ignore
            status=JobStatus.COMPLETED,
        )

        assert job.can_cleanup() is True

    def test_job_cannot_cleanup_when_processing(self):
        """Job não pode ser limpo quando em processamento."""
        job = WebhookJob(
            job_id="test-123",
            event=None,  # type: ignore
            status=JobStatus.PROCESSING,
        )

        assert job.can_cleanup() is False

    def test_mark_processing(self):
        """Deve marcar job como em processamento."""
        job = WebhookJob(
            job_id="test-123",
            event=None,  # type: ignore
            status=JobStatus.PENDING,
        )

        job.mark_processing()

        assert job.status == JobStatus.PROCESSING
        assert job.started_at is not None

    def test_mark_completed(self):
        """Deve marcar job como completado."""
        job = WebhookJob(
            job_id="test-123",
            event=None,  # type: ignore
            status=JobStatus.PROCESSING,
        )

        job.mark_completed()

        assert job.status == JobStatus.COMPLETED
        assert job.completed_at is not None

    def test_mark_failed(self):
        """Deve marcar job como falhou."""
        job = WebhookJob(
            job_id="test-123",
            event=None,  # type: ignore
            status=JobStatus.PROCESSING,
        )

        job.mark_failed("Test error")

        assert job.status == JobStatus.FAILED
        assert job.error_message == "Test error"
        assert job.completed_at is not None


class TestWorktreeNameGeneration:
    """Testa geração de nomes de worktree e branch."""

    def test_generate_worktree_name_for_issue(self):
        """Deve gerar nome de worktree para issue do GitHub."""
        event = WebhookEvent(
            source=WebhookSource.GITHUB,
            event_type="issues.opened",
            event_id="12345",
            payload={"issue": {"number": 225}},
            received_at=datetime.utcnow(),
        )
        job = WebhookJob(
            job_id="github-issues.opened-abc12345",
            event=event,
            status=JobStatus.PENDING,
            issue_number=225,
        )

        name = generate_worktree_name(job)
        assert name.startswith("skybridge-github-225-")
        assert "abc12345" in name

    def test_generate_branch_name_for_issue(self):
        """Deve gerar nome de branch para issue do GitHub."""
        event = WebhookEvent(
            source=WebhookSource.GITHUB,
            event_type="issues.opened",
            event_id="12345",
            payload={"issue": {"number": 225}},
            received_at=datetime.utcnow(),
        )
        job = WebhookJob(
            job_id="github-issues.opened-abc12345",
            event=event,
            status=JobStatus.PENDING,
            issue_number=225,
        )

        branch = generate_branch_name(job)
        assert branch.startswith("webhook/github/issue/225/")
        assert "abc12345" in branch

    def test_generate_branch_name_without_issue(self):
        """Deve gerar nome de branch usando job_id quando não há issue."""
        event = WebhookEvent(
            source=WebhookSource.GITHUB,
            event_type="issues.opened",
            event_id="12345",
            payload={},
            received_at=datetime.utcnow(),
        )
        job = WebhookJob(
            job_id="test-123",
            event=event,
            status=JobStatus.PENDING,
            issue_number=None,
        )

        branch = generate_branch_name(job)
        assert branch == "webhook/github/test-123"
