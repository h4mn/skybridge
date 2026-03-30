# -*- coding: utf-8 -*-
"""
SendButtonsCommand.

Comando CQRS para enviar mensagem com botões interativos.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Self

from ...domain.value_objects import ChannelId


@dataclass
class ButtonData:
    """Dados de botão Discord."""

    id: str  # custom_id
    label: str
    style: str = "primary"  # primary, secondary, success, danger, link
    emoji: str | None = None
    disabled: bool = False


@dataclass(frozen=True)
class SendButtonsCommand:
    """
    Command para enviar mensagem com botões.

    Máximo 5 botões por mensagem (limite Discord).
    """

    channel_id: ChannelId
    text: str
    buttons: list[ButtonData] = field(default_factory=list)

    def __post_init__(self) -> None:
        if len(self.buttons) > 5:
            raise ValueError("Discord permite no máximo 5 botões por linha")

    @classmethod
    def create(
        cls,
        channel_id: str,
        text: str,
        buttons: list[dict],
    ) -> Self:
        """
        Factory method.

        Args:
            channel_id: ID do canal
            text: Texto da mensagem
            buttons: Lista de botões [{id, label, style, emoji}]

        Returns:
            Nova instância do comando
        """
        button_data = []
        for b in buttons:
            button_data.append(
                ButtonData(
                    id=b["id"],
                    label=b["label"],
                    style=b.get("style", "primary"),
                    emoji=b.get("emoji"),
                    disabled=b.get("disabled", False),
                )
            )

        return cls(
            channel_id=ChannelId(channel_id),
            text=text,
            buttons=button_data,
        )
