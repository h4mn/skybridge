# -*- coding: utf-8 -*-
"""
Git Service - Abstração para operações git.

PRD018 Fase 3: Serviço que abstrai operações git comuns:
- git add (stage arquivos)
- git commit (cria commit)
- git push (envia para remoto)
- git status (verifica estado)

Este serviço é usado após os guardrails passarem
e antes/depois de criar o PR.
"""
from __future__ import annotations

import subprocess
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from kernel.contracts.result import Result

from kernel.contracts.result import Result


@dataclass
class CommitResult:
    """
    Resultado de uma operação de commit.

    Attributes:
        success: Se o commit foi criado com sucesso
        commit_hash: Hash do commit criado
        commit_message: Mensagem do commit
        files_changed: Quantidade de arquivos alterados
        insertions: Quantidade de linhas inseridas
        deletions: Quantidade de linhas deletadas
    """
    success: bool = False
    commit_hash: str = ""
    commit_message: str = ""
    files_changed: int = 0
    insertions: int = 0
    deletions: int = 0


@dataclass
class PushResult:
    """
    Resultado de uma operação de push.

    Attributes:
        success: Se o push foi enviado com sucesso
        remote_url: URL do branch remoto
        branch_name: Nome do branch
        commit_hash: Hash do commit pushed
    """
    success: bool = False
    remote_url: str = ""
    branch_name: str = ""
    commit_hash: str = ""


class GitService:
    """
    Serviço para operações git.

    Responsabilidades:
    - Executar comandos git de forma segura
    - Capturar output e erros
    - Retornar resultados estruturados

    Attributes:
        timeout: Timeout padrão para comandos git (segundos)
    """

    def __init__(self, timeout: int = 60):
        """
        Inicializa serviço.

        Args:
            timeout: Timeout padrão para comandos (segundos)
        """
        self.timeout = timeout

    async def add_all(self, worktree_path: str) -> Result[None, str]:
        """
        Executa git add para staged todos os arquivos.

        Args:
            worktree_path: Caminho para o repositório/worktree

        Returns:
            Result ok ou erro
        """
        try:
            subprocess.run(
                ["git", "add", "."],
                cwd=worktree_path,
                check=True,
                capture_output=True,
                encoding='utf-8',
                timeout=self.timeout,
            )
            return Result.ok(None)

        except subprocess.CalledProcessError as e:
            return Result.err(f"git add falhou: {e.stderr}")
        except subprocess.TimeoutExpired:
            return Result.err(f"git add timeout após {self.timeout}s")
        except FileNotFoundError:
            return Result.err("Git não encontrado")

    async def commit(
        self,
        worktree_path: str,
        message: str,
    ) -> Result[CommitResult, str]:
        """
        Cria commit com mensagem fornecida.

        Args:
            worktree_path: Caminho para o repositório/worktree
            message: Mensagem do commit

        Returns:
            Result com CommitResult ou erro

        Note:
            Usa git commit com flag -m para mensagem.
            Captura o hash do commit criado.
        """
        try:
            # Executa commit
            proc = subprocess.run(
                ["git", "commit", "-m", message],
                cwd=worktree_path,
                check=True,
                capture_output=True,
                encoding='utf-8',
                timeout=self.timeout,
            )

            # Extrai hash do commit criado
            commit_hash = await self._get_last_commit_hash(worktree_path)
            if commit_hash.is_err:
                return Result.err(f"Commit criado mas erro ao obter hash: {commit_hash.error}")

            # Extrai estatísticas do commit
            stats = await self._get_commit_stats(worktree_path, commit_hash.value)

            return Result.ok(CommitResult(
                success=True,
                commit_hash=commit_hash.value,
                commit_message=message,
                files_changed=stats.get("files_changed", 0),
                insertions=stats.get("insertions", 0),
                deletions=stats.get("deletions", 0),
            ))

        except subprocess.CalledProcessError as e:
            # Verifica se é "nothing to commit"
            stderr_text = e.stderr.lower() if e.stderr else ""
            if "nothing to commit" in stderr_text:
                return Result.err("Nada para commitar (nenhuma mudança staged)")
            return Result.err(f"git commit falhou: {e.stderr or 'stderr=None'}")
        except subprocess.TimeoutExpired:
            return Result.err(f"git commit timeout após {self.timeout}s")
        except FileNotFoundError:
            return Result.err("Git não encontrado")

    async def push(
        self,
        worktree_path: str,
        remote: str = "origin",
        branch_name: str | None = None,
        upstream: bool = True,
    ) -> Result[PushResult, str]:
        """
        Envia commits para o remoto.

        Args:
            worktree_path: Caminho para o repositório/worktree
            remote: Nome do remoto (default: origin)
            branch_name: Nome do branch (default: branch atual)
            upstream: Se deve configurar upstream (-u flag)

        Returns:
            Result com PushResult ou erro

        Note:
            Usa -u para configurar upstream na primeira vez.
        """
        try:
            # Se não informou branch, pega o atual
            if branch_name is None:
                current_branch = await self._get_current_branch(worktree_path)
                if current_branch.is_err:
                    return Result.err(f"Erro ao obter branch atual: {current_branch.error}")
                branch_name = current_branch.value

            # Constrói comando
            cmd = ["git", "push", remote]
            if upstream:
                cmd.append("-u")
            cmd.append(branch_name)

            # Executa push
            subprocess.run(
                cmd,
                cwd=worktree_path,
                check=True,
                capture_output=True,
                encoding='utf-8',
                timeout=self.timeout * 2,  # Push pode demorar mais
            )

            # Extrai hash do último commit
            commit_hash = await self._get_last_commit_hash(worktree_path)
            if commit_hash.is_err:
                commit_hash = Result.ok("")  # Não é crítico

            # Constrói URL remota
            remote_url = await self._get_remote_url(worktree_path, remote)
            if remote_url.is_err:
                remote_url = Result.ok("")  # Não é crítico

            return Result.ok(PushResult(
                success=True,
                remote_url=f"{remote_url.value}/{branch_name}",
                branch_name=branch_name,
                commit_hash=commit_hash.value,
            ))

        except subprocess.CalledProcessError as e:
            return Result.err(f"git push falhou: {e.stderr}")
        except subprocess.TimeoutExpired:
            return Result.err(f"git push timeout após {self.timeout * 2}s")
        except FileNotFoundError:
            return Result.err("Git não encontrado")

    async def get_status(self, worktree_path: str) -> Result[dict, str]:
        """
        Obtém status do repositório.

        Args:
            worktree_path: Caminho para o repositório/worktree

        Returns:
            Result com dict de status ou erro
        """
        try:
            output = subprocess.check_output(
                ["git", "status", "--porcelain"],
                cwd=worktree_path,
                encoding='utf-8',
                stderr=subprocess.DEVNULL,
                timeout=self.timeout,
            )

            lines = output.strip().splitlines()

            # Parse das linhas (XY filename)
            staged = [l for l in lines if l and l[0] in "MADRC"]
            unstaged = [l for l in lines if len(l) > 1 and l[1] in "MADRC"]
            untracked = [l for l in lines if l.startswith("??")]

            return Result.ok({
                "clean": len(lines) == 0,
                "staged": len(staged),
                "unstaged": len(unstaged),
                "untracked": len(untracked),
                "total": len(lines),
            })

        except subprocess.CalledProcessError as e:
            return Result.err(f"git status falhou: {e}")
        except FileNotFoundError:
            return Result.err("Git não encontrado")

    async def get_current_branch(self, worktree_path: str) -> Result[str, str]:
        """
        Obtém nome do branch atual.

        Args:
            worktree_path: Caminho para o repositório/worktree

        Returns:
            Result com nome do branch ou erro
        """
        result = await self._get_current_branch(worktree_path)
        return result

    # Métodos privados auxiliares

    async def _get_last_commit_hash(self, worktree_path: str) -> Result[str, str]:
        """Obtém hash do último commit."""
        try:
            output = subprocess.check_output(
                ["git", "rev-parse", "HEAD"],
                cwd=worktree_path,
                encoding='utf-8',
                stderr=subprocess.DEVNULL,
                timeout=self.timeout,
            )
            return Result.ok(output.strip())

        except (subprocess.CalledProcessError, FileNotFoundError):
            return Result.err("Erro ao obter hash do commit")

    async def _get_current_branch(self, worktree_path: str) -> Result[str, str]:
        """Obtém nome do branch atual."""
        try:
            output = subprocess.check_output(
                ["git", "rev-parse", "--abbrev-ref", "HEAD"],
                cwd=worktree_path,
                encoding='utf-8',
                stderr=subprocess.DEVNULL,
                timeout=self.timeout,
            )
            return Result.ok(output.strip())

        except (subprocess.CalledProcessError, FileNotFoundError):
            return Result.err("Erro ao obter branch atual")

    async def _get_commit_stats(self, worktree_path: str, commit_hash: str) -> dict:
        """
        Extrai estatísticas do commit (linhas inseridas/deletadas).

        Args:
            worktree_path: Caminho para o repositório
            commit_hash: Hash do commit

        Returns:
            Dict com stats
        """
        try:
            output = subprocess.check_output(
                ["git", "show", "--stat", "--format=", commit_hash],
                cwd=worktree_path,
                encoding='utf-8',
                stderr=subprocess.DEVNULL,
                timeout=self.timeout,
            )

            # Parse output: " 1 file changed, 10 insertions(+), 2 deletions(-)"
            stats = {
                "files_changed": 0,
                "insertions": 0,
                "deletions": 0,
            }

            import re
            files_match = re.search(r'(\d+) file', output)
            if files_match:
                stats["files_changed"] = int(files_match.group(1))

            insertions_match = re.search(r'(\d+) insertion', output)
            if insertions_match:
                stats["insertions"] = int(insertions_match.group(1))

            deletions_match = re.search(r'(\d+) deletion', output)
            if deletions_match:
                stats["deletions"] = int(deletions_match.group(1))

            return stats

        except (subprocess.CalledProcessError, FileNotFoundError):
            return {"files_changed": 0, "insertions": 0, "deletions": 0}

    async def _get_remote_url(self, worktree_path: str, remote: str) -> Result[str, str]:
        """Obtém URL do remoto."""
        try:
            output = subprocess.check_output(
                ["git", "remote", "get-url", remote],
                cwd=worktree_path,
                encoding='utf-8',
                stderr=subprocess.DEVNULL,
                timeout=self.timeout,
            )
            return Result.ok(output.strip())

        except (subprocess.CalledProcessError, FileNotFoundError):
            return Result.err(f"Erro ao obter URL do remoto {remote}")
