# -*- coding: utf-8 -*-
"""
UserId Value Object.

Identificador único de usuário Discord.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Self


@dataclass(frozen=True)
class UserId:
    """
    Value Object para ID de usuário Discord.

    Discord usa IDs numéricos como strings (snowflake).
    """

    value: str

    def __post_init__(self) -> None:
        if not self.value:
            raise ValueError("UserId não pode ser vazio")
        if not self.value.isdigit():
            raise ValueError(f"UserId inválido: {self.value} (deve ser numérico)")

    def __str__(self) -> str:
        return self.value

    def __repr__(self) -> str:
        return f"UserId({self.value})"

    @classmethod
    def from_int(cls, value: int) -> Self:
        """Cria UserId a partir de inteiro."""
        return cls(str(value))

    def to_int(self) -> int:
        """Converte para inteiro."""
        return int(self.value)
