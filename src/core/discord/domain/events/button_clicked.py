# -*- coding: utf-8 -*-
"""
ButtonClickedEvent.

Evento de domínio emitido quando usuário clica em botão interativo.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Self

from .base import DomainEvent


@dataclass(frozen=True)
class ButtonClickedEvent(DomainEvent):
    """
    Evento emitido quando usuário clica em botão Discord.

    Usado para fluxos interativos como confirmação de ordens.
    """

    interaction_id: str = ""
    channel_id: str = ""
    message_id: str = ""
    user_id: str = ""
    user_name: str = ""
    button_label: str = ""
    button_custom_id: str = ""
    event_type: str = field(default="ButtonClickedEvent", init=False)

    def to_dict(self) -> dict:
        """Serializa evento."""
        data = super().to_dict()
        data.update(
            {
                "interaction_id": self.interaction_id,
                "channel_id": self.channel_id,
                "message_id": self.message_id,
                "user_id": self.user_id,
                "user_name": self.user_name,
                "button_label": self.button_label,
                "button_custom_id": self.button_custom_id,
            }
        )
        return data

    @classmethod
    def from_dict(cls, data: dict) -> Self:
        """Deserializa evento de dicionário."""
        return cls(
            event_id=data["event_id"],
            occurred_at=datetime.fromisoformat(data["occurred_at"]),
            interaction_id=data["interaction_id"],
            channel_id=data["channel_id"],
            message_id=data["message_id"],
            user_id=data["user_id"],
            user_name=data["user_name"],
            button_label=data["button_label"],
            button_custom_id=data["button_custom_id"],
        )

    @classmethod
    def create(
        cls,
        interaction_id: str,
        channel_id: str,
        message_id: str,
        user_id: str,
        user_name: str,
        button_label: str,
        button_custom_id: str,
    ) -> Self:
        """Factory method."""
        return cls(
            interaction_id=interaction_id,
            channel_id=channel_id,
            message_id=message_id,
            user_id=user_id,
            user_name=user_name,
            button_label=button_label,
            button_custom_id=button_custom_id,
        )
