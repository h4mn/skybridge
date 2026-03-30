# -*- coding: utf-8 -*-
"""
ChannelRepository Interface.

Port (interface) para repositório de canais.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Self

from ..entities import Channel
from ..value_objects import ChannelId


class ChannelRepository(ABC):
    """
    Interface para repositório de canais.

    Define contrato para consulta de canais e autorização.
    Implementações ficam em Infrastructure Layer.
    """

    @abstractmethod
    async def get_by_id(self, channel_id: ChannelId) -> Channel | None:
        """
        Busca canal por ID.

        Args:
            channel_id: ID do canal

        Returns:
            Channel se encontrado, None caso contrário
        """
        pass

    @abstractmethod
    async def is_authorized(self, channel_id: ChannelId) -> bool:
        """
        Verifica se canal está autorizado.

        Args:
            channel_id: ID do canal

        Returns:
            True se autorizado
        """
        pass

    @abstractmethod
    async def save(self, channel: Channel) -> None:
        """
        Salva canal (cache).

        Args:
            channel: Canal a salvar
        """
        pass

    @classmethod
    @abstractmethod
    def create(cls) -> Self:
        """Factory method."""
        pass
