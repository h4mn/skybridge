# -*- coding: utf-8 -*-
"""
Testes unitários para ListThreadsHandler.

DOC: openspec/changes/discord-ddd-migration/specs/discord-application/spec.md
"""

from __future__ import annotations

from unittest.mock import AsyncMock

import pytest

from src.core.discord.application.queries import ListThreadsQuery
from src.core.discord.domain.entities import Thread
from src.core.discord.domain.repositories import ChannelRepository


class TestListThreadsHandler:
    """Testa ListThreadsHandler.handle()."""

    @pytest.fixture
    def mock_channel_repo(self) -> ChannelRepository:
        """Mock de ChannelRepository."""
        repo = AsyncMock(spec=ChannelRepository)
        repo.is_authorized = AsyncMock(return_value=True)
        return repo

    @pytest.fixture
    def mock_thread_repo(self) -> AsyncMock:
        """Mock de ThreadRepository."""
        repo = AsyncMock()
        return repo

    @pytest.fixture
    def handler(
        self,
        mock_channel_repo: ChannelRepository,
        mock_thread_repo: AsyncMock,
    ):
        """Cria instância do ListThreadsHandler."""
        from src.core.discord.application.handlers import list_threads_handler

        return list_threads_handler.ListThreadsHandler(
            channel_repository=mock_channel_repo,
            thread_repository=mock_thread_repo,
        )

    @pytest.mark.asyncio
    async def test_handle_lista_threads_ativas(
        self,
        handler,
        mock_channel_repo: ChannelRepository,
        mock_thread_repo: AsyncMock,
    ):
        """
        DOC: specs/discord-application/spec.md
        Scenario: ListThreadsHandler retorna threads

        WHEN handler.handle(query) é chamado
        THEN SHALL retornar lista de threads ativas
        """
        query = ListThreadsQuery.create(
            channel_id="123456789",
        )

        # Mock threads
        mock_threads = [
            Thread.create(
                thread_id="1",
                name="Thread 1",
                parent_channel_id="123456789",
                root_message_id="111111",  # ID numérico
                guild_id="999999999",  # ID numérico
            ),
            Thread.create(
                thread_id="2",
                name="Thread 2",
                parent_channel_id="123456789",
                root_message_id="222222",  # ID numérico
                guild_id="999999999",  # ID numérico
            ),
        ]
        mock_thread_repo.list_threads = AsyncMock(return_value=mock_threads)

        result = await handler.handle(query)

        assert len(result.threads) == 2
        assert result.threads[0].name == "Thread 1"

    @pytest.mark.asyncio
    async def test_handle_inclui_threads_arquivadas_quando_solicitado(
        self,
        handler,
        mock_thread_repo: AsyncMock,
    ):
        """
        DOC: specs/discord-application/spec.md
        Scenario: include_archived=True

        WHEN query.include_archived=True
        THEN SHALL buscar threads arquivadas também
        """
        query = ListThreadsQuery.create(
            channel_id="123456789",
            include_archived=True,
        )

        mock_thread_repo.list_threads = AsyncMock(return_value=[])

        await handler.handle(query)

        # Assert - passou include_archived
        mock_thread_repo.list_threads.assert_called_once()
        call_args = mock_thread_repo.list_threads.call_args
        assert call_args[1]["include_archived"] is True

    @pytest.mark.asyncio
    async def test_handle_retorna_lista_vazia_sem_threads(
        self,
        handler,
        mock_thread_repo: AsyncMock,
    ):
        """WHEN não há threads, THEN SHALL retornar lista vazia."""
        query = ListThreadsQuery.create(channel_id="123456789")

        mock_thread_repo.list_threads = AsyncMock(return_value=[])

        result = await handler.handle(query)

        assert result.threads == []
        assert result.total == 0

    @pytest.mark.asyncio
    async def test_handle_rejeita_canal_nao_autorizado(
        self,
        handler,
        mock_channel_repo: ChannelRepository,
    ):
        """WHEN canal não autorizado, THEN SHALL lançar PermissionError."""
        mock_channel_repo.is_authorized = AsyncMock(return_value=False)

        query = ListThreadsQuery.create(channel_id="999999999")

        with pytest.raises(PermissionError, match="não está autorizado"):
            await handler.handle(query)
