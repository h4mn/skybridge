# -*- coding: utf-8 -*-
"""
Teste de debug para Issue #4: 'str' object has no attribute 'get'

Este teste simula o fluxo completo do webhook com logs debug detalhados
para identificar onde o payload está se tornando uma string.
"""
from __future__ import annotations

import asyncio
import json
from datetime import datetime
from unittest.mock import Mock, patch

import pytest

from core.webhooks.domain import WebhookEvent, WebhookJob, WebhookSource
from core.webhooks.infrastructure.agents.claude_agent import (
    ClaudeCodeAdapter,
)
from core.webhooks.application.job_orchestrator import (
    JobOrchestrator,
)
from infra.webhooks.adapters.in_memory_queue import (
    InMemoryJobQueue,
)
from kernel.contracts.result import Result


class TestIssue4StrObjectDebug:
    """
    Teste de regressão para Issue #4: 'str' object has no attribute 'get'

    Cenário do erro histórico:
    - Webhook recebido com event_type="issues.opened"
    - Job criado e enfileirado
    - Worker chama orchestrator.execute_job()
    - Erro: 'str' object has no attribute 'get'

    Este teste garante que o payload NÃO vira string em nenhum ponto do fluxo.
    """

    @pytest.fixture
    def event_bus(self):
        """Event bus para testes."""
        from infra.domain_events.in_memory_event_bus import InMemoryEventBus
        return InMemoryEventBus()

    @pytest.fixture
    def github_webhook_payload(self):
        """Payload real do GitHub para issues.opened."""
        return {
            "action": "opened",
            "issue": {
                "number": 5,
                "title": "Test issue for debug",
                "body": "Testing the str object error",
                "user": {
                    "login": "h4mn",
                },
            },
            "repository": {
                "owner": {
                    "login": "h4mn",
                },
                "name": "skybridge",
                "full_name": "h4mn/skybridge",
            },
            "sender": {
                "login": "h4mn",
            },
        }

    @pytest.fixture
    def webhook_event(self, github_webhook_payload):
        """Cria WebhookEvent simulando o que routes.py faz."""
        print("\n[DEBUG] Creating WebhookEvent...")
        print(f"[DEBUG] payload type: {type(github_webhook_payload)}")
        print(f"[DEBUG] payload: {json.dumps(github_webhook_payload, indent=2)}")

        event = WebhookEvent(
            source=WebhookSource.GITHUB,
            event_type="issues.opened",  # Após correção do bug
            event_id="5",
            payload=github_webhook_payload,
            received_at=datetime.utcnow(),
            signature="sha256=test",
        )

        print(f"[DEBUG] event.event_type: {event.event_type}")
        print(f"[DEBUG] event.payload type: {type(event.payload)}")
        print(f"[DEBUG] event.payload.get('issue'): {event.payload.get('issue')}")

        return event

    @pytest.fixture
    def webhook_job(self, webhook_event):
        """Cria WebhookJob simulando o que WebhookProcessor faz."""
        print("\n[DEBUG] Creating WebhookJob...")
        job = WebhookJob.create(webhook_event)

        print(f"[DEBUG] job.job_id: {job.job_id}")
        print(f"[DEBUG] job.issue_number: {job.issue_number}")
        print(f"[DEBUG] job.event.payload type: {type(job.event.payload)}")

        # Simula worktree criado
        job.worktree_path = "B:\\_repositorios\\skybridge-worktrees\\skybridge-github-5-test123"
        job.branch_name = "webhook/github/issue/5/test123"

        return job

    def test_full_flow_with_debug_logs(
        self, webhook_job, github_webhook_payload, event_bus
    ):
        """
        Teste completo simulando o fluxo do worker com logs debug.

        Este teste reproduz exatamente o que acontece quando o worker processa um job.
        """
        print("\n" + "=" * 80)
        print("[DEBUG] INÍCIO DO TESTE - Simulando worker processando job")
        print("=" * 80)

        # Setup
        job_queue = InMemoryJobQueue()

        # Mock worktree manager
        mock_worktree_manager = Mock()
        mock_worktree_manager.create_worktree = Mock(return_value=Result.ok(
            webhook_job.worktree_path
        ))

        # ✅ ASSERT DE REGRESSÃO: Payload deve ser dict ANTES de qualquer processamento
        assert isinstance(webhook_job.event.payload, dict), (
            f"REGRESSÃO: Payload deve ser dict no início, mas é {type(webhook_job.event.payload)}"
        )

        # Mock GitExtractor
        with patch(
            "runtime.observability.snapshot.extractors.git_extractor.GitExtractor"
        ) as mock_extractor_class:
            mock_extractor = Mock()
            mock_extractor.capture.return_value = Mock(
                metadata=Mock(model_dump=lambda: {}),
                stats=Mock(model_dump=lambda: {}),
                structure={},
            )
            mock_extractor_class.return_value = mock_extractor

            # Cria orchestrator com adapter REAL (não mockado)
            adapter = ClaudeCodeAdapter()
            orchestrator = JobOrchestrator(
                job_queue=job_queue,
                worktree_manager=mock_worktree_manager,
                event_bus=event_bus,
                agent_adapter=adapter,
            )

            # Enfileira job
            print(f"\n[DEBUG] Enfileirando job: {webhook_job.job_id}")
            asyncio.run(job_queue.enqueue(webhook_job))

            # === PONTO DE INTERVENÇÃO ===
            # Vamos verificar cada passo do _execute_agent

            print("\n[DEBUG] Verificando skybridge_context...")

            # ✅ ASSERT DE REGRESSÃO: Payload deve continuar sendo dict
            assert isinstance(webhook_job.event.payload, dict), (
                f"REGRESSÃO: Payload virou {type(webhook_job.event.payload)} antes de _get_repo_name"
            )

            # Simula o que _execute_agent faz
            skybridge_context = {
                "worktree_path": webhook_job.worktree_path,
                "branch_name": webhook_job.branch_name or "unknown",
                "repo_name": orchestrator._get_repo_name(webhook_job),
            }

            print(f"[DEBUG] skybridge_context: {skybridge_context}")

            # === TESTE DO ADAPTER SPAWN ===
            print("\n[DEBUG] Chamando adapter.spawn()...")
            print(f"[DEBUG] job.event type: {type(webhook_job.event)}")
            print(f"[DEBUG] job.event.payload type: {type(webhook_job.event.payload)}")

            # ✅ ASSERT DE REGRESSÃO: Payload ainda é dict aqui
            assert isinstance(webhook_job.event.payload, dict), (
                f"REGRESSÃO: Payload virou {type(webhook_job.event.payload)} antes do adapter"
            )

            print(
                f"[DEBUG] job.event.payload.get('issue'): {webhook_job.event.payload.get('issue')}"
            )

            # Testa cada passo do _build_system_prompt
            print("\n[DEBUG] Testando _build_system_prompt passos:")

            # Passo 1: load_system_prompt_config
            print("[DEBUG] 1. load_system_prompt_config()...")
            from runtime.config.agent_prompts import load_system_prompt_config

            template = load_system_prompt_config()
            print(f"[DEBUG]    template type: {type(template)}")
            print(f"[DEBUG]    template keys: {list(template.keys()) if isinstance(template, dict) else 'N/A'}")

            # Passo 2: Constrói context
            print("[DEBUG] 2. Construindo context para render_system_prompt...")

            # ✅ ASSERT DE REGRESSÃO: Payload NÃO pode virar string antes de extrair issue
            assert isinstance(webhook_job.event.payload, dict), (
                f"REGRESSÃO: Payload virou {type(webhook_job.event.payload)} antes de extrair issue"
            )

            # ✅ ASSERT DE REGRESSÃO: issue.get() não pode falhar com AttributeError
            issue = webhook_job.event.payload.get("issue", {})
            assert isinstance(issue, dict), (
                f"REGRESSÃO: issue deve ser dict, mas é {type(issue)}"
            )

            context = {
                "worktree_path": webhook_job.worktree_path,
                "branch_name": webhook_job.branch_name or "unknown",
                "skill": "resolve-issue",
                "issue_number": webhook_job.issue_number or 0,
                # === PONTO CRÍTICO ===
                "issue_title": issue.get("title", ""),
                "issue_body": issue.get("body", ""),
                "repo_name": skybridge_context["repo_name"],
                "job_id": webhook_job.job_id,
            }

            print(f"[DEBUG]    context type: {type(context)}")
            print(f"[DEBUG]    context['issue_title']: {context.get('issue_title')}")
            print(f"[DEBUG]    context['issue_body'] type: {type(context.get('issue_body'))}")

            # Passo 3: render_system_prompt
            print("[DEBUG] 3. render_system_prompt()...")
            from runtime.config.agent_prompts import render_system_prompt

            try:
                system_prompt = render_system_prompt(template, context)
                print(f"[DEBUG]    system_prompt type: {type(system_prompt)}")
                print(f"[DEBUG]    system_prompt length: {len(system_prompt)}")
            except Exception as e:
                print(f"[DEBUG]    ERRO em render_system_prompt: {e}")
                raise

            # Passo 4: _build_main_prompt
            print("[DEBUG] 4. _build_main_prompt()...")

            # === PONTO CRÍTICO ===
            issue = webhook_job.event.payload.get("issue", {})
            print(f"[DEBUG]    issue type: {type(issue)}")
            print(f"[DEBUG]    issue: {issue}")

            main_prompt = (
                f"Resolve issue #{webhook_job.issue_number}: {issue.get('title', '')}\n\n"
                f"{issue.get('body', '')}"
            )

            print(f"[DEBUG]    main_prompt: {main_prompt[:100]}...")

            # Passo 5: _build_command
            print("[DEBUG] 5. _build_command()...")
            try:
                cmd = adapter._build_command(webhook_job.worktree_path, system_prompt)
                print(f"[DEBUG]    cmd: {' '.join(cmd[:5])}...")
            except Exception as e:
                print(f"[DEBUG]    ERRO em _build_command: {e}")
                raise

            # === TESTE DO SPAWN COMPLETO ===
            print("\n[DEBUG] Tentando adapter.spawn() completo...")
            print("=" * 80)

            # ✅ ASSERT DE REGRESSÃO FINAL: Payload ainda é dict no final do fluxo
            assert isinstance(webhook_job.event.payload, dict), (
                f"REGRESSÃO FINAL: Payload virou {type(webhook_job.event.payload)} no final do fluxo"
            )

            # ✅ ASSERT DE REGRESSÃO: Issue ainda existe e é dict
            final_issue = webhook_job.event.payload.get("issue")
            assert final_issue is not None, "REGRESSÃO: 'issue' desapareceu do payload"
            assert isinstance(final_issue, dict), (
                f"REGRESSÃO: 'issue' virou {type(final_issue)} no final do fluxo"
            )

            # ✅ ASSERT DE REGRESSÃO: Campos críticos existem
            assert "title" in final_issue, "REGRESSÃO: 'title' desapareceu de issue"
            assert "body" in final_issue, "REGRESSÃO: 'body' desapareceu de issue"

            # NOTA: Este teste NÃO chama subprocess (Claude Code não está instalado)
            # Ele apenas valida que os dados estão corretos até o ponto de spawn

            print("\n" + "=" * 80)
            print("[DEBUG] TESTE COMPLETO - Todas as validações passaram")
            print("=" * 80)

    def test_get_repo_name_does_not_cause_str_error(
        self, webhook_job, event_bus
    ):
        """
        Testa especificamente o _get_repo_name para identificar o problema.

        Este é um teste de regressão: garante que _get_repo_name não causa
        o erro "AttributeError: 'str' object has no attribute 'get'".
        """
        print("\n[DEBUG] Testando _get_repo_name()...")

        # ✅ ASSERT DE REGRESSÃO: Payload deve ser dict antes do teste
        assert isinstance(webhook_job.event.payload, dict), (
            f"REGRESSÃO: Payload deve ser dict, mas é {type(webhook_job.event.payload)}"
        )

        orchestrator = JobOrchestrator(
            job_queue=InMemoryJobQueue(),
            worktree_manager=Mock(),
            event_bus=event_bus,
        )

        # Valida payload antes
        print(f"[DEBUG] job.event.payload: {webhook_job.event.payload}")
        print(f"[DEBUG] job.event.payload type: {type(webhook_job.event.payload)}")

        # ✅ ASSERT DE REGRESSÃO: repository deve existir e ser dict
        repository = webhook_job.event.payload.get("repository")
        assert repository is not None, "REGRESSÃO: 'repository' desapareceu do payload"
        assert isinstance(repository, dict), (
            f"REGRESSÃO: 'repository' deve ser dict, mas é {type(repository)}"
        )

        # Chama _get_repo_name
        try:
            repo_name = orchestrator._get_repo_name(webhook_job)
            print(f"[DEBUG] repo_name: {repo_name}")
            assert repo_name == "h4mn/skybridge"
        except AttributeError as e:
            print(f"[DEBUG] ERRO em _get_repo_name: {e}")
            print(f"[DEBUG] Isso significa que algum .get() está sendo chamado em string")
            raise

        # ✅ ASSERT DE REGRESSÃO: Payload ainda é dict após _get_repo_name
        assert isinstance(webhook_job.event.payload, dict), (
            f"REGRESSÃO: Payload virou {type(webhook_job.event.payload)} após _get_repo_name"
        )

    def test_claude_adapter_build_system_prompt_with_real_data(
        self, webhook_job
    ):
        """
        Testa especificamente o ClaudeCodeAdapter._build_system_prompt.
        """
        print("\n[DEBUG] Testando ClaudeCodeAdapter._build_system_prompt()...")

        adapter = ClaudeCodeAdapter()

        skybridge_context = {
            "worktree_path": webhook_job.worktree_path,
            "branch_name": webhook_job.branch_name or "unknown",
            "repo_name": "h4mn/skybridge",
        }

        print(f"[DEBUG] skybridge_context: {skybridge_context}")

        try:
            system_prompt = adapter._build_system_prompt(
                webhook_job, "resolve-issue", skybridge_context
            )
            print(f"[DEBUG] system_prompt gerado com sucesso")
            print(f"[DEBUG] system_prompt length: {len(system_prompt)}")
        except AttributeError as e:
            print(f"[DEBUG] ERRO: {e}")
            print(f"[DEBUG] Provável causa: payload é string em vez de dict")
            print(f"[DEBUG] job.event.payload type: {type(webhook_job.event.payload)}")
            print(f"[DEBUG] job.event.payload value: {webhook_job.event.payload}")
            raise

    def test_payload_stays_dict_through_queue(
        self, webhook_job, github_webhook_payload
    ):
        """
        Testa que o payload permanece como dict através da fila.
        """
        print("\n[DEBUG] Testando payload através da fila...")

        job_queue = InMemoryJobQueue()

        # Enfileira
        asyncio.run(job_queue.enqueue(webhook_job))

        # Dequeue
        retrieved_job = asyncio.run(job_queue.dequeue())

        assert retrieved_job is not None
        assert isinstance(retrieved_job.event.payload, dict), (
            f"Payload após dequeue deve ser dict, mas é {type(retrieved_job.event.payload)}"
        )
        assert retrieved_job.event.payload == github_webhook_payload

        print(f"[DEBUG] Payload preservado corretamente através da fila")
