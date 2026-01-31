# -*- coding: utf-8 -*-
"""
Demo Scenarios — Implementações de demos específicas.

Cada arquivo neste módulo implementa demos de uma categoria específica,
portando os scripts originais de testing/ para a nova estrutura.

Categorias:
- trello_scenarios.py: Demos de integração com Trello
- github_scenarios.py: Demos de integração com GitHub
- e2e_scenarios.py: Demos end-to-end completas
- queue_scenarios.py: Demos de sistema de fila
- engine_scenarios.py: Demos que testam a própria engine/CLI
- prd020_scenarios.py: Demos do fluxo bidirecional GitHub ↔ Trello (PRD020)
- prd021_scenarios.py: Demos da reorganização de prompts e skills (PRD021)
- spec009_e2e_demo.py: Demo interativa do workflow multi-agente (SPEC009)

NOTA: agent_sdk_scenarios.py foi removido conforme ADR021 (migração completa para SDK).
Os benchmarks comparativos não são mais necessários.
"""

# Import de todos os cenários para registrar automaticamente
from runtime.demo.scenarios.trello_scenarios import (
    TrelloFlowDemo,
    MockAgentTrelloDemo,
    GitHubToTrelloDemo,
)

from runtime.demo.scenarios.e2e_scenarios import (
    E2EDemo,
    FinalDemo,
)

from runtime.demo.scenarios.github_scenarios import (
    GitHubRealFlowDemo,
    GitHubToTrelloSimpleDemo,
)

from runtime.demo.scenarios.queue_scenarios import (
    QueueE2EDemo,
)

from runtime.demo.scenarios.engine_scenarios import (
    CLITestSuiteDemo,
    DemoEngineValidationDemo,
)

from runtime.demo.scenarios.prd021_scenarios import (
    PRD021StructureDemo,
    PRD021ImportDemo,
)

from runtime.demo.scenarios.spec009_e2e_demo import (
    SPEC009InteractiveDemo,
)

from runtime.demo.scenarios.prd020_scenarios import (
    TrelloToGitHubAnalysisDemo,
)

__all__ = [
    # Trello
    "TrelloFlowDemo",
    "MockAgentTrelloDemo",
    "GitHubToTrelloDemo",
    # E2E
    "E2EDemo",
    "FinalDemo",
    # GitHub
    "GitHubRealFlowDemo",
    "GitHubToTrelloSimpleDemo",
    # Queue
    "QueueE2EDemo",
    # Engine
    "CLITestSuiteDemo",
    "DemoEngineValidationDemo",
    # PRD021 - Refatoração de Prompts e Skills
    "PRD021StructureDemo",
    "PRD021ImportDemo",
    # SPEC009 - Workflow Multi-Agente
    "SPEC009InteractiveDemo",
    # PRD020 - Fluxo Bidirecional GitHub ↔ Trello
    "TrelloToGitHubAnalysisDemo",
]
