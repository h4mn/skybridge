# -*- coding: utf-8 -*-
"""
Allowed Path — Caminho permitido para operações de arquivo.

Value object que representa um caminho seguro dentro do allowlist.
"""

from pathlib import Path
from dataclasses import dataclass
from typing import Literal

AllowlistMode = Literal["dev", "production"]


@dataclass(frozen=True)
class AllowedPath:
    """
    Representa um caminho permitido dentro do allowlist.

    O allowlist define quais diretórios podem ser acessados pelo FileOps.
    """

    root: Path
    mode: AllowlistMode

    def is_allowed(self, path: str) -> bool:
        """
        Verifica se um path está dentro do allowlist.

        Args:
            path: Path relativo a ser validado

        Returns:
            True se o path está permitido, False caso contrário
        """
        # Previnir path traversal
        if ".." in path or path.startswith("/") or path.startswith("\\"):
            return False

        # Resolver path completo
        full_path = (self.root / path).resolve()

        # Verificar se está dentro do root
        try:
            full_path.relative_to(self.root.resolve())
            return True
        except ValueError:
            return False

    def resolve(self, path: str) -> Path:
        """
        Resolve um path relativo para o path absoluto.

        Args:
            path: Path relativo

        Returns:
            Path absoluto dentro do allowlist

        Raises:
            ValueError: Se o path não está permitido
        """
        if not self.is_allowed(path):
            raise ValueError(f"Path not allowed: {path}")

        return (self.root / path).resolve()


def create_dev_allowed_path(root: str | Path) -> AllowedPath:
    """Cria allowlist para desenvolvimento (codebase)."""
    return AllowedPath(root=Path(root), mode="dev")


def create_prod_allowed_path(root: str | Path = r"\workspace") -> AllowedPath:
    """Cria allowlist para produção (workspace)."""
    return AllowedPath(root=Path(root), mode="production")
