# -*- coding: utf-8 -*-
"""
E2E Scenarios — Demos end-to-end completas.

Port dos demos originais que demonstram fluxos completos
envolvendo múltiplos componentes (GitHub, Trello, Agent, etc.).
"""

from __future__ import annotations

import asyncio
from datetime import datetime
from os import getenv

from kernel import Result
from runtime.demo.base import (
    BaseDemo,
    DemoCategory,
    DemoContext,
    DemoLifecycle,
    DemoFlow,
    DemoFlowType,
    DemoResult,
)
from runtime.demo.registry import DemoRegistry


@DemoRegistry.register
class E2EDemo(BaseDemo):
    """
    Demonstração End-to-End da integração GitHub → Trello → Agent.

    Port de: src/core/kanban/testing/e2e_demo.py

    Fluxo completo:
    1. Webhook GitHub chega
    2. WebhookProcessor cria card no Trello
    3. JobOrchestrator executa agente
    4. Agente atualiza card com progresso
    5. Card marcado como DONE
    """

    demo_id = "e2e-github-trello-agent"
    demo_name = "E2E Demo - GitHub → Trello → Agent"
    description = "Demonstração E2E completa: webhook → Trello → agent → done"
    category = DemoCategory.E2E
    required_configs = ["TRELLO_API_KEY", "TRELLO_API_TOKEN", "TRELLO_BOARD_ID"]
    estimated_duration_seconds = 60
    tags = ["e2e", "github", "trello", "agent", "webhook", "complete"]
    related_issues = [36, 38, 40]
    lifecycle = DemoLifecycle.DEV
    last_reviewed = datetime.now().strftime("%Y-%m-%d")

    def define_flow(self) -> DemoFlow:
        return DemoFlow(
            flow_type=DemoFlowType.ISSUE_LIFECYCLE,
            description="Fluxo completo de issue desde webhook até conclusão pelo agente",
            actors=["GitHub", "WebhookProcessor", "TrelloIntegrationService", "MockAgent", "Trello"],
            steps=[
                "Webhook GitHub recebido (issues.opened)",
                "Card criado no Trello via TrelloIntegrationService",
                "Job criado e executado",
                "MockAgent executa com atualizações em tempo real",
                "Card marcado como DONE",
            ],
            entry_point="webhook",
            expected_outcome="Card no Trello criado e atualizado com progresso do agente, marcado como DONE",
        )

    async def validate_prerequisites(self) -> Result[None, str]:
        return await self._validate_configs()

    async def run(self, context: DemoContext) -> DemoResult:
        from infra.kanban.adapters.trello_adapter import TrelloAdapter
        from core.kanban.application.trello_integration_service import TrelloIntegrationService
        from core.webhooks.domain.webhook_event import WebhookEvent, WebhookSource, WebhookJob
        from core.agents.mock.mock_agent import MockAgent, MockAgentConfig, MockScenario

        api_key = getenv("TRELLO_API_KEY")
        api_token = getenv("TRELLO_API_TOKEN")
        board_id = getenv("TRELLO_BOARD_ID")

        trello_adapter = TrelloAdapter(api_key, api_token, board_id)
        trello_service = TrelloIntegrationService(trello_adapter)

        self.card_id: str | None = None
        self.job_id: str | None = None

        # Sample webhook payload
        payload = {
            "action": "opened",
            "issue": {
                "id": 123456789,
                "number": 42,
                "title": "[Feature] Implementar dark mode na interface do usuário",
                "body": "Usuários estão solicitando suporte a dark mode há meses.",
                "user": {"login": "dev-ux", "id": 12345},
                "labels": [{"name": "feature"}, {"name": "ui"}],
                "html_url": "https://github.com/skybridge/skybridge/issues/42",
                "state": "open",
                "created_at": "2025-01-17T00:00:00Z",
            },
            "repository": {
                "id": 987654321,
                "name": "skybridge",
                "full_name": "skybridge/skybridge",
                "owner": {"login": "skybridge"},
            },
            "sender": {"login": "dev-ux"},
        }

        issue_data = payload["issue"]

        # Step 1: Simula webhook recebido
        self.log_progress(1, 5, "Recebendo webhook GitHub...")
        self.log_info(f"Issue #{issue_data['number']}: {issue_data['title']}")
        self.log_info(f"Autor: @{issue_data['user']['login']}")

        # Step 2: Cria card no Trello
        self.log_progress(2, 5, "Criando card no Trello...")

        result = await trello_service.create_card_from_github_issue(
            issue_number=issue_data["number"],
            issue_title=issue_data["title"],
            issue_body=issue_data.get("body"),
            issue_url=issue_data["html_url"],
            author=issue_data["user"]["login"],
            repo_name=payload["repository"]["full_name"],
            labels=[l["name"] for l in issue_data.get("labels", [])],
        )

        if result.is_err:
            return DemoResult.error(f"Erro ao criar card: {result.error}")

        self.card_id = result.unwrap()
        self.log_success(f"Card criado: https://trello.com/c/{self.card_id}")

        # Step 3: Cria job
        self.log_progress(3, 5, "Criando job de processamento...")

        event = WebhookEvent(
            source=WebhookSource.GITHUB,
            event_type="issues.opened",
            event_id=str(payload["issue"]["number"]),
            payload=payload,
            received_at=datetime.utcnow(),
        )

        job = WebhookJob.create(event)
        job.metadata["trello_card_id"] = self.card_id
        self.job_id = job.job_id

        self.log_success(f"Job criado: {job.job_id}")

        # Step 4: Executa agente com atualizações
        self.log_progress(4, 5, "Executando agente MockAgent...")

        scenario = MockScenario.FIX_WEBHOOK_DEDUPLICATION
        config = MockAgentConfig(scenario=scenario)
        agent = MockAgent(config)

        self.log_info(f"Cenário: {scenario.name}")

        try:
            async for xml in agent.execute():
                await self._update_trello_from_xml(trello_adapter, xml)

            self.log_success("Agente concluído!")
        except Exception as e:
            return DemoResult.error(f"Erro na execução: {e}")

        # Step 5: Marca como DONE
        self.log_progress(5, 5, "Marcando card como DONE...")

        result = await trello_service.mark_card_complete(
            card_id=self.card_id,
            summary="Dark mode implementado com sucesso",
            changes=[
                "DarkToggle component criado",
                "ThemeContext adicionado",
                "CSS variables para temas configuradas",
                "Preferência salva em localStorage",
            ],
        )

        if result.is_err:
            return DemoResult.error(f"Erro ao marcar DONE: {result.error}")

        self.log_success("Card marcado como DONE!")

        return DemoResult.success(
            message="Fluxo E2E concluído com sucesso",
            card_url=f"https://trello.com/c/{self.card_id}",
            card_id=self.card_id,
            job_id=self.job_id,
        )

    async def _update_trello_from_xml(self, trello_adapter, xml: str) -> None:
        """Atualiza card no Trello baseado em XML do agente."""
        if not self.card_id:
            return

        if "<started>" in xml:
            self.log_info("Agente iniciado...")
            await trello_adapter.add_card_comment(
                card_id=self.card_id,
                comment=f"""🟡 **Agente Iniciado**

🕐 {datetime.now().strftime('%H:%M:%S')}
📋 Job: {self.job_id}

O agente está analisando a issue e preparando implementação..."""
            )
        elif "<progress>" in xml:
            phase_start = xml.find("<phase>") + 6
            phase_end = xml.find("</phase>")
            status_start = xml.find("<status>") + 7
            status_end = xml.find("</status>")

            if phase_start > 5 and phase_end > phase_start:
                phase = xml[phase_start:phase_end]
                status = xml[status_start:status_end] if status_start > 6 else "Processando..."

                self.log_info(f"{phase}: {status}")

                await trello_adapter.add_card_comment(
                    card_id=self.card_id,
                    comment=f"""🔄 **Progresso: {phase}**

🕐 {datetime.now().strftime('%H:%M:%S')}
{status}"""
                )
        elif "<completed>" in xml:
            self.log_info("Agente completado!")
            await trello_adapter.add_card_comment(
                card_id=self.card_id,
                comment=f"""✅ **Agente Concluído**

🕐 {datetime.now().strftime('%H:%M:%S')}

Implementação finalizada com sucesso!"""
            )


@DemoRegistry.register
class FinalDemo(BaseDemo):
    """
    DEMO FINAL da integração completa Skybridge ↔ Trello.

    Port de: src/core/kanban/testing/final_demo.py

    Mostra TODA a integração funcionando com MockJobQueue e MockWorktreeManager.
    """

    demo_id = "final-demo"
    demo_name = "DEMO FINAL - Skybridge + Trello"
    description = "Demo FINAL mostrando toda a integração funcionando (com mocks)"
    category = DemoCategory.E2E
    required_configs = ["TRELLO_API_KEY", "TRELLO_API_TOKEN", "TRELLO_BOARD_ID"]
    estimated_duration_seconds = 45
    tags = ["e2e", "final", "trello", "integration", "complete"]
    related_issues = [39]
    lifecycle = DemoLifecycle.DEV
    last_reviewed = datetime.now().strftime("%Y-%m-%d")

    def define_flow(self) -> DemoFlow:
        return DemoFlow(
            flow_type=DemoFlowType.ISSUE_LIFECYCLE,
            description="Demonstração final completa com todos os componentes integrados",
            actors=["WebhookProcessor", "MockJobQueue", "JobOrchestrator", "TrelloIntegrationService", "MockAgent"],
            steps=[
                "Webhook GitHub recebido",
                "Card criado no Trello automaticamente",
                "JobOrchestrator executa com atualizações em TEMPO REAL",
                "Card marcado como DONE",
            ],
            entry_point="webhook",
            expected_outcome="Demonstração completa da integração GitHub → Trello → Agent",
        )

    async def validate_prerequisites(self) -> Result[None, str]:
        return await self._validate_configs()

    async def run(self, context: DemoContext) -> DemoResult:
        from infra.kanban.adapters.trello_adapter import TrelloAdapter
        from core.kanban.application.trello_integration_service import TrelloIntegrationService
        from core.webhooks.application.webhook_processor import WebhookProcessor
        from core.webhooks.application.job_orchestrator import JobOrchestrator

        # Mock JobQueue
        class MockJobQueue:
            def __init__(self):
                self._jobs = {}

            async def enqueue(self, job):
                self._jobs[job.job_id] = job
                self.log_info(f"Job enfileirado: {job.job_id}")

            async def get_job(self, job_id: str):
                return self._jobs.get(job_id)

            async def complete(self, job_id: str, result: dict | None = None):
                if job_id in self._jobs:
                    self._jobs[job_id].mark_completed()

            def log_info(self, msg):
                from runtime.observability.logger import Colors
                print(f"  {Colors.INFO}✅{Colors.RESET} {msg}")

        # Mock WorktreeManager
        class MockWorktreeManager:
            def create_worktree(self, job):
                from runtime.observability.logger import Colors
                print(f"  {Colors.INFO}🌳{Colors.RESET} Worktree mock criada para job {job.job_id}")
                from kernel.contracts.result import Result
                job.worktree_path = f"/tmp/worktrees/{job.job_id}"
                job.branch_name = f"mock-branch-{job.job_id[:8]}"
                return Result.ok(job.worktree_path)

        # Sample issue
        SAMPLE_ISSUE = {
            "action": "opened",
            "issue": {
                "id": 123456789,
                "number": 99,
                "title": "[Feature] Implementar busca fuzzy em queries",
                "body": "Queries atuais usam busca exata. Usuários querem encontrar arquivos mesmo com erros.",
                "user": {"login": "dev-core", "id": 12345},
                "labels": [{"name": "feature"}, {"name": "enhancement"}],
                "html_url": "https://github.com/skybridge/skybridge/issues/99",
                "state": "open",
            },
            "repository": {
                "id": 987654321,
                "name": "skybridge",
                "full_name": "skybridge/skybridge",
                "owner": {"login": "skybridge"},
            },
            "sender": {"login": "dev-core"},
        }

        api_key = getenv("TRELLO_API_KEY")
        api_token = getenv("TRELLO_API_TOKEN")
        board_id = getenv("TRELLO_BOARD_ID")

        trello_adapter = TrelloAdapter(api_key, api_token, board_id)
        trello_service = TrelloIntegrationService(trello_adapter)

        # Inicializa componentes
        job_queue = MockJobQueue()
        worktree_manager = MockWorktreeManager()

        webhook_processor = WebhookProcessor(job_queue, trello_service)
        job_orchestrator = JobOrchestrator(job_queue, worktree_manager, trello_service=trello_service)

        issue_data = SAMPLE_ISSUE["issue"]
        self.log_progress(1, 2, f"Processando webhook: #{issue_data['number']} - {issue_data['title']}")

        # Processa webhook
        result = await webhook_processor.process_github_issue(SAMPLE_ISSUE, "issues.opened")

        if result.is_err:
            return DemoResult.error(f"Erro ao processar webhook: {result.error}")

        job_id = result.unwrap()
        self.log_success(f"Webhook processado: job_id={job_id}")

        # Executa job
        self.log_progress(2, 2, "Executando job com atualizações no Trello...")

        job_result = await job_orchestrator.execute_job(job_id)

        if job_result.is_err:
            return DemoResult.error(f"Erro ao executar job: {job_result.error}")

        job = await job_queue.get_job(job_id)
        card_id = job.metadata.get("trello_card_id")

        self.log_success(f"Job executado: {job_id}")
        self.log_info(f"Card: https://trello.com/c/{card_id}")

        return DemoResult.success(
            message="Demo FINAL concluída",
            card_url=f"https://trello.com/c/{card_id}",
            card_id=card_id,
            job_id=job_id,
        )
