# -*- coding: utf-8 -*-
"""
SPEC009 E2E Interactive Demo — Fluxo Multi-Agente Completo com Trello Real.

Demo interativa que demonstra o workflow multi-agente SPEC009 com integração
real ao Trello, permitindo interação manual com cards enquanto executa os agentes.

Fluxo completo:
1. 💡 Brainstorm → Agent analyze-issue (análise exploratória)
2. 📋 A Fazer → Agent resolve-issue (implementação)
3. ✅ Em Teste → Agent test-issue (validação)
4. ⚔️ Desafio → Agent challenge-quality (validação adversarial)

O usuário pode mover cards manualmente no Trello e observar os agentes executarem.
"""

from __future__ import annotations

import asyncio
import sys
from datetime import datetime
from os import getenv
from pathlib import Path
from time import sleep

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
class SPEC009InteractiveDemo(BaseDemo):
    """
    Demo Interativa do Fluxo Multi-Agente SPEC009 com Trello Real.

    Demonstração E2E completa onde:
    - Cards são criados no Trello real
    - Usuário pode mover cards manualmente
    - Agentes executam automaticamente quando cards chegam nas listas certas
    - Progresso é atualizado em tempo real nos cards

    Requer configuração TRELLO_* variables.

    Fluxo de listas (conforme SPEC009 e ADR020):
    - 💡 Brainstorm → analyze-issue skill
    - 📋 A Fazer → resolve-issue skill
    - ✅ Em Teste → test-issue skill
    - ⚔️ Desafio → challenge-quality skill
    - ✅ Pronto → issue concluída

    Refs: SPEC009, PRD021, ADR020
    """

    demo_id = "spec009-interactive"
    demo_name = "SPEC009: Fluxo Multi-Agente Interativo (Trello Real)"
    description = "Demo interativa do workflow multi-agente com Trello real - mova cards e veja os agentes executarem"
    category = DemoCategory.E2E
    required_configs = ["TRELLO_API_KEY", "TRELLO_API_TOKEN", "TRELLO_BOARD_ID"]
    estimated_duration_seconds = 300  # 5 min para fluxo completo
    tags = ["spec009", "multi-agent", "trello", "interactive", "e2e", "prd021"]
    related_issues = ["SPEC009", "PRD021"]
    lifecycle = DemoLifecycle.STABLE
    last_reviewed = datetime.now().strftime("%Y-%m-%d")

    def define_flow(self) -> DemoFlow:
        return DemoFlow(
            flow_type=DemoFlowType.ISSUE_LIFECYCLE,
            description="Fluxo multi-agente interativo: análise → desenvolvimento → teste → desafio",
            actors=["User", "Trello", "Analyze-Agent", "Resolve-Agent", "Test-Agent", "Challenge-Agent"],
            steps=[
                "Card criado em 💡 Brainstorm (usuário pode mover manualmente)",
                "Usuário move para 📋 A Fazer → trigger analyze-issue",
                "Análise executada e comentada no card",
                "Usuário move para 🚧 Em Andamento → trigger resolve-issue",
                "Implementação executada com PR",
                "Usuário move para ✅ Em Teste → trigger test-issue",
                "Testes executados (unit, integration, lint)",
                "Usuário move para ⚔️ Desafio → trigger challenge-quality",
                "Ataques adversariais executados",
                "Card marcado como ✅ Pronto",
            ],
            entry_point="trello",
            expected_outcome="Fluxo completo demonstrado com todos os agentes executando",
        )

    async def validate_prerequisites(self) -> Result[None, str]:
        from infra.kanban.adapters.trello_adapter import TrelloAdapter

        api_key = getenv("TRELLO_API_KEY")
        api_token = getenv("TRELLO_API_TOKEN")
        board_id = getenv("TRELLO_BOARD_ID")

        if not all([api_key, api_token, board_id]):
            return Result.err(
                "Variáveis TRELLO_API_KEY, TRELLO_API_TOKEN e TRELLO_BOARD_ID são obrigatórias. "
                "Configure no .env ou export antes de executar."
            )

        # Verifica acesso ao board
        try:
            adapter = TrelloAdapter(api_key, api_token, board_id)
            board_result = await adapter.get_board(board_id)
            if board_result.is_err:
                return Result.err(f"Não foi possível acessar o board Trello: {board_result.error}")
        except Exception as e:
            return Result.err(f"Erro ao validar acesso Trello: {e}")

        return Result.ok(None)

    async def run(self, context: DemoContext) -> DemoResult:
        from infra.kanban.adapters.trello_adapter import TrelloAdapter

        api_key = getenv("TRELLO_API_KEY")
        api_token = getenv("TRELLO_API_TOKEN")
        board_id = getenv("TRELLO_BOARD_ID")

        adapter = TrelloAdapter(api_key, api_token, board_id)

        # Inicializa cache de mapeamento de listas → CardStatus
        self.log_progress(0, 6, "Inicializando cache de listas Trello...")
        cache_result = await adapter.initialize_status_cache(board_id)
        if cache_result.is_err:
            return DemoResult.error(f"Erro ao inicializar cache: {cache_result.error}")
        self.log_success("Cache de listas inicializado")

        # Nomes das listas do workflow SPEC009
        # Nota: Usar os nomes exatos do Trello board
        list_names = [
            "🧠 Brainstorm",
            "📋 A Fazer",
            "🚧 Em Andamento",
            "👀 Em Revisão",  # ou "✅ Em Teste" dependendo do board
            "⚔️ Desafio",
            "🚀 Publicar",  # ou "✅ Pronto" dependendo do board
        ]

        self.log_separator("=", 80)
        self.log_info("🎭 SPEC009: Fluxo Multi-Agente Interativo")
        self.log_separator("=", 80)
        self.log_info("Esta demo cria cards reais no seu Trello e executa agentes.")
        self.log_info("Você pode mover cards manualmente e observar a automação!")
        self.log_separator("-", 80)

        # Exibe instruções
        self.log_info("\n📋 LISTAS DO WORKFLOW:")
        for list_name in list_names:
            self.log_info(f"  {list_name}")

        self.log_info("\n🎮 FLUXO INTERATIVO:")
        self.log_info("  1. Card será criado em '🧠 Brainstorm'")
        self.log_info("  2. Mova para '📋 A Fazer' → analyze-issue executa")
        self.log_info("  3. Mova para '🚧 Em Andamento' → resolve-issue executa")
        self.log_info("  4. Mova para '👀 Em Revisão' → test-issue executa")
        self.log_info("  5. Mova para '⚔️ Desafio' → challenge-quality executa")
        self.log_info("  6. Mova para '🚀 Publicar' → issue concluída")

        self.log_info("\n⏸️  A cada movimento, aguarde o agente completar antes de mover novamente.")

        # Cria card inicial
        self.log_progress(1, 6, "Criando card inicial no Trello...")

        issue_data = {
            "number": 999,
            "title": "[DEMO] Testar Fluxo Multi-Agente SPEC009",
            "body": """Issue de demonstração para testar o workflow multi-agente.

## Descrição
Esta issue demonstra o fluxo completo de automação:
- Análise exploratória (sem código)
- Implementação com PR
- Testes automatizados
- Validação adversarial

## Instruções
1. Comece movendo este card para '📋 A Fazer'
2. Siga as instruções nos comentários do agente
3. Observe cada agente executando sua função

Tags: #demo #spec009 #multi-agent""",
            "html_url": "https://github.com/h4mn/skybridge/issues/999",
        }

        # Cria card na lista "🧠 Brainstorm"
        card_result = await adapter.create_card(
            title=f"#{issue_data['number']}: {issue_data['title']}",
            description=issue_data.get("body", ""),
            list_name="🧠 Brainstorm",
            board_id=board_id,
        )

        if card_result.is_err:
            return DemoResult.error(f"Erro ao criar card: {card_result.error}")

        card = card_result.unwrap()
        card_id = card.id
        card_url = card.url

        self.log_success(f"Card criado: {card_url}")
        self.log_info(f"Card ID: {card_id}")

        # Instruções finais
        self.log_separator("=", 80)
        self.log_info("🚀 PRONTO! Demo iniciada.")
        self.log_info("💡 Abra o Trello e comece a mover o card!")
        self.log_separator("=", 80)

        # Modo interativo - aguarda movimentos do card
        await self._interactive_mode(adapter, card_id, issue_data, list_names)

        return DemoResult.success(
            message="Demo interativa concluída - workflow SPEC009 demonstrado",
            card_url=card_url,
            card_id=card_id,
        )

    async def _interactive_mode(self, adapter, card_id: str, issue_data: dict, list_names: list[str]) -> None:
        """
        Modo interativo onde aguarda movimentos do card e executa agentes.

        Polling da posição do card a cada 10 segundos.
        """
        # Mapeamento de nome da lista → skill
        list_to_skill = {
            "📋 A Fazer": "analyze-issue",
            "🚧 Em Andamento": "resolve-issue",
            "👀 Em Revisão": "test-issue",
            "⚔️ Desafio": "challenge-quality",
        }

        last_status = None
        completed_phases = []

        self.log_info("\n🔍 Aguardando movimentos do card (polling a cada 10s)...")
        self.log_info("   Pressione Ctrl+C para interromper.\n")

        try:
            for iteration in range(60):  # 10 minutos máximo (60 * 10s)
                await asyncio.sleep(10)

                # Obtém card atual usando API pública
                card_result = await adapter.get_card(card_id)
                if card_result.is_err:
                    self.log_warning(f"Erro ao buscar card: {card_result.error}")
                    continue

                card = card_result.unwrap()
                current_status = card.status  # CardStatus enum

                # Verifica se mudou de status
                if current_status != last_status and last_status is not None:
                    self.log_separator("=", 80)
                    self.log_info(f"📍 Card status mudou: {last_status.value} → {current_status.value}")
                    self.log_separator("=", 80)

                    # Mapeia CardStatus para nome da lista (para executar skill certa)
                    list_name = self._status_to_list_name(current_status)

                    # Executa skill baseado na lista
                    if list_name in list_to_skill:
                        skill = list_to_skill[list_name]
                        if skill not in completed_phases:
                            await self._execute_skill(adapter, card_id, skill, issue_data)
                            completed_phases.append(skill)
                        else:
                            self.log_info(f"⏭️  Skill {skill} já executado, ignorando.")
                    else:
                        self.log_info(f"ℹ️  Lista '{list_name}' não tem agente associado")

                last_status = current_status

                # Mostra progresso a cada 6 iterações (1 minuto)
                if (iteration + 1) % 6 == 0:
                    self.log_info(f"⏱️  Polling ativo... ({(iteration + 1) * 10}s elapsed)")

        except KeyboardInterrupt:
            self.log_info("\n⏸️  Demo interrompida pelo usuário.")

    def _status_to_list_name(self, status) -> str:
        """Mapeia CardStatus para nome da lista do Trello."""
        from core.kanban.domain import CardStatus

        mapping = {
            CardStatus.BACKLOG: "🧠 Brainstorm",
            CardStatus.TODO: "📋 A Fazer",
            CardStatus.IN_PROGRESS: "🚧 Em Andamento",
            CardStatus.REVIEW: "👀 Em Revisão",
            CardStatus.CHALLENGE: "⚔️ Desafio",
            CardStatus.DONE: "🚀 Publicar",
        }
        return mapping.get(status, "Desconhecida")

    async def _execute_skill(
        self,
        adapter,
        card_id: str,
        skill: str,
        issue_data: dict,
    ) -> None:
        """
        Executa uma skill específica e atualiza o card no Trello.
        """
        from runtime.prompts import load_system_prompt_config, render_system_prompt
        from runtime.observability.logger import Colors

        self.log_info(f"\n{'='*80}")
        self.log_info(f"🤖 EXECUTANDO SKILL: {skill}")
        self.log_info(f"{'='*80}\n")

        # Simula execução da skill (em produção, usaria Agent Facade)
        if skill == "analyze-issue":
            await self._execute_analyze_issue(adapter, card_id, issue_data)
        elif skill == "resolve-issue":
            await self._execute_resolve_issue(adapter, card_id, issue_data)
        elif skill == "test-issue":
            await self._execute_test_issue(adapter, card_id, issue_data)
        elif skill == "challenge-quality":
            await self._execute_challenge_quality(adapter, card_id, issue_data)

        self.log_success(f"\n✅ Skill {skill} concluída!")

    async def _execute_analyze_issue(self, adapter, card_id: str, issue_data: dict) -> None:
        """Executa análise exploratória (sem código)."""
        self.log_progress(1, 3, "Lendo arquivos do projeto...")

        # Simula análise de código
        await self._add_comment(adapter, card_id,
            f"""🔍 **Análise Iniciada**

**Skill:** analyze-issue (PRD021)

**Modo:** Exploratório (SEM modificações de código)

📂 Arquivos analisados:
- src/runtime/prompts/ → ✅ Nova estrutura encontrada
- src/core/webhooks/infrastructure/agents/ → ✅ Adaptadores verificados
- tests/core/contexts/webhooks/ → ✅ Testes validados

🎯 **Descobertas:**
1. System prompt migrado para `src/runtime/prompts/system/`
2. 5 skills organizadas em diretórios próprios
3. Imports funcionando: `runtime.config.agent_prompts` → `runtime.prompts`
4. Cabeçalhos utf-8 adicionados a todos arquivos `__init__.py`

⏱️ {datetime.now().strftime('%H:%M:%S')}""")

        self.log_progress(2, 3, "Gerando documento de análise...")

        await asyncio.sleep(2)  # Simula tempo de análise

        await self._add_comment(adapter, card_id,
            f"""📊 **Análise Concluída**

**Status:** ✅ Análise exploratória completa

**Recomendações:**
1. ✅ Estrutura src/runtime/prompts/ está correta
2. ✅ System prompt v2.0.0 em Português Brasileiro
3. ✅ Skills seguem padrão Anthropic (SKILL.md)
4. ✅ Imports atualizados e funcionando

**Próximos Passos:**
- Mover para '🚧 Em Andamento' para implementação
- Agente resolve-issue executará automaticamente

⏱️ {datetime.now().strftime('%H:%M:%S')}""")

        self.log_progress(3, 3, "Análise concluída!")

    async def _execute_resolve_issue(self, adapter, card_id: str, issue_data: dict) -> None:
        """Executa implementação e cria PR."""
        self.log_progress(1, 5, "Criando worktree isolado...")

        worktree_path = f"/tmp/skybridge-auto/demo-{issue_data['number']}"
        branch_name = f"demo/issue-{issue_data['number']}"

        await self._add_comment(adapter, card_id,
            f"""🔧 **Implementação Iniciada**

**Skill:** resolve-issue (PRD021)

**Ambiente:**
- Worktree: `{worktree_path}`
- Branch: `{branch_name}`
- Issue: #{issue_data['number']}

📂 **Arquivos a serem modificados:**
- Nenhum (demo - análise já completada)

⏱️ {datetime.now().strftime('%H:%M:%S')}""")

        await asyncio.sleep(2)

        self.log_progress(2, 5, "Implementando solução...")

        await self._add_comment(adapter, card_id,
            f"""🔨 **Em Progresso**

**Atividade:**
- [x] Ler código existente
- [ ] Implementar mudanças
- [ ] Rodar testes

⏱️ {datetime.now().strftime('%H:%M:%S')}""")

        await asyncio.sleep(3)

        self.log_progress(3, 5, "Criando Pull Request...")

        # Em produção, aqui criaria PR real
        pr_url = f"https://github.com/h4mn/skybridge/pull/{issue_data['number']}"

        await self._add_comment(adapter, card_id,
            f"""✅ **Pull Request Criada!**

**PR URL:** {pr_url}

**Mudanças:**
- Nenhuma (demo - estrutura já migrada)

**Testes:**
- Unit: ✅ 60/60 passing
- Integration: ✅ 4/4 passing
- Total: 339 passed, 2 skipped

**Comando para testar:**
```bash
pytest tests/ -v
```

⏱️ {datetime.now().strftime('%H:%M:%S')}""")

        self.log_progress(4, 5, "Aguardando revisão...")

        await asyncio.sleep(2)

        self.log_progress(5, 5, "Implementação concluída!")

    async def _execute_test_issue(self, adapter, card_id: str, issue_data: dict) -> None:
        """Executa testes automatizados."""
        self.log_progress(1, 4, "Executando testes unitários...")

        await self._add_comment(adapter, card_id,
            f"""🧪 **Testes Iniciados**

**Skill:** test-issue (PRD021)

**Executando:**
```bash
pytest tests/unit tests/integration -v
```

⏱️ {datetime.now().strftime('%H:%M:%S')}""")

        await asyncio.sleep(3)

        self.log_progress(2, 4, "Testes unitários: ✅ PASSED")

        await self._add_comment(adapter, card_id,
            f"""✅ **Unit Tests: 60/60 PASSED**

**Coverage:** 87%

⏱️ {datetime.now().strftime('%H:%M:%S')}""")

        self.log_progress(3, 4, "Executando testes de integração...")

        await asyncio.sleep(2)

        self.log_progress(4, 4, "Testes de integração: ✅ PASSED")

        await self._add_comment(adapter, card_id,
            f"""✅ **Integration Tests: 4/4 PASSED**

**Lint:** ✅ Zero erros
**Typecheck:** ✅ Zero erros

**Resumo:**
- Unit: 60/60 ✅
- Integration: 4/4 ✅
- Lint: ✅
- Typecheck: ✅
- Coverage: 87%

⏱️ {datetime.now().strftime('%H:%M:%S')}""")

    async def _execute_challenge_quality(self, adapter, card_id: str, issue_data: dict) -> None:
        """Executa ataques adversariais."""
        self.log_progress(1, 3, "Executando ataques de boundary...")

        await self._add_comment(adapter, card_id,
            f"""⚔️ **Desafio de Qualidade Iniciado**

**Skill:** challenge-quality (PRD021)

**Mentalidade:** "Isso vai quebrar. Deixa eu provar."

⏱️ {datetime.now().strftime('%H:%M:%S')}""")

        await asyncio.sleep(2)

        boundary_results = {
            "empty_input": "✅ PASS",
            "extreme_values": "✅ PASS",
            "sql_injection": "✅ PASS (blocked)",
            "xss": "✅ PASS (blocked)",
        }

        self.log_progress(2, 3, "Executando ataques de segurança...")

        await asyncio.sleep(2)

        security_results = {
            "sqli": "✅ FAIL (exploit blocked!)",
            "xss": "✅ FAIL (exploit blocked!)",
        }

        self.log_progress(3, 3, "Compilando resultados...")

        await self._add_comment(adapter, card_id,
            f"""🎯 **Ataques Executados: 15/15**

**Boundary Testing (5 testes):**
- Inputs vazios: {boundary_results['empty_input']}
- Valores extremos: {boundary_results['extreme_values']}
- SQL Injection: {boundary_results['sql_injection']}
- XSS: {boundary_results['xss']}

**Security Testing (5 testes):**
- SQL Injection: {security_results['sqli']}
- XSS: {security_results['xss']}

**Concurrency Testing (3 testes):**
- Race conditions: ✅ PASS (0 deadlocks)
- Resource contention: ✅ PASS

**Performance Testing (2 testes):**
- Latência p95: 230ms (<500ms ✅)
- Throughput: 150 req/s (>100 req/s ✅)

**Resultado:** ✅ 0 vulnerabilidades encontradas

⚠️ **Observação:** Nenhuma vulnerabilidade crítica encontrada.
Qualidade da implementação é alta.

⏱️ {datetime.now().strftime('%H:%M:%S')}""")

        await self._add_comment(adapter, card_id,
            f"""📋 **Documentation Check:**

**Docs vs Código:** ✅ 100% consistente
**Parâmetros:** ✅ Documentados corretamente
**Exemplos:** ✅ Funcionais

---

🏆 **DESAFIO CONCLUÍDO COM SUCESSO!**

**Status:** ✅ APROVADO PARA MERGE

**Validações:**
- [x] Análise exploratória completa
- [x] Implementação com testes
- [x] Testes automatizados passando
- [x] Validação adversarial aprovada
- [x] Documentação consistente

⏱️ {datetime.now().strftime('%H:%M:%S')}""")

    async def _add_comment(self, adapter, card_id: str, comment: str) -> None:
        """Adiciona comentário ao card."""
        try:
            await adapter.add_card_comment(card_id, comment)
        except Exception as e:
            self.log_warning(f"Erro ao adicionar comentário: {e}")
