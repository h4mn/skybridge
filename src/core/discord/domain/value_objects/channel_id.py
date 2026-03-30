# -*- coding: utf-8 -*-
"""
ChannelId Value Object.

Identificador único de canal Discord.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Self


@dataclass(frozen=True)
class ChannelId:
    """
    Value Object para ID de canal Discord.

    Discord usa IDs numéricos como strings (snowflake).
    """

    value: str

    def __post_init__(self) -> None:
        if not self.value:
            raise ValueError("ChannelId não pode ser vazio")
        if not self.value.isdigit():
            raise ValueError(f"ChannelId inválido: {self.value} (deve ser numérico)")

    def __str__(self) -> str:
        return self.value

    def __repr__(self) -> str:
        return f"ChannelId({self.value})"

    @classmethod
    def from_int(cls, value: int) -> Self:
        """Cria ChannelId a partir de inteiro."""
        return cls(str(value))

    def to_int(self) -> int:
        """Converte para inteiro."""
        return int(self.value)
