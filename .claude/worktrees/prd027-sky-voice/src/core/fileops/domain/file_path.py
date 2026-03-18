# -*- coding: utf-8 -*-
"""
File Path — Value object para caminhos de arquivo validados.
"""

from pathlib import Path
from dataclasses import dataclass


@dataclass(frozen=True)
class FilePath:
    """
    Value object representando um caminho de arquivo validado.

    Encapsula a lógica de validação de paths.
    """

    value: str

    def __post_init__(self):
        """Valida o path após criação."""
        if not self.value or not self.value.strip():
            raise ValueError("Path cannot be empty")

        # Path não pode ser absoluto
        if Path(self.value).is_absolute():
            raise ValueError(f"Path must be relative: {self.value}")

    def __str__(self) -> str:
        return self.value

    def relative_to(self, base: Path) -> Path:
        """Retorna o path relativo a uma base."""
        return Path(self.value)
