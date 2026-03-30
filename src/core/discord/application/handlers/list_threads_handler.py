# -*- coding: utf-8 -*-
"""
ListThreadsHandler.

Handler CQRS para ListThreadsQuery.

DOC: openspec/changes/discord-ddd-migration/specs/discord-application/spec.md
"""

from __future__ import annotations

from dataclasses import dataclass

from ...domain.entities import Thread
from ...domain.repositories import ChannelRepository
from ..queries import ListThreadsQuery
from .base_handler import BaseHandler


@dataclass
class ListThreadsResult:
    """Resultado de ListThreadsQuery."""

    threads: list[Thread]
    """Lista de threads recuperadas."""

    total: int
    """Total de threads retornadas."""

    @classmethod
    def from_list(cls, threads: list[Thread]) -> "ListThreadsResult":
        """Cria resultado a partir de lista de threads."""
        return cls(threads=threads, total=len(threads))


class ListThreadsHandler(BaseHandler):
    """
    Handler para ListThreadsQuery.

    Processa queries de listagem de threads:
    1. Valida acesso ao canal (herdado de BaseHandler)
    2. Lista threads via ThreadRepository.list_threads()

    Args:
        channel_repository: Repositório de canais para validação
        thread_repository: Repositório de threads para busca
    """

    def __init__(
        self,
        channel_repository: ChannelRepository,
        thread_repository,
    ) -> None:
        """Inicializa handler com dependências."""
        super().__init__(channel_repository, lambda _: None)
        self._thread_repo = thread_repository

    async def handle(self, query: ListThreadsQuery) -> ListThreadsResult:
        """
        Processa query de listagem de threads.

        Args:
            query: ListThreadsQuery com channel_id e include_archived

        Returns:
            ListThreadsResult com lista de threads

        Raises:
            PermissionError: Se canal não está autorizado
        """
        # 1. Validar acesso ao canal (herdado)
        await self._validate_access(query.channel_id)

        # 2. Listar threads
        threads = await self._thread_repo.list_threads(
            channel_id=query.channel_id,
            include_archived=query.include_archived,
        )

        # 3. Retornar resultado
        return ListThreadsResult.from_list(threads)
