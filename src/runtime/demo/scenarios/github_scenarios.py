# -*- coding: utf-8 -*-
"""
GitHub Scenarios — Demos de integração com GitHub.

Port dos demos originais que criam issues reais no GitHub
e observam o processamento via webhooks.
"""

from __future__ import annotations

import asyncio
import random
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
class GitHubRealFlowDemo(BaseDemo):
    """
    Demo FLUXO COMPLETO - GitHub REAL + Webhook Server + Trello REAL.

    Port de: src/core/kanban/testing/demo_github_real_flow.py

    Estratégia:
    1. FakeGitHubAgent cria issues REAIS no GitHub
    2. GitHub dispara webhook REAL para nosso servidor
    3. WebhookProcessor processa e cria card no Trello REAL
    4. JobOrchestrator executa e atualiza Trello em tempo real
    """

    demo_id = "github-real-flow"
    demo_name = "GitHub Real Flow Demo"
    description = "Fluxo completo: issues reais GitHub → webhook → Trello real"
    category = DemoCategory.GITHUB
    required_configs = ["GITHUB_TOKEN", "GITHUB_REPO", "TRELLO_API_KEY", "TRELLO_API_TOKEN", "TRELLO_BOARD_ID"]
    estimated_duration_seconds = 120
    tags = ["github", "real", "webhook", "trello", "e2e", "complete"]
    related_issues = [36, 38, 40]
    lifecycle = DemoLifecycle.DEV
    last_reviewed = datetime.now().strftime("%Y-%m-%d")

    def define_flow(self) -> DemoFlow:
        return DemoFlow(
            flow_type=DemoFlowType.WEBHOOK_PROCESSING,
            description="Fluxo completo com issues e webhooks reais do GitHub",
            actors=["FakeGitHubAgent", "GitHub", "Webhook Server", "WebhookProcessor", "TrelloIntegrationService", "Trello"],
            steps=[
                "FakeGitHubAgent cria issues REAIS no GitHub",
                "GitHub dispara webhook REAL para nosso servidor",
                "WebhookProcessor processa e cria card no Trello",
                "JobOrchestrator executa (se configurado)",
                "Trello card é atualizado em tempo real",
            ],
            entry_point="cli",
            expected_outcome="Issues criadas no GitHub e cards correspondentes no Trello",
        )

    async def validate_prerequisites(self) -> Result[None, str]:
        return await self._validate_configs()

    async def run(self, context: DemoContext) -> DemoResult:
        from core.agents.mock.fake_github_agent import (
            FakeGitHubAgent,
            RealisticIssueTemplates,
        )

        github_token = getenv("GITHUB_TOKEN")
        github_repo = getenv("GITHUB_REPO", "skybridge/skybridge")

        if not github_token:
            return DemoResult.error("GITHUB_TOKEN não configurado")

        owner, name = github_repo.split("/", 1)

        self.log_info(f"Repositório: {github_repo}")

        # Seleciona templates
        templates = RealisticIssueTemplates()
        available_issues = [
            templates.fuzzy_search_feature(),
            templates.webhook_deduplication_bug(),
            templates.trello_integration_feature(),
        ]

        num_issues = context.params.get("num_issues", 1)
        issues_to_create = available_issues[:num_issues]

        self.log_info(f"Criando {len(issues_to_create)} issue(s)...")

        # Cria issues
        async with FakeGitHubAgent(owner, name, github_token) as agent:
            created_urls = []

            for i, issue in enumerate(issues_to_create):
                self.log_progress(i + 1, len(issues_to_create), f"Criando issue: {issue.title[:50]}...")

                response = await agent.create_issue(issue)

                if response:
                    data = response.json()
                    url = data["html_url"]
                    number = data["number"]
                    created_urls.append((number, url))

                    self.log_success(f"Issue #{number} criada: {url}")
                else:
                    self.log_error(f"Falha ao criar issue")

                if i < len(issues_to_create) - 1:
                    await asyncio.sleep(2)

        self.log_info("\n📋 Issues criadas com sucesso!")
        self.log_info("💡 Próximos passos:")
        self.log_info("   1. GitHub enviará webhook para seu servidor via ngrok")
        self.log_info("   2. WebhookProcessor receberá e processará")
        self.log_info("   3. Trello cards serão criados automaticamente")

        return DemoResult.success(
            message=f"{len(created_urls)} issue(s) criada(s)",
            issues_created=[{"number": n, "url": u} for n, u in created_urls],
            repo_url=f"https://github.com/{github_repo}",
        )


@DemoRegistry.register
class GitHubToTrelloSimpleDemo(BaseDemo):
    """
    Demo SIMPLES - GitHub → Trello (Fluxo Completo).

    Port de: src/core/kanban/testing/demo_github_to_trello.py

    Cria uma issue REAL no GitHub e observa:
    1. Issue criada no GitHub
    2. Webhook enviado para nosso servidor
    3. Card criado no Trello
    4. Link do card para verificar
    """

    demo_id = "github-to-trello-simple"
    demo_name = "GitHub → Trello Simple Demo"
    description = "Demo simples: cria issue GitHub e observa card ser criado no Trello"
    category = DemoCategory.GITHUB
    required_configs = ["GITHUB_TOKEN", "GITHUB_REPO"]
    estimated_duration_seconds = 30
    tags = ["github", "trello", "simple", "webhook", "quick"]
    related_issues = [36, 38]
    lifecycle = DemoLifecycle.DEV
    last_reviewed = datetime.now().strftime("%Y-%m-%d")

    def define_flow(self) -> DemoFlow:
        return DemoFlow(
            flow_type=DemoFlowType.CARD_SYNC,
            description="Demo simples de sincronização GitHub → Trello",
            actors=["FakeGitHubAgent", "GitHub", "Webhook Server", "TrelloIntegrationService"],
            steps=[
                "Issue criada no GitHub",
                "Webhook enviado para nosso servidor",
                "Card criado no Trello",
                "Link do card para verificar",
            ],
            entry_point="cli",
            expected_outcome="Issue no GitHub e card correspondente no Trello",
        )

    async def validate_prerequisites(self) -> Result[None, str]:
        return await self._validate_configs()

    async def run(self, context: DemoContext) -> DemoResult:
        from core.agents.mock.fake_github_agent import (
            FakeGitHubAgent,
            RealisticIssueTemplates,
        )

        github_token = getenv("GITHUB_TOKEN")
        github_repo = getenv("GITHUB_REPO", "h4mn/skybridge")

        if not github_token:
            return DemoResult.error("GITHUB_TOKEN não configurado")

        owner, name = github_repo.split("/", 1)

        # Seleciona template
        templates = RealisticIssueTemplates()

        # Mapa de opções para templates
        issue_map = {
            "1": templates.fuzzy_search_feature(),
            "2": templates.webhook_deduplication_bug(),
            "3": templates.trello_integration_feature(),
            "4": templates.agent_orchestrator_refactor(),
            "5": templates.rate_limiting_feature(),
        }

        # Seleção baseada em parâmetro ou aleatório
        choice = context.params.get("issue_choice", "1")
        issue = issue_map.get(choice, templates.fuzzy_search_feature())

        self.log_info(f"Criando issue: {issue.title}")
        self.log_info(f"Labels: {', '.join(issue.labels)}")

        # Cria issue
        async with FakeGitHubAgent(owner, name, github_token) as agent:
            response = await agent.create_issue(issue)

            if not response:
                return DemoResult.error("Falha ao criar issue")

            data = response.json()
            issue_number = data["number"]
            issue_url = data["html_url"]

            self.log_success(f"Issue #{issue_number} criada!")
            self.log_info(f"URL: {issue_url}")

            self.log_info("\n💡 O que acontece AGORA:")
            self.log_info("   1. GitHub envia webhook para seu servidor via ngrok")
            self.log_info("   2. Webhook Server recebe e processa")
            self.log_info("   3. TrelloIntegrationService cria card")
            self.log_info("   4. Card aparece no Trello com dados da issue")

            self.log_info(f"\n📋 Verifique:")
            self.log_info(f"   • Logs do servidor webhook")
            self.log_info(f"   • Board do Trello (cards devem aparecer)")
            self.log_info(f"   • Issue: {issue_url}")

            # Aguarda um pouco para o webhook ser processado
            self.log_info("\n⏱️  Aguardando 5 segundos para webhook ser processado...")
            await asyncio.sleep(5)

            return DemoResult.success(
                message="Issue criada, aguardando processamento do webhook",
                issue_number=issue_number,
                issue_url=issue_url,
                repo=github_repo,
            )
