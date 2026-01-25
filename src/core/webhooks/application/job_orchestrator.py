# -*- coding: utf-8 -*-
"""
Job Orchestrator Application Service.

Orquestra a execução de jobs: cria worktree, captura snapshot,
executa agente e valida cleanup.

PRD018 ARCH-09: Migrado para emitir Domain Events.
Emite JobStartedEvent, JobCompletedEvent, JobFailedEvent.
"""
from __future__ import annotations

import asyncio
import logging
from datetime import datetime
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from core.webhooks.ports.job_queue_port import JobQueuePort
    from core.domain_events.event_bus import EventBus

from core.agents.worktree_validator import safe_worktree_cleanup
from core.webhooks.infrastructure.agents.claude_agent import (
    ClaudeCodeAdapter,
)
from core.webhooks.application.worktree_manager import (
    WorktreeManager,
)
from core.domain_events.job_events import (
    JobStartedEvent,
    JobCompletedEvent,
    JobFailedEvent,
    JobCommittedEvent,
    JobPushedEvent,
    PRCreatedEvent,
)
from kernel.contracts.result import Result


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
    # PRD020: Trello webhooks
    "card.moved.💡 Brainstorm": "analyze-issue",
    "card.moved.📋 A Fazer": "resolve-issue",
    "card.moved.🚧 Em Andamento": "resolve-issue",
    "card.moved.👁️ Em Revisão": "review-issue",
    "card.moved.🚀 Publicar": "publish-issue",
}

# PRD020: Mapeamento de autonomy_level para skill override
AUTONOMY_LEVEL_TO_SKILL = {
    "analysis": "analyze-issue",
    "development": "resolve-issue",
    "review": "review-issue",
    "publish": "publish-issue",
}


class JobOrchestrator:
    """
    Orquestra execução de jobs de webhook.

    Responsabilidades:
    - Criar worktree isolado
    - Capturar snapshot inicial
    - Executar agente (TODO: integrar com Task tool)
    - Validar e limpar worktree
    - Emitir Domain Events (JobStarted, JobCompleted, JobFailed)
    - PRD018 Fase 3: Commit/push/PR automático após job completado

    Fluxo:
        1. Dequeue job
        2. Emit JobStartedEvent
        3. Create worktree
        4. Capture initial snapshot
        5. Execute agent /resolve-issue skill
        6. Validate worktree before cleanup
        7. Emit JobCompletedEvent
        8. PRD018 Fase 3: Guardrails → Commit → Push → PR
        9. Emit JobCommittedEvent, JobPushedEvent, PRCreatedEvent
        10. Remove worktree if safe

    PRD018 ARCH-09: Desacoplado via Domain Events.
    PRD018 Fase 3: Autonomia 70% com commit/push/PR.
    """

    def __init__(
        self,
        job_queue: "JobQueuePort",
        worktree_manager: WorktreeManager,
        event_bus: "EventBus",
        agent_adapter: ClaudeCodeAdapter | None = None,
        guardrails=None,
        commit_message_generator=None,
        git_service=None,
        github_client=None,
        enable_auto_commit: bool = True,
        enable_auto_pr: bool = True,
    ):
        """
        Inicializa orchestrator.

        Args:
            job_queue: Fila de jobs
            worktree_manager: Gerenciador de worktrees
            event_bus: Event bus para emitir Domain Events
            agent_adapter: Adapter de agentes (opcional, cria default se None)
            guardrails: Guardrails para validação (opcional)
            commit_message_generator: Gerador de commit messages (opcional)
            git_service: Serviço de operações git (opcional)
            github_client: Cliente GitHub API (opcional)
            enable_auto_commit: Habilita commit/push automático (default: True)
            enable_auto_pr: Habilita criação de PR automática (default: True)
        """
        self.job_queue = job_queue
        self.worktree_manager = worktree_manager
        self.event_bus = event_bus

        # PRD019: Feature flag para selecionar adapter
        if agent_adapter is not None:
            self.agent_adapter = agent_adapter
        else:
            # Verifica feature flag USE_SDK_ADAPTER
            from runtime.config import get_feature_flags
            flags = get_feature_flags()
            if flags.use_sdk_adapter:
                from core.webhooks.infrastructure.agents.claude_sdk_adapter import ClaudeSDKAdapter
                self.agent_adapter = ClaudeSDKAdapter()
            else:
                self.agent_adapter = ClaudeCodeAdapter()

        self.guardrails = guardrails
        self.commit_message_generator = commit_message_generator
        self.git_service = git_service
        self.github_client = github_client
        self.enable_auto_commit = enable_auto_commit
        self.enable_auto_pr = enable_auto_pr
        self._job_start_time: dict[str, datetime] = {}
        logger = logging.getLogger(__name__)

    @staticmethod
    def _get_skill_for_event_type(event_type: str, autonomy_level: "AutonomyLevel | None" = None) -> str | None:
        """
        Retorna o skill apropriado para um event_type.

        PRD020: Considera autonomy_level para sobrescrever o skill padrão.

        Args:
            event_type: Tipo do evento (ex: "issues.opened", "issues.closed")
            autonomy_level: Nível de autonomia (PRD020)

        Returns:
            Nome do skill ou None se não deve executar agente
        """
        # PRD020: Se autonomy_level for especificado, usa mapeamento específico
        if autonomy_level is not None:
            # Usa getattr para pegar o valor .value do enum sem depender de isinstance
            autonomy_value = getattr(autonomy_level, "value", None)
            if autonomy_value:
                skill = AUTONOMY_LEVEL_TO_SKILL.get(autonomy_value)
                if skill:
                    return skill

        # Fallback para mapeamento padrão por event_type
        return EVENT_TYPE_TO_SKILL.get(event_type)

    async def execute_job(self, job_id: str) -> Result[None, str]:
        """
        Executa job completo: worktree → agent → cleanup.

        Emite JobStartedEvent, JobCompletedEvent ou JobFailedEvent.

        PRD018 ARCH-09: Desacoplado via Domain Events.

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

        # Registra tempo de início
        self._job_start_time[job_id] = datetime.utcnow()

        # PRD020: Determina skill baseado no event_type E autonomy_level
        skill = self._get_skill_for_event_type(job.event.event_type, job.autonomy_level)
        agent_type = skill or "none"

        # PRD018 ARCH-09: Emite JobStartedEvent
        repo_name = self._get_repo_name(job)
        await self.event_bus.publish(
            JobStartedEvent(
                aggregate_id=job_id,
                job_id=job_id,
                issue_number=job.issue_number,
                repository=repo_name,
                agent_type=agent_type,
            )
        )
        logging.getLogger(__name__).info(
            f"JobStartedEvent emitido | job_id={job_id} | issue=#{job.issue_number}"
        )

        if skill is None:
            # Evento não requer execução de agente
            from runtime.observability.logger import get_logger
            logger = get_logger()
            logger.info(
                f"Tipo de evento não requer execução de agente - pulando",
                extra={
                    "job_id": job.job_id,
                    "event_type": job.event.event_type,
                },
            )
            await self.job_queue.complete(job_id, {"skipped": True, "reason": "event_type does not require agent"})

            # Emite JobCompletedEvent mesmo para skipped jobs
            duration = (datetime.utcnow() - self._job_start_time[job_id]).total_seconds()
            await self.event_bus.publish(
                JobCompletedEvent(
                    aggregate_id=job_id,
                    job_id=job_id,
                    issue_number=job.issue_number,
                    repository=repo_name,
                    files_modified=0,
                    duration_seconds=duration,
                    worktree_path=job.worktree_path or "",
                )
            )

            return Result.ok(None)

        # Passo 1: Criar worktree
        worktree_result = self.worktree_manager.create_worktree(job)
        if worktree_result.is_err:
            # PRD018 ARCH-09: Emite JobFailedEvent
            duration = (datetime.utcnow() - self._job_start_time[job_id]).total_seconds()
            await self.event_bus.publish(
                JobFailedEvent(
                    aggregate_id=job_id,
                    job_id=job_id,
                    issue_number=job.issue_number,
                    repository=repo_name,
                    error_message=worktree_result.error,
                    error_type="WorktreeError",
                    duration_seconds=duration,
                    retry_count=0,
                )
            )
            await self.job_queue.fail(job_id, worktree_result.error)
            return worktree_result

        worktree_path = worktree_result.value

        # Passo 2: Capturar snapshot inicial
        from runtime.observability.snapshot.extractors.git_extractor import (
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
            error_msg = f"Erro ao capturar snapshot: {str(e)}"
            # PRD018 ARCH-09: Emite JobFailedEvent
            duration = (datetime.utcnow() - self._job_start_time[job_id]).total_seconds()
            await self.event_bus.publish(
                JobFailedEvent(
                    aggregate_id=job_id,
                    job_id=job_id,
                    issue_number=job.issue_number,
                    repository=repo_name,
                    error_message=error_msg,
                    error_type="SnapshotError",
                    duration_seconds=duration,
                    retry_count=0,
                )
            )
            await self.job_queue.fail(job_id, error_msg)
            return Result.err(error_msg)

        # Passo 3: Executar agente (RF004)
        from runtime.observability.logger import get_logger
        logger = get_logger()

        logger.info(
            f"Spawnando subagente para issue #{job.issue_number}",
            extra={
                "job_id": job_id,
                "worktree_path": job.worktree_path,
                "issue_number": job.issue_number,
            },
        )

        agent_result = await self._execute_agent(job, skill)
        if agent_result.is_err:
            # PRD018 ARCH-09: Emite JobFailedEvent
            duration = (datetime.utcnow() - self._job_start_time[job_id]).total_seconds()
            await self.event_bus.publish(
                JobFailedEvent(
                    aggregate_id=job_id,
                    job_id=job_id,
                    issue_number=job.issue_number,
                    repository=repo_name,
                    error_message=agent_result.error,
                    error_type="AgentError",
                    duration_seconds=duration,
                    retry_count=0,
                )
            )
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
            # Validação falhou - ainda assim marca como completo
            await self.job_queue.complete(job_id)

            # PRD018 ARCH-09: Emite JobCompletedEvent mesmo com advertências
            duration = (datetime.utcnow() - self._job_start_time[job_id]).total_seconds()
            files_modified = validation_result.value.get("status", {}).get("staged", 0) \
                + validation_result.value.get("status", {}).get("unstaged", 0) \
                + validation_result.value.get("status", {}).get("untracked", 0)

            await self.event_bus.publish(
                JobCompletedEvent(
                    aggregate_id=job_id,
                    job_id=job_id,
                    issue_number=job.issue_number,
                    repository=repo_name,
                    files_modified=files_modified,
                    duration_seconds=duration,
                    worktree_path=job.worktree_path or "",
                )
            )

            return Result.ok(
                f"Job completado mas validação falhou: {validation_result.error}"
            )

        # Marca job como completado
        await self.job_queue.complete(job_id)

        validation_info = validation_result.value

        # PRD018 ARCH-09: Emite JobCompletedEvent
        duration = (datetime.utcnow() - self._job_start_time[job_id]).total_seconds()
        files_modified = validation_info.get("status", {}).get("staged", 0) \
            + validation_info.get("status", {}).get("unstaged", 0) \
            + validation_info.get("status", {}).get("untracked", 0)

        await self.event_bus.publish(
            JobCompletedEvent(
                aggregate_id=job_id,
                job_id=job_id,
                issue_number=job.issue_number,
                repository=repo_name,
                files_modified=files_modified,
                duration_seconds=duration,
                worktree_path=job.worktree_path or "",
            )
        )
        logging.getLogger(__name__).info(
            f"JobCompletedEvent emitido | job_id={job_id} | files_modified={files_modified}"
        )

        # PRD018 Fase 3: Commit/Push/PR automático
        if self.enable_auto_commit:
            commit_push_result = await self._commit_and_push_pr(
                job=job,
                job_id=job_id,
                repo_name=repo_name,
            )
            # Não falha se commit/push/PR falhar - apenas loga
            if commit_push_result.is_err:
                logging.getLogger(__name__).warning(
                    f"Commit/Push/PR falhou (não-bloqueante): {commit_push_result.error}",
                    extra={"job_id": job_id},
                )

        return Result.ok({
            "message": "Job completado com sucesso",
            "worktree_path": job.worktree_path,
            "branch_name": job.branch_name,
            "validation": validation_info,
        })

    async def _execute_agent(self, job, skill: str) -> Result[dict, str]:
        """
        Executa agente no worktree (RF004) usando Agent Facade Pattern.

        Args:
            job: Job a ser executado
            skill: Nome do skill a executar (ex: "resolve-issue")

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
        from runtime.observability.logger import get_logger
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

    async def _commit_and_push_pr(
        self,
        job,
        job_id: str,
        repo_name: str,
    ) -> Result[dict, str]:
        """
        Executa commit/push/PR após job completado.

        PRD018 Fase 3: Fluxo completo de autonomia 70%.

        Args:
            job: Job completado
            job_id: ID do job
            repo_name: Nome do repositório

        Returns:
            Result com dict contendo commit_hash, pr_url, etc ou erro

        Fluxo:
            1. Guardrails (diff, syntax, pytest)
            2. Commit message generation
            3. Git add + commit
            4. Git push
            5. PR creation (via GitHub API)
            6. Emit events (JobCommitted, JobPushed, PRCreated)
        """
        worktree_path = job.worktree_path
        if not worktree_path:
            return Result.err("Worktree path não disponível")

        # Importa serviços sob demanda se não fornecidos
        if self.guardrails is None:
            from core.webhooks.application.guardrails import JobGuardrails
            self.guardrails = JobGuardrails()

        if self.commit_message_generator is None:
            from core.webhooks.application.commit_message_generator import CommitMessageGenerator
            self.commit_message_generator = CommitMessageGenerator(self.agent_adapter)

        if self.git_service is None:
            from core.webhooks.application.git_service import GitService
            self.git_service = GitService()

        # Passo 1: Guardrails
        guardrails_result = await self.guardrails.validate_all(worktree_path)
        if guardrails_result.is_err:
            return Result.err(f"Guardrails falharam: {guardrails_result.error}")

        guardrails_data = guardrails_result.value
        logging.getLogger(__name__).info(
            f"Guardrails passados | passed={guardrails_data.passed} | warnings={guardrails_data.warnings}",
            extra={"job_id": job_id, "metadata": guardrails_data.metadata},
        )

        # Passo 2: Commit message generation
        commit_msg_result = await self.commit_message_generator.generate(job, worktree_path)
        if commit_msg_result.is_err:
            return Result.err(f"Erro ao gerar commit message: {commit_msg_result.error}")

        commit_message = commit_msg_result.value

        # Passo 3: Git add + commit
        add_result = await self.git_service.add_all(worktree_path)
        if add_result.is_err:
            return Result.err(f"Git add falhou: {add_result.error}")

        commit_result = await self.git_service.commit(worktree_path, commit_message)
        if commit_result.is_err:
            return Result.err(f"Git commit falhou: {commit_result.error}")

        commit_hash = commit_result.value.commit_hash

        # Emite JobCommittedEvent
        await self.event_bus.publish(
            JobCommittedEvent(
                aggregate_id=job_id,
                job_id=job_id,
                issue_number=job.issue_number,
                repository=repo_name,
                commit_hash=commit_hash,
                commit_message=commit_message,
            )
        )
        logging.getLogger(__name__).info(
            f"JobCommittedEvent emitido | job_id={job_id} | commit_hash={commit_hash[:8]}"
        )

        # Passo 4: Git push
        push_result = await self.git_service.push(
            worktree_path=worktree_path,
            branch_name=job.branch_name,
        )
        if push_result.is_err:
            return Result.err(f"Git push falhou: {push_result.error}")

        # Emite JobPushedEvent
        await self.event_bus.publish(
            JobPushedEvent(
                aggregate_id=job_id,
                job_id=job_id,
                issue_number=job.issue_number,
                repository=repo_name,
                branch_name=job.branch_name,
                commit_hash=commit_hash,
            )
        )
        logging.getLogger(__name__).info(
            f"JobPushedEvent emitido | job_id={job_id} | branch={job.branch_name}"
        )

        # Passo 5: PR creation (se habilitado)
        pr_url = None
        pr_number = None

        if self.enable_auto_pr and self.github_client:
            # Extrai informações do issue
            issue = job.event.payload.get("issue", {})
            issue_title = issue.get("title", "")
            issue_body = issue.get("body", "")
            issue_labels = [l.get("name", "") for l in issue.get("labels", [])]

            # Determina branch base (main/dev)
            base_branch = await self._detect_base_branch(worktree_path)
            if base_branch.is_err:
                base_branch = Result.ok("main")  # Default

            pr_result = await self.github_client.create_pr(
                repo=repo_name,
                head=job.branch_name,
                base=base_branch.value,
                issue_number=job.issue_number,
                issue_title=issue_title,
                issue_body=issue_body,
                issue_labels=issue_labels,
            )

            if pr_result.is_ok:
                pr_data = pr_result.value
                pr_url = pr_data["pr_url"]
                pr_number = pr_data["pr_number"]

                # Emite PRCreatedEvent
                await self.event_bus.publish(
                    PRCreatedEvent(
                        aggregate_id=str(pr_number),
                        pr_number=pr_number,
                        issue_number=job.issue_number,
                        repository=repo_name,
                        pr_url=pr_url,
                        pr_title=pr_data["pr_title"],
                        branch_name=job.branch_name,
                    )
                )
                logging.getLogger(__name__).info(
                    f"PRCreatedEvent emitido | job_id={job_id} | pr_number={pr_number}"
                )

        return Result.ok({
            "commit_hash": commit_hash,
            "commit_message": commit_message,
            "pr_url": pr_url,
            "pr_number": pr_number,
            "branch_name": job.branch_name,
            "guardrails_metadata": guardrails_data.metadata,
        })

    async def _detect_base_branch(self, worktree_path: str) -> Result[str, str]:
        """
        Detecta branch base (main/dev) do repositório.

        Args:
            worktree_path: Caminho para o worktree

        Returns:
            Result com nome do branch base ou erro
        """
        try:
            # Tenta determinar branch remoto
            result = subprocess.run(
                ["git", "symbolic-ref", "refs/remotes/origin/HEAD"],
                cwd=worktree_path,
                capture_output=True,
                text=True,
                timeout=10,
            )

            if result.returncode == 0:
                # Output: refs/remotes/origin/main
                ref = result.stdout.strip()
                branch = ref.split("/")[-1]
                return Result.ok(branch)

            # Fallback: tenta listar branches remotos
            result = subprocess.run(
                ["git", "branch", "-r"],
                cwd=worktree_path,
                capture_output=True,
                text=True,
                timeout=10,
            )

            branches = result.stdout.strip().splitlines()
            # Procura por origin/main ou origin/master
            for branch in branches:
                if "origin/main" in branch:
                    return Result.ok("main")
                if "origin/master" in branch:
                    return Result.ok("master")
                if "origin/dev" in branch:
                    return Result.ok("dev")

            return Result.ok("main")  # Default

        except (subprocess.CalledProcessError, FileNotFoundError, subprocess.TimeoutExpired):
            return Result.ok("main")  # Default
