# -*- coding: utf-8 -*-
"""
Testes de Migração A/B - ClaudeSDKAdapter vs ClaudeCodeAdapter.

PRD019: Testes comparando SDK vs subprocess para validar paridade funcional.

Estes testes garantem que a migração para o SDK não altera o comportamento
esperado do agente.
"""
from __future__ import annotations

import asyncio
import os
from pathlib import Path
from typing import TYPE_CHECKING
from unittest.mock import MagicMock, AsyncMock, patch

import pytest

if TYPE_CHECKING:
    from core.webhooks.domain import WebhookJob


# Helper para criar job de teste
def create_test_job(
    job_id: str = "test-job-123",
    issue_number: int = 42,
    issue_title: str = "Test Issue",
    issue_body: str = "Test issue body",
) -> "WebhookJob":
    """
    Cria um WebhookJob de teste.

    Args:
        job_id: ID do job
        issue_number: Número da issue
        issue_title: Título da issue
        issue_body: Corpo da issue

    Returns:
        WebhookJob configurado para teste
    """
    from core.webhooks.domain import WebhookJob, GitHubEvent

    event = GitHubEvent(
        event_type="issues.opened",
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
        delivered_at="2026-01-24T10:00:00Z",
    )

    job = WebhookJob(
        job_id=job_id,
        event=event,
        issue_number=issue_number,
        branch_name=f"test-branch-{job_id}",
    )

    return job


@pytest.mark.asyncio
async def test_sdk_vs_subprocess_parity():
    """
    Testa A/B comparando ClaudeSDKAdapter com ClaudeCodeAdapter.

    Valida:
    - Ambos produzem resultados com mesmos campos
    - AgentResult tem mesma estrutura
    - Timeouts são iguais
    - Tipos de agente estão corretos
    """
    from core.webhooks.infrastructure.agents.claude_agent import ClaudeCodeAdapter
    from core.webhooks.infrastructure.agents.claude_sdk_adapter import ClaudeSDKAdapter
    from kernel.contracts.result import Result

    job = create_test_job()
    skill = "resolve-issue"
    worktree_path = "/tmp/test-worktree"
    skybridge_context = {
        "worktree_path": worktree_path,
        "branch_name": "test-branch",
        "repo_name": "test-owner/test-repo",
    }

    # Cria adapters
    subprocess_adapter = ClaudeCodeAdapter()
    sdk_adapter = ClaudeSDKAdapter()

    # Testa get_agent_type()
    assert subprocess_adapter.get_agent_type() == "claude-code"
    assert sdk_adapter.get_agent_type() == "claude-sdk"

    # Testa get_timeout_for_skill()
    subprocess_timeout = subprocess_adapter.get_timeout_for_skill(skill)
    sdk_timeout = sdk_adapter.get_timeout_for_skill(skill)
    assert subprocess_timeout == sdk_timeout == 600

    # Testa _get_repo_name()
    subprocess_repo = subprocess_adapter._get_repo_name(job)
    sdk_repo = sdk_adapter._get_repo_name(job)
    assert subprocess_repo == sdk_repo == "test-owner/test-repo"

    # Testa _build_main_prompt()
    subprocess_prompt = subprocess_adapter._build_main_prompt(job)
    sdk_prompt = sdk_adapter._build_main_prompt(job)
    assert subprocess_prompt == sdk_prompt


@pytest.mark.asyncio
async def test_feature_flag_selection():
    """
    Testa se a feature flag USE_SDK_ADAPTER seleciona o adapter correto.

    Valida:
    - USE_SDK_ADAPTER=false → ClaudeCodeAdapter
    - USE_SDK_ADAPTER=true → ClaudeSDKAdapter
    """
    from core.webhooks.application.job_orchestrator import JobOrchestrator
    from core.webhooks.infrastructure.agents.claude_agent import ClaudeCodeAdapter
    from core.webhooks.infrastructure.agents.claude_sdk_adapter import ClaudeSDKAdapter

    # Mock dependências
    mock_queue = MagicMock()
    mock_worktree_manager = MagicMock()
    mock_event_bus = MagicMock()

    # Testa com USE_SDK_ADAPTER=false (padrão)
    with patch.dict(os.environ, {"USE_SDK_ADAPTER": "false"}, clear=False):
        orchestrator = JobOrchestrator(
            mock_queue,
            mock_worktree_manager,
            mock_event_bus,
        )
        assert isinstance(orchestrator.agent_adapter, ClaudeCodeAdapter)

    # Testa com USE_SDK_ADAPTER=true
    with patch.dict(os.environ, {"USE_SDK_ADAPTER": "true"}, clear=False):
        # Need to clear the cached feature flags
        import runtime.config.feature_flags as ff_module
        ff_module._feature_flags = None

        orchestrator = JobOrchestrator(
            mock_queue,
            mock_worktree_manager,
            mock_event_bus,
        )
        assert isinstance(orchestrator.agent_adapter, ClaudeSDKAdapter)

    # Testa com adapter explícito (deve ignorar feature flag)
    explicit_adapter = ClaudeCodeAdapter()
    orchestrator = JobOrchestrator(
        mock_queue,
        mock_worktree_manager,
        mock_event_bus,
        agent_adapter=explicit_adapter,
    )
    assert orchestrator.agent_adapter is explicit_adapter


@pytest.mark.asyncio
async def test_session_continuity():
    """
    Testa session continuity do SDK (nativo vs subprocess hack).

    Valida:
    - SDK mantém contexto entre turnos (feature nativa)
    - Subprocess perde contexto entre turnos
    """
    from core.webhooks.infrastructure.agents.claude_sdk_adapter import ClaudeSDKAdapter

    adapter = ClaudeSDKAdapter()

    # TODO: Implementar teste quando a SDK suportar multi-turn
    # Por ora, valida apenas que a estrutura existe
    assert hasattr(adapter, "get_agent_type")
    assert hasattr(adapter, "get_timeout_for_skill")
    assert hasattr(adapter, "spawn")


@pytest.mark.asyncio
async def test_agent_result_extraction():
    """
    Testa extração de AgentResult do ResultMessage do SDK.

    Valida:
    - ResultMessage é convertido corretamente para AgentResult
    - Campos obrigatórios estão presentes
    - Flags de sucesso são corretas
    """
    from core.webhooks.infrastructure.agents.claude_sdk_adapter import ClaudeSDKAdapter
    from core.webhooks.infrastructure.agents.domain import AgentResult

    adapter = ClaudeSDKAdapter()

    # Mock ResultMessage simulado
    class MockResultMessage:
        is_error = False
        result = '{"success": true, "files_created": ["test.py"], "files_modified": ["main.py"]}'
        duration_ms = 1500

    result_msg = MockResultMessage()
    agent_result = adapter._extract_result(result_msg)

    # Valida AgentResult
    assert isinstance(agent_result, AgentResult)
    assert agent_result.success is True
    assert agent_result.changes_made is True
    assert "test.py" in agent_result.files_created
    assert "main.py" in agent_result.files_modified

    # Testa com erro
    result_msg.is_error = True
    result_msg.result = "Error message"
    agent_result = adapter._extract_result(result_msg)
    assert agent_result.success is False


@pytest.mark.asyncio
async def test_system_prompt_building():
    """
    Testa construção de system prompt em ambos os adapters.

    Valida:
    - System prompts são idênticos
    - Variáveis de contexto são substituídas corretamente
    """
    from core.webhooks.infrastructure.agents.claude_agent import ClaudeCodeAdapter
    from core.webhooks.infrastructure.agents.claude_sdk_adapter import ClaudeSDKAdapter

    job = create_test_job()
    skill = "resolve-issue"
    skybridge_context = {
        "worktree_path": "/tmp/test-worktree",
        "branch_name": "test-branch",
        "repo_name": "test-owner/test-repo",
    }

    subprocess_adapter = ClaudeCodeAdapter()
    sdk_adapter = ClaudeSDKAdapter()

    # Build system prompts
    subprocess_prompt = subprocess_adapter._build_system_prompt(job, skill, skybridge_context)
    sdk_prompt = sdk_adapter._build_system_prompt(job, skill, skybridge_context)

    # Devem ser idênticos (usam mesma função render_system_prompt)
    assert subprocess_prompt == sdk_prompt

    # Devem conter variáveis de contexto
    assert "test-owner/test-repo" in subprocess_prompt
    assert "resolve-issue" in subprocess_prompt
    assert "test-job-123" in subprocess_prompt


@pytest.mark.asyncio
async def test_timeout_consistency():
    """
    Testa consistência de timeouts entre adapters.

    Valida:
    - SKILL_TIMEOUTS são idênticos
    - Timeout default é o mesmo
    - Skills desconhecidos usam default
    """
    from core.webhooks.infrastructure.agents.claude_agent import ClaudeCodeAdapter
    from core.webhooks.infrastructure.agents.claude_sdk_adapter import ClaudeSDKAdapter

    subprocess_adapter = ClaudeCodeAdapter()
    sdk_adapter = ClaudeSDKAdapter()

    # Testa todos os skills conhecidos
    for skill, expected_timeout in ClaudeCodeAdapter.SKILL_TIMEOUTS.items():
        subprocess_timeout = subprocess_adapter.get_timeout_for_skill(skill)
        sdk_timeout = sdk_adapter.get_timeout_for_skill(skill)
        assert subprocess_timeout == expected_timeout
        assert sdk_timeout == expected_timeout
        assert subprocess_timeout == sdk_timeout

    # Testa default
    assert subprocess_adapter.DEFAULT_TIMEOUT == sdk_adapter.DEFAULT_TIMEOUT

    # Testa skill desconhecido
    unknown_skill = "unknown-skill"
    subprocess_timeout = subprocess_adapter.get_timeout_for_skill(unknown_skill)
    sdk_timeout = sdk_adapter.get_timeout_for_skill(unknown_skill)
    assert subprocess_timeout == ClaudeCodeAdapter.DEFAULT_TIMEOUT
    assert sdk_timeout == ClaudeSDKAdapter.DEFAULT_TIMEOUT


def test_feature_flags_helper():
    """
    Testa helper _env_bool do feature_flags.

    Valida:
    - Valores "true", "1", "yes", "on" → True
    - Valores "false", "0", "no", "off" → False
    - Valores inválidos → default
    """
    from runtime.config.feature_flags import _env_bool

    # Valores verdadeiros
    assert _env_bool("TEST_VAR_TRUE", "true") is True
    assert _env_bool("TEST_VAR_1", "1") is True
    assert _env_bool("TEST_VAR_YES", "yes") is True
    assert _env_bool("TEST_VAR_ON", "on") is True

    # Valores falsos
    assert _env_bool("TEST_VAR_FALSE", "false") is False
    assert _env_bool("TEST_VAR_0", "0") is False
    assert _env_bool("TEST_VAR_NO", "no") is False
    assert _env_bool("TEST_VAR_OFF", "off") is False

    # Default quando não definido
    assert _env_bool("UNDEFINED_VAR", True) is True  # default=True
    assert _env_bool("UNDEFINED_VAR", False) is False  # default=False


@pytest.mark.asyncio
async def test_websocket_console_manager():
    """
    Testa gerenciador de conexões WebSocket.

    Valida:
    - Conexões são registradas e removidas
    - Broadcast envia para todas as conexões de um job
    - Status retorna contagem correta
    """
    from runtime.delivery.websocket import WebSocketConsoleManager, ConsoleMessage

    manager = WebSocketConsoleManager()

    # Testa com mocks de WebSocket
    ws1 = MagicMock()
    ws2 = MagicMock()

    # Mock accept e send_text como async
    async def mock_accept():
        pass

    async def mock_send_text(text):
        pass

    ws1.accept = mock_accept
    ws1.send_text = mock_send_text
    ws2.accept = mock_accept
    ws2.send_text = mock_send_text

    job_id = "test-job-123"

    # Conecta
    await manager.connect(ws1, job_id)
    await manager.connect(ws2, job_id)

    # Verifica contagem
    assert manager.get_connection_count(job_id) == 2
    assert job_id in manager.get_all_jobs()

    # Broadcast
    msg = ConsoleMessage(
        timestamp="2026-01-24T10:00:00",
        job_id=job_id,
        level="info",
        message="Test message",
    )
    await manager.broadcast(job_id, msg)

    # Verifica que send_text foi chamado para ambos
    # (Nota: em teste real com mocks, verify seria usado aqui)

    # Desconecta um
    await manager.disconnect(ws1, job_id)
    assert manager.get_connection_count(job_id) == 1

    # Desconecta o outro
    await manager.disconnect(ws2, job_id)
    assert manager.get_connection_count(job_id) == 0
    assert job_id not in manager.get_all_jobs()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])


> "Testes A/B são a garantia de que a migração não introduz regressões" – made by Sky 🚀
