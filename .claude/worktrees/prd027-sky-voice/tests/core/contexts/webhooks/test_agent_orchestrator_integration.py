# -*- coding: utf-8 -*-
"""
Tests for JobOrchestrator integration with Agent Facade Pattern.

Estes testes verificam que o JobOrchestrator está corretamente integrado
com o ClaudeSDKAdapter (ADR021), incluindo:
- Uso do Agent Facade Pattern
- SDK oficial da Anthropic
- Compatibilidade com o fluxo existente
"""
from __future__ import annotations

import asyncio
from unittest.mock import Mock, AsyncMock, patch

import pytest
from datetime import datetime

from core.webhooks.domain import WebhookEvent, WebhookJob, WebhookSource
from core.webhooks.infrastructure.agents.claude_sdk_adapter import (
    ClaudeSDKAdapter,
)
from core.webhooks.infrastructure.agents.domain import (
    AgentState,
    AgentExecution,
    AgentResult,
)
from core.webhooks.application.job_orchestrator import (
    JobOrchestrator,
)
from infra.webhooks.adapters.in_memory_queue import (
    InMemoryJobQueue,
)
from kernel.contracts.result import Result


class TestJobOrchestratorAgentIntegration:
    """
    Testes de integração do JobOrchestrator com ClaudeSDKAdapter.

    Verifica que o Agent Facade Pattern está corretamente integrado
    ao fluxo de execução de jobs via SDK oficial (ADR021).
    """

    @pytest.fixture
    def job_queue(self):
        """Fila de jobs para testes."""
        return InMemoryJobQueue()

    @pytest.fixture
    def event_bus(self):
        """Event bus para testes."""
        from infra.domain_events.in_memory_event_bus import InMemoryEventBus
        return InMemoryEventBus()

    @pytest.fixture
    def mock_worktree_manager(self):
        """Mock do WorktreeManager."""
        manager = Mock()
        manager.create_worktree = Mock(return_value=Result.ok("/tmp/worktree-test"))
        return manager

    @pytest.fixture
    def sample_webhook_job(self):
        """
        Cria job de webhook para testes.

        PRD026: Usa card.moved.todo que executa agente,
        issues.opened não executa mais agente.
        """
        event = WebhookEvent(
            source=WebhookSource.TRELLO,
            event_type="card.moved.todo",
            event_id="123",
            payload={
                "action": {
                    "data": {
                        "card": {
                            "id": "card-123",
                            "name": "[#225] Test issue",
                            "desc": "Repository: testowner/testrepo",
                        },
                        "listAfter": {"name": "📋 A Fazer"},
                    }
                },
                "model": {"id": "board-1"},
            },
            received_at=datetime.utcnow(),
        )
        job = WebhookJob.create(event)
        job.worktree_path = "/tmp/worktree-test"
        job.branch_name = "test-branch"
        return job

    @pytest.mark.asyncio
    async def test_orchestrator_uses_claude_code_adapter(
        self, job_queue, event_bus, mock_worktree_manager, sample_webhook_job
    ):
        """
        Verifica que JobOrchestrator usa ClaudeSDKAdapter.

        Este teste valida que a refatorização para Agent Facade Pattern
        foi corretamente integrada ao JobOrchestrator.
        """
        from unittest.mock import patch

        # Cria orchestrator sem adapter mockado (usa SDK real)
        orchestrator = JobOrchestrator(
            job_queue=job_queue,
            worktree_manager=mock_worktree_manager,
            event_bus=event_bus,
        )

        # Verifica que o adapter e ClaudeSDKAdapter
        assert isinstance(orchestrator.agent_adapter, ClaudeSDKAdapter)
        assert orchestrator.agent_adapter.get_agent_type() == "claude-sdk"

    @pytest.mark.asyncio
    @patch("runtime.observability.snapshot.extractors.git_extractor.GitExtractor")
    async def test_orchestrator_processes_xml_commands_in_real_time(
        self, mock_git_extractor_class, job_queue, event_bus, mock_worktree_manager
    ):
        """
        Teste E2E: JobOrchestrator integra com SDK.

        Este teste valida que o JobOrchestrator funciona corretamente
        com o ClaudeSDKAdapter assincrono.
        """
        # Mock GitExtractor
        mock_git_extractor = Mock()
        mock_git_extractor.capture.return_value = Mock(
            metadata=Mock(model_dump=lambda: {}),
            stats=Mock(model_dump=lambda: {}),
            structure={},
        )
        mock_git_extractor_class.return_value = mock_git_extractor

        # Cria job simples
        event = WebhookEvent(
            source=WebhookSource.GITHUB,
            event_type="issues.opened",
            event_id="123",
            payload={
                "issue": {
                    "number": 225,
                    "title": "Test issue",
                    "body": "Test body",
                },
                "repository": {
                    "owner": {"login": "testowner"},
                    "name": "testrepo",
                },
            },
            received_at=datetime.utcnow(),
        )
        job = WebhookJob.create(event)
        job.worktree_path = "/tmp/worktree-test"
        job.branch_name = "test-branch"

        # Cria orchestrator
        orchestrator = JobOrchestrator(
            job_queue=job_queue,
            worktree_manager=mock_worktree_manager,
            event_bus=event_bus,
        )

        # Enfileira e executa job (mockado para nao rodar agent real)
        await job_queue.enqueue(job)

        # Patch o spawn do SDK para mockar execução
        async def mock_spawn(*args, **kwargs):
            # Simula um delay do agent real
            await asyncio.sleep(0.001)
            return Result.ok(AgentExecution(
                agent_type="claude-sdk",
                job_id=job.job_id,
                worktree_path=job.worktree_path,
                skill="resolve-issue",
                state=AgentState.COMPLETED,
                result=AgentResult(
                    success=True,
                    changes_made=True,
                    files_created=[],
                    files_modified=[],
                    files_deleted=[],
                    commit_hash="abc123",
                    pr_url=None,
                    message="Done",
                    issue_title="Test",
                    output_message="Fixed",
                    thinkings=[],
                ),
            ))

        with patch.object(orchestrator.agent_adapter, 'spawn', side_effect=mock_spawn):
            result = await orchestrator.execute_job(job.job_id)

        # Verifica que job completou
        assert result.is_ok

    @pytest.mark.asyncio
    async def test_orchestrator_includes_skybridge_context(
        self, job_queue, event_bus, mock_worktree_manager, sample_webhook_job
    ):
        """
        Verifica que JobOrchestrator passa skybridge_context correto.

        O skybridge_context deve incluir:
        - worktree_path
        - branch_name
        - repo_name
        """
        from unittest.mock import patch, AsyncMock

        # Cria orchestrator sem adapter mockado (usa SDK real)
        orchestrator = JobOrchestrator(
            job_queue=job_queue,
            worktree_manager=mock_worktree_manager,
            event_bus=event_bus,
        )

        # Enfileira job
        await job_queue.enqueue(sample_webhook_job)

        # Mock o spawn para capturar os argumentos
        captured_args = {}

        async def mock_spawn(job, skill, worktree_path, skybridge_context):
            captured_args["skybridge_context"] = skybridge_context
            # Simula um delay do agent real
            await asyncio.sleep(0.001)
            return Result.ok(AgentExecution(
                agent_type="claude-sdk",
                job_id=job.job_id,
                worktree_path=worktree_path,
                skill=skill,
                state=AgentState.COMPLETED,
                result=AgentResult(
                    success=True,
                    changes_made=False,
                    files_created=[],
                    files_modified=[],
                    files_deleted=[],
                    commit_hash=None,
                    pr_url=None,
                    message="No changes",
                    issue_title="Test",
                    output_message="Output",
                    thinkings=[],
                ),
            ))

        with patch.object(orchestrator.agent_adapter, 'spawn', side_effect=mock_spawn):
            with patch("runtime.observability.snapshot.extractors.git_extractor.GitExtractor") as mock_extractor_class:
                mock_extractor = Mock()
                mock_extractor.capture.return_value = Mock(
                    metadata=Mock(model_dump=lambda: {}),
                    stats=Mock(model_dump=lambda: {}),
                    structure={},
                )
                mock_extractor_class.return_value = mock_extractor

                result = await orchestrator.execute_job(sample_webhook_job.job_id)

        # Verifica que spawn foi chamado com contexto correto
        skybridge_context = captured_args["skybridge_context"]

        assert "worktree_path" in skybridge_context
        assert "branch_name" in skybridge_context
        assert "repo_name" in skybridge_context
        # PRD026: Eventos Trello não têm repository info, usa "unknown/unknown"
        assert skybridge_context["repo_name"] in ["testowner/testrepo", "unknown/unknown"]

        assert result.is_ok

    @pytest.mark.asyncio
    async def test_orchestrator_handles_agent_errors_gracefully(
        self, job_queue, event_bus, mock_worktree_manager, sample_webhook_job
    ):
        """
        Verifica que JobOrchestrator lida com erros do agente gracefulmente.
        """
        from unittest.mock import patch

        # Cria orchestrator sem adapter mockado (usa SDK real)
        orchestrator = JobOrchestrator(
            job_queue=job_queue,
            worktree_manager=mock_worktree_manager,
            event_bus=event_bus,
        )

        # Enfileira job
        await job_queue.enqueue(sample_webhook_job)

        # Mock o spawn para retornar erro
        async def mock_spawn_error(*args, **kwargs):
            # Simula um delay do agent real
            await asyncio.sleep(0.001)
            return Result.err("Timeout na execução do agente")

        with patch.object(orchestrator.agent_adapter, 'spawn', side_effect=mock_spawn_error):
            with patch("runtime.observability.snapshot.extractors.git_extractor.GitExtractor") as mock_extractor_class:
                mock_extractor = Mock()
                mock_extractor.capture.return_value = Mock(
                    metadata=Mock(model_dump=lambda: {}),
                    stats=Mock(model_dump=lambda: {}),
                    structure={},
                )
                mock_extractor_class.return_value = mock_extractor

                result = await orchestrator.execute_job(sample_webhook_job.job_id)

        # Verifica que erro foi propagado corretamente
        assert result.is_err
        assert "Timeout" in result.error
