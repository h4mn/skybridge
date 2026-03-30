# -*- coding: utf-8 -*-
"""
UpdateComponentCommand.

Comando CQRS para atualizar componente existente.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Self

from ...domain.value_objects import ChannelId, MessageId


@dataclass(frozen=True)
class UpdateComponentCommand:
    """
    Command para atualizar componente de mensagem.

    Permite modificar progress, botões ou menu de mensagem existente.
    """

    channel_id: ChannelId
    message_id: MessageId
    new_text: str | None = None
    disable_buttons: bool = False
    new_progress_percentage: int | None = None
    new_progress_status: str | None = None  # running, success, error

    @classmethod
    def disable_buttons(
        cls,
        channel_id: str,
        message_id: str,
    ) -> Self:
        """Cria comando para desabilitar botões."""
        return cls(
            channel_id=ChannelId(channel_id),
            message_id=MessageId(message_id),
            disable_buttons=True,
        )

    @classmethod
    def update_progress(
        cls,
        channel_id: str,
        message_id: str,
        percentage: int | None = None,
        status: str | None = None,
        new_text: str | None = None,
    ) -> Self:
        """Cria comando para atualizar progresso."""
        return cls(
            channel_id=ChannelId(channel_id),
            message_id=MessageId(message_id),
            new_text=new_text,
            new_progress_percentage=percentage,
            new_progress_status=status,
        )
