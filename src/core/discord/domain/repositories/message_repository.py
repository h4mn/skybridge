# -*- coding: utf-8 -*-
"""
MessageRepository Interface.

Port (interface) para repositório de mensagens.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Self

from ..entities import Message
from ..value_objects import ChannelId, MessageId


class MessageRepository(ABC):
    """
    Interface para repositório de mensagens.

    Define contrato para persistência de mensagens.
    Implementações ficam em Infrastructure Layer.
    """

    @abstractmethod
    async def get_by_id(self, message_id: MessageId) -> Message | None:
        """
        Busca mensagem por ID.

        Args:
            message_id: ID da mensagem

        Returns:
            Message se encontrada, None caso contrário
        """
        pass

    @abstractmethod
    async def save(self, message: Message) -> None:
        """
        Salva mensagem.

        Args:
            message: Mensagem a salvar
        """
        pass

    @abstractmethod
    async def get_history(
        self,
        channel_id: ChannelId,
        limit: int = 20,
    ) -> list[Message]:
        """
        Busca histórico de mensagens do canal.

        Args:
            channel_id: ID do canal
            limit: Máximo de mensagens

        Returns:
            Lista de mensagens (mais recentes primeiro)
        """
        pass

    @abstractmethod
    async def delete(self, message_id: MessageId) -> bool:
        """
        Remove mensagem.

        Args:
            message_id: ID da mensagem

        Returns:
            True se removida, False se não encontrada
        """
        pass

    @classmethod
    @abstractmethod
    def create(cls) -> Self:
        """Factory method."""
        pass
