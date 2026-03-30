# -*- coding: utf-8 -*-
"""
Testes unitários para FetchMessagesHandler.

DOC: openspec/changes/discord-ddd-migration/specs/discord-application/spec.md
- Handler busca histórico de mensagens
- Retorna lista de MessageDTO
- Valida acesso ao canal
"""

from __future__ import annotations

from unittest.mock import AsyncMock

import pytest

from src.core.discord.application.queries import FetchMessagesQuery
from src.core.discord.domain.entities import Message
from src.core.discord.domain.repositories import ChannelRepository, MessageRepository


class TestFetchMessagesHandler:
    """
    Testa FetchMessagesHandler.handle().

    Especificação: Application Layer - Query Handlers
    """

    @pytest.fixture
    def mock_channel_repo(self) -> ChannelRepository:
        """Mock de ChannelRepository."""
        repo = AsyncMock(spec=ChannelRepository)
        repo.is_authorized = AsyncMock(return_value=True)
        return repo

    @pytest.fixture
    def mock_message_repo(self) -> MessageRepository:
        """Mock de MessageRepository."""
        repo = AsyncMock(spec=MessageRepository)
        return repo

    @pytest.fixture
    def handler(
        self,
        mock_channel_repo: ChannelRepository,
        mock_message_repo: MessageRepository,
    ):
        """
        Cria instância do FetchMessagesHandler.

        TODO: Implementar handler após teste falhar (RED).
        """
        from src.core.discord.application.handlers import fetch_messages_handler

        return fetch_messages_handler.FetchMessagesHandler(
            channel_repository=mock_channel_repo,
            message_repository=mock_message_repo,
        )

    @pytest.mark.asyncio
    async def test_handle_busca_historico_mensagens(
        self,
        handler,
        mock_channel_repo: ChannelRepository,
        mock_message_repo: MessageRepository,
    ):
        """
        DOC: specs/discord-application/spec.md
        Scenario: FetchMessagesHandler retorna mensagens

        WHEN handler.handle(query) é chamado
        THEN SHALL:
          - validar acesso
          - buscar mensagens via MessageRepository.get_history()
          - retornar lista de mensagens
        """
        # Setup - query válida
        query = FetchMessagesQuery.create(
            channel_id="123456789",
            limit=10,
        )

        # Setup - mensagens mockadas
        mock_messages = [
            Message.create(
                message_id="1",
                channel_id="123456789",
                author_id="123456",  # IDs numéricos
                content="Mensagem 1",
                is_bot=False,
            ),
            Message.create(
                message_id="2",
                channel_id="123456789",
                author_id="789012",  # IDs numéricos
                content="Mensagem 2",
                is_bot=False,
            ),
        ]
        mock_message_repo.get_history = AsyncMock(return_value=mock_messages)

        # Act
        result = await handler.handle(query)

        # Assert - validação de acesso
        mock_channel_repo.is_authorized.assert_called_once()

        # Assert - buscou histórico
        mock_message_repo.get_history.assert_called_once()

        # Assert - retornou mensagens
        assert len(result.messages) == 2
        assert str(result.messages[0].content) == "Mensagem 1"
        assert str(result.messages[1].content) == "Mensagem 2"

    @pytest.mark.asyncio
    async def test_handle_respeita_limit(
        self,
        handler,
        mock_message_repo: MessageRepository,
    ):
        """
        DOC: specs/discord-application/spec.md
        Scenario: Limit controla quantidade de mensagens

        WHEN query.limit=N
        THEN SHALL buscar exatamente N mensagens
        """
        query = FetchMessagesQuery.create(
            channel_id="123456789",
            limit=5,
        )

        mock_message_repo.get_history = AsyncMock(return_value=[])

        await handler.handle(query)

        # Assert - passou o limit correto
        mock_message_repo.get_history.assert_called_once()
        call_args = mock_message_repo.get_history.call_args
        assert call_args[1]["limit"] == 5

    @pytest.mark.asyncio
    async def test_handle_retorna_lista_vazia_sem_mensagens(
        self,
        handler,
        mock_message_repo: MessageRepository,
    ):
        """
        DOC: specs/discord-application/spec.md
        Scenario: Canal sem mensagens

        WHEN não há mensagens no canal
        THEN SHALL retornar lista vazia (sem erro)
        """
        query = FetchMessagesQuery.create(
            channel_id="123456789",
        )

        mock_message_repo.get_history = AsyncMock(return_value=[])

        result = await handler.handle(query)

        assert result.messages == []
        assert result.total == 0

    @pytest.mark.asyncio
    async def test_handle_rejeita_canal_nao_autorizado(
        self,
        handler,
        mock_channel_repo: ChannelRepository,
    ):
        """
        DOC: specs/discord-application/spec.md
        Scenario: Handler valida permissões

        WHEN canal não está autorizado
        THEN SHALL lançar PermissionError
        """
        mock_channel_repo.is_authorized = AsyncMock(return_value=False)

        query = FetchMessagesQuery.create(
            channel_id="999999999",
        )

        with pytest.raises(PermissionError, match="não está autorizado"):
            await handler.handle(query)
