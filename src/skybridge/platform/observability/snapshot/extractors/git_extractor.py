# -*- coding: utf-8 -*-
"""
Git Worktree Extractor - Validação de estado para worktree cleanup.

Este extractor captura informações específicas do git para validar
se um worktree está pronto para ser removido (sem mudanças pendentes).
"""
from __future__ import annotations

from datetime import datetime
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Any
import subprocess

from skybridge.platform.observability.snapshot.capture import generate_snapshot_id
from skybridge.platform.observability.snapshot.extractors.base import StateExtractor
from skybridge.platform.observability.snapshot.models import (
    Snapshot,
    SnapshotMetadata,
    SnapshotSubject,
)


class GitFileStatus(Enum):
    """Status de arquivos no git."""
    UNMODIFIED = " "
    MODIFIED = "M"
    ADDED = "A"
    DELETED = "D"
    RENAMED = "R"
    COPIED = "C"
    UNTRACKED = "?"
    IGNORED = "!"


@dataclass
class GitWorktreeStatus:
    """Status completo do worktree git."""
    is_clean: bool
    is_dirty: bool
    has_staged: bool
    has_unstaged: bool
    has_untracked: bool
    branch: str | None
    head_hash: str | None
    staged_files: list[str]
    unstaged_files: list[str]
    untracked_files: list[str]
    merge_conflicts: list[str]

    def can_safely_remove(self) -> tuple[bool, str]:
        """
        Verifica se o worktree pode ser removido com segurança.

        Returns:
            tuple[bool, str]: (pode_remover, razão)
        """
        if self.merge_conflicts:
            return False, f"Worktree tem {len(self.merge_conflicts)} conflitos não resolvidos"

        if self.has_staged:
            return False, f"Worktree tem {len(self.staged_files)} arquivos staged não commitados"

        if self.has_unstaged:
            return False, f"Worktree tem {len(self.unstaged_files)} arquivos modificados não commitados"

        # Untracked files são OK (geralmente são artefatos de build)
        if self.has_untracked:
            return True, f"Worktree limpo (com {len(self.untracked_files)} arquivos untracked)"

        return True, "Worktree completamente limpo"

    def to_dict(self) -> dict[str, Any]:
        """Converte para dict para serialização."""
        return {
            "is_clean": self.is_clean,
            "is_dirty": self.is_dirty,
            "has_staged": self.has_staged,
            "has_unstaged": self.has_unstaged,
            "has_untracked": self.has_untracked,
            "branch": self.branch,
            "head_hash": self.head_hash,
            "staged_files": self.staged_files,
            "unstaged_files": self.unstaged_files,
            "untracked_files": self.untracked_files,
            "merge_conflicts": self.merge_conflicts,
        }


class GitExtractor(StateExtractor):
    """Extractor para estado de worktree git."""

    @property
    def subject(self) -> SnapshotSubject:
        # TODO: Adicionar GIT ao enum SnapshotSubject
        return SnapshotSubject.FILEOPS  # Temporário

    def capture(
        self,
        target: str,
        **options,
    ) -> Snapshot:
        """
        Captura estado completo do worktree git.

        Args:
            target: Caminho para o worktree

        Returns:
            Snapshot com status do git
        """
        root_path = Path(target).resolve()
        if not root_path.exists():
            raise ValueError(f"Caminho não encontrado: {root_path}")

        status = self._get_git_status(root_path)

        # Estrutura simplificada para o snapshot
        structure = {
            "name": "git_status",
            "type": "git",
            "status": status.to_dict(),
        }

        git_hash, git_branch = self._get_git_info(root_path)
        snapshot_id = generate_snapshot_id(self.subject, f"git:{root_path}")
        timestamp = datetime.utcnow()

        # Stats baseadas no status
        stats = {
            "total_files": len(status.staged_files) + len(status.unstaged_files) + len(status.untracked_files),
            "staged": len(status.staged_files),
            "unstaged": len(status.unstaged_files),
            "untracked": len(status.untracked_files),
            "conflicts": len(status.merge_conflicts),
            "is_clean": status.is_clean,
            "can_remove": status.can_safely_remove()[0],
        }

        metadata = SnapshotMetadata(
            snapshot_id=snapshot_id,
            timestamp=timestamp,
            subject=self.subject,
            target=str(root_path),
            git_hash=git_hash,
            git_branch=git_branch,
            tags={"git_worktree": "true"},
        )

        return Snapshot(
            metadata=metadata,
            stats=stats,
            structure=structure,
            files=[],  # Git não tem "files" no sentido tradicional
        )

    def validate_worktree(self, target: str) -> tuple[bool, str, GitWorktreeStatus]:
        """
        Valida se o worktree pode ser removido com segurança.

        Args:
            target: Caminho para o worktree

        Returns:
            tuple[bool, str, GitWorktreeStatus]: (pode_remover, mensagem, status_completo)
        """
        root_path = Path(target).resolve()
        status = self._get_git_status(root_path)
        can_remove, message = status.can_safely_remove()
        return can_remove, message, status

    def _get_git_status(self, path: Path) -> GitWorktreeStatus:
        """Obtém status completo do git."""
        try:
            # git status --porcelain: formato parseável
            result = subprocess.run(
                ["git", "status", "--porcelain"],
                cwd=path,
                capture_output=True,
                text=True,
                timeout=5,
            )

            if result.returncode != 0:
                # Não é um repo git ou erro
                return GitWorktreeStatus(
                    is_clean=False,
                    is_dirty=False,
                    has_staged=False,
                    has_unstaged=False,
                    has_untracked=False,
                    branch=None,
                    head_hash=None,
                    staged_files=[],
                    unstaged_files=[],
                    untracked_files=[],
                    merge_conflicts=[],
                )

            staged_files: list[str] = []
            unstaged_files: list[str] = []
            untracked_files: list[str] = []
            merge_conflicts: list[str] = []

            for line in result.stdout.strip().split("\n"):
                if not line:
                    continue

                # Formato: XY filename
                # X = staged status, Y = unstaged status
                x_status = line[0] if len(line) > 0 else " "
                y_status = line[1] if len(line) > 1 else " "
                filename = line[3:] if len(line) > 3 else line

                # Conflicts detectados por ambos os status terem "U"
                if x_status == "U" and y_status == "U":
                    merge_conflicts.append(filename)
                    continue

                # Staged changes (X não é espaço ou "?")
                if x_status not in (" ", "?"):
                    staged_files.append(filename)

                # Unstaged changes (Y é "M")
                if y_status == "M":
                    unstaged_files.append(filename)

                # Untracked (Y é "?")
                if y_status == "?":
                    untracked_files.append(filename)

            # Detect merge conflicts via ls-files
            conflict_result = subprocess.run(
                ["git", "diff", "--name-only", "--diff-filter=U"],
                cwd=path,
                capture_output=True,
                text=True,
                timeout=5,
            )
            if conflict_result.returncode == 0:
                for line in conflict_result.stdout.strip().split("\n"):
                    if line and line not in merge_conflicts:
                        merge_conflicts.append(line)

            is_clean = not (staged_files or unstaged_files)
            is_dirty = not is_clean
            has_staged = bool(staged_files)
            has_unstaged = bool(unstaged_files)
            has_untracked = bool(untracked_files)

            branch, head_hash = self._get_git_info(path)

            return GitWorktreeStatus(
                is_clean=is_clean,
                is_dirty=is_dirty,
                has_staged=has_staged,
                has_unstaged=has_unstaged,
                has_untracked=has_untracked,
                branch=branch,
                head_hash=head_hash,
                staged_files=staged_files,
                unstaged_files=unstaged_files,
                untracked_files=untracked_files,
                merge_conflicts=merge_conflicts,
            )

        except (subprocess.TimeoutExpired, FileNotFoundError, Exception) as e:
            # Erro ao executar git
            return GitWorktreeStatus(
                is_clean=False,
                is_dirty=False,
                has_staged=False,
                has_unstaged=False,
                has_untracked=False,
                branch=None,
                head_hash=None,
                staged_files=[],
                unstaged_files=[],
                untracked_files=[],
                merge_conflicts=[],
            )

    def _get_git_info(self, path: Path) -> tuple[str | None, str | None]:
        """Obtém branch e hash atual."""
        try:
            result = subprocess.run(
                ["git", "rev-parse", "HEAD"],
                cwd=path,
                capture_output=True,
                text=True,
                timeout=5,
            )
            head_hash = result.stdout.strip() if result.returncode == 0 else None

            result = subprocess.run(
                ["git", "rev-parse", "--abbrev-ref", "HEAD"],
                cwd=path,
                capture_output=True,
                text=True,
                timeout=5,
            )
            branch = result.stdout.strip() if result.returncode == 0 else None

            return branch, head_hash
        except (subprocess.TimeoutExpired, FileNotFoundError, Exception):
            return None, None


# Função de conveniência para validação rápida
def validate_worktree_before_cleanup(path: str) -> tuple[bool, str]:
    """
    Valida worktree antes de remover.

    Args:
        path: Caminho para o worktree

    Returns:
        tuple[bool, str]: (pode_remover, mensagem)

    Example:
        >>> can_remove, msg = validate_worktree_before_cleanup("../skybridge-fix-225")
        >>> if can_remove:
        ...     git worktree remove ../skybridge-fix-225
        ... else:
        ...     print(f"Cannot remove: {msg}")
    """
    extractor = GitExtractor()
    can_remove, message, status = extractor.validate_worktree(path)
    return can_remove, message
