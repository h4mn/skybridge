# -*- coding: utf-8 -*-
"""
MessageId Value Object.

Identificador único de mensagem Discord.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Self


@dataclass(frozen=True)
class MessageId:
    """
    Value Object para ID de mensagem Discord.

    Discord usa IDs numéricos como strings (snowflake).
    """

    value: str

    def __post_init__(self) -> None:
        if not self.value:
            raise ValueError("MessageId não pode ser vazio")
        if not self.value.isdigit():
            raise ValueError(f"MessageId inválido: {self.value} (deve ser numérico)")

    def __str__(self) -> str:
        return self.value

    def __repr__(self) -> str:
        return f"MessageId({self.value})"

    @classmethod
    def from_int(cls, value: int) -> Self:
        """Cria MessageId a partir de inteiro."""
        return cls(str(value))

    def to_int(self) -> int:
        """Converte para inteiro."""
        return int(self.value)
