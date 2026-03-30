# -*- coding: utf-8 -*-
"""
SendProgressCommand.

Comando CQRS para enviar indicador de progresso.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Self

from ...domain.value_objects import ChannelId


class ProgressStatus(str, Enum):
    """Status de progresso."""

    RUNNING = "running"  # Em execução
    SUCCESS = "success"  # Concluído com sucesso
    ERROR = "error"  # Erro
    WARNING = "warning"  # Aviso


@dataclass(frozen=True)
class SendProgressCommand:
    """
    Command para enviar indicador de progresso.

    Usa emoji ou embed para mostrar status visual.
    """

    channel_id: ChannelId
    status: ProgressStatus
    message: str
    percentage: int | None = None  # 0-100, None para indeterminado

    def __post_init__(self) -> None:
        if self.percentage is not None and not (0 <= self.percentage <= 100):
            raise ValueError("Percentual deve estar entre 0 e 100")

    @classmethod
    def running(
        cls,
        channel_id: str,
        message: str,
        percentage: int | None = None,
    ) -> Self:
        """Cria comando de progresso em execução."""
        return cls(
            channel_id=ChannelId(channel_id),
            status=ProgressStatus.RUNNING,
            message=message,
            percentage=percentage,
        )

    @classmethod
    def success(cls, channel_id: str, message: str) -> Self:
        """Cria comando de sucesso."""
        return cls(
            channel_id=ChannelId(channel_id),
            status=ProgressStatus.SUCCESS,
            message=message,
        )

    @classmethod
    def error(cls, channel_id: str, message: str) -> Self:
        """Cria comando de erro."""
        return cls(
            channel_id=ChannelId(channel_id),
            status=ProgressStatus.ERROR,
            message=message,
        )
