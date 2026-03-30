# -*- coding: utf-8 -*-
"""
SendMenuCommand.

Comando CQRS para enviar menu dropdown (Select Menu).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Self

from ...domain.value_objects import ChannelId


@dataclass
class MenuOption:
    """Opção de menu."""

    value: str  # Valor retornado na seleção
    label: str  # Texto visível
    description: str | None = None
    emoji: str | None = None
    default: bool = False


@dataclass(frozen=True)
class SendMenuCommand:
    """
    Command para enviar menu dropdown.

    Máximo 25 opções por menu (limite Discord).
    """

    channel_id: ChannelId
    text: str
    options: list[MenuOption] = field(default_factory=list)
    placeholder: str = "Selecione uma opção..."
    multi_select: bool = False
    min_values: int = 1
    max_values: int = 1

    def __post_init__(self) -> None:
        if len(self.options) > 25:
            raise ValueError("Discord permite no máximo 25 opções por menu")
        if self.max_values < self.min_values:
            raise ValueError("max_values deve ser >= min_values")
        if self.max_values > len(self.options):
            raise ValueError("max_values não pode exceder número de opções")

    @classmethod
    def create(
        cls,
        channel_id: str,
        text: str,
        options: list[dict],
        placeholder: str = "Selecione uma opção...",
        multi_select: bool = False,
    ) -> Self:
        """
        Factory method.

        Args:
            channel_id: ID do canal
            text: Texto da mensagem
            options: Lista de opções [{value, label, description, emoji}]
            placeholder: Texto placeholder
            multi_select: Se permite seleção múltipla

        Returns:
            Nova instância do comando
        """
        menu_options = []
        for o in options:
            menu_options.append(
                MenuOption(
                    value=o["value"],
                    label=o["label"],
                    description=o.get("description"),
                    emoji=o.get("emoji"),
                    default=o.get("default", False),
                )
            )

        max_vals = len(menu_options) if multi_select else 1

        return cls(
            channel_id=ChannelId(channel_id),
            text=text,
            options=menu_options,
            placeholder=placeholder,
            multi_select=multi_select,
            max_values=max_vals,
        )
