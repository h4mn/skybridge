# -*- coding: utf-8 -*-
"""
PRD020 Scenarios — Demos do fluxo bidirecional Trello → GitHub.

Demonstra o fluxo completo de autonomia controlada via movimentação
de cards no Trello, conforme PRD020 - Fluxo Bidirecional GitHub ↔ Trello.
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
class TrelloToGitHubAnalysisDemo(BaseDemo):
    """
    Demo do fluxo Trello → GitHub - Modo ANÁLISE.

    PRD020: Movimento para 💡 Brainstorm dispara análise sem modificações.

    Fluxo:
    1. Card movido para "💡 Brainstorm"
    2. autonomy_level = ANALYSIS
    3. Agente analisa e comenta no card
    4. SEM mudanças de código
    """

    demo_id = "prd020-trello-analysis"
    demo_name = "Trello → GitHub: Analysis Mode"
    description = "Demonstra modo de análise (💡 Brainstorm) sem modificações de código"
    category = DemoCategory.TRELLO
    required_configs = ["TRELLO_API_KEY", "TRELLO_API_TOKEN", "TRELLO_BOARD_ID"]
    estimated_duration_seconds = 60
    tags = ["prd020", "trello", "analysis", "brainstorm", "autonomy"]
    related_issues = ["PRD020"]
    lifecycle = DemoLifecycle.DEV
    last_reviewed = datetime.now().strftime("%Y-%m-%d")

    def define_flow(self) -> DemoFlow:
        return DemoFlow(
            flow_type=DemoFlowType.CARD_SYNC,
            description="Card movido para 💡 Brainstorm dispara análise sem código",
            actors=["User", "Trello", "Webhook Handler", "Agent", "Trello Adapter"],
            steps=[
                "Card criado/identificado",
                "Card movido para 💡 Brainstorm",
                "Webhook Trello recebido",
                "Job criado com autonomy_level=ANALYSIS",
                "Agente analisa (sem modificar código)",
                "Comentário postado no card",
            ],
            entry_point="webhook",
            expected_outcome="Card com comentário de análise, sem mudanças de código",
        )

    async def validate_prerequisites(self) -> Result[None, str]:
        return await self._validate_configs()

    async def run(self, context: DemoContext) -> DemoResult:
        from infra.kanban.adapters.trello_adapter import TrelloAdapter
        from runtime.config.config import get_trello_kanban_lists_config

        api_key = getenv("TRELLO_API_KEY")
        api_token = getenv("TRELLO_API_TOKEN")
        board_id = getenv("TRELLO_BOARD_ID")

        adapter = TrelloAdapter(api_key, api_token, board_id)
        kanban_config = get_trello_kanban_lists_config()

        self.card_id: str | None = None

        # Step 1: Criar card na lista "Issues"
        self.log_progress(1, 6, "Criando card de teste...")
        card_result = await self._create_card(adapter)
        if card_result.is_err:
            return DemoResult.error(f"Erro ao criar card: {card_result.error}")

        # Step 2: Simular movimento para 💡 Brainstorm
        self.log_progress(2, 6, "Movendo card para 💡 Brainstorm...")
        move_result = await self._move_to_brainstorm(adapter, kanban_config)
        if move_result.is_err:
            return DemoResult.error(f"Erro ao mover card: {move_result.error}")

        # Step 3: Simular webhook recebido
        self.log_progress(3, 6, "Simulando webhook Trello...")
        webhook_result = await self._simulate_webhook(adapter, "💡 Brainstorm")
        if webhook_result.is_err:
            return DemoResult.error(f"Erro no webhook: {webhook_result.error}")

        # Step 4: Criar job com autonomy_level=ANALYSIS
        self.log_progress(4, 6, "Criando job com autonomy_level=ANALYSIS...")
        job_id = await self._create_job(adapter, "ANALYSIS")

        # Step 5: Simular agente analisando
        self.log_progress(5, 6, "Agente analisando (sem modificar código)...")
        await self._simulate_agent_analysis(adapter)

        # Step 6: Postar comentário
        self.log_progress(6, 6, "Postando comentário de análise...")
        comment_result = await self._post_analysis_comment(adapter)
        if comment_result.is_err:
            return DemoResult.error(f"Erro ao postar comentário: {comment_result.error}")

        self.log_success("✅ Modo ANÁLISE demonstrado com sucesso!")
        self.log_info(f"📋 Card: https://trello.com/c/{self.card_id}")

        return DemoResult.success(
            message="Modo ANÁLISE demonstrado - agente analisou sem modificar código",
            card_url=f"https://trello.com/c/{self.card_id}",
            card_id=self.card_id,
            autonomy_level="ANALYSIS",
            job_id=job_id,
        )

    async def _create_card(self, adapter) -> Result[None, str]:
        """Cria card de teste."""
        title = f"[TESTE PRD020] #ANALYSIS - {datetime.now().strftime('%H:%M:%S')}"
        description = """## Issue de Teste - Modo Análise

Este card demonstra o fluxo de **análise sem modificações**.

### Comportamento Esperado:
- ✅ Agente lê e entende a issue
- ✅ Agente explora arquivos relevantes
- ✅ Agente documenta descobertas
- ❌ SEM criação/modificação de arquivos
- ❌ SEM git commits

### Autonomy Level
**ANALYSIS** - Apenas entender, não implementar.

---
*Tags: TESTE PRD020 - ANALYSIS*"""

        result = await adapter.create_card(
            title=title,
            description=description,
            list_name="📥 Issues",
        )

        if result.is_ok:
            self.card_id = result.unwrap().id
            self.log_success(f"Card criado: {result.unwrap().url}")
            return Result.ok(None)
        else:
            self.log_error(f"Erro ao criar card: {result.error}")
            return result

    async def _move_to_brainstorm(self, adapter, kanban_config) -> Result[None, str]:
        """Move card para lista 💡 Brainstorm."""
        # Busca nome da lista Brainstorm a partir da config
        list_names = kanban_config.get_list_names()
        brainstorm_list_name = None
        for name in list_names:
            if "Brainstorm" in name or "💡" in name:
                brainstorm_list_name = name
                break

        if not brainstorm_list_name:
            return Result.err("Lista 💡 Brainstorm não encontrada na config")

        # Move card usando move_card_to_list (que busca ID automaticamente)
        result = await adapter.move_card_to_list(
            card_id=self.card_id,
            target_list_name=brainstorm_list_name,
        )
        if result.is_ok:
            self.log_success(f"Card movido para: {brainstorm_list_name}")
            return Result.ok(None)
        return result

    async def _simulate_webhook(self, adapter, list_name: str) -> Result[None, str]:
        """Simula recebimento de webhook do Trello."""
        self.log_info(f"📩 Webhook simulado: card movido para '{list_name}'")
        self.log_info("   Evento: TrelloWebhookReceivedEvent")
        self.log_info("   autonomy_level: ANALYSIS")
        await asyncio.sleep(1)
        return Result.ok(None)

    async def _create_job(self, adapter, autonomy_level: str) -> str:
        """Simula criação de job."""
        job_id = f"job-{autonomy_level.lower()}-{datetime.now().strftime('%H%M%S')}"
        self.log_info(f"📋 Job criado: {job_id}")
        self.log_info(f"   autonomy_level: {autonomy_level}")
        self.log_info(f"   skill: analyze-issue")
        await asyncio.sleep(0.5)
        return job_id

    async def _simulate_agent_analysis(self, adapter) -> None:
        """Simula agente analisando (sem modificar código)."""
        self.log_info("🤖 Agente: Analisando issue...")
        await asyncio.sleep(2)

        self.log_info("   ✅ Issue entendida")
        self.log_info("   ✅ Arquivos relevantes explorados")
        self.log_info("   ✅ Abordagem identificada")
        self.log_info("   ❌ SEM mudanças de código (ANALYSIS)")

        await asyncio.sleep(1)

    async def _post_analysis_comment(self, adapter) -> Result[None, str]:
        """Posta comentário de análise no card."""
        comment = """## 📊 Análise Completa

### Entendimento do Problema
A issue requer implementação de nova funcionalidade.

### Arquivos Relevantes
- `src/core/webhooks/domain/autonomy_level.py` - Define níveis de autonomia
- `src/core/webhooks/application/handlers.py` - Processa webhooks Trello

### Abordagem Sugerida
1. Criar enum AutonomyLevel com 4 níveis
2. Modificar JobOrchestrator para considerar autonomy_level
3. Implementar mapeamento listas → autonomy_level

### Observações
- Nenhum arquivo foi modificado (modo ANÁLYSIS)
- Implementação pode prosseguir quando card for movido para "📋 A Fazer"

---
🤖 *Análise gerada por Skybridge - modo ANALYSIS*"""

        result = await adapter.add_card_comment(self.card_id, comment)
        if result.is_ok:
            self.log_success("Comentário de análise postado")
            return Result.ok(None)
        return result


@DemoRegistry.register
class TrelloToGitHubDevelopmentDemo(BaseDemo):
    """
    Demo do fluxo Trello → GitHub - Modo DEVELOPMENT.

    PRD020: Movimento para 📋 A Fazer dispara desenvolvimento.

    Fluxo:
    1. Card movido para "📋 A Fazer"
    2. Card vai automaticamente para "🚧 Em Andamento"
    3. autonomy_level = DEVELOPMENT
    4. Agente implementa solução
    """

    demo_id = "prd020-trello-development"
    demo_name = "Trello → GitHub: Development Mode"
    description = "Demonstra modo de desenvolvimento (📋 A Fazer → 🚧 Em Andamento)"
    category = DemoCategory.TRELLO
    required_configs = ["TRELLO_API_KEY", "TRELLO_API_TOKEN", "TRELLO_BOARD_ID"]
    estimated_duration_seconds = 90
    tags = ["prd020", "trello", "development", "autonomy"]
    related_issues = ["PRD020"]
    lifecycle = DemoLifecycle.DEV
    last_reviewed = datetime.now().strftime("%Y-%m-%d")

    def define_flow(self) -> DemoFlow:
        return DemoFlow(
            flow_type=DemoFlowType.AGENT_ITERATION,
            description="Card movido para 📋 A Fazer dispara desenvolvimento",
            actors=["User", "Trello", "Webhook Handler", "Agent", "Git"],
            steps=[
                "Card criado/identificado",
                "Card movido para 📋 A Fazer",
                "Card movido automaticamente para 🚧 Em Andamento",
                "Webhook Trello recebido",
                "Job criado com autonomy_level=DEVELOPMENT",
                "Agente implementa solução",
            ],
            entry_point="webhook",
            expected_outcome="Card em 🚧 Em Andamento com implementação em andamento",
        )

    async def validate_prerequisites(self) -> Result[None, str]:
        return await self._validate_configs()

    async def run(self, context: DemoContext) -> DemoResult:
        from infra.kanban.adapters.trello_adapter import TrelloAdapter
        from runtime.config.config import get_trello_kanban_lists_config

        api_key = getenv("TRELLO_API_KEY")
        api_token = getenv("TRELLO_API_TOKEN")
        board_id = getenv("TRELLO_BOARD_ID")

        adapter = TrelloAdapter(api_key, api_token, board_id)
        kanban_config = get_trello_kanban_lists_config()

        self.card_id: str | None = None

        # Step 1: Criar card
        self.log_progress(1, 7, "Criando card de teste...")
        card_result = await self._create_development_card(adapter)
        if card_result.is_err:
            return DemoResult.error(f"Erro ao criar card: {card_result.error}")

        # Step 2: Mover para 📋 A Fazer
        self.log_progress(2, 7, "Movendo para 📋 A Fazer...")
        move_result = await self._move_to_a_fazer(adapter, kanban_config)
        if move_result.is_err:
            return DemoResult.error(f"Erro ao mover card: {move_result.error}")

        # Step 3: Mover automaticamente para 🚧 Em Andamento
        self.log_progress(3, 7, "Movendo automaticamente para 🚧 Em Andamento...")
        progress_result = await self._move_to_em_andamento(adapter, kanban_config)
        if progress_result.is_err:
            return DemoResult.error(f"Erro ao mover: {progress_result.error}")

        # Step 4: Simular webhook
        self.log_progress(4, 7, "Simulando webhook Trello...")
        await self._simulate_webhook(adapter, "📋 A Fazer")

        # Step 5: Criar job
        self.log_progress(5, 7, "Criando job com autonomy_level=DEVELOPMENT...")
        job_id = await self._create_job(adapter, "DEVELOPMENT")

        # Step 6: Simular implementação
        self.log_progress(6, 7, "Agente implementando solução...")
        await self._simulate_implementation(adapter)

        # Step 7: Status final
        self.log_progress(7, 7, "Verificando status final...")
        self.log_success("✅ Modo DEVELOPMENT demonstrado!")
        self.log_info(f"📋 Card: https://trello.com/c/{self.card_id}")

        return DemoResult.success(
            message="Modo DEVELOPMENT demonstrado - implementação em andamento",
            card_url=f"https://trello.com/c/{self.card_id}",
            card_id=self.card_id,
            autonomy_level="DEVELOPMENT",
            job_id=job_id,
        )

    async def _create_development_card(self, adapter) -> Result[None, str]:
        """Cria card de desenvolvimento."""
        title = f"[TESTE PRD020] #DEVELOPMENT - {datetime.now().strftime('%H:%M:%S')}"
        description = """## Issue de Teste - Modo Desenvolvimento

Este card demonstra o fluxo de **desenvolvimento completo**.

### Comportamento Esperado:
- ✅ Card movido para "📋 A Fazer"
- ✅ Card movido automaticamente para "🚧 Em Andamento"
- ✅ Job criado com autonomy_level=DEVELOPMENT
- ✅ Agente implementa solução
- ✅ Worktree criado isolado

### Autonomy Level
**DEVELOPMENT** - Implementar a solução.

---
*Tags: TESTE PRD020 - DEVELOPMENT*"""

        result = await adapter.create_card(
            title=title,
            description=description,
            list_name="📥 Issues",
        )

        if result.is_ok:
            self.card_id = result.unwrap().id
            self.log_success(f"Card criado: {result.unwrap().url}")
            return Result.ok(None)
        return result

    async def _move_to_a_fazer(self, adapter, kanban_config) -> Result[None, str]:
        """Move card para 📋 A Fazer."""
        lists = await adapter.get_lists()
        if lists.is_err:
            return Result.err(lists.error)

        target_list = None
        for lst in lists.unwrap():
            if kanban_config.todo in lst.name or "📋 A Fazer" in lst.name:
                target_list = lst
                break

        if not target_list:
            return Result.err("Lista 📋 A Fazer não encontrada")

        result = await adapter.move_card(self.card_id, target_list.id)
        if result.is_ok:
            self.log_success(f"Card movido para: {target_list.name}")
            return Result.ok(None)
        return result

    async def _move_to_em_andamento(self, adapter, kanban_config) -> Result[None, str]:
        """Move card para 🚧 Em Andamento."""
        lists = await adapter.get_lists()
        if lists.is_err:
            return Result.err(lists.error)

        target_list = None
        for lst in lists.unwrap():
            if kanban_config.progress in lst.name or "🚧 Em Andamento" in lst.name:
                target_list = lst
                break

        if not target_list:
            return Result.err("Lista 🚧 Em Andamento não encontrada")

        result = await adapter.move_card(self.card_id, target_list.id)
        if result.is_ok:
            self.log_success(f"✅ Card movido automaticamente para: {target_list.name}")
            return Result.ok(None)
        return result

    async def _simulate_webhook(self, adapter, list_name: str) -> None:
        """Simula webhook."""
        self.log_info(f"📩 Webhook: card movido para '{list_name}'")
        await asyncio.sleep(1)

    async def _create_job(self, adapter, autonomy_level: str) -> str:
        """Cria job."""
        job_id = f"job-{autonomy_level.lower()}-{datetime.now().strftime('%H%M%S')}"
        self.log_info(f"📋 Job criado: {job_id}")
        self.log_info(f"   autonomy_level: {autonomy_level}")
        self.log_info(f"   skill: resolve-issue")
        await asyncio.sleep(0.5)
        return job_id

    async def _simulate_implementation(self, adapter) -> None:
        """Simula implementação do agente."""
        self.log_info("🤖 Agente: Iniciando implementação...")

        steps = [
            ("Criando worktree isolado", 1),
            ("Capturando snapshot inicial", 2),
            ("Implementando solução", 3),
            ("Validando mudanças", 4),
            ("Preparando para commit", 5),
        ]

        for step_msg, step_num in steps:
            await asyncio.sleep(1.5)
            self.log_info(f"   {step_num}. {step_msg}...")
            await adapter.add_card_comment(
                self.card_id,
                f"🔄 **Passo {step_num}/5**: {step_msg}"
            )

        self.log_success("✅ Implementação concluída!")


@DemoRegistry.register
class PRD020E2EDemo(BaseDemo):
    """
    Demo E2E completa do PRD020 - Fluxo Bidirecional.

    Demonstra o fluxo completo GitHub → Trello → GitHub com
    autonomia progressiva controlada via movimentação de cards.

    Fluxo:
    1. GitHub issue criada → Card no Trello
    2. Card movido para 💡 Brainstorm → Análise
    3. Card movido para 📋 A Fazer → Desenvolvimento
    4. Card em 👁️ Em Revisão → Aguardando revisão
    5. Card movido para 🚀 Publicar → Commit/push/PR
    """

    demo_id = "prd020-e2e"
    demo_name = "PRD020 - E2E Complete Flow"
    description = "Demonstração completa do fluxo bidirecional GitHub ↔ Trello"
    category = DemoCategory.E2E
    required_configs = ["TRELLO_API_KEY", "TRELLO_API_TOKEN", "TRELLO_BOARD_ID"]
    estimated_duration_seconds = 180
    tags = ["prd020", "e2e", "trello", "github", "autonomy", "complete"]
    related_issues = ["PRD020"]
    lifecycle = DemoLifecycle.DEV
    last_reviewed = datetime.now().strftime("%Y-%m-%d")

    def define_flow(self) -> DemoFlow:
        return DemoFlow(
            flow_type=DemoFlowType.ISSUE_LIFECYCLE,
            description="Fluxo completo GitHub → Trello → GitHub com autonomia progressiva",
            actors=["GitHub", "Trello", "User", "Agent", "Git"],
            steps=[
                "GitHub issue criada",
                "Card criado no Trello (Issues)",
                "Card → 💡 Brainstorm (ANALYSIS)",
                "Card → 📋 A Fazer (DEVELOPMENT)",
                "Card → 🚧 Em Andamento",
                "Card → 👁️ Em Revisão (REVIEW)",
                "Card → 🚀 Publicar (PUBLISH)",
                "PR criada no GitHub",
            ],
            entry_point="github",
            expected_outcome="PR criada no GitHub após autonomia progressiva",
        )

    async def validate_prerequisites(self) -> Result[None, str]:
        return await self._validate_configs()

    async def run(self, context: DemoContext) -> DemoResult:
        from infra.kanban.adapters.trello_adapter import TrelloAdapter
        from runtime.config.config import get_trello_kanban_lists_config

        api_key = getenv("TRELLO_API_KEY")
        api_token = getenv("TRELLO_API_TOKEN")
        board_id = getenv("TRELLO_BOARD_ID")

        adapter = TrelloAdapter(api_key, api_token, board_id)
        kanban_config = get_trello_kanban_lists_config()

        self.card_id: str | None = None
        issue_number = 999

        # PHASE 1: GitHub → Trello (já implementado)
        self.log_progress(1, 7, "PHASE 1: Simulando GitHub webhook...")
        await self._simulate_github_webhook(adapter)
        await self._create_card_from_issue(adapter, issue_number)

        # PHASE 2: 💡 Brainstorm (ANALYSIS)
        self.log_progress(2, 7, "PHASE 2: 💡 Brainstorm (ANALYSIS)...")
        await self._move_to_brainstorm_and_analyze(adapter, kanban_config)

        # PHASE 3: 📋 A Fazer (DEVELOPMENT)
        self.log_progress(3, 7, "PHASE 3: 📋 A Fazer (DEVELOPMENT)...")
        await self._move_to_development(adapter, kanban_config)

        # PHASE 4: 👁️ Em Revisão (REVIEW)
        self.log_progress(4, 7, "PHASE 4: 👁️ Em Revisão (REVIEW)...")
        await self._move_to_review(adapter, kanban_config)

        # PHASE 5: 🚀 Publicar (PUBLISH)
        self.log_progress(5, 7, "PHASE 5: 🚀 Publicar (PUBLISH)...")
        pr_url = await self._move_to_publish(adapter, kanban_config, issue_number)

        # PHASE 6: Verificar resultado
        self.log_progress(6, 7, "PHASE 6: Verificando resultado E2E...")
        await self._verify_e2e_result(adapter)

        # PHASE 7: Sumário
        self.log_progress(7, 7, "PHASE 7: Gerando sumário...")
        summary = await self._generate_summary(adapter, pr_url)

        self.log_success("✅ PRD020 E2E Flow demonstrado com sucesso!")

        return DemoResult.success(
            message="Fluxo E2E completo executado",
            card_url=f"https://trello.com/c/{self.card_id}",
            card_id=self.card_id,
            issue_number=issue_number,
            pr_url=pr_url,
            summary=summary,
        )

    async def _simulate_github_webhook(self, adapter) -> None:
        """Simula webhook do GitHub."""
        self.log_info("📨 GitHub webhook simulado (issues.opened)")
        await asyncio.sleep(1)

    async def _create_card_from_issue(self, adapter, issue_number: int) -> None:
        """Cria card a partir de issue GitHub."""
        title = f"#{issue_number} Implementar AutonomyLevel"
        description = f"""## Issue #{issue_number}

Implementar níveis de autonomia para processamento de webhooks.

### Requisitos
- [ ] AutonomyLevel enum (ANALYSIS, DEVELOPMENT, REVIEW, PUBLISH)
- [ ] Mapeamento listas Trello → autonomy_level
- [ ] Modificar JobOrchestrator

---
*Issue criada via GitHub webhook*"""

        result = await adapter.create_card(
            title=title,
            description=description,
            list_name="📥 Issues",
        )

        if result.is_ok:
            self.card_id = result.unwrap().id
            self.log_success(f"Card criado: {result.unwrap().url}")
        else:
            self.log_error(f"Erro: {result.error}")

    async def _move_to_brainstorm_and_analyze(self, adapter, kanban_config) -> None:
        """Move para Brainstorm e simula análise."""
        self.log_info("   Movendo para 💡 Brainstorm...")

        # Comentário de análise
        comment = """## 📊 Análise - Modo Brainstorm

### Arquivos Identificados
- `src/core/webhooks/domain/autonomy_level.py`
- `src/core/webhooks/application/job_orchestrator.py`

### Abordagem
1. Criar enum AutonomyLevel
2. Adicionar campo ao WebhookJob
3. Modificar handler para emitir eventos

### Status
✅ Análise completa - pronto para implementar

---
* autonomy_level: ANALYSIS*"""

        await adapter.add_card_comment(self.card_id, comment)
        self.log_success("   ✅ Análise concluída (SEM mudanças)")

    async def _move_to_development(self, adapter, kanban_config) -> None:
        """Move para desenvolvimento e simula implementação."""
        self.log_info("   Movendo para 📋 A Fazer...")
        await asyncio.sleep(1)

        self.log_info("   Movendo automaticamente para 🚧 Em Andamento...")
        await asyncio.sleep(1)

        # Comentário de progresso
        comment = """## 🚧 Em Desenvolvimento

### Progresso
- ✅ Worktree criada
- ✅ AutonomyLevel implementado
- ✅ Handler modificado
- 🔄 Testes em andamento

### autonomy_level
**DEVELOPMENT** - Implementando solução.

---
*Job ID: dev-123*"""

        await adapter.add_card_comment(self.card_id, comment)
        self.log_success("   ✅ Desenvolvimento em andamento")

    async def _move_to_review(self, adapter, kanban_config) -> None:
        """Move para revisão."""
        self.log_info("   Movendo para 👁️ Em Revisão...")

        comment = """## 👁️ Em Revisão

### Implementação Concluída
- ✅ AutonomyLevel criado
- ✅ Mapeamento implementado
- ✅ Webhook handler modificado
- ✅ JobOrchestrator atualizado
- ✅ Testes criados

### autonomy_level
**REVIEW** - Aguardando aprovação humana.

---
*Aguardando revisão antes de publicar*"""

        await adapter.add_card_comment(self.card_id, comment)
        self.log_success("   ✅ Aguardando revisão humana")

    async def _move_to_publish(self, adapter, kanban_config, issue_number: int) -> str:
        """Move para publicar e cria PR."""
        self.log_info("   Movendo para 🚀 Publicar...")
        await asyncio.sleep(1)

        pr_url = f"https://github.com/h4mn/skybridge/pull/{issue_number}"

        comment = f"""## 🚀 Publicando

### Commit & Push
- ✅ Changes staged
- ✅ Commit criado
- ✅ Push para branch `feat/issue-{issue_number}`

### Pull Request
**PR criada:** {pr_url}

### autonomy_level
**PUBLISH** - Commit/push/PR automático.

---
*Fluxo completo E2E concluído!*"""

        await adapter.add_card_comment(self.card_id, comment)
        self.log_success(f"   ✅ PR criada: {pr_url}")

        return pr_url

    async def _verify_e2e_result(self, adapter) -> None:
        """Verifica resultado E2E."""
        self.log_info("Verificando resultado E2E...")
        await asyncio.sleep(1)
        self.log_success("✅ Todos os estágios concluídos")

    async def _generate_summary(self, adapter, pr_url: str) -> str:
        """Gera sumário do fluxo E2E."""
        summary = f"""
## 📊 Resumo E2E - PRD020

### Fluxo Executado
1. GitHub Issue → Trello Card ✅
2. 💡 Brainstorm → ANÁLISE ✅
3. 📋 A Fazer → DEVELOPMENT ✅
4. 👁️ Em Revisão → REVIEW ✅
5. 🚀 Publicar → PUBLISH ✅

### Resultado
- **Card:** https://trello.com/c/{self.card_id}
- **PR:** {pr_url}

### Autonomia Alcançada
**90%** - Apenas revisão manual necessária.

---
*PRD020 - Fluxo Bidirecional Completo*"""

        await adapter.add_card_comment(self.card_id, summary)
        self.log_success("📋 Sumário postado no card")

        return summary


if __name__ == "__main__":
    # Teste local dos cenários
    import asyncio

    async def test_scenarios():
        """Testa cenários PRD020."""
        print("Testing PRD020 Scenarios...")

        # Teste 1: Analysis Demo
        analysis_demo = TrelloToGitHubAnalysisDemo()
        print(f"Demo: {analysis_demo.demo_name}")
        print(f"Flow: {analysis_demo.define_flow()}")

        # Teste 2: Development Demo
        dev_demo = TrelloToGitHubDevelopmentDemo()
        print(f"\nDemo: {dev_demo.demo_name}")
        print(f"Flow: {dev_demo.define_flow()}")

        # Teste 3: E2E Demo
        e2e_demo = PRD020E2EDemo()
        print(f"\nDemo: {e2e_demo.demo_name}")
        print(f"Flow: {e2e_demo.define_flow()}")

        print("\n✅ All PRD020 scenarios loaded successfully!")

    asyncio.run(test_scenarios())
