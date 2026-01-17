# -*- coding: utf-8 -*-
"""
Worktree Validator - Validação antes de cleanup usando Snapshot.

Este módulo integra o GitExtractor com o sistema de snapshots para
validar worktrees antes da remoção.
"""
from pathlib import Path
from typing import Any

from runtime.observability.snapshot.extractors.git_extractor import (
    GitExtractor,
    GitWorktreeStatus,
    validate_worktree_before_cleanup,
)


class WorktreeValidator:
    """
    Valida worktrees antes da remoção usando snapshots.

    Fluxo:
    1. Snapshot antes de começar o trabalho
    2. Agente trabalha no worktree
    3. Snapshot + validação antes de remover
    4. Remove se seguro, alerta se não
    """

    def __init__(self):
        self.git_extractor = GitExtractor()
        self._snapshots: dict[str, dict[str, Any]] = {}

    def capture_initial_state(self, worktree_path: str) -> dict[str, Any]:
        """
        Captura estado inicial do worktree.

        Args:
            worktree_path: Caminho para o worktree

        Returns:
            Snapshot inicial para comparação posterior
        """
        snapshot = self.git_extractor.capture(target=worktree_path)
        self._snapshots[worktree_path] = snapshot
        return snapshot

    def validate_before_cleanup(
        self,
        worktree_path: str,
        require_clean: bool = True,
    ) -> tuple[bool, str, GitWorktreeStatus]:
        """
        Valida se o worktree pode ser removido com segurança.

        Args:
            worktree_path: Caminho para o worktree
            require_clean: Se True, requer worktree 100% limpo.
                          Se False, permite untracked files.

        Returns:
            tuple[bool, str, GitWorktreeStatus]: (pode_remover, mensagem, status)

        Example:
            >>> validator = WorktreeValidator()
            >>> can_remove, msg, status = validator.validate_before_cleanup(
            ...     "../skybridge-fix-225",
            ...     require_clean=False  # Permite artefatos de build
            ... )
            >>> if can_remove:
            ...     git worktree remove ../skybridge-fix-225
        """
        can_remove, message, status = self.git_extractor.validate_worktree(worktree_path)

        if require_clean:
            # Modo estrito: requer 100% limpo
            return can_remove, message, status
        else:
            # Modo relaxado: permite untracked (artefatos de build)
            if status.has_staged or status.has_unstaged or status.merge_conflicts:
                return False, message, status
            return True, f"Worktree pronto para cleanup (untracked OK)", status

    def get_worktree_summary(self, status: GitWorktreeStatus) -> dict[str, Any]:
        """
        Gera resumo do status do worktree para logging/alertas.

        Args:
            status: Status do worktree

        Returns:
            Dict com resumo formatado
        """
        return {
            "branch": status.branch,
            "clean": status.is_clean,
            "staged": len(status.staged_files),
            "unstaged": len(status.unstaged_files),
            "untracked": len(status.untracked_files),
            "conflicts": len(status.merge_conflicts),
            "can_remove": status.can_safely_remove()[0],
            "files": {
                "staged": status.staged_files[:5],  # Primeiros 5
                "unstaged": status.unstaged_files[:5],
                "conflicts": status.merge_conflicts,
            },
        }


# Função de conveniência para uso em skills/agents
def safe_worktree_cleanup(
    worktree_path: str,
    require_clean: bool = False,
    dry_run: bool = False,
) -> dict[str, Any]:
    """
    Executa validação e (opcionalmente) cleanup do worktree.

    Args:
        worktree_path: Caminho para o worktree
        require_clean: Se True, requer 100% limpo. Se False, permite untracked.
        dry_run: Se True, apenas valida sem remover.

    Returns:
        Dict com resultado da validação

    Example:
        >>> # No skill /resolve-issue
        >>> result = safe_worktree_cleanup("../skybridge-fix-225", dry_run=True)
        >>> if result["can_remove"]:
        ...     # Confirmar com usuário antes de remover
        ...     safe_worktree_cleanup("../skybridge-fix-225", dry_run=False)
    """
    validator = WorktreeValidator()
    can_remove, message, status = validator.validate_before_cleanup(
        worktree_path,
        require_clean=require_clean,
    )

    summary = validator.get_worktree_summary(status)

    result = {
        "worktree": worktree_path,
        "can_remove": can_remove,
        "message": message,
        "status": summary,
    }

    if can_remove and not dry_run:
        import subprocess

        try:
            subprocess.run(
                ["git", "worktree", "remove", worktree_path],
                check=True,
                capture_output=True,
            )
            result["removed"] = True
            result["cleanup_message"] = f"Worktree {worktree_path} removido com sucesso"
        except subprocess.CalledProcessError as e:
            result["removed"] = False
            result["error"] = str(e)
            result["cleanup_message"] = f"Erro ao remover worktree: {e}"
    elif dry_run:
        result["dry_run"] = True
        result["cleanup_message"] = f"DRY RUN: Worktree {'pode' if can_remove else 'NÃO pode'} ser removido"

    return result
