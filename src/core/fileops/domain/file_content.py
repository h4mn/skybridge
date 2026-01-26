# -*- coding: utf-8 -*-
"""
File Content — Value object para conteúdo de arquivo.
"""

from dataclasses import dataclass


@dataclass
class FileContent:
    """
    Value object representando conteúdo de arquivo.

    Encapsula o conteúdo bruto e metadados.
    """

    content: str
    encoding: str = "utf-8"

    @property
    def size(self) -> int:
        """Tamanho do conteúdo em bytes."""
        return len(self.content.encode(self.encoding))

    def __str__(self) -> str:
        return self.content

    def __len__(self) -> int:
        return self.size
