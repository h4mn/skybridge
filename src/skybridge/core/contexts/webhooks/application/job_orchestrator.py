# -*- coding: utf-8 -*-
"""
Job Orchestrator Application Service.

Orquestra a execução de jobs: cria worktree, captura snapshot,
executa agente e valida cleanup.
"""
from __future__ import annotations

import asyncio
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from skybridge.core.contexts.webhooks.ports.job_queue_port import JobQueuePort

from skybridge.core.contexts.agents.worktree_validator import safe_worktree_cleanup
from skybridge.core.contexts.webhooks.infrastructure.agents.claude_agent import (
    ClaudeCodeAdapter,
)
from skybridge.core.contexts.webhooks.application.worktree_manager import (
    WorktreeManager,
)
from skybridge.kernel.contracts.result import Result


# Mapeamento de event_type para skill (PRD013)
EVENT_TYPE_TO_SKILL = {
    # Issues - apenas opened/reopened/edited precisam de resolução
    "issues.opened": "resolve-issue",
    "issues.reopened": "resolve-issue",
    "issues.edited": "resolve-issue",
    # Issues closed/deleted não executam agente (None)
    "issues.closed": None,
    "issues.deleted": None,
    "issues.labeled": None,
    "issues.unlabeled": None,
    "issues.assigned": None,
    "issues.unassigned": None,
    # Issue comments - responder via Discord (TODO)
    "issue_comment.created": "respond-discord",
    "issue_comment.edited": "respond-discord",
    "issue_comment.deleted": None,
    # Pull requests (TODO)
    "pull_request.opened": None,
    "pull_request.closed": None,
    "pull_request.edited": None,
}


class JobOrchestrator:
    """
    Orquestra execução de jobs de webhook.

    Responsabilidades:
    - Criar worktree isolado
    - Capturar snapshot inicial
    - Executar agente (TODO: integrar com Task tool)
    - Validar e limpar worktree

    Fluxo:
        1. Dequeue job
        2. Create worktree
        3. Capture initial snapshot
        4. Execute agent /resolve-issue skill
        5. Validate worktree before cleanup
        6. Remove worktree if safe

    Attributes:
        job_queue: Fila de jobs
        worktree_manager: Gerenciador de worktrees
    """

    def __init__(
        self,
        job_queue: "JobQueuePort",
        worktree_manager: WorktreeManager,
        agent_adapter: ClaudeCodeAdapter | None = None,
    ):
        """
        Inicializa orchestrator.

        Args:
            job_queue: Fila de jobs
            worktree_manager: Gerenciador de worktrees
            agent_adapter: Adapter de agentes (opcional, cria default se None)
        """
        self.job_queue = job_queue
        self.worktree_manager = worktree_manager
        self.agent_adapter = agent_adapter or ClaudeCodeAdapter()

    @staticmethod
    def _get_skill_for_event_type(event_type: str) -> str | None:
        """
        Retorna o skill apropriado para um event_type.

        Args:
            event_type: Tipo do evento (ex: "issues.opened", "issues.closed")

        Returns:
            Nome do skill ou None se não deve executar agente
        """
        return EVENT_TYPE_TO_SKILL.get(event_type)

    async def execute_job(self, job_id: str) -> Result[None, str]:
        """
        Executa job completo: worktree → agent → cleanup.

        Args:
            job_id: ID do job a executar

        Returns:
            Result indicando sucesso ou erro
        """
        # Busca job
        job = await self.job_queue.get_job(job_id)
        if not job:
            return Result.err(f"Job não encontrado: {job_id}")

        # Marca como em processamento
        job.mark_processing()

        # Determina skill baseado no event_type (alguns eventos não executam agente)
        skill = self._get_skill_for_event_type(job.event.event_type)
        if skill is None:
            # Evento não requer execução de agente (ex: issues.closed, issues.deleted)
            from skybridge.platform.observability.logger import get_logger
            logger = get_logger()
            logger.info(
                f"Tipo de evento não requer execução de agente - pulando",
                extra={
                    "job_id": job.job_id,
                    "event_type": job.event.event_type,
                },
            )
            await self.job_queue.complete(job_id, {"skipped": True, "reason": "event_type does not require agent"})
            return Result.ok(None)

        # Passo 1: Criar worktree
        worktree_result = self.worktree_manager.create_worktree(job)
        if worktree_result.is_err:
            await self.job_queue.fail(job_id, worktree_result.error)
            return worktree_result

        worktree_path = worktree_result.value

        # Passo 2: Capturar snapshot inicial
        from skybridge.platform.observability.snapshot.extractors.git_extractor import (
            GitExtractor,
        )

        extractor = GitExtractor()
        try:
            initial_snapshot = extractor.capture(worktree_path)
            job.initial_snapshot = {
                "metadata": initial_snapshot.metadata.model_dump(),
                "stats": initial_snapshot.stats.model_dump(),
                "structure": initial_snapshot.structure,
            }
        except Exception as e:
            await self.job_queue.fail(job_id, f"Erro ao capturar snapshot: {str(e)}")
            return Result.err(f"Erro ao capturar snapshot: {str(e)}")

        # Passo 3: Executar agente (RF004)
        from skybridge.platform.observability.logger import get_logger
        logger = get_logger()

        logger.info(
            f"Spawnando subagente para issue #{job.issue_number}",
            extra={
                "job_id": job_id,
                "worktree_path": job.worktree_path,
                "issue_number": job.issue_number,
            },
        )

        agent_result = await self._execute_agent(job)
        if agent_result.is_err:
            await self.job_queue.fail(job_id, agent_result.error)
            return agent_result

        # RF004 executado com sucesso
        agent_output = agent_result.value
        logger.info(
            f"Subagente completou: {agent_output.get('message', 'OK')}",
            extra={
                "job_id": job_id,
                "changes_made": agent_output.get("changes_made", False),
                "simulated": agent_output.get("simulated", False),
            },
        )

        # Passo 4: Validar worktree (RF005 - NÃO remove)
        validation_result = self._validate_worktree(job)
        if validation_result.is_err:
            # Validação falhou
            await self.job_queue.complete(job_id)
            return Result.ok(
                f"Job completado mas validação falhou: {validation_result.error}"
            )

        # Marca job como completado
        await self.job_queue.complete(job_id)

        validation_info = validation_result.value
        return Result.ok({
            "message": "Job completado com sucesso",
            "worktree_path": job.worktree_path,
            "branch_name": job.branch_name,
            "validation": validation_info,
        })

    async def _execute_agent(self, job) -> Result[dict, str]:
        """
        Executa agente no worktree (RF004) usando Agent Facade Pattern.

        Args:
            job: Job a ser executado

        Returns:
            Result com output do agente ou erro

        Note:
            RF004: Spawna subagente com contexto específico no worktree.
            Conforme SPEC008: Usa ClaudeCodeAdapter com streaming em tempo real.
        """
        import asyncio

        # Prepara contexto Skybridge para o agente
        skybridge_context = {
            "worktree_path": job.worktree_path,
            "branch_name": job.branch_name or "unknown",
            "repo_name": self._get_repo_name(job),
        }

        # Spawna agente com ClaudeCodeAdapter (SPEC008)
        execution_result = self.agent_adapter.spawn(
            job=job,
            skill=skill,  # Skill determinado pelo mapeamento event_type → skill
            worktree_path=job.worktree_path,
            skybridge_context=skybridge_context,
        )

        if execution_result.is_err:
            return Result.err(f"Erro ao executar agente: {execution_result.error}")

        execution = execution_result.value

        # Extrai resultado da execução
        if execution.result is None:
            return Result.err("Agente completou sem resultado")

        # Converte AgentResult para dict (para compatibilidade)
        output_dict = execution.result.to_dict()

        # Aguarda um momento para garantir que operações assíncronas completem
        await asyncio.sleep(0.1)

        return Result.ok(output_dict)

    def _get_repo_name(self, job) -> str:
        """
        Extrai nome do repositório do payload.

        Args:
            job: Job de webhook

        Returns:
            Nome do repositório (owner/repo)
        """
        repository = job.event.payload.get("repository", {})
        owner = repository.get("owner", {}).get("login", "unknown")
        name = repository.get("name", "unknown")
        return f"{owner}/{name}"

    def _validate_worktree(self, job) -> Result[dict, str]:
        """
        Valida estado do worktree SEM remover (RF005).

        Args:
            job: Job com worktree a validar

        Returns:
            Result com informações da validação

        Note:
            RF005 agora APENAS valida o worktree.
            O worktree é preservado para inspeção manual.
        """
        if not job.worktree_path:
            return Result.ok({"validated": False, "message": "Sem worktree"})

        # Valida estado (dry-run)
        validation = safe_worktree_cleanup(
            job.worktree_path,
            require_clean=False,  # Permite untracked files
            dry_run=True,
        )

        # Log da validação
        from skybridge.platform.observability.logger import get_logger
        logger = get_logger()

        logger.info(
            f"Worktree validado: {validation['message']}",
            extra={
                "job_id": job.job_id,
                "worktree_path": job.worktree_path,
                "can_remove": validation["can_remove"],
                "is_clean": validation.get("status", {}).get("clean", False),
                "staged": validation.get("status", {}).get("staged", 0),
                "unstaged": validation.get("status", {}).get("unstaged", 0),
                "untracked": validation.get("status", {}).get("untracked", 0),
            },
        )

        return Result.ok({
            "validated": True,
            "can_remove": validation["can_remove"],
            "message": validation["message"],
            "status": validation.get("status", {}),
        })
