# -*- coding: utf-8 -*-
"""
Trello Scenarios — Demos de integração com Trello.

Port dos demos originais em src/core/kanban/testing/ para a nova
estrutura do Demo Engine.
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
class TrelloFlowDemo(BaseDemo):
    """
    Demo do fluxo de trabalho com Trello.

    Port de: src/core/kanban/testing/trello_flow_demo.py

    Demonstra o ciclo de vida de um agente executando uma tarefa,
    atualizando um card no Trello em cada etapa do fluxo.
    """

    demo_id = "trello-flow"
    demo_name = "Trello Flow Demo"
    description = "Demonstra o fluxo completo de agente com Trello (5 steps)"
    category = DemoCategory.TRELLO
    required_configs = ["TRELLO_API_KEY", "TRELLO_API_TOKEN", "TRELLO_BOARD_ID"]
    estimated_duration_seconds = 30
    tags = ["trello", "agent", "flow", "webhook"]
    related_issues = []
    lifecycle = DemoLifecycle.DEV
    last_reviewed = datetime.now().strftime("%Y-%m-%d")

    def define_flow(self) -> DemoFlow:
        return DemoFlow(
            flow_type=DemoFlowType.AGENT_ITERATION,
            description="Ciclo de vida de execução de agente com atualizações no Trello",
            actors=["Agent", "TrelloAdapter", "Trello"],
            steps=[
                "Card criado (TODO)",
                "Agente inicia execução (IN_PROGRESS)",
                "Agente processa (atualiza descrição)",
                "Agente finaliza (DONE)",
            ],
            entry_point="cli",
            expected_outcome="Card no Trello com comentários de progresso em cada etapa",
        )

    async def validate_prerequisites(self) -> Result[None, str]:
        return await self._validate_configs()

    async def run(self, context: DemoContext) -> DemoResult:
        from infra.kanban.adapters.trello_adapter import TrelloAdapter

        api_key = getenv("TRELLO_API_KEY")
        api_token = getenv("TRELLO_API_TOKEN")
        board_id = getenv("TRELLO_BOARD_ID")

        adapter = TrelloAdapter(api_key, api_token, board_id)
        self.card_id: str | None = None

        # Captura snapshot ANTES
        exec_logger = context.metadata.get("exec_logger")
        if exec_logger:
            self.log_info("📸 Capturando snapshot ANTES...")
            await self.capture_trello_before(exec_logger, board_id)

        # Step 1: Criar card
        self.log_progress(1, 5, "Criando card no Trello...")
        card_result = await self._create_card(adapter)
        if card_result.is_err:
            return DemoResult.error(f"Erro ao criar card: {card_result.error}")

        # Step 2: Iniciar agente
        self.log_progress(2, 5, "Iniciando agente mock...")
        start_result = await self._start_agent(adapter)
        if start_result.is_err:
            return DemoResult.error(f"Erro ao iniciar: {start_result.error}")

        # Step 3: Agente processando
        self.log_progress(3, 5, "Agente processando...")
        thinking_result = await self._agent_thinking(adapter)
        if thinking_result.is_err:
            return DemoResult.error(f"Erro no processamento: {thinking_result.error}")

        # Step 4: Agente executando
        self.log_progress(4, 5, "Agente executando tarefas...")
        exec_result = await self._agent_executing(adapter)
        if exec_result.is_err:
            return DemoResult.error(f"Erro na execução: {exec_result.error}")

        # Step 5: Finalizar
        self.log_progress(5, 5, "Finalizando tarefa...")
        complete_result = await self._complete_task(adapter)
        if complete_result.is_err:
            return DemoResult.error(f"Erro ao finalizar: {complete_result.error}")

        # Captura snapshot DEPOIS
        if exec_logger:
            self.log_info("📸 Capturando snapshot DEPOIS...")
            after_id, before_id, diff_id = await self.capture_trello_after(exec_logger, board_id)

            self.log_success(f"Snapshots: before={before_id}, after={after_id}")
            if diff_id:
                self.log_success(f"Diff: {diff_id}")

        self.log_success("Fluxo concluído com sucesso!")

        return DemoResult.success(
            message="Fluxo completo executado",
            card_url=f"https://trello.com/c/{self.card_id}",
            card_id=self.card_id,
            snapshot_before=before_id,
            snapshot_after=after_id,
            diff_id=diff_id,
        )

    async def _create_card(self, adapter) -> Result[None, str]:
        title = f"[TESTE] Agente Mock - {datetime.now().strftime('%H:%M:%S')}"
        description = f"""**Tarefa de Teste**

Este card demonstra o fluxo de integração entre agentes e Trello.

**Status:** 🔵 Criado
**Agente:** MockAgent v1.0
**Início:** {datetime.now().isoformat()}

---
*Este card será atualizado automaticamente durante o teste.*"""

        result = await adapter.create_card(
            title=title,
            description=description,
            list_name="🎯 Foco Janeiro - Março",
        )

        if result.is_ok:
            self.card_id = result.unwrap().id
            self.log_success(f"Card criado: {result.unwrap().url}")
            return Result.ok(None)
        else:
            self.log_error(f"Erro ao criar card: {result.error}")
            return result

    async def _start_agent(self, adapter) -> Result[None, str]:
        result = await adapter.add_card_comment(
            card_id=self.card_id,
            comment="""🟡 **Em Progresso**

Agente: MockAgent v1.0
Passo: Inicializando ambiente de execução...""",
        )

        if result.is_ok:
            self.log_success("Status atualizado no Trello")
            return Result.ok(None)
        else:
            return Result.err(result.error)

    async def _agent_thinking(self, adapter) -> Result[None, str]:
        await asyncio.sleep(2)

        result = await adapter.add_card_comment(
            card_id=self.card_id,
            comment="""🟡 **Processando**

Passo: Analisando requisitos e planejando execução...

**Progresso:**
- ✅ Ambiente inicializado
- ✅ Dependências verificadas
- 🔄 Executando análise...""",
        )

        if result.is_ok:
            self.log_success("Progresso registrado no Trello")
            return Result.ok(None)
        else:
            return Result.err(result.error)

    async def _agent_executing(self, adapter) -> Result[None, str]:
        await asyncio.sleep(2)

        result = await adapter.add_card_comment(
            card_id=self.card_id,
            comment="""🟢 **Quase pronto!**

Passo: Executando implementação...

**Progresso:**
- ✅ Ambiente inicializado
- ✅ Análise concluída
- ✅ Implementação realizada
- ✅ Testes validados
- 🔄 Finalizando...

A implementação foi concluída com sucesso!""",
        )

        if result.is_ok:
            self.log_success("Ações registradas no Trello")
            return Result.ok(None)
        else:
            return Result.err(result.error)

    async def _complete_task(self, adapter) -> Result[None, str]:
        result = await adapter.add_card_comment(
            card_id=self.card_id,
            comment=f"""✅ **Concluído!**

Agente: MockAgent v1.0
Finalizado: {datetime.now().isoformat()}

**Resumo da Execução:**
- ✅ Ambiente inicializado
- ✅ Análise concluída
- ✅ Implementação realizada
- ✅ Testes validados
- ✅ Tarefa finalizada

Fluxo de demonstração concluído com sucesso! 🎉""",
        )

        if result.is_ok:
            self.log_success("Tarefa concluída no Trello")
            return Result.ok(None)
        else:
            return Result.err(result.error)


@DemoRegistry.register
class MockAgentTrelloDemo(BaseDemo):
    """
    Demo de MockAgent integrado com Trello.

    Port de: src/core/kanban/testing/mock_agent_trello_demo.py

    Demonstra o fluxo E2E:
    1. Cria card no Trello com issue realista
    2. Executa MockAgent com cenário Skybridge
    3. Atualiza card com XML progressivo
    4. Marca como DONE ao finalizar
    """

    demo_id = "mock-agent-trello"
    demo_name = "Mock Agent + Trello Demo"
    description = "MockAgent integrado com Trello usando cenários realistas"
    category = DemoCategory.TRELLO
    required_configs = ["TRELLO_API_KEY", "TRELLO_API_TOKEN", "TRELLO_BOARD_ID"]
    estimated_duration_seconds = 45
    tags = ["trello", "agent", "mock", "scenarios"]
    related_issues = []
    lifecycle = DemoLifecycle.DEV
    last_reviewed = datetime.now().strftime("%Y-%m-%d")

    def define_flow(self) -> DemoFlow:
        return DemoFlow(
            flow_type=DemoFlowType.AGENT_ITERATION,
            description="MockAgent executa cenário realista e atualiza Trello em tempo real",
            actors=["MockAgent", "TrelloAdapter", "Trello"],
            steps=[
                "Card criado a partir de cenário",
                "MockAgent executado",
                "Trello atualizado com progresso XML",
                "Card marcado como concluído",
            ],
            entry_point="cli",
            expected_outcome="Card no Trello com comentários de progresso do MockAgent",
        )

    async def validate_prerequisites(self) -> Result[None, str]:
        return await self._validate_configs()

    async def run(self, context: DemoContext) -> DemoResult:
        from infra.kanban.adapters.trello_adapter import TrelloAdapter
        from core.agents.mock.mock_agent import MockAgent, MockAgentConfig, MockScenario
        import random

        api_key = getenv("TRELLO_API_KEY")
        api_token = getenv("TRELLO_API_TOKEN")
        board_id = getenv("TRELLO_BOARD_ID")

        adapter = TrelloAdapter(api_key, api_token, board_id)
        self.card_id: str | None = None

        # Escolhe cenário aleatório
        scenario = random.choice(list(MockScenario))

        self.log_info(f"Cenário: {scenario.name}")
        self.log_info(scenario.value.split('\n')[0])

        # Step 1: Criar card
        self.log_progress(1, 3, "Criando card no Trello...")

        description = scenario.value
        lines = description.split('\n')
        title = lines[0]

        full_description = f"""**[MOCK/TESTE] - Demonstração de Integração**

{description}

---
**Meta:** Este card simula a resolução de uma issue real da Skybridge.
**Início:** {datetime.now().isoformat()}
**Agente:** MockAgent v1.0
"""

        result = await adapter.create_card(
            title=title,
            description=full_description,
            list_name="🎯 Foco Janeiro - Março",
        )

        if result.is_err:
            return DemoResult.error(f"Erro ao criar card: {result.error}")

        self.card_id = result.unwrap().id
        self.log_success(f"Card criado: {result.unwrap().url}")

        # Step 2: Executar MockAgent
        self.log_progress(2, 3, "Executando MockAgent...")

        config = MockAgentConfig(scenario=scenario)
        agent = MockAgent(config)

        try:
            async for xml in agent.execute():
                await self._update_trello_from_xml(adapter, xml)
                self.log_info("Progresso enviado ao Trello")

            self.log_success("MockAgent concluído")
        except Exception as e:
            return DemoResult.error(f"Erro na execução: {e}")

        # Step 3: Marcar done
        self.log_progress(3, 3, "Marcando card como concluído...")

        result = await adapter.add_card_comment(
            card_id=self.card_id,
            comment=f"""---
🎉 **Demonstração Concluída**

**Agente:** MockAgent
**Finalizado:** {datetime.now().isoformat()}

Este foi um teste de integração usando o MockAgent.
Em produção, o ClaudeCodeAgent executaria de forma similar.

---
*Tags: MOCK/TESTE*"""
        )

        if result.is_err:
            return DemoResult.error(f"Erro ao finalizar: {result.error}")

        self.log_success("Card finalizado!")

        return DemoResult.success(
            message="Demonstração concluída",
            card_url=f"https://trello.com/c/{self.card_id}",
            card_id=self.card_id,
            scenario=scenario.name,
        )

    async def _update_trello_from_xml(self, adapter, xml: str) -> None:
        """Processa XML e atualiza card no Trello."""
        if not self.card_id:
            return

        if "<started>" in xml:
            await adapter.add_card_comment(
                card_id=self.card_id,
                comment=f"""🟡 **[MOCK] Agente Iniciado**

🕐 {datetime.now().strftime('%H:%M:%S')}
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

                await adapter.add_card_comment(
                    card_id=self.card_id,
                    comment=f"""🔄 **[MOCK] {phase}**

🕐 {datetime.now().strftime('%H:%M:%S')}
{status}"""
                )
        elif "<completed>" in xml:
            await adapter.add_card_comment(
                card_id=self.card_id,
                comment=f"""✅ **[MOCK] Concluído!**

🕐 {datetime.now().strftime('%H:%M:%S')}
Implementação finalizada com sucesso.

Ver detalhes no card para resumo completo."""
            )


@DemoRegistry.register
class GitHubToTrelloDemo(BaseDemo):
    """
    Demo de integração GitHub → Trello.

    Port de: src/core/kanban/testing/github_to_trello_demo.py

    Simula webhooks do GitHub criando issues automaticamente no Trello.
    """

    demo_id = "github-to-trello"
    demo_name = "GitHub → Trello Demo"
    description = "Simula webhooks GitHub criando cards automaticamente no Trello"
    category = DemoCategory.TRELLO
    required_configs = ["TRELLO_API_KEY", "TRELLO_API_TOKEN", "TRELLO_BOARD_ID"]
    estimated_duration_seconds = 60
    tags = ["github", "trello", "webhook", "sync"]
    related_issues = []
    lifecycle = DemoLifecycle.DEV
    last_reviewed = datetime.now().strftime("%Y-%m-%d")

    def define_flow(self) -> DemoFlow:
        return DemoFlow(
            flow_type=DemoFlowType.CARD_SYNC,
            description="Sincronização de issues do GitHub para cards do Trello",
            actors=["GitHub", "TrelloIntegrationService", "Trello"],
            steps=[
                "Webhook simulado (issues.opened)",
                "Card criado no Trello com dados da issue",
                "Comentário de confirmação adicionado",
            ],
            entry_point="webhook",
            expected_outcome="Card no Trello criado a partir de issue GitHub",
        )

    async def validate_prerequisites(self) -> Result[None, str]:
        return await self._validate_configs()

    async def run(self, context: DemoContext) -> DemoResult:
        from infra.kanban.adapters.trello_adapter import TrelloAdapter
        from core.kanban.application.trello_integration_service import TrelloIntegrationService

        api_key = getenv("TRELLO_API_KEY")
        api_token = getenv("TRELLO_API_TOKEN")
        board_id = getenv("TRELLO_BOARD_ID")

        trello_adapter = TrelloAdapter(api_key, api_token, board_id)
        service = TrelloIntegrationService(trello_adapter)

        # Issues realistas
        issues_data = [
            {
                "title": "[Feature] Adicionar suporte a webhooks do GitLab",
                "body": """## Contexto
Atualmente só suportamos webhooks do GitHub. O GitLab é muito popular em empresas.

## Requisitos
- Implementar `GitlabWebhookProcessor`
- Suportar eventos: `issue.opened`, `merge_request.opened`
- Adaptar `JobOrchestrator` para ser agnóstico à fonte""",
                "author": "dev-senior",
                "labels": ["feature", "gitlab", "high-priority"],
            },
            {
                "title": "[Bug] Worktrees não estão sendo limpas após job finalizar",
                "body": """## Problema
Worktrees criadas pelo `JobOrchestrator` permanecem em `_worktrees/` após o job finalizar.

## Impacto
Consumo de disco cresce indefinidamente. Em 1 semana: ~5GB de worktrees órfãs.""",
                "author": "devops",
                "labels": ["bug", "cleanup", "urgent"],
            },
        ]

        num_issues = context.params.get("num_issues", 1)
        self.log_info(f"Simulando {num_issues} issue(s) do GitHub...")

        cards_created = []

        for i in range(min(num_issues, len(issues_data))):
            issue = issues_data[i]
            issue_number = 123 + i

            self.log_progress(i + 1, num_issues, f"Processando issue #{issue_number}...")

            self.log_info(f"Issue: {issue['title']}")
            self.log_info(f"Autor: @{issue['author']}")
            self.log_info(f"Labels: {', '.join(issue['labels'])}")

            await asyncio.sleep(0.5)

            result = await service.create_card_from_github_issue(
                issue_number=issue_number,
                issue_title=issue["title"],
                issue_body=issue["body"],
                issue_url=f"https://github.com/skybridge/skybridge/issues/{issue_number}",
                author=issue["author"],
                repo_name="skybridge/skybridge",
                labels=issue["labels"],
            )

            if result.is_err:
                self.log_error(f"Erro: {result.error}")
                continue

            card_id = result.unwrap()
            card_url = f"https://trello.com/c/{card_id}"
            cards_created.append(card_url)

            self.log_success(f"Card criado: {card_url}")

            if i < num_issues - 1:
                await asyncio.sleep(2)

        return DemoResult.success(
            message=f"{len(cards_created)} card(s) criado(s)",
            cards_created=cards_created,
            board_url=f"https://trello.com/b/{board_id}",
        )
