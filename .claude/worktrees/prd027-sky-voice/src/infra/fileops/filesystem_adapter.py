# -*- coding: utf-8 -*-
"""
File System Adapter — Implementação concreta do FileSystemPort.

Infra layer implementando interface do domain.
"""

from pathlib import Path
from typing import Optional

from core.fileops.ports.filesystem_port import (
    FileSystemPort,
    FileNotFoundError,
    PathNotAllowedError,
    ReadError,
)
from core.fileops.domain.allowed_path import (
    AllowedPath,
    create_dev_allowed_path,
    create_prod_allowed_path,
)
from kernel import Result


class FileSystemAdapter(FileSystemPort):
    """
    Implementação concreta do FileSystemPort.

    Usa pathlib para operações de arquivo com allowlist.
    """

    def __init__(self, allowed_path: AllowedPath):
        """
        Inicializa adapter com allowlist configurado.

        Args:
            allowed_path: Configuração de allowlist (dev ou production)
        """
        self.allowed_path = allowed_path

    def read_file(self, path: str) -> Result[str, str]:
        """
        Lê um arquivo dentro do allowlist.

        Args:
            path: Path relativo ao allowlist root

        Returns:
            Result com conteúdo do arquivo ou erro
        """
        # Validar allowlist
        if not self.is_allowed(path):
            return Result.err(f"Path not allowed: {path}")

        # Resolver path completo
        full_path = self.allowed_path.resolve(path)

        # Verificar se é arquivo
        if not full_path.is_file():
            return Result.err(f"File not found: {path}")

        # Ler arquivo
        try:
            with open(full_path, "r", encoding="utf-8") as f:
                content = f.read()
            return Result.ok(content)
        except PermissionError:
            return Result.err(f"Permission denied: {path}")
        except Exception as e:
            return Result.err(f"Error reading file: {str(e)}")

    def file_exists(self, path: str) -> bool:
        """Verifica se um arquivo existe e é permitido."""
        if not self.is_allowed(path):
            return False

        full_path = self.allowed_path.resolve(path)
        return full_path.is_file()

    def is_allowed(self, path: str) -> bool:
        """Verifica se um path está dentro do allowlist."""
        return self.allowed_path.is_allowed(path)


def create_filesystem_adapter(mode: str, root: Optional[str] = None) -> FileSystemAdapter:
    """
    Factory para criar FileSystemAdapter configurado.

    Args:
        mode: "dev" ou "production"
        root: Root path (opcional, usa default se não fornecido)

    Returns:
        FileSystemAdapter configurado
    """
    if mode == "dev":
        allowed_path = create_dev_allowed_path(root or Path.cwd())
    elif mode == "production":
        allowed_path = create_prod_allowed_path(root or r"\workspace")
    else:
        raise ValueError(f"Invalid mode: {mode}")

    return FileSystemAdapter(allowed_path)
