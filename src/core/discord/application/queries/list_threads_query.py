# -*- coding: utf-8 -*-
"""
ListThreadsQuery.

Query CQRS para listar threads de um canal.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Self

from ...domain.value_objects import ChannelId


@dataclass(frozen=True)
class ListThreadsQuery:
    """
    Query para listar threads de um canal.

    DTO para entrada de query (sem lógica).
    """

    channel_id: ChannelId
    include_archived: bool = False

    @classmethod
    def create(
        cls,
        channel_id: str,
        include_archived: bool = False,
    ) -> Self:
        """
        Factory method.

        Args:
            channel_id: ID do canal
            include_archived: Incluir threads arquivadas

        Returns:
            Nova instância da query
        """
        return cls(
            channel_id=ChannelId(channel_id),
            include_archived=include_archived,
        )
