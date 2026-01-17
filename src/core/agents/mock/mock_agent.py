# -*- coding: utf-8 -*-
"""
Mock Agent — Simula agente autônomo para testes.

Emite XML progressivo como ClaudeCodeAgent, mas com cenários
realistas de desenvolvimento da Skybridge.
"""

import asyncio
import random
from datetime import datetime
from typing import Optional
from dataclasses import dataclass
from enum import Enum


class MockScenario(Enum):
    """Cenários realistas de desenvolvimento Skybridge."""

    FIX_WEBHOOK_DEDUPLICATION = """[MOCK/TESTE] Corrigir duplicação de webhooks

**Problema:** Webhooks do GitHub estão sendo processados múltiplas vezes,
causando criação de jobs duplicados.

**Análise:**
- O WebhookProcessor não está verificando jobs existentes
- Falta um índice único no correlation_id

**Solução:**
1. Adicionar verificação de duplicação antes de criar job
2. Implementar cache de GUIDs processados
3. Adicionar teste de regressão"""

    IMPLEMENT_KANBAN_INTEGRATION = """[MOCK/TESTE] Integrar Trello com JobOrchestrator

**Feature:** Permitir que agentes atualizem cards do Trello durante execução.

**Requisitos:**
- Criar card ao iniciar job (TODO → IN_PROGRESS)
- Atualizar card durante progresso (comentários)
- Mover para DONE ao finalizar

**Implementação:**
1. Adicionar TrelloAdapter no JobOrchestrator
2. Emitir eventos de progresso
3. Mapear status do job para listas do Trello"""

    REFACTOR_AGENT_ORCHESTRATOR = """[MOCK/TESTE] Refatorar JobOrchestrator para domain events

**Problema:** JobOrchestrator está acoplado a adapters externos.

**Solução:**
- Implementar Domain Events (JobCreated, JobProgress, JobCompleted)
- Usar EventDispatcher para desacoplar
- Adicionar TrelloEventListener

**Benefícios:**
- Arquitetura mais limpa
- Fácil adicionar novos listeners (Slack, Discord, etc)"""

    ADD_RATE_LIMITING = """[MOCK/TESTE] Implementar rate limiting na API

**Problema:** API está vulnerável a abuse.

**Solução:**
1. Configurar rate limiting por IP
2. Adicionar headers X-RateLimit-*
3. Implementar backoff automático
4. Adicionar testes de carga"""

    FIX_WORKTREE_CLEANUP = """[MOCK/TESTE] Corrigir limpeza de worktrees órfãos

**Problema:** Worktrees não são removidos após job finalizar,
acumulando diretórios em `_worktrees/`.

**Solução:**
1. Implementar cleanup automático no JobOrchestrator
2. Adicionar hook post-job
3. Configurar retenção (ex: 24h)
4. Adicionar comando manual de limpeza"""


@dataclass
class MockAgentConfig:
    """Configuração do MockAgent."""
    scenario: MockScenario
    card_id: Optional[str] = None  # Se fornecido, atualiza card no Trello
    total_duration_seconds: int = 30  # Duração total simulada


class MockAgent:
    """
    Agente mock que simula execução de Claude Code.

    Emite XML progressivo como o protocolo real, permitindo testar
    o fluxo de integração com Trello sem depender do Claude Code CLI.
    """

    def __init__(self, config: MockAgentConfig):
        self.config = config
        self._start_time: Optional[datetime] = None

    async def execute(self) -> str:
        """
        Executa o cenário simulado.

        Returns:
            XML string com o resultado completo da execução
        """
        self._start_time = datetime.now()
        scenario = self.config.scenario.value

        # Emitir início
        yield self._xml_start(scenario)

        # Fase 1: Setup e análise
        await asyncio.sleep(2)
        yield self._xml_phase(
            phase="Análise",
            status="Lendo arquivos do projeto...",
            details=[
                "src/runtime/orchestration/job_orchestrator.py",
                "src/core/webhooks/application/processor.py",
                "tests/test_webhooks.py"
            ]
        )

        # Fase 2: Entendendo o problema
        await asyncio.sleep(3)
        yield self._xml_phase(
            phase="Análise",
            status="Analisando código existente...",
            details=[
                "Identificando ponto de inserção",
                "Verificando dependências",
                "Mapeando afetados"
            ]
        )

        # Fase 3: Planejamento
        await asyncio.sleep(2)
        yield self._xml_phase(
            phase="Planejamento",
            status="Planejando implementação...",
            details=[
                "Definindo abordagem",
                "Listando arquivos a modificar",
                "Preparando testes"
            ]
        )

        # Fase 4: Implementação
        await asyncio.sleep(5)
        yield self._xml_phase(
            phase="Implementação",
            status="Escrevendo código...",
            details=[
                "Criando novo módulo",
                "Modificando adapters",
                "Adicionando validações"
            ]
        )

        # Fase 5: Testes
        await asyncio.sleep(4)
        yield self._xml_phase(
            phase="Testes",
            status="Executando testes...",
            details=[
                "pytest tests/unit/...",
                "pytest tests/integration/...",
                "Verificando cobertura"
            ]
        )

        # Fase 6: Finalização
        await asyncio.sleep(2)
        yield self._xml_complete(
            summary="Implementação concluída com sucesso",
            changes=[
                "3 arquivos criados",
                "2 arquivos modificados",
                "12 testes adicionados",
                "Cobertura: 94%"
            ]
        )

    def _xml_start(self, scenario: str) -> str:
        """XML inicial: início da execução."""
        return f"""<started>
  <timestamp>{datetime.now().isoformat()}</timestamp>
  <scenario>{scenario[:50]}...</scenario>
  <message>Iniciando análise e implementação...</message>
</started>"""

    def _xml_phase(
        self,
        phase: str,
        status: str,
        details: list[str]
    ) -> str:
        """XML de progresso: fase atual."""
        details_xml = "\n    ".join(details)
        elapsed = (datetime.now() - self._start_time).total_seconds() if self._start_time else 0

        return f"""<progress>
  <timestamp>{datetime.now().isoformat()}</timestamp>
  <elapsed>{elapsed:.1f}s</elapsed>
  <phase>{phase}</phase>
  <status>{status}</status>
  <details>
    <item>{details_xml}</item>
  </details>
</progress>"""

    def _xml_complete(self, summary: str, changes: list[str]) -> str:
        """XML final: conclusão."""
        changes_xml = "\n    ".join(changes)
        elapsed = (datetime.now() - self._start_time).total_seconds() if self._start_time else 0

        return f"""<completed>
  <timestamp>{datetime.now().isoformat()}</timestamp>
  <elapsed>{elapsed:.1f}s</elapsed>
  <summary>{summary}</summary>
  <changes>
    <item>{changes_xml}</item>
  </changes>
  <exit_code>0</exit_code>
</completed>"""


async def demo_mock_agent():
    """Demo do MockAgent executando um cenário realista."""

    print("🤖 MOCK AGENT DEMO")
    print("=" * 60)

    # Escolhe cenário aleatório
    scenario = random.choice(list(MockScenario))
    config = MockAgentConfig(scenario=scenario)
    agent = MockAgent(config)

    print(f"\n📋 Cenário: {scenario.name}")
    print(f"📝 Descrição: {scenario.value[:80]}...")

    print("\n🔄 Executando...")

    # Executa e imprime XML
    async for xml in agent.execute():
        print("\n--- XML ---")
        print(xml)

    print("\n" + "=" * 60)
    print("✅ Execução concluída!")


if __name__ == "__main__":
    asyncio.run(demo_mock_agent())
