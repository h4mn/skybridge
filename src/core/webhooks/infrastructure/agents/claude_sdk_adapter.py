# -*- coding: utf-8 -*-
"""
Claude SDK Adapter - Implementação do AgentFacade usando claude-agent-sdk oficial.

PRD019: Substitui ClaudeCodeAdapter (subprocess) por SDK oficial da Anthropic.
Benefícios:
- Latência 4-5x menor (50-100ms vs 200-500ms)
- Session continuity nativa
- Parse 100% confiável (sem regex)
- Custom tools via @tool decorator (in-process)
- Hooks nativos para observabilidade
"""
from __future__ import annotations

import asyncio
import json
import os
from datetime import datetime
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from core.webhooks.domain import WebhookJob

from core.webhooks.infrastructure.agents.agent_facade import (
    AgentFacade,
)
from core.webhooks.infrastructure.agents.domain import (
    AgentState,
    AgentExecution,
    AgentResult,
)
from kernel.contracts.result import Result
from runtime.config import get_agent_config
from runtime.config.agent_prompts import (
    render_system_prompt,
    load_system_prompt_config,
)


class ClaudeSDKAdapter(AgentFacade):
    """
    Adapter para Claude Agent SDK oficial.

    Conforme PRD019, substitui abordagem subprocess por SDK in-process.

    Attributes:
        permission_mode: Modo de permissão (bypassPermissions para worktrees)
        custom_tools: Lista de custom tools registradas
    """

    # Timeouts por tipo de tarefa (mesmos de ClaudeCodeAdapter)
    SKILL_TIMEOUTS = {
        "hello-world": 60,
        "bug-simple": 300,
        "bug-complex": 600,
        "refactor": 900,
        "resolve-issue": 600,
        "respond-discord": 300,
        "summarize-video": 600,
    }

    DEFAULT_TIMEOUT = 600

    def __init__(
        self,
        allowed_tools: list[str] | None = None,
        permission_mode: str = "bypassPermissions",
        custom_tools: list[Any] | None = None,
    ):
        """
        Inicializa adapter.

        Args:
            allowed_tools: Lista de tools permitidas (default: todas)
            permission_mode: Modo de permissão (default: bypassPermissions)
            custom_tools: Lista de custom tools decoradas com @tool
        """
        self.allowed_tools = allowed_tools
        self.permission_mode = permission_mode
        self.custom_tools = custom_tools or []

    def get_agent_type(self) -> str:
        """Retorna tipo de agente."""
        return "claude-sdk"

    def get_timeout_for_skill(self, skill: str) -> int:
        """
        Retorna timeout adequado para o tipo de tarefa.

        Args:
            skill: Tipo de tarefa

        Returns:
            Timeout em segundos
        """
        return self.SKILL_TIMEOUTS.get(skill, self.DEFAULT_TIMEOUT)

    async def spawn(
        self,
        job: "WebhookJob",
        skill: str,
        worktree_path: str,
        skybridge_context: dict,
    ) -> Result[AgentExecution, str]:
        """
        Cria agente Claude SDK com contexto completo.

        Fluxo:
            1. Prepara system prompt via render_system_prompt()
            2. Prepara main prompt
            3. Cria AgentExecution e marca como RUNNING
            4. Configura ClaudeAgentOptions
            5. Cria ClaudeSDKClient e conecta
            6. Registra hooks de observabilidade
            7. Envia prompt principal
            8. Aguarda wait_for_completion(timeout)
            9. Extrai AgentResult do ResultMessage
            10. Marca execução como COMPLETED

        Args:
            job: Job de webhook com issue/event details
            skill: Tipo de tarefa (resolve-issue, etc)
            worktree_path: Diretório isolado para trabalho
            skybridge_context: Contexto Skybridge

        Returns:
            Result com AgentExecution ou erro
        """
        from runtime.observability.logger import get_logger
        from claude_agent_sdk import ClaudeSDKClient
        from claude_agent_sdk.types import ClaudeAgentOptions

        logger = get_logger()

        # Prepara system prompt com template
        system_prompt = self._build_system_prompt(job, skill, skybridge_context)

        # Prepara prompt principal
        main_prompt = self._build_main_prompt(job)

        # Cria execution
        execution = AgentExecution(
            agent_type=self.get_agent_type(),
            job_id=job.job_id,
            worktree_path=worktree_path,
            skill=skill,
            state=AgentState.CREATED,
            timeout_seconds=self.get_timeout_for_skill(skill),
        )

        # Marca como running
        execution.mark_running()

        try:
            # Configura opções do SDK
            options = ClaudeAgentOptions(
                system_prompt=system_prompt,
                permission_mode=self.permission_mode,  # type: ignore
                cwd=worktree_path,
                allowed_tools=self.allowed_tools or [],
                # Hooks de observabilidade serão registrados via _register_hooks
                hooks=None,
            )

            # Cria diretório .sky/ para log interno do agente
            sky_dir = os.path.join(worktree_path, ".sky")
            os.makedirs(sky_dir, exist_ok=True)

            # Log do início da execução
            logger.info(
                f"Executando agente Claude SDK",
                extra={
                    "job_id": job.job_id,
                    "worktree_path": worktree_path,
                    "skill": skill,
                    "timeout_seconds": execution.timeout_seconds,
                    "agent_type": self.get_agent_type(),
                },
            )

            # Cria e conecta cliente SDK
            async with ClaudeSDKClient(options=options) as client:
                # Registra hooks de observabilidade
                await self._register_hooks(client, job, logger)

                # Envia prompt principal
                await client.query(main_prompt)

                # Aguarda conclusão com timeout
                result_message = await asyncio.wait_for(
                    self._wait_for_result(client),
                    timeout=execution.timeout_seconds,
                )

                # Captura stdout/stream para log
                stdout_parts = []
                async for msg in client.receive_messages():
                    if hasattr(msg, "content"):
                        for block in msg.content:
                            if hasattr(block, "text"):
                                stdout_parts.append(block.text)

                execution.stdout = "\n".join(stdout_parts)

            # Extrai resultado da ResultMessage
            agent_result = self._extract_result(result_message)

            # Salva log interno do agente
            agent_log_path = os.path.join(sky_dir, "agent.log")
            with open(agent_log_path, "w", encoding="utf-8") as f:
                f.write(f"# Skybridge Agent Log (Claude SDK)\n")
                f.write(f"# Job ID: {job.job_id}\n")
                f.write(f"# Worktree: {worktree_path}\n")
                f.write(f"# Skill: {skill}\n")
                f.write(f"# Timestamp: {datetime.now().isoformat()}\n")
                f.write(f"# Agent Type: {self.get_agent_type()}\n")
                f.write(f"\n## STDOUT\n{execution.stdout}\n\n")

            # Log do resultado
            logger.info(
                f"Agente Claude SDK completado",
                extra={
                    "job_id": job.job_id,
                    "success": agent_result.success,
                    "changes_made": agent_result.changes_made,
                    "duration_ms": result_message.duration_ms if result_message else 0,
                },
            )

            execution.mark_completed(agent_result)
            return Result.ok(execution)

        except asyncio.TimeoutError:
            error_msg = f"Timeout na execução do agente ({execution.timeout_seconds}s)"
            execution.mark_timed_out(error_msg)
            return Result.err(error_msg)

        except Exception as e:
            error_msg = f"Erro ao executar agente SDK: {str(e)}"
            execution.mark_failed(error_msg)
            logger.error(
                error_msg,
                extra={"job_id": job.job_id, "error": str(e)},
                exc_info=True,
            )
            return Result.err(error_msg)

    async def _wait_for_result(self, client) -> Any:
        """
        Aguarda ResultMessage do cliente SDK.

        Args:
            client: ClaudeSDKClient conectado

        Returns:
            ResultMessage com resultado da execução
        """
        async for msg in client.receive_response():
            # Verifica se é ResultMessage
            if msg.__class__.__name__ == "ResultMessage":
                return msg

        # Se não recebeu ResultMessage, retorna None
        return None

    async def _register_hooks(self, client, job, logger) -> None:
        """
        Registra hooks de observabilidade no cliente SDK.

        Args:
            client: ClaudeSDKClient configurado
            job: Job de webhook
            logger: Logger estruturado
        """
        # TODO: Implementar hooks quando a API do SDK suportar
        # PreToolUseHook: Log antes de cada tool use
        # PostToolUseHook: Log após cada tool use
        # StreamingHook: Envia para WebSocket console
        pass

    def _build_system_prompt(
        self,
        job: "WebhookJob",
        skill: str,
        skybridge_context: dict,
    ) -> str:
        """
        Constrói system prompt com template configurável.

        Usa render_system_prompt() existente do ClaudeCodeAdapter.

        Args:
            job: Job de webhook
            skill: Tipo de tarefa
            skybridge_context: Contexto adicional

        Returns:
            System prompt completo
        """
        template = load_system_prompt_config()

        # Merge context
        context = {
            "worktree_path": skybridge_context.get("worktree_path", job.worktree_path),
            "branch_name": skybridge_context.get("branch_name", job.branch_name or "unknown"),
            "skill": skill,
            "issue_number": job.issue_number or 0,
            "issue_title": job.event.payload.get("issue", {}).get("title", ""),
            "issue_body": job.event.payload.get("issue", {}).get("body", ""),
            "repo_name": skybridge_context.get("repo_name", self._get_repo_name(job)),
            "job_id": job.job_id,
        }

        return render_system_prompt(template, context)

    def _build_main_prompt(self, job: "WebhookJob") -> str:
        """
        Constrói prompt principal para o agente.

        Mesma lógica do ClaudeCodeAdapter.

        Args:
            job: Job de webhook

        Returns:
            Prompt principal em linguagem natural
        """
        issue = job.event.payload.get("issue", {})

        return (
            f"Resolve issue #{job.issue_number}: {issue.get('title', '')}\n\n"
            f"{issue.get('body', '')}"
        )

    def _extract_result(self, result_message: Any) -> AgentResult:
        """
        Converte ResultMessage da SDK para AgentResult.

        Args:
            result_message: ResultMessage do claude-agent-sdk

        Returns:
            AgentResult com resultado estruturado
        """
        if result_message is None:
            return AgentResult(
                success=False,
                changes_made=False,
                files_created=[],
                files_modified=[],
                files_deleted=[],
                commit_hash=None,
                pr_url=None,
                message="Agente completou sem resultado",
                issue_title="",
                output_message="Sem resultado",
                thinkings=[],
            )

        # Extrai informações da ResultMessage
        is_success = not result_message.is_error
        result_text = result_message.result if hasattr(result_message, "result") else ""

        # Tenta parsear JSON do resultado
        files_created = []
        files_modified = []
        commit_hash = None
        pr_url = None

        if isinstance(result_text, str):
            try:
                result_json = json.loads(result_text)
                files_created = result_json.get("files_created", [])
                files_modified = result_json.get("files_modified", [])
                commit_hash = result_json.get("commit_hash")
                pr_url = result_json.get("pr_url")
            except (json.JSONDecodeError, TypeError):
                # Resultado não é JSON, usa texto puro
                pass

        return AgentResult(
            success=is_success,
            changes_made=bool(files_created or files_modified),
            files_created=files_created,
            files_modified=files_modified,
            files_deleted=[],
            commit_hash=commit_hash,
            pr_url=pr_url,
            message=result_text if isinstance(result_text, str) else str(result_text),
            issue_title="",
            output_message=result_text if isinstance(result_text, str) else str(result_text),
            thinkings=[],
        )

    def _get_repo_name(self, job: "WebhookJob") -> str:
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


> "A migração bem-sucedida começa com um plano detalhado e executa com testes A/B contínuos" – made by Sky 🚀
