# -*- coding: utf-8 -*-
"""
File System Port — Interface para operações de sistema de arquivos.

Port (interface) following Hexagonal Architecture.
"""

from abc import ABC, abstractmethod
from pathlib import Path
from typing import Literal

from skybridge.kernel import Result


class FileSystemPortError(Exception):
    """Base exception for FileSystem errors."""
    pass


class FileNotFoundError(FileSystemPortError):
    """Arquivo não encontrado."""
    pass


class PathNotAllowedError(FileSystemPortError):
    """Path não permitido pelo allowlist."""
    pass


class ReadError(FileSystemPortError):
    """Erro na leitura do arquivo."""
    pass


class FileSystemPort(ABC):
    """
    Interface para operações de arquivo.

    Implementações concretas vivem em infra/contexts/fileops/.
    """

    @abstractmethod
    def read_file(self, path: str) -> Result[str, str]:
        """
        Lê um arquivo.

        Args:
            path: Path relativo ao allowlist root

        Returns:
            Result com conteúdo do arquivo ou erro
        """
        pass

    @abstractmethod
    def file_exists(self, path: str) -> bool:
        """Verifica se um arquivo existe."""
        pass

    @abstractmethod
    def is_allowed(self, path: str) -> bool:
        """Verifica se um path está permitido."""
        pass
