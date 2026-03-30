# -*- coding: utf-8 -*-
"""
FetchMessagesQuery.

Query CQRS para buscar histórico de mensagens.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Self

from ...domain.value_objects import ChannelId


@dataclass(frozen=True)
class FetchMessagesQuery:
    """
    Query para buscar histórico de mensagens de um canal.

    DTO para entrada de query (sem lógica).
    """

    channel_id: ChannelId
    limit: int = 20  # Padrão Discord

    def __post_init__(self) -> None:
        """Valida limit."""
        if self.limit < 1:
            raise ValueError("Limit deve ser maior que 0")
        if self.limit > 100:
            raise ValueError("Discord limita a 100 mensagens por requisição")

    @classmethod
    def create(
        cls,
        channel_id: str,
        limit: int = 20,
    ) -> Self:
        """
        Factory method.

        Args:
            channel_id: ID do canal
            limit: Máximo de mensagens (1-100)

        Returns:
            Nova instância da query
        """
        return cls(
            channel_id=ChannelId(channel_id),
            limit=limit,
        )
