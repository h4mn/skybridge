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
from runtime.prompts import (
    render_system_prompt,
    load_system_prompt_config,
)

# Import de tipos do SDK - deve ser no topo para evitar NameError
try:
    from claude_agent_sdk.types import HookMatcher, HookContext
except ImportError:
    # Fallback para versões antigas do SDK
    HookMatcher = None  # type: ignore
    HookContext = None  # type: ignore


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
            # Configura opções do SDK com hooks de observabilidade
            options = ClaudeAgentOptions(
                system_prompt=system_prompt,
                permission_mode=self.permission_mode,  # type: ignore
                cwd=worktree_path,
                allowed_tools=self.allowed_tools or [],
                hooks=self._build_hooks_config(job, logger),
                max_turns=50,  # Limita turnos para evitar loop infinito
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

            # Cria e conecta cliente SDK (hooks já configurados nas options)
            logger.info(
                f"[SPAWN-1] Criando ClaudeSDKClient com hooks de observabilidade",
                extra={
                    "job_id": job.job_id,
                    "worktree": worktree_path,
                    "permission_mode": self.permission_mode,
                    "max_turns": 50,
                },
            )

            async with ClaudeSDKClient(options=options) as client:
                logger.info(
                    f"[SPAWN-2] Cliente SDK conectado, enviando query",
                    extra={
                        "job_id": job.job_id,
                        "prompt_length": len(main_prompt),
                        "prompt_preview": main_prompt[:200],
                    },
                )

                # Envia prompt principal
                await client.query(main_prompt)

                logger.info(
                    f"[SPAWN-3] Query enviada, iniciando consumo do stream (receive_response)",
                    extra={
                        "job_id": job.job_id,
                        "timeout": execution.timeout_seconds,
                        "method": "receive_response",
                    },
                )

                # CONSUME STREAM ÚNICO - captura stdout E aguarda ResultMessage
                # ADR021: Refatoração para streams - não usar receive_messages() separado
                result_message = None
                stdout_parts = []
                msg_count = 0

                try:
                    # Timeout aplicado ao stream completo
                    # BUG FIX: Usar asyncio.timeout() (Python 3.11+) ao invés de
                    # asyncio.wait_for() que não funciona com async for diretamente
                    logger.info(
                        f"[SPAWN-STREAM] Iniciando loop async for com timeout={execution.timeout_seconds}s",
                        extra={"job_id": job.job_id},
                    )

                    # Python 3.11+: usa asyncio.timeout() context manager
                    async with asyncio.timeout(execution.timeout_seconds):
                        async for msg in client.receive_response():
                            msg_count += 1
                            msg_type = msg.__class__.__name__
                            msg_subtype = getattr(msg, 'subtype', None)

                            # INFO para visibilidade - mostra cada mensagem recebida
                            logger.info(
                                f"[SPAWN-STREAM #{msg_count}] {msg_type} (subtype: {msg_subtype})",
                                extra={
                                    "job_id": job.job_id,
                                    "msg_count": msg_count,
                                    "msg_type": msg_type,
                                    "msg_subtype": str(msg_subtype),
                                    "has_content": hasattr(msg, "content"),
                                },
                            )

                            # Captura stdout durante o stream (AssistantMessage)
                            if hasattr(msg, "content") and msg.content is not None:
                                content_blocks = len(msg.content) if msg.content else 0
                                for block in msg.content:
                                    if hasattr(block, "text"):
                                        stdout_parts.append(block.text)

                                logger.info(
                                    f"[SPAWN-STREAM #{msg_count}] {msg_type} processou {content_blocks} blocos",
                                    extra={"job_id": job.job_id, "content_blocks": content_blocks},
                                )

                            # Captura ResultMessage quando aparecer (múltiplas formas de detecção)
                            # BUG FIX: hasattr(msg, 'is_error') retorna True para qualquer Mock
                            # SOLUÇÃO: Verificar se is_error é explicitamente True ou False
                            is_error_value = getattr(msg, 'is_error', None)
                            is_result_message = (
                                msg_type == "ResultMessage" or
                                msg_subtype in ['success', 'error'] or
                                is_error_value in [True, False]  # ← Detecta apenas se for bool
                            )

                            if is_result_message:
                                result_message = msg
                                logger.info(
                                    f"[SPAWN-4] ResultMessage capturada após {msg_count} mensagens - is_error={getattr(msg, 'is_error', None)}",
                                    extra={
                                        "job_id": job.job_id,
                                        "is_error": getattr(msg, 'is_error', None),
                                        "duration_ms": getattr(msg, 'duration_ms', None),
                                    },
                                )
                                break  # Stream termina aqui

                    # Log após o loop completar
                    logger.info(
                        f"[SPAWN-LOOP] Loop encerrou naturalmente - {msg_count} mensagens processadas",
                        extra={"job_id": job.job_id, "has_result": result_message is not None},
                    )

                except (asyncio.TimeoutError, TimeoutError) as timeout_err:
                    # asyncio.timeout() (Python 3.11+) levanta TimeoutError built-in
                    # asyncio.wait_for() levanta asyncio.TimeoutError
                    error_msg = f"Timeout no stream ({execution.timeout_seconds}s) após {msg_count} mensagens"
                    logger.error(
                        f"[SPAWN-ERROR] {error_msg}",
                        extra={"job_id": job.job_id, "messages_received": msg_count},
                    )
                    execution.mark_timed_out(error_msg)

                    # Salva execução com timeout no store
                    try:
                        from core.webhooks.application.handlers import get_agent_execution_store
                        store = get_agent_execution_store()
                        store.save(execution)
                    except Exception as save_error:
                        logger.error(
                            f"Erro ao salvar execução timeout: {save_error}",
                            extra={"job_id": job.job_id},
                        )

                    return Result.err(error_msg)

                # Verifica se recebeu ResultMessage
                if result_message is None:
                    error_msg = f"Stream encerrou sem ResultMessage ({msg_count} mensagens recebidas)"
                    logger.error(
                        f"[SPAWN-ERROR] {error_msg}",
                        extra={
                            "job_id": job.job_id,
                            "messages_received": msg_count,
                            "stdout_parts_count": len(stdout_parts),
                            "stdout_preview": "\n".join(stdout_parts)[:500] if stdout_parts else None,
                        },
                    )
                    execution.stdout = "\n".join(stdout_parts)  # Salva o que capturou
                    execution.mark_failed(error_msg)

                    # Salva execução falha no store
                    try:
                        from core.webhooks.application.handlers import get_agent_execution_store
                        store = get_agent_execution_store()
                        store.save(execution)
                    except Exception as save_error:
                        logger.error(
                            f"Erro ao salvar execução falha: {save_error}",
                            extra={"job_id": job.job_id},
                        )

                    return Result.err(error_msg)

                logger.info(
                    f"[SPAWN-5] Stream consumido com SUCESSO: {msg_count} mensagens, {len(stdout_parts)} partes de stdout",
                    extra={
                        "job_id": job.job_id,
                        "msg_count": msg_count,
                        "stdout_parts": len(stdout_parts),
                        "stdout_length": sum(len(p) for p in stdout_parts),
                    },
                )
                execution.stdout = "\n".join(stdout_parts)

            # Extrai resultado da ResultMessage
            logger.info(
                f"[SPAWN-6] Extraindo resultado da ResultMessage",
                extra={
                    "job_id": job.job_id,
                    "is_error": getattr(result_message, 'is_error', None),
                    "duration_ms": getattr(result_message, 'duration_ms', None),
                    "has_result": hasattr(result_message, 'result'),
                },
            )
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

            # Salva execução no store para consulta via API
            from core.webhooks.application.handlers import get_agent_execution_store
            store = get_agent_execution_store()
            store.save(execution)

            return Result.ok(execution)

        except Exception as e:
            error_msg = f"Erro ao executar agente SDK: {str(e)}"
            execution.mark_failed(error_msg)
            logger.error(
                error_msg,
                extra={"job_id": job.job_id, "error": str(e)},
            )

            # Salva execução falha no store
            try:
                from core.webhooks.application.handlers import get_agent_execution_store
                store = get_agent_execution_store()
                store.save(execution)
            except Exception as save_error:
                logger.error(
                    f"Erro ao salvar execução falha: {save_error}",
                    extra={"job_id": job.job_id},
                )

            return Result.err(error_msg)

    async def _wait_for_result(self, client, job_id: str) -> Any:
        """
        Aguarda ResultMessage do cliente SDK.

        .. DEPRECATED::
            ADR021 Refatoração de Streams (2026-01-31):
            Este método não é mais usado. O stream é consumido diretamente
            em spawn() para capturar stdout e ResultMessage em um único loop.

            Mantido apenas para compatibilidade. Será removido em versão futura.

        Args:
            client: ClaudeSDKClient conectado
            job_id: ID do job para logging

        Returns:
            ResultMessage com resultado da execução
        """
        from runtime.observability.logger import get_logger
        logger = get_logger()

        message_count = 0
        async for msg in client.receive_response():
            message_count += 1
            msg_type = msg.__class__.__name__
            msg_name = getattr(msg, 'name', None)

            logger.debug(
                f"[WAIT-FOR-RESULT] Mensagem #{message_count} recebida",
                extra={
                    "job_id": job_id,
                    "msg_type": msg_type,
                    "msg_name": msg_name,
                    "msg_class": str(type(msg)),
                },
            )

            # Verifica se é ResultMessage
            if msg_type == "ResultMessage":
                logger.debug(
                    f"[WAIT-FOR-RESULT] ResultMessage encontrada após {message_count} mensagens",
                    extra={"job_id": job_id, "is_error": getattr(msg, 'is_error', None)},
                )
                return msg

        # Se não recebeu ResultMessage, retorna None
        logger.warning(
            f"[WAIT-FOR-RESULT] receive_response() encerrou sem ResultMessage ({message_count} mensagens)",
            extra={"job_id": job_id},
        )
        return None

    def _build_hooks_config(self, job, logger) -> dict[str, Any]:
        """
        Constrói configuração de hooks de observabilidade para o SDK.

        Os hooks interceptam eventos do SDK para logging e telemetry:
        - PreToolUse: Log antes de cada tool use
        - PostToolUse: Log após cada tool use (com resultado)

        Args:
            job: Job de webhook
            logger: Logger estruturado

        Returns:
            Dict com configuração de hooks por evento
        """
        # Se HookMatcher não disponível (SDK antigo), retorna config vazio
        if HookMatcher is None:
            logger.warning("HookMatcher não disponível - hooks de observabilidade desabilitados")
            return {}

        async def pre_tool_hook(
            input_data: dict[str, Any],
            tool_use_id: str | None,
            context: HookContext,
        ) -> dict[str, Any]:
            """
            Hook executado antes de cada tool use.

            Loga detalhes da tool que será executada para observabilidade.
            CRÍTICO: Usa timeout no WebSocket para não travar o stream.
            """
            tool_name = input_data.get("tool_name", "unknown")
            tool_input = input_data.get("tool_input", {})

            logger.info(
                f"[HOOK] PreToolUse: {tool_name}",
                extra={
                    "job_id": job.job_id,
                    "tool": tool_name,
                    "tool_use_id": tool_use_id,
                    "input_keys": list(tool_input.keys()) if isinstance(tool_input, dict) else str(type(tool_input)),
                },
            )

            # Envia para WebSocket console se disponível - COM TIMEOUT para não travar stream
            try:
                from runtime.delivery.websocket import get_console_manager
                console_manager = get_console_manager()
                # Timeout de 1 segundo para evitar travar o stream
                await asyncio.wait_for(
                    console_manager.broadcast_raw(
                        job.job_id,
                        "tool_use",
                        f"Executando: {tool_name}",
                        {"tool": tool_name, "input": tool_input},
                    ),
                    timeout=1.0,
                )
            except asyncio.TimeoutError:
                logger.debug(
                    f"[HOOK] WebSocket broadcast timeout (pre_tool_hook) - continuando sem WebSocket",
                    extra={"job_id": job.job_id, "tool": tool_name},
                )
            except Exception as e:
                # WebSocket console não disponível, ignora silenciosamente
                logger.debug(
                    f"[HOOK] WebSocket broadcast falhou: {e}",
                    extra={"job_id": job.job_id, "tool": tool_name},
                )

            return {}

        async def post_tool_hook(
            input_data: dict[str, Any],
            tool_use_id: str | None,
            context: HookContext,
        ) -> dict[str, Any]:
            """
            Hook executado após cada tool use.

            Loga resultado da tool executada para observabilidade.
            CRÍTICO: Usa timeout no WebSocket para não travar o stream.
            """
            tool_name = input_data.get("tool_name", "unknown")
            tool_result = input_data.get("tool_result", {})
            is_error = tool_result.get("is_error", False)

            logger.info(
                f"[HOOK] PostToolUse: {tool_name} - {'SUCESSO' if not is_error else 'ERRO'}",
                extra={
                    "job_id": job.job_id,
                    "tool": tool_name,
                    "tool_use_id": tool_use_id,
                    "success": not is_error,
                    "is_error": is_error,
                },
            )

            # Não envia para WebSocket no post_tool_hook para evitar overhead
            # O resultado já está sendo capturado no stream principal

            return {}

        logger.info(
            f"[HOOKS] Configurando hooks de observabilidade",
            extra={"job_id": job.job_id, "hooks": ["PreToolUse", "PostToolUse"]},
        )

        return {
            "PreToolUse": [
                HookMatcher(hooks=[pre_tool_hook]),
            ],
            "PostToolUse": [
                HookMatcher(hooks=[post_tool_hook]),
            ],
        }

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

        Args:
            job: Job de webhook

        Returns:
            Prompt principal em linguagem natural
        """
        issue = job.event.payload.get("issue", {})

        return (
            f"Task: {issue.get('title', '')}\n\n"
            f"{issue.get('body', '')}\n\n"
            f"IMPORTANTE: Após completar esta task, retorne APENAS um JSON válido como sua resposta final. "
            f"Não continue executando comandos indefinidamente."
        )

    def _extract_result(self, result_message: Any) -> AgentResult:
        """
        Converte ResultMessage da SDK para AgentResult.

        Args:
            result_message: ResultMessage do claude-agent-sdk

        Returns:
            AgentResult com resultado estruturado
        """
        from runtime.observability.logger import get_logger
        logger = get_logger()

        if result_message is None:
            logger.warning(
                "[EXTRACT-RESULT] ResultMessage é None, retornando resultado sem sucesso",
                extra={"has_result": False},
            )
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
        # CORREÇÃO: is_error pode virar como True/False ou None
        # Se is_error é None ou não está presente, consideramos como sucesso
        is_error_value = getattr(result_message, 'is_error', None)
        is_success = is_error_value is not True  # Só é falha se for explicitamente True

        result_text = result_message.result if hasattr(result_message, "result") else ""

        logger.info(
            f"[EXTRACT-RESULT] Extraindo resultado da ResultMessage",
            extra={
                "is_error_value": str(is_error_value),
                "is_success": is_success,
                "has_result": hasattr(result_message, "result"),
                "result_text_length": len(result_text) if isinstance(result_text, str) else 0,
            },
        )

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
