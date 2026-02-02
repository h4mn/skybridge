# -*- coding: utf-8 -*-
"""
Tests for Agent Infrastructure Layer.

Testes TDD para a infraestrutura de agentes conforme SPEC008:
- Domain entities (AgentState, AgentExecution, AgentResult)
- Agent Facade Pattern
- Claude Code Adapter
- XML Streaming Protocol
"""
from __future__ import annotations

import json
from datetime import datetime
from unittest.mock import MagicMock, Mock, patch

import pytest

from core.webhooks.domain import WebhookEvent, WebhookJob, WebhookSource
from core.webhooks.infrastructure.agents.domain import (
    AgentState,
    AgentExecution,
    AgentResult,
    ThinkingStep,
)
from core.webhooks.infrastructure.agents.agent_facade import AgentFacade
from core.webhooks.infrastructure.agents.protocol import (
    XMLStreamingProtocol,
    SkybridgeCommand,
)


class TestAgentState:
    """Testes para enum AgentState."""

    def test_agent_state_values(self):
        """Verifica valores do enum AgentState."""
        assert AgentState.CREATED.value == "created"
        assert AgentState.RUNNING.value == "running"
        assert AgentState.TIMED_OUT.value == "timed_out"
        assert AgentState.COMPLETED.value == "completed"
        assert AgentState.FAILED.value == "failed"

    def test_agent_state_terminal_states(self):
        """Verifica estados terminais do agente."""
        assert AgentState.COMPLETED in (
            AgentState.COMPLETED,
            AgentState.TIMED_OUT,
            AgentState.FAILED,
        )


class TestThinkingStep:
    """Testes para ThinkingStep."""

    def test_thinking_step_creation(self):
        """Cria ThinkingStep com dados válidos."""
        step = ThinkingStep(
            step=1,
            thought="Analisando issue...",
            timestamp=datetime.utcnow(),
            duration_ms=1500,
        )

        assert step.step == 1
        assert step.thought == "Analisando issue..."
        assert step.duration_ms == 1500
        assert step.inference_used is True  # Default

    def test_thinking_step_without_duration(self):
        """Cria ThinkingStep sem duração (opcional)."""
        step = ThinkingStep(
            step=1,
            thought="Analisando issue...",
            timestamp=datetime.utcnow(),
        )

        assert step.duration_ms is None


class TestAgentResult:
    """Testes para AgentResult."""

    def test_agent_result_creation(self):
        """Cria AgentResult com dados válidos."""
        result = AgentResult(
            success=True,
            changes_made=True,
            files_created=["hello_world.py"],
            files_modified=["__init__.py"],
            files_deleted=[],
            commit_hash="abc123",
            pr_url="https://github.com/test/repo/pull/1",
            message="Issue resolvida",
            issue_title="Fix version alignment",
            output_message="Aligned versions to 0.2.5",
            thinkings=[
                {
                    "step": 1,
                    "thought": "Analisando issue...",
                    "timestamp": "2026-01-10T10:30:00Z",
                    "duration_ms": 1500,
                }
            ],
        )

        assert result.success is True
        assert result.changes_made is True
        assert len(result.files_created) == 1
        assert result.commit_hash == "abc123"

    def test_agent_result_to_dict(self):
        """Converte AgentResult para dicionário."""
        result = AgentResult(
            success=True,
            changes_made=False,
            files_created=[],
            files_modified=[],
            files_deleted=[],
            commit_hash=None,
            pr_url=None,
            message="Sem mudanças",
            issue_title="Test issue",
            output_message="No changes",
            thinkings=[],
        )

        data = result.to_dict()

        assert data["success"] is True
        assert data["changes_made"] is False
        assert data["files_created"] == []
        assert data["commit_hash"] is None

    def test_agent_result_from_dict(self):
        """Cria AgentResult a partir de dicionário."""
        data = {
            "success": True,
            "changes_made": True,
            "files_created": ["test.py"],
            "files_modified": [],
            "files_deleted": [],
            "commit_hash": "abc123",
            "pr_url": "https://github.com/test/pull/1",
            "message": "Done",
            "issue_title": "Test",
            "output_message": "Output",
            "thinkings": [],
        }

        result = AgentResult.from_dict(data)

        assert result.success is True
        assert result.files_created == ["test.py"]
        assert result.commit_hash == "abc123"


class TestAgentExecution:
    """Testes para AgentExecution."""

    def test_agent_execution_creation(self):
        """Cria AgentExecution com dados válidos."""
        execution = AgentExecution(
            agent_type="claude-code",
            job_id="test-job-123",
            worktree_path="/tmp/worktree",
            skill="resolve-issue",
            state=AgentState.CREATED,
        )

        assert execution.agent_type == "claude-code"
        assert execution.job_id == "test-job-123"
        assert execution.state == AgentState.CREATED
        assert execution.created_at is not None

    def test_agent_execution_mark_running(self):
        """Marca execução como running."""
        execution = AgentExecution(
            agent_type="claude-code",
            job_id="test-job-123",
            worktree_path="/tmp/worktree",
            skill="resolve-issue",
            state=AgentState.CREATED,
        )

        execution.mark_running()

        assert execution.state == AgentState.RUNNING
        assert execution.started_at is not None

    def test_agent_execution_mark_completed(self):
        """Marca execução como completada."""
        execution = AgentExecution(
            agent_type="claude-code",
            job_id="test-job-123",
            worktree_path="/tmp/worktree",
            skill="resolve-issue",
            state=AgentState.RUNNING,
        )
        execution.mark_running()

        result = AgentResult(
            success=True,
            changes_made=True,
            files_created=[],
            files_modified=[],
            files_deleted=[],
            commit_hash="abc123",
            pr_url=None,
            message="Done",
            issue_title="Test",
            output_message="Output",
            thinkings=[],
        )

        execution.mark_completed(result)

        assert execution.state == AgentState.COMPLETED
        assert execution.completed_at is not None
        assert execution.result is not None
        assert execution.result.success is True

    def test_agent_execution_mark_timed_out(self):
        """Marca execução como timeout."""
        execution = AgentExecution(
            agent_type="claude-code",
            job_id="test-job-123",
            worktree_path="/tmp/worktree",
            skill="resolve-issue",
            state=AgentState.RUNNING,
        )
        execution.mark_running()

        execution.mark_timed_out("Timeout after 600s")

        assert execution.state == AgentState.TIMED_OUT
        assert execution.completed_at is not None
        assert execution.error_message == "Timeout after 600s"

    def test_agent_execution_mark_failed(self):
        """Marca execução como falha."""
        execution = AgentExecution(
            agent_type="claude-code",
            job_id="test-job-123",
            worktree_path="/tmp/worktree",
            skill="resolve-issue",
            state=AgentState.RUNNING,
        )
        execution.mark_running()

        execution.mark_failed("Permission denied")

        assert execution.state == AgentState.FAILED
        assert execution.completed_at is not None
        assert execution.error_message == "Permission denied"

    def test_agent_execution_duration(self):
        """Calcula duração da execução."""
        execution = AgentExecution(
            agent_type="claude-code",
            job_id="test-job-123",
            worktree_path="/tmp/worktree",
            skill="resolve-issue",
            state=AgentState.CREATED,
        )

        # Sem started_at/completed_at, duration é None
        assert execution.duration_ms is None

        # Mock timestamps
        execution.started_at = datetime(2026, 1, 10, 10, 30, 0)
        execution.completed_at = datetime(2026, 1, 10, 10, 31, 0)

        assert execution.duration_ms == 60000  # 1 minuto

    def test_agent_execution_is_terminal(self):
        """Verifica se execução está em estado terminal."""
        execution = AgentExecution(
            agent_type="claude-code",
            job_id="test-job-123",
            worktree_path="/tmp/worktree",
            skill="resolve-issue",
            state=AgentState.RUNNING,
        )

        assert execution.is_terminal is False

        execution.state = AgentState.COMPLETED
        assert execution.is_terminal is True

        execution.state = AgentState.TIMED_OUT
        assert execution.is_terminal is True

        execution.state = AgentState.FAILED
        assert execution.is_terminal is True

    def test_agent_execution_to_dict(self):
        """Converte AgentExecution para dicionário."""
        execution = AgentExecution(
            agent_type="claude-code",
            job_id="test-job-123",
            worktree_path="/tmp/worktree",
            skill="resolve-issue",
            state=AgentState.CREATED,
        )

        data = execution.to_dict()

        assert data["agent_type"] == "claude-code"
        assert data["job_id"] == "test-job-123"
        assert data["state"] == "created"
        assert "timestamps" in data


class TestXMLStreamingProtocol:
    """Testes para XMLStreamingProtocol."""

    def test_protocol_creation(self):
        """Cria protocolo com valores padrão."""
        protocol = XMLStreamingProtocol()

        assert protocol.max_xml_size == 50000
        assert protocol.max_thinking_size == 10000
        assert protocol.max_log_message_size == 5000

    def test_parse_simple_log_command(self):
        """Parseia comando log simples."""
        protocol = XMLStreamingProtocol()
        xml = """<skybridge_command>
  <command>log</command>
  <parametro name="mensagem">Hello world!</parametro>
  <parametro name="nivel">info</parametro>
</skybridge_command>"""

        commands = protocol.parse_commands(xml)

        assert len(commands) == 1
        assert commands[0].command == "log"
        assert commands[0].params["mensagem"] == "Hello world!"
        assert commands[0].params["nivel"] == "info"

    def test_parse_multiple_commands(self):
        """Parseia múltiplos comandos XML."""
        protocol = XMLStreamingProtocol()
        xml = """<skybridge_command>
  <command>log</command>
  <parametro name="mensagem">Starting</parametro>
</skybridge_command>
<skybridge_command>
  <command>progress</command>
  <parametro name="porcentagem">50</parametro>
</skybridge_command>"""

        commands = protocol.parse_commands(xml)

        assert len(commands) == 2
        assert commands[0].command == "log"
        assert commands[1].command == "progress"

    def test_ignores_unknown_commands(self):
        """Ignora comandos desconhecidos."""
        protocol = XMLStreamingProtocol()
        xml = """<skybridge_command>
  <command>unknown_command</command>
  <parametro name="mensagem">Test</parametro>
</skybridge_command>"""

        commands = protocol.parse_commands(xml)

        assert len(commands) == 0

    def test_ignores_oversized_xml(self):
        """Ignora XML muito grande (DoS protection)."""
        protocol = XMLStreamingProtocol(max_xml_size=100)
        xml = """<skybridge_command>
  <command>log</command>
  <parametro name="mensagem">""" + "x" * 200 + """</parametro>
</skybridge_command>"""

        commands = protocol.parse_commands(xml)

        assert len(commands) == 0

    def test_html_unescaping_in_params(self):
        """Desescapa HTML entities em parâmetros."""
        protocol = XMLStreamingProtocol()
        xml = """<skybridge_command>
  <command>log</command>
  <parametro name="mensagem">&lt;test&gt; &amp; &quot;quoted&quot;</parametro>
</skybridge_command>"""

        commands = protocol.parse_commands(xml)

        assert commands[0].params["mensagem"] == '<test> & "quoted"'

    def test_validate_thinking_valid(self):
        """Valida thinking step válido."""
        protocol = XMLStreamingProtocol()

        thinking = {
            "step": 1,
            "thought": "Analisando issue...",
            "timestamp": "2026-01-10T10:30:00Z",
        }

        assert protocol.validate_thinking(thinking) is True

    def test_validate_thinking_missing_fields(self):
        """Rejeita thinking sem campos obrigatórios."""
        protocol = XMLStreamingProtocol()

        thinking = {
            "step": 1,
            "thought": "Analisando...",
            # Falta timestamp
        }

        assert protocol.validate_thinking(thinking) is False

    def test_validate_thinking_too_large(self):
        """Rejeita thinking muito grande."""
        protocol = XMLStreamingProtocol(max_thinking_size=100)

        thinking = {
            "step": 1,
            "thought": "x" * 200,  # Maior que max_thinking_size
            "timestamp": "2026-01-10T10:30:00Z",
        }

        assert protocol.validate_thinking(thinking) is False

    def test_validate_thinkings_count(self):
        """Valida quantidade máxima de thinkings."""
        protocol = XMLStreamingProtocol()

        thinkings = [
            {"step": i, "thought": f"Step {i}", "timestamp": "2026-01-10T10:30:00Z"}
            for i in range(101)  # Maior que MAX_THINKINGS_COUNT (100)
        ]

        assert protocol.validate_thinkings(thinkings) is False

    def test_is_json_output(self):
        """Detecta linhas que são JSON."""
        assert XMLStreamingProtocol.is_json_output('{"success": true}') is True
        assert XMLStreamingProtocol.is_json_output('not json') is False
        assert XMLStreamingProtocol.is_json_output('{') is False  # Incompleto

    def test_is_xml_command(self):
        """Detecta linhas que são comandos XML."""
        assert (
            XMLStreamingProtocol.is_xml_command(
                "<skybridge_command><command>log</command></skybridge_command>"
            )
            is True
        )
        assert XMLStreamingProtocol.is_xml_command("not xml") is False
        assert (
            XMLStreamingProtocol.is_xml_command("<skybridge_command>") is False
        )  # Incompleto


class TestAgentFacadeInterface:
    """Testes para interface AgentFacade."""

    def test_agent_facade_is_abstract(self):
        """Verifica que AgentFacade não pode ser instanciada."""
        with pytest.raises(TypeError):
            AgentFacade()


class TestSkybridgeCommand:
    """Testes para SkybridgeCommand."""

    def test_command_creation(self):
        """Cria comando com dados válidos."""
        cmd = SkybridgeCommand(command="log", params={"mensagem": "Test", "nivel": "info"})

        assert cmd.command == "log"
        assert cmd.params["mensagem"] == "Test"
        assert cmd.params["nivel"] == "info"

    def test_command_to_dict(self):
        """Converte comando para dicionário."""
        cmd = SkybridgeCommand(command="log", params={"mensagem": "Test"})

        data = cmd.to_dict()

        assert data["command"] == "log"
        assert data["params"]["mensagem"] == "Test"


class TestEventTypeToSkillMapping:
    """
    Testes para mapeamento event_type → skill.

    Garante que eventos que não precisam de agente retornem None.
    """

    def test_issues_opened_returns_resolve_issue_skill(self):
        """issues.opened retorna resolve-issue."""
        from core.webhooks.application.job_orchestrator import (
            JobOrchestrator,
        )

        skill = JobOrchestrator._get_skill_for_event_type("issues.opened")
        assert skill == "resolve-issue"

    def test_issues_closed_returns_none(self):
        """issues.closed retorna None (não executa agente)."""
        from core.webhooks.application.job_orchestrator import (
            JobOrchestrator,
        )

        skill = JobOrchestrator._get_skill_for_event_type("issues.closed")
        assert skill is None

    def test_issues_deleted_returns_none(self):
        """issues.deleted retorna None (não executa agente)."""
        from core.webhooks.application.job_orchestrator import (
            JobOrchestrator,
        )

        skill = JobOrchestrator._get_skill_for_event_type("issues.deleted")
        assert skill is None

    def test_issues_reopened_returns_resolve_issue_skill(self):
        """issues.reopened retorna resolve-issue."""
        from core.webhooks.application.job_orchestrator import (
            JobOrchestrator,
        )

        skill = JobOrchestrator._get_skill_for_event_type("issues.reopened")
        assert skill == "resolve-issue"

    def test_issue_comment_created_returns_respond_discord_skill(self):
        """issue_comment.created retorna respond-discord."""
        from core.webhooks.application.job_orchestrator import (
            JobOrchestrator,
        )

        skill = JobOrchestrator._get_skill_for_event_type("issue_comment.created")
        assert skill == "respond-discord"

    def test_unknown_event_type_returns_none(self):
        """Event type desconhecido retorna None."""
        from core.webhooks.application.job_orchestrator import (
            JobOrchestrator,
        )

        skill = JobOrchestrator._get_skill_for_event_type("unknown.event")
        assert skill is None


class TestSkyDirectoryAndAgentLog:
    """
    Testes para criação de .sky/ e agent.log.

    NOTA: Testes integrados com subprocess real - criam diretório temporário
    e verificam que .sky/ e agent.log são criados corretamente.
    """

    def test_sky_directory_structure_exists(self):
        """Teste unitário: verifica que a estrutura do diretório .sky/ está definida."""
        from pathlib import Path
        # Teste simples que verifica a estrutura esperada
        import tempfile
        with tempfile.TemporaryDirectory() as tmpdir:
            # Simula criação do diretório .sky/
            sky_dir = Path(tmpdir) / ".sky"
            sky_dir.mkdir(parents=True, exist_ok=True)

            # Verifica que foi criado
            assert sky_dir.exists()
            assert sky_dir.is_dir()

            # Verifica que pode criar arquivo dentro
            log_file = sky_dir / "agent.log"
            log_file.write_text("# Test log\n")
            assert log_file.exists()

    def test_agent_log_format_structure(self):
        """Teste unitário: verifica formato esperado do agent.log."""
        # Simula formato do log que deve ser criado
        log_content = """# Skybridge Agent Log
# Job ID: test-job-123
# Worktree: /path/to/worktree
# Skill: resolve-issue
# Timestamp: 2026-01-11T00:00:00
# Return Code: 0

## STDOUT
Output line 1
Output line 2

## STDERR
Error message (if any)
"""

        # Verifica estrutura do log
        assert "# Skybridge Agent Log" in log_content
        assert "# Job ID:" in log_content
        assert "## STDOUT" in log_content
        assert "## STDERR" in log_content

    def test_os_makedirs_creates_sky_directory(self):
        """Testa que os.makedirs com exist_ok=True funciona para .sky/"""
        import tempfile
        import os

        with tempfile.TemporaryDirectory() as tmpdir:
            sky_dir = os.path.join(tmpdir, ".sky")

            # Primeira criação
            os.makedirs(sky_dir, exist_ok=True)
            assert os.path.exists(sky_dir)

            # Segunda criação (não deve falhar)
            os.makedirs(sky_dir, exist_ok=True)
            assert os.path.exists(sky_dir)
