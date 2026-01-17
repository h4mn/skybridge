# -*- coding: utf-8 -*-
"""
Agent Facade - Interface abstrata para agentes AI.

Conforme SPEC008 seção 5 - Agent Facade (Framework).

O Agent Facade é uma camada de abstração que:
- Isola o orchestrator de diferenças entre agentes (Claude, Roo, Copilot)
- Fornece interface única para criação de agentes
- Traduz contexto Skybridge para formato específico de cada agente
- Normaliza saída de diferentes agentes para formato comum
"""
from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from core.webhooks.domain import WebhookJob
    from core.webhooks.infrastructure.agents.domain import (
        AgentExecution,
    )

from kernel.contracts.result import Result


class AgentFacade(ABC):
    """
    Interface abstrata para criação de agentes AI.

    Conforme SPEC008 seção 5.2 - Interface.

    Esta interface define o contrato que todos os adapters de agentes
    devem implementar, permitindo que o orchestrator trabalhe
    com diferentes tipos de agentes de forma uniforme.
    """

    @abstractmethod
    def spawn(
        self,
        job: "WebhookJob",
        skill: str,
        worktree_path: str,
        skybridge_context: dict,
    ) -> Result["AgentExecution", str]:
        """
        Cria agente com contexto completo.

        Args:
            job: Job de webhook com issue/event details
            skill: Tipo de tarefa (resolve-issue, respond-discord, etc)
            worktree_path: Diretório isolado para trabalho
            skybridge_context: Contexto Skybridge (repo, branch, issue_number, etc)

        Returns:
            Result com AgentExecution ou erro (mensagem)

        Example:
            >>> from core.webhooks.infrastructure.agents import ClaudeCodeAdapter
            >>> facade = ClaudeCodeAdapter()
            >>> result = facade.spawn(job, "resolve-issue", worktree_path, context)
            >>> if result.is_ok:
            ...     execution = result.value
            ...     # Agente executou com sucesso
        """
        pass

    @abstractmethod
    def get_agent_type(self) -> str:
        """
        Retorna tipo de agente.

        Returns:
            Tipo de agente (claude-code, roo-code, copilot, etc)
        """
        pass

    @abstractmethod
    def get_timeout_for_skill(self, skill: str) -> int:
        """
        Retorna timeout adequado para o tipo de tarefa.

        Conforme SPEC008 seção 8.2 - Timeout.

        Args:
            skill: Tipo de tarefa

        Returns:
            Timeout em segundos
        """
        pass
