# -*- coding: utf-8 -*-
"""
Unit tests for Webhook Application Services.

Testa WebhookProcessor e WorktreeManager.
"""
from datetime import datetime
from pathlib import Path
from unittest.mock import Mock, AsyncMock, patch

import pytest

from core.webhooks.application.webhook_processor import (
    WebhookProcessor,
)
from core.webhooks.application.worktree_manager import (
    WorktreeManager,
)
from core.webhooks.domain import (
    WebhookEvent,
    WebhookJob,
    WebhookSource,
)
from kernel.contracts.result import Result


class TestWebhookProcessor:
    """Testa WebhookProcessor."""

    @pytest.fixture
    def job_queue(self):
        """Retorna fila mockada."""
        queue = Mock()
        queue.enqueue = AsyncMock(return_value="job-123")
        return queue

    @pytest.fixture
    def event_bus(self):
        """Retorna event bus mockado."""
        bus = Mock()
        bus.publish = AsyncMock()
        return bus

    @pytest.fixture
    def processor(self, job_queue, event_bus):
        """Retorna processor com fila e event bus mockados."""
        return WebhookProcessor(job_queue, event_bus)

    @pytest.mark.asyncio
    async def test_process_github_issue_success(self, processor):
        """Deve processar issue do GitHub com sucesso."""
        payload = {
            "issue": {"number": 225, "title": "Test issue"}
        }

        result = await processor.process_github_issue(
            payload=payload,
            event_type="issues.opened",
            signature="sha256=abc",
        )

        assert result.is_ok
        # job_id format: github-issue{issue_number}-{uuid}
        assert result.value.startswith("github-issue")

    @pytest.mark.asyncio
    async def test_process_github_issue_missing_issue_number(self, processor):
        """Deve falhar quando issue number não está no payload."""
        payload = {"issue": {"number": None}}

        result = await processor.process_github_issue(
            payload=payload,
            event_type="issues.opened",
            signature="sha256=abc",
        )

        assert result.is_err
        assert "Issue number não encontrado" in result.error

    @pytest.mark.asyncio
    async def test_process_github_issue_missing_issue_data(self, processor):
        """Deve falhar quando payload não tem issue."""
        payload = {}

        result = await processor.process_github_issue(
            payload=payload,
            event_type="issues.opened",
            signature="sha256=abc",
        )

        assert result.is_err
        assert "Payload não contém dados da issue" in result.error

    @pytest.mark.asyncio
    async def test_process_webhook_unsupported_source(self, processor):
        """Deve falhar para fonte não suportada."""
        result = await processor.process_webhook(
            source="discord",  # Não implementado ainda
            event_type="message.create",
            payload={},
        )

        assert result.is_err
        assert "não suportada" in result.error


class TestWorktreeManager:
    """Testa WorktreeManager."""

    @pytest.fixture
    def temp_path(self, tmp_path):
        """Retorna caminho temporário para testes."""
        return tmp_path / "worktrees"

    @pytest.fixture
    def manager(self, temp_path):
        """Retorna manager com path temporário."""
        temp_path.mkdir(exist_ok=True)
        return WorktreeManager(str(temp_path), base_branch="main")  # Test usa main por padrão

    @pytest.fixture
    def sample_job(self):
        """Retorna job de exemplo."""
        event = WebhookEvent(
            source=WebhookSource.GITHUB,
            event_type="issues.opened",
            event_id="12345",
            payload={"issue": {"number": 225}},
            received_at=datetime.utcnow(),
        )
        job = WebhookJob.create(event)
        return job

    def test_generate_worktree_name_for_job(self, sample_job):
        """Deve gerar nome correto para worktree."""
        from core.webhooks.domain import generate_worktree_name

        name = generate_worktree_name(sample_job)
        assert name.startswith("skybridge-github-225-")

    def test_generate_branch_name_for_job(self, sample_job):
        """Deve gerar nome correto para branch."""
        from core.webhooks.domain import generate_branch_name

        branch = generate_branch_name(sample_job)
        assert branch.startswith("webhook/github/issue/225/")

    @patch("subprocess.run")
    def test_create_worktree_success(self, mock_run, manager, sample_job):
        """Deve criar worktree com sucesso."""
        mock_run.return_value = Mock(
            returncode=0,
            stdout="",
            stderr=""
        )

        result = manager.create_worktree(sample_job)

        assert result.is_ok
        assert "skybridge-github-225-" in result.value
        assert sample_job.worktree_path == result.value
        assert sample_job.branch_name.startswith("webhook/github/issue/225/")

        # Verifica que subprocess.run foi chamado corretamente
        mock_run.assert_called_once()
        call_args = mock_run.call_args
        assert "git" in call_args[0][0]
        assert "worktree" in call_args[0][0]
        assert "add" in call_args[0][0]

    @patch("subprocess.run")
    def test_create_worktree_failure(self, mock_run, manager, sample_job):
        """Deve falhar quando git worktree add falha."""
        import subprocess
        mock_run.side_effect = subprocess.CalledProcessError(
            returncode=1,
            cmd="git worktree add",
            stderr="Error: worktree already exists"
        )

        result = manager.create_worktree(sample_job)

        assert result.is_err
        assert "Falha ao criar worktree" in result.error

    @patch("subprocess.run")
    def test_remove_worktree_success(self, mock_run, manager):
        """Deve remover worktree com sucesso."""
        mock_run.return_value = Mock(
            returncode=0,
            stdout="",
            stderr=""
        )

        result = manager.remove_worktree("/path/to/worktree")

        assert result.is_ok

    @patch("subprocess.run")
    def test_remove_worktree_failure(self, mock_run, manager):
        """Deve falhar quando remoção falha."""
        import subprocess
        mock_run.side_effect = subprocess.CalledProcessError(
            returncode=1,
            cmd="git worktree remove",
            stderr="Error: worktree not found"
        )

        result = manager.remove_worktree("/path/to/worktree")

        assert result.is_err
        assert "Falha ao remover worktree" in result.error

    @patch("subprocess.run")
    def test_list_worktrees(self, mock_run, manager):
        """Deve listar worktrees."""
        mock_run.return_value = Mock(
            returncode=0,
            stdout=(
                "worktree /path/to/branch1\n"
                "HEAD abc123\n"
                "branch refs/heads/branch1\n"
            ),
            stderr=""
        )

        worktrees = manager.list_worktrees()

        assert isinstance(worktrees, list)
        assert len(worktrees) > 0
