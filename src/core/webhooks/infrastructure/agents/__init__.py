# -*- coding: utf-8 -*-
"""
Agent Infrastructure Layer.

Camada de infraestrutura para criação e gerenciamento de agentes AI.
Implementa o Agent Facade Pattern conforme SPEC008.

Esta camada isola o orchestrator de detalhes específicos de cada agente
(Claude Code, Roo Code, Copilot, etc).
"""
from __future__ import annotations

from core.webhooks.infrastructure.agents.domain import (
    AgentState,
    AgentExecution,
    AgentResult,
    ThinkingStep,
)
from core.webhooks.infrastructure.agents.agent_facade import (
    AgentFacade,
)
from core.webhooks.infrastructure.agents.claude_agent import (
    ClaudeCodeAdapter,
)
from core.webhooks.infrastructure.agents.protocol import (
    XMLStreamingProtocol,
    SkybridgeCommand,
)

__all__ = [
    "AgentState",
    "AgentExecution",
    "AgentResult",
    "ThinkingStep",
    "AgentFacade",
    "ClaudeCodeAdapter",
    "XMLStreamingProtocol",
    "SkybridgeCommand",
]
