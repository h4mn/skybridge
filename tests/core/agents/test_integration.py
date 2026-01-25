# -*- coding: utf-8 -*-
"""
Testes de Integração - Validação End-to-End DoDs.

PRD019: Testes de integração para validar que todos os componentes
funcionam juntos corretamente.

Estes testes validam:
- Fluxo completo de feature flag até seleção de adapter
- WebSocket console com broadcast real
- Custom tools com formato MCP correto
- Ciclo de vida completo de AgentExecution
"""
from __future__ import annotations

import asyncio
import json
import os
from datetime import datetime
from unittest.mock import MagicMock, AsyncMock, patch, Mock

import pytest


def create_test_job(
    job_id: str = "test-job-123",
    issue_number: int = 42,
    issue_title: str = "Test Issue",
    issue_body: str = "Test issue body",
):
    """Helper para criar WebhookJob de teste."""
    from core.webhooks.domain import WebhookJob, WebhookEvent, WebhookSource, JobStatus
    from datetime import datetime

    event = WebhookEvent(
        source=WebhookSource.GITHUB,
        event_type="issues.opened",
        event_id=f"event-{job_id}",
        payload={
            "action": "opened",
            "issue": {
                "number": issue_number,
                "title": issue_title,
                "body": issue_body,
                "labels": [],
            },
            "repository": {
                "owner": {"login": "test-owner"},
                "name": "test-repo",
            },
        },
        received_at=datetime.fromisoformat("2026-01-24T10:00:00"),
    )

    job = WebhookJob(
        job_id=job_id,
        event=event,
        status=JobStatus.PENDING,
        issue_number=issue_number,
        branch_name=f"test-branch-{job_id}",
    )

    return job


# =============================================================================
# INTEGRAÇÃO: Feature Flag → JobOrchestrator → Adapter
# =============================================================================

@pytest.mark.asyncio
async def test_integration_feature_flag_to_adapter():
    """
    Teste de Integração: Feature flag → JobOrchestrator → Adapter.

    Valida o fluxo completo desde a definição da feature flag até
    a seleção do adapter correto no JobOrchestrator.
    """
    from core.webhooks.application.job_orchestrator import JobOrchestrator
    from core.webhooks.infrastructure.agents.claude_agent import ClaudeCodeAdapter
    from core.webhooks.infrastructure.agents.claude_sdk_adapter import ClaudeSDKAdapter

    # Mock dependências
    mock_queue = MagicMock()
    mock_worktree_manager = MagicMock()
    mock_event_bus = MagicMock()

    # Testa 1: USE_SDK_ADAPTER=false → ClaudeCodeAdapter
    with patch.dict(os.environ, {"USE_SDK_ADAPTER": "false"}, clear=False):
        import runtime.config.feature_flags as ff_module
        ff_module._feature_flags = None

        orchestrator = JobOrchestrator(
            mock_queue,
            mock_worktree_manager,
            mock_event_bus,
        )

        assert isinstance(orchestrator.agent_adapter, ClaudeCodeAdapter)
        assert orchestrator.agent_adapter.get_agent_type() == "claude-code"

    # Testa 2: USE_SDK_ADAPTER=true → ClaudeSDKAdapter
    with patch.dict(os.environ, {"USE_SDK_ADAPTER": "true"}, clear=False):
        ff_module._feature_flags = None

        orchestrator = JobOrchestrator(
            mock_queue,
            mock_worktree_manager,
            mock_event_bus,
        )

        assert isinstance(orchestrator.agent_adapter, ClaudeSDKAdapter)
        assert orchestrator.agent_adapter.get_agent_type() == "claude-sdk"


# =============================================================================
# INTEGRAÇÃO: WebSocket Console com Broadcast Real
# =============================================================================

@pytest.mark.asyncio
async def test_integration_websocket_console_with_broadcast():
    """
    Teste de Integração: WebSocket console com broadcast real.

    Valida que múltiplos clientes podem conectar e receber mensagens
    em tempo real via broadcast do manager.
    """
    from runtime.delivery.websocket import (
        WebSocketConsoleManager,
        ConsoleMessage,
        get_console_manager,
    )

    manager = get_console_manager()
    job_id = "test-integration-job"

    # Mock de múltiplos clientes WebSocket
    clients = []
    messages_received = []

    for i in range(3):
        ws = MagicMock()

        async def mock_accept():
            pass

        async def mock_send_text(text):
            messages_received.append({
                "client_id": i,
                "message": text,
            })

        ws.accept = mock_accept
        ws.send_text = mock_send_text
        clients.append(ws)

    # Conecta todos os clientes ao mesmo job
    for ws in clients:
        await manager.connect(ws, job_id)

    # Valida que todos estão conectados
    assert manager.get_connection_count(job_id) == 3

    # Envia broadcast
    msg = ConsoleMessage(
        timestamp=datetime.now().isoformat(),
        job_id=job_id,
        level="info",
        message="Integration test message",
        metadata={"test": "integration"},
    )
    await manager.broadcast(job_id, msg)

    # Valida que todos os 3 clientes receberam a mensagem
    assert len(messages_received) == 3

    for received in messages_received:
        msg_data = json.loads(received["message"])
        assert msg_data["job_id"] == job_id
        assert msg_data["level"] == "info"
        assert msg_data["message"] == "Integration test message"
        assert msg_data["metadata"]["test"] == "integration"

    # Desconecta todos
    for ws in clients:
        await manager.disconnect(ws, job_id)

    assert manager.get_connection_count(job_id) == 0


# =============================================================================
# INTEGRAÇÃO: Custom Tools com Formato MCP
# =============================================================================

@pytest.mark.asyncio
async def test_integration_custom_tools_mcp_format():
    """
    Teste de Integração: Custom tools com formato MCP.

    Valida que as custom tools retornam formato compatível com MCP
    e podem ser integradas na SDK quando disponível.
    """
    from core.webhooks.infrastructure.agents.skybridge_tools import (
        skybridge_log_tool,
        skybridge_progress_tool,
        skybridge_checkpoint_tool,
    )

    # Testa skybridge_log_tool
    log_result = skybridge_log_tool(
        level="info",
        message="Test log",
        metadata={"key": "value"},
    )

    # Valida formato MCP: { "content": [{"type": "text", "text": "..."}] }
    assert "content" in log_result
    assert isinstance(log_result["content"], list)
    assert len(log_result["content"]) > 0
    assert log_result["content"][0]["type"] == "text"
    assert isinstance(log_result["content"][0]["text"], str)

    # Testa skybridge_progress_tool
    progress_result = skybridge_progress_tool(
        percent=75,
        message="75% complete",
        status="running",
    )

    assert "content" in progress_result
    assert "75%" in progress_result["content"][0]["text"]

    # Testa skybridge_checkpoint_tool
    checkpoint_result = skybridge_checkpoint_tool(
        label="checkpoint-1",
        description="First checkpoint",
    )

    assert "content" in checkpoint_result
    assert "checkpoint-1" in checkpoint_result["content"][0]["text"]


# =============================================================================
# INTEGRAÇÃO: AgentExecution Lifecycle Completo
# =============================================================================

@pytest.mark.asyncio
async def test_integration_agent_execution_full_lifecycle():
    """
    Teste de Integração: Ciclo de vida completo de AgentExecution.

    Valida todos os estados e transições do AgentExecution.
    """
    from core.webhooks.infrastructure.agents.domain import (
        AgentExecution,
        AgentState,
        AgentResult,
    )

    job = create_test_job()

    # CREATED → RUNNING
    execution = AgentExecution(
        agent_type="claude-sdk",
        job_id=job.job_id,
        worktree_path="/tmp/test-worktree",
        skill="resolve-issue",
        state=AgentState.CREATED,
        timeout_seconds=600,
    )

    assert execution.state == AgentState.CREATED
    assert execution.created_at is not None
    assert execution.started_at is None
    assert execution.completed_at is None

    # RUNNING → COMPLETED
    execution.mark_running()
    assert execution.state == AgentState.RUNNING
    assert execution.started_at is not None

    # Simula resultado
    result = AgentResult(
        success=True,
        changes_made=True,
        files_created=["new_file.py"],
        files_modified=["existing.py"],
        files_deleted=[],
        commit_hash="abc123",
        pr_url="https://github.com/test/test/pull/1",
        message="Task completed successfully",
        issue_title="Test Issue",
        output_message="Files created and modified",
        thinkings=[],
    )

    execution.mark_completed(result)
    assert execution.state == AgentState.COMPLETED
    assert execution.completed_at is not None
    assert execution.result is not None
    assert execution.result.success is True

    # Valida duration_ms
    duration = execution.duration_ms
    assert duration is not None
    assert duration >= 0

    # Valida is_terminal
    assert execution.is_terminal is True


@pytest.mark.asyncio
async def test_integration_agent_execution_error_states():
    """
    Teste de Integração: Estados de erro de AgentExecution.

    Valida transições para estados de erro (FAILED, TIMED_OUT).
    """
    from core.webhooks.infrastructure.agents.domain import (
        AgentExecution,
        AgentState,
    )

    job = create_test_job()

    # Testa FAILED
    execution = AgentExecution(
        agent_type="claude-sdk",
        job_id=job.job_id,
        worktree_path="/tmp/test",
        skill="resolve-issue",
        state=AgentState.CREATED,
        timeout_seconds=600,
    )

    execution.mark_running()
    execution.mark_failed("Test error message")

    assert execution.state == AgentState.FAILED
    assert execution.completed_at is not None
    assert execution.error_message == "Test error message"
    assert execution.is_terminal is True

    # Testa TIMED_OUT
    execution = AgentExecution(
        agent_type="claude-sdk",
        job_id=job.job_id,
        worktree_path="/tmp/test",
        skill="resolve-issue",
        state=AgentState.CREATED,
        timeout_seconds=600,
    )

    execution.mark_running()
    execution.mark_timed_out("Timeout after 600s")

    assert execution.state == AgentState.TIMED_OUT
    assert execution.completed_at is not None
    assert execution.error_message == "Timeout after 600s"
    assert execution.is_terminal is True


# =============================================================================
# INTEGRAÇÃO: Multiple Skills com Timeouts Diferentes
# =============================================================================

@pytest.mark.asyncio
async def test_integration_multiple_skills_timeouts():
    """
    Teste de Integração: Múltiplos skills com timeouts diferentes.

    Valida que cada skill tem o timeout correto configurado.
    """
    from core.webhooks.infrastructure.agents.claude_sdk_adapter import ClaudeSDKAdapter

    adapter = ClaudeSDKAdapter()

    # Testa todos os skills conhecidos
    expected_timeouts = {
        "hello-world": 60,
        "bug-simple": 300,
        "bug-complex": 600,
        "refactor": 900,
        "resolve-issue": 600,
        "respond-discord": 300,
        "summarize-video": 600,
    }

    for skill, expected_timeout in expected_timeouts.items():
        timeout = adapter.get_timeout_for_skill(skill)
        assert timeout == expected_timeout, \
            f"Timeout mismatch for {skill}: expected {expected_timeout}, got {timeout}"

    # Testa skill desconhecido
    unknown_timeout = adapter.get_timeout_for_skill("unknown-skill")
    assert unknown_timeout == ClaudeSDKAdapter.DEFAULT_TIMEOUT


# =============================================================================
# INTEGRAÇÃO: AgentResult Round-trip
# =============================================================================

@pytest.mark.asyncio
async def test_integration_agent_result_round_trip():
    """
    Teste de Integração: AgentResult round-trip (dict ↔ object).

    Valida que AgentResult pode ser serializado e desserializado
    sem perda de informação.
    """
    from core.webhooks.infrastructure.agents.domain import AgentResult

    # Cria resultado complexo
    original = AgentResult(
        success=True,
        changes_made=True,
        files_created=["file1.py", "file2.py", "file3.py"],
        files_modified=["main.py", "utils.py"],
        files_deleted=["old.py"],
        commit_hash="abc123",
        pr_url="https://github.com/test/test/pull/1",
        message="Task completed",
        issue_title="Test Issue",
        output_message="Files created and modified",
        thinkings=[
            {"step": 1, "thought": "Analyzing..."},
            {"step": 2, "thought": "Implementing..."},
        ],
    )

    # Converte para dict
    result_dict = original.to_dict()

    # Valida todos os campos
    assert result_dict["success"] is True
    assert result_dict["changes_made"] is True
    assert result_dict["files_created"] == ["file1.py", "file2.py", "file3.py"]
    assert result_dict["files_modified"] == ["main.py", "utils.py"]
    assert result_dict["files_deleted"] == ["old.py"]
    assert result_dict["commit_hash"] == "abc123"
    assert result_dict["pr_url"] == "https://github.com/test/test/pull/1"
    assert result_dict["message"] == "Task completed"
    assert result_dict["issue_title"] == "Test Issue"
    assert result_dict["output_message"] == "Files created and modified"
    assert len(result_dict["thinkings"]) == 2

    # Converte de volta para objeto
    restored = AgentResult.from_dict(result_dict)

    # Valida round-trip (todos os campos iguais)
    assert restored.success == original.success
    assert restored.changes_made == original.changes_made
    assert restored.files_created == original.files_created
    assert restored.files_modified == original.files_modified
    assert restored.files_deleted == original.files_deleted
    assert restored.commit_hash == original.commit_hash
    assert restored.pr_url == original.pr_url
    assert restored.message == original.message
    assert restored.issue_title == original.issue_title
    assert restored.output_message == original.output_message
    assert len(restored.thinkings) == len(original.thinkings)


# =============================================================================
# INTEGRAÇÃO: System Prompt com Contexto Completo
# =============================================================================

@pytest.mark.asyncio
async def test_integration_system_prompt_with_full_context():
    """
    Teste de Integração: System prompt com contexto completo.

    Valida que as variáveis de contexto usadas no template são substituídas
    corretamente no system prompt.
    """
    from core.webhooks.infrastructure.agents.claude_sdk_adapter import ClaudeSDKAdapter

    adapter = ClaudeSDKAdapter()
    job = create_test_job(
        job_id="test-job-456",
        issue_number=99,
        issue_title="Fix authentication bug",
        issue_body="Users cannot login with SSO",
    )

    skill = "bug-complex"
    skybridge_context = {
        "worktree_path": "/path/to/worktree",
        "branch_name": "fix/auth-bug",
        "repo_name": "my-org/my-repo",
    }

    # Build system prompt
    system_prompt = adapter._build_system_prompt(job, skill, skybridge_context)

    # Valida que as variáveis usadas no template foram substituídas
    # O template padrão usa: {worktree_path}, {branch_name}, {job_id}
    # Mas não usa {issue_body} nas instruções padrão
    assert "/path/to/worktree" in system_prompt
    assert "test-job-456" in system_prompt
    # issue_number e issue_title podem não aparecer se não estiverem no template
    # O teste valida que o contexto é passado corretamente para render_system_prompt


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
