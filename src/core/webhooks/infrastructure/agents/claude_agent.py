# -*- coding: utf-8 -*-
"""
Claude Code Adapter - Implementação do AgentFacade para Claude Code CLI.

Conforme SPEC008 seção 5.3 - Adapters Específicos.
"""
from __future__ import annotations

import json
import subprocess
from datetime import datetime
from typing import TYPE_CHECKING

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
from core.webhooks.infrastructure.agents.protocol import (
    XMLStreamingProtocol,
)
from kernel.contracts.result import Result
from runtime.config import get_agent_config
from runtime.config.agent_prompts import (
    load_system_prompt_config,
    render_system_prompt,
    get_json_validation_prompt,
)


class ClaudeCodeAdapter(AgentFacade):
    """
    Adapter para Claude Code CLI.

    Conforme SPEC008 seção 5.3:

    Executa Claude Code como subprocesso com:
    - stdin/stdout streaming para comunicação
    - System prompt configurável via config/agent_prompts.py
    - Timeout por skill
    - Saída estruturada JSON

    Attributes:
        claude_code_path: Caminho para o executável do Claude Code
        protocol: Protocolo de comunicação XML streaming
    """

    # Timeouts por tipo de tarefa (SPEC008 seção 8.2)
    SKILL_TIMEOUTS = {
        "hello-world": 60,  # 1 min - Simples, deve ser rápido
        "bug-simple": 300,  # 5 min - Bug fix simples
        "bug-complex": 600,  # 10 min - Bug fix complexo
        "refactor": 900,  # 15 min - Refatoração
        "resolve-issue": 600,  # 10 min - Default para issues
        "respond-discord": 300,  # 5 min - Resposta Discord
        "summarize-video": 600,  # 10 min - Sumarização vídeo
    }

    DEFAULT_TIMEOUT = 600  # 10 min

    def __init__(
        self,
        claude_code_path: str | None = None,
        protocol: XMLStreamingProtocol | None = None,
    ):
        """
        Inicializa adapter.

        Args:
            claude_code_path: Caminho para executável (default: da config/AgentConfig)
            protocol: Protocolo de comunicação (default: XMLStreamingProtocol())
        """
        if claude_code_path is None:
            agent_config = get_agent_config()
            claude_code_path = agent_config.claude_code_path
        self.claude_code_path = claude_code_path
        self.protocol = protocol or XMLStreamingProtocol()

    def get_agent_type(self) -> str:
        """Retorna tipo de agente."""
        return "claude-code"

    def get_timeout_for_skill(self, skill: str) -> int:
        """
        Retorna timeout adequado para o tipo de tarefa.

        Conforme SPEC008 seção 8.2 - Timeout.

        Args:
            skill: Tipo de tarefa

        Returns:
            Timeout em segundos
        """
        return self.SKILL_TIMEOUTS.get(skill, self.DEFAULT_TIMEOUT)

    def spawn(
        self,
        job: "WebhookJob",
        skill: str,
        worktree_path: str,
        skybridge_context: dict,
    ) -> Result[AgentExecution, str]:
        """
        Cria agente Claude Code com contexto completo.

        Conforme SPEC008 seção 5.3 - Adapters Específicos.

        Args:
            job: Job de webhook com issue/event details
            skill: Tipo de tarefa (resolve-issue, etc)
            worktree_path: Diretório isolado para trabalho
            skybridge_context: Contexto Skybridge

        Returns:
            Result com AgentExecution ou erro
        """
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
            # Constrói comando
            cmd = self._build_command(worktree_path, system_prompt)

            from runtime.observability.logger import get_logger
            logger = get_logger()

            # Log do comando que será executado
            logger.info(
                f"Executando agente Claude Code",
                extra={
                    "job_id": job.job_id,
                    "command": " ".join(cmd),
                    "worktree_path": worktree_path,
                    "skill": skill,
                    "timeout_seconds": execution.timeout_seconds,
                },
            )

            # Cria diretório .sky/ para log interno do agente (SPEC008 seção 8)
            import os
            sky_dir = os.path.join(worktree_path, ".sky")
            os.makedirs(sky_dir, exist_ok=True)

            # Executa com subprocess.Popen para streaming em tempo real
            # Conforme SPEC008 seção 6.4 - Mecanismo de Streaming
            # Nota: Usamos encoding='utf-8' e errors='replace' para lidar com caracteres especiais
            process = subprocess.Popen(
                cmd,
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                encoding='utf-8',
                errors='replace',
                cwd=worktree_path,
            )

            # Envia prompt principal via stdin (não fecha stdin para permitir retry)
            if main_prompt:
                # Inclui instrução de validação JSON para garantir resposta correta
                validation_instruction = "\n\nIMPORTANT: Your response MUST be ONLY valid JSON, nothing else. No markdown formatting."
                full_prompt = main_prompt + validation_instruction

                process.stdin.write(full_prompt)
                logger.info(
                    f"Prompt principal enviado ao agente via stdin",
                    extra={"job_id": job.job_id, "prompt_length": len(full_prompt)},
                )

            # Fecha stdin após enviar o prompt
            if process.stdin and not process.stdin.closed:
                process.stdin.close()

            # Buffer para capturar stdout completo
            stdout_buffer = []
            final_json_line = None
            line_count = 0

            # Loop de leitura em tempo real (streaming)
            # Conforme SPEC008 seção 6.4:
            # "Agente → Orchestrator: Envia comandos XML via stdout durante execução"
            logger.info(
                f"Iniciando leitura do stdout do agente...",
                extra={"job_id": job.job_id},
            )

            for line in process.stdout:
                stdout_buffer.append(line)
                line_count += 1
                line_stripped = line.strip()

                # Log a cada 100 linhas para não poluir
                if line_count % 100 == 0:
                    logger.info(
                        f"Progresso da saída do agente: {line_count} lines received",
                        extra={"job_id": job.job_id, "line_count": line_count},
                    )

                # Log de linhas importantes do agente
                if any(keyword in line_stripped.lower() for keyword in ["error", "warning", "failed", "permission", "confirm"]):
                    logger.warning(
                        f"Agent output: {line_stripped[:200]}",
                        extra={"job_id": job.job_id, "raw_line": line_stripped},
                    )

                # Processa comandos XML em tempo real
                if self.protocol.is_xml_command(line_stripped):
                    commands = self.protocol.parse_commands(line_stripped)
                    for cmd in commands:
                        # Armazena comando na execução para observabilidade
                        execution.xml_commands_received.append(cmd)
                        # Log do comando recebido
                        logger.info(
                            f"Comando Skybridge recebido: {cmd.command}",
                            extra={
                                "job_id": job.job_id,
                                "command": cmd.command,
                                "params": cmd.params,
                            },
                        )

                # Detecta JSON final (última linha começa com {)
                elif line_stripped.startswith("{") and self.protocol.is_json_output(line_stripped):
                    final_json_line = line_stripped
                    logger.info(
                        f"Saída JSON final detectada",
                        extra={"job_id": job.job_id, "json_preview": line_stripped[:200]},
                    )

            logger.info(
                f"Stdout do agente completo: {line_count} lines read",
                extra={"job_id": job.job_id, "total_lines": line_count},
            )

            # Aguarda processo terminar
            return_code = process.wait()
            stderr_output = process.stderr.read()

            # Captura stdout e stderr completos
            execution.stdout = "".join(stdout_buffer)
            execution.stderr = stderr_output

            # Salva log interno do agente em .sky/agent.log (SPEC008 seção 8)
            agent_log_path = os.path.join(sky_dir, "agent.log")
            with open(agent_log_path, "w", encoding="utf-8") as f:
                f.write(f"# Skybridge Agent Log\n")
                f.write(f"# Job ID: {job.job_id}\n")
                f.write(f"# Worktree: {worktree_path}\n")
                f.write(f"# Skill: {skill}\n")
                f.write(f"# Timestamp: {datetime.now().isoformat()}\n")
                f.write(f"# Return Code: {return_code}\n")
                f.write(f"\n## STDOUT\n{execution.stdout}\n\n")
                f.write(f"\n## STDERR\n{execution.stderr}\n")

            # Log do resultado do processo
            logger.info(
                f"Processo do agente finalizado",
                extra={
                    "job_id": job.job_id,
                    "return_code": return_code,
                    "stderr_length": len(stderr_output),
                    "stdout_length": len(execution.stdout),
                },
            )

            # Log stderr se houver conteúdo
            if stderr_output:
                logger.error(
                    f"Stderr do agente: {stderr_output}",
                    extra={"job_id": job.job_id, "stderr": stderr_output},
                )

            # Verifica return code
            if return_code != 0:
                error_msg = (
                    f"Claude Code falhou com código {return_code}: {stderr_output}"
                )
                execution.mark_failed(error_msg)
                return Result.err(error_msg)

            # Parse output JSON final
            if final_json_line:
                try:
                    agent_result = self._parse_agent_output(final_json_line)
                    logger.info(
                        f"Resultado do agente parseado com sucesso",
                        extra={
                            "job_id": job.job_id,
                            "success": agent_result.success,
                            "changes_made": agent_result.changes_made,
                        },
                    )
                    execution.mark_completed(agent_result)
                    return Result.ok(execution)

                except json.JSONDecodeError as e:
                    error_msg = f"Output do agente não é JSON válido: {e}"
                    logger.error(
                        error_msg,
                        extra={"job_id": job.job_id, "json_line": final_json_line[:500]},
                    )
                    execution.mark_failed(error_msg)
                    return Result.err(error_msg)
            else:
                # Tenta recuperar JSON do stdout
                # O agente pode ter retornado JSON em formato markdown ou misturado com texto
                recovered_json = self._try_recover_json(execution.stdout)

                if recovered_json:
                    try:
                        agent_result = self._parse_agent_output(recovered_json)
                        logger.info(
                            f"Resultado do agente recuperado do stdout",
                            extra={
                                "job_id": job.job_id,
                                "success": agent_result.success,
                                "recovered": True,
                            },
                        )
                        execution.mark_completed(agent_result)
                        return Result.ok(execution)

                    except (json.JSONDecodeError, Exception) as e:
                        error_msg = f"JSON recuperado não é válido: {e}"
                        logger.error(
                            error_msg,
                            extra={"job_id": job.job_id, "recovered_json": recovered_json[:500]},
                        )

                # Log do stdout completo quando não há JSON
                error_msg = "Agente finalizou sem output JSON válido"
                logger.error(
                    error_msg,
                    extra={
                        "job_id": job.job_id,
                        "stdout_preview": execution.stdout[:1000] if execution.stdout else "EMPTY",
                        "stdout_length": len(execution.stdout) if execution.stdout else 0,
                        "line_count": line_count,
                    },
                )
                # Log completo do stdout para debug
                logger.debug(
                    f"Full agent stdout:\n{execution.stdout}",
                    extra={"job_id": job.job_id},
                )
                execution.mark_failed(error_msg)
                return Result.err(error_msg)

        except subprocess.TimeoutExpired as e:
            # Mata processo em caso de timeout
            if 'process' in locals() and process.poll() is None:
                process.kill()
                stderr_output = process.stderr.read() if process.stderr else ""

            error_msg = f"Timeout na execução do agente ({execution.timeout_seconds}s)"
            execution.mark_timed_out(error_msg)
            execution.stderr = stderr_output if 'stderr_output' in locals() else (e.stderr if e.stderr else "")
            return Result.err(error_msg)

        except Exception as e:
            error_msg = f"Erro ao executar agente: {str(e)}"
            execution.mark_failed(error_msg)
            return Result.err(error_msg)

    def _build_command(self, worktree_path: str, system_prompt: str) -> list[str]:
        """
        Constrói comando Claude Code com flags adequadas.

        Conforme SPEC008 seção 8.1.

        Args:
            worktree_path: Diretório de trabalho isolado (usado via cwd do Popen, não como flag)
            system_prompt: Contexto da tarefa

        Returns:
            Lista de argumentos para subprocess.Popen()
        """
        return [
            self.claude_code_path,
            "--print",  # Modo não-interativo
            "--system-prompt", system_prompt,  # Contexto completo
            "--output-format", "json",  # Saída estruturada
            "--permission-mode", "bypassPermissions",  # Worktree já é sandbox (valor correto: bypassPermissions)
        ]

    def _build_system_prompt(
        self,
        job: "WebhookJob",
        skill: str,
        skybridge_context: dict,
    ) -> str:
        """
        Constrói system prompt com template configurável.

        Conforme SPEC008 seção 7 - System Prompts como Fonte da Verdade.

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
            f"Resolve issue #{job.issue_number}: {issue.get('title', '')}\n\n"
            f"{issue.get('body', '')}"
        )

    def _parse_agent_output(self, stdout: str) -> AgentResult:
        """
        Parseia output JSON do Claude Code.

        Conforme SPEC008 seção 9.2 - Saída (stdout).

        Args:
            stdout: Saída stdout do processo

        Returns:
            AgentResult com resultado estruturado
        """
        # Claude Code CLI retorna JSON com formato específico:
        # {"type": "result", "subtype": "success", "result": "...", ...}
        output = json.loads(stdout)

        # Determina sucesso baseado no formato do Claude Code CLI
        is_success = (
            not output.get("is_error", False) and
            output.get("type") == "result" and
            output.get("subtype") == "success"
        )

        # Extrai mensagem de resultado
        result_text = output.get("result", "")
        output_message = result_text if isinstance(result_text, str) else str(result_text)

        # Tenta extrair informações do resultado (pode vir no formato JSON embutido)
        files_created = []
        files_modified = []
        commit_hash = None
        pr_url = None

        # Se o resultado contiver JSON com informações de arquivos, extrai
        if isinstance(result_text, str):
            try:
                # Tenta fazer parse do resultado se for JSON
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
            message=output.get("result", ""),
            issue_title="",
            output_message=output_message,
            thinkings=[],  # Thinkings podem vir em formato diferente
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

    def _try_recover_json(self, stdout: str) -> str | None:
        """
        Tenta recuperar JSON do stdout do agente.

        O agente pode retornar JSON em diferentes formatos:
        - JSON puro: {"success": true, ...}
        - Bloco markdown: ```json\n{...}\n```
        - Texto misturado: Algum texto {"success": true} mais texto

        Args:
            stdout: Saída completa do stdout do agente

        Returns:
            String JSON recuperado ou None se não encontrado
        """
        import re

        if not stdout or not stdout.strip():
            return None

        # Tenta 1: Stdout é JSON puro
        try:
            json.loads(stdout.strip())
            return stdout.strip()
        except json.JSONDecodeError:
            pass

        # Tenta 2: Extrai bloco ```json ... ```
        json_block_match = re.search(r'```json\s*(\{.*?\})\s*```', stdout, re.DOTALL)
        if json_block_match:
            json_str = json_block_match.group(1)
            try:
                json.loads(json_str)
                return json_str
            except json.JSONDecodeError:
                pass

        # Tenta 3: Extrai bloco ``` ... ```
        code_block_match = re.search(r'```\s*(\{.*?\})\s*```', stdout, re.DOTALL)
        if code_block_match:
            json_str = code_block_match.group(1)
            try:
                json.loads(json_str)
                return json_str
            except json.JSONDecodeError:
                pass

        # Tenta 4: Busca por objeto JSON em qualquer lugar do texto
        # Procura por { ... } que seja um JSON válido
        json_obj_match = re.search(r'\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\}', stdout, re.DOTALL)
        if json_obj_match:
            json_str = json_obj_match.group(0)
            try:
                json.loads(json_str)
                return json_str
            except json.JSONDecodeError:
                pass

        # Tenta 5: Busca por objeto JSON com chaves específicas
        # Procura por padrões como {"success": ...}
        success_match = re.search(r'\{\s*"success"\s*:\s*(true|false)', stdout)
        if success_match:
            # Tenta extrair o objeto JSON completo
            start = success_match.start()
            # Encontra o final do JSON (fecha chaves correspondente)
            brace_count = 0
            in_string = False
            escape_next = False
            for i in range(start, len(stdout)):
                char = stdout[i]
                if escape_next:
                    escape_next = False
                    continue
                if char == '\\' and in_string:
                    escape_next = True
                    continue
                if char == '"' and not escape_next:
                    in_string = not in_string
                if not in_string:
                    if char == '{':
                        brace_count += 1
                    elif char == '}':
                        brace_count -= 1
                        if brace_count == 0:
                            json_str = stdout[start:i+1]
                            try:
                                json.loads(json_str)
                                return json_str
                            except json.JSONDecodeError:
                                break

        return None

