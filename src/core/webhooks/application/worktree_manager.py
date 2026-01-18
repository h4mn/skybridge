# -*- coding: utf-8 -*-
"""
Worktree Manager Application Service.

Gerencia ciclo de vida de worktrees git para processamento de webhooks.
"""
from __future__ import annotations

import subprocess
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from core.webhooks.domain import WebhookJob

from core.webhooks.domain import (
    generate_branch_name,
    generate_worktree_name,
)
from kernel.contracts.result import Result


class WorktreeManager:
    """
    Service para gerenciar worktrees git.

    Responsabilidades:
    - Criar worktrees isolados para cada job
    - Gerar nomes únicos e consistentes
    - Remover worktrees após processamento

    Worktrees garantem isolamento completo: cada job trabalha
    em seu próprio diretório sem afetar o repositório principal.

    Attributes:
        base_path: Caminho base onde worktrees são criados
        base_branch: Branch base para criar worktrees (configurável)
    """

    def __init__(self, base_path: str | Path, base_branch: str = "dev"):
        """
        Inicializa manager.

        Args:
            base_path: Caminho base para worktrees (ex: "../skybridge-worktrees")
            base_branch: Branch base para criar worktrees (padrão: "dev")
        """
        self.base_path = Path(base_path)
        self.base_branch = base_branch

    def create_worktree(self, job: "WebhookJob") -> Result[str, str]:
        """
        Cria worktree isolado para o job.

        Args:
            job: Job de webhook

        Returns:
            Result com caminho do worktree criado ou erro

        Example:
            >>> manager = WorktreeManager("../skybridge-worktrees")
            >>> result = manager.create_worktree(job)
            >>> if result.is_ok:
            ...     worktree_path = result.value
            ...     # Agente trabalha no worktree...
        """
        worktree_name = generate_worktree_name(job)
        branch_name = generate_branch_name(job)
        worktree_path = self.base_path / worktree_name

        try:
            # Cria diretório base se não existe
            self.base_path.mkdir(parents=True, exist_ok=True)

            # Executa git worktree add com branch base configurada
            # Isso garante que worktrees sejam criadas a partir da branch correta
            result = subprocess.run(
                [
                    "git",
                    "worktree",
                    "add",
                    str(worktree_path),
                    "-b",
                    branch_name,
                    self.base_branch,  # Branch base configurada (ex: "dev")
                ],
                capture_output=True,
                text=True,
                check=True,
                timeout=30,
            )

            # Atualiza job com caminho e branch
            job.worktree_path = str(worktree_path)
            job.branch_name = branch_name

            return Result.ok(str(worktree_path))

        except subprocess.CalledProcessError as e:
            return Result.err(
                f"Falha ao criar worktree: {e.stderr}\nReturn code: {e.returncode}"
            )
        except subprocess.TimeoutExpired:
            return Result.err("Timeout ao criar worktree (>30s)")
        except Exception as e:
            return Result.err(f"Erro inesperado ao criar worktree: {str(e)}")

    def remove_worktree(self, worktree_path: str) -> Result[None, str]:
        """
        Remove worktree após processamento.

        Args:
            worktree_path: Caminho do worktree a remover

        Returns:
            Result indicando sucesso ou erro

        Note:
            Antes de chamar este método, use safe_worktree_cleanup()
            para validar que o worktree pode ser removido com segurança.
        """
        try:
            result = subprocess.run(
                ["git", "worktree", "remove", worktree_path],
                capture_output=True,
                text=True,
                check=True,
                timeout=30,
            )

            return Result.ok(None)

        except subprocess.CalledProcessError as e:
            return Result.err(
                f"Falha ao remover worktree: {e.stderr}\nReturn code: {e.returncode}"
            )
        except subprocess.TimeoutExpired:
            return Result.err("Timeout ao remover worktree (>30s)")
        except Exception as e:
            return Result.err(f"Erro inesperado ao remover worktree: {str(e)}")

    def list_worktrees(self) -> list[dict[str, str]]:
        """
        Lista todos os worktrees existentes.

        Returns:
            Lista de worktrees com informações

        Useful para:
            - Debug de worktrees órfãos
            - Monitoramento de recursos
            - Limpeza manual
        """
        try:
            result = subprocess.run(
                ["git", "worktree", "list", "--porcelain"],
                capture_output=True,
                text=True,
                check=True,
            )

            worktrees = []
            current = {}

            for line in result.stdout.split("\n"):
                if not line:
                    if current:
                        worktrees.append(current)
                        current = {}
                    continue

                if line.startswith("worktree "):
                    current["path"] = line[9:]
                elif line.startswith("HEAD "):
                    current["head"] = line[5:]
                elif line.startswith("branch "):
                    current["branch"] = line[7:]
                elif line.startswith("detached"):
                    current["detached"] = True

            if current:
                worktrees.append(current)

            return worktrees

        except subprocess.CalledProcessError:
            return []
