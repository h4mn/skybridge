# -*- coding: utf-8 -*-
"""
FetchMessagesHandler.

Handler CQRS para FetchMessagesQuery.

DOC: openspec/changes/discord-ddd-migration/specs/discord-application/spec.md
"""

from __future__ import annotations

from dataclasses import dataclass

from ...domain.entities import Message
from ...domain.repositories import ChannelRepository, MessageRepository
from ..queries import FetchMessagesQuery
from .base_handler import BaseHandler


@dataclass
class FetchMessagesResult:
    """Resultado de FetchMessagesQuery."""

    messages: list[Message]
    """Lista de mensagens recuperadas."""

    total: int
    """Total de mensagens retornadas."""

    @classmethod
    def from_list(cls, messages: list[Message]) -> "FetchMessagesResult":
        """Cria resultado a partir de lista de mensagens."""
        return cls(messages=messages, total=len(messages))


class FetchMessagesHandler(BaseHandler):
    """
    Handler para FetchMessagesQuery.

    Processa queries de busca de histórico:
    1. Valida acesso ao canal (herdado de BaseHandler)
    2. Busca mensagens via MessageRepository.get_history()

    Args:
        channel_repository: Repositório de canais para validação de acesso
        message_repository: Repositório de mensagens para busca
    """

    def __init__(
        self,
        channel_repository: ChannelRepository,
        message_repository: MessageRepository,
    ) -> None:
        """Inicializa handler com dependências."""
        # Nota: Query handlers não precisam de event_publisher
        # Passamos None para o base_handler
        super().__init__(channel_repository, lambda _: None)
        self._message_repo = message_repository

    async def handle(self, query: FetchMessagesQuery) -> FetchMessagesResult:
        """
        Processa query de busca de mensagens.

        Args:
            query: FetchMessagesQuery com channel_id e limit

        Returns:
            FetchMessagesResult com lista de mensagens

        Raises:
            PermissionError: Se canal não está autorizado
        """
        # 1. Validar acesso ao canal (herdado)
        await self._validate_access(query.channel_id)

        # 2. Buscar histórico
        messages = await self._message_repo.get_history(
            channel_id=query.channel_id,
            limit=query.limit,
        )

        # 3. Retornar resultado
        return FetchMessagesResult.from_list(messages)
