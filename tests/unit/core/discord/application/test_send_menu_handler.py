# -*- coding: utf-8 -*-
"""
Testes unitários para SendMenuHandler.

DOC: openspec/changes/discord-ddd-migration/specs/discord-application/spec.md
- Handler valida permissões
- Handler cria Message com menu select
- Handler valida opções (mínimo 1, máximo 25)
- Handler publica MessageSentEvent
"""

from __future__ import annotations

from unittest.mock import AsyncMock

import pytest

from src.core.discord.application.commands import SendMenuCommand
from src.core.discord.domain.entities import Message
from src.core.discord.domain.events import MessageSentEvent
from src.core.discord.domain.repositories import ChannelRepository, MessageRepository


class TestSendMenuHandler:
    """
    Testa SendMenuHandler.process().

    Especificação: Application Layer - Command Handlers
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
        repo.save = AsyncMock()
        return repo

    @pytest.fixture
    def mock_event_publisher(self) -> AsyncMock:
        """Mock de publicador de eventos."""
        return AsyncMock()

    @pytest.fixture
    def handler(
        self,
        mock_channel_repo: ChannelRepository,
        mock_message_repo: MessageRepository,
        mock_event_publisher: AsyncMock,
    ):
        """Cria instância do SendMenuHandler."""
        from src.core.discord.application.handlers import send_menu_handler

        return send_menu_handler.SendMenuHandler(
            channel_repository=mock_channel_repo,
            message_repository=mock_message_repo,
            event_publisher=mock_event_publisher,
        )

    @pytest.mark.asyncio
    async def test_handle_envia_menu_com_opcoes(self, handler, mock_channel_repo, mock_message_repo, mock_event_publisher):
        """
        DOC: specs/discord-application/spec.md
        Scenario: SendMenuHandler executa comando

        WHEN handler.handle(command) é chamado com opções válidas
        THEN SHALL:
          - validar acesso via ChannelRepository.is_authorized()
          - criar Message com menu select
          - salvar via MessageRepository.save()
          - publicar MessageSentEvent
        """
        command = SendMenuCommand.create(
            channel_id="123456789",
            text="Escolha uma opção:",
            placeholder="Escolha uma opção",
            options=[
                {"label": "Opção 1", "value": "opt1"},
                {"label": "Opção 2", "value": "opt2"},
                {"label": "Opção 3", "value": "opt3"},
            ],
        )

        result = await handler.handle(command)

        # Assert - validação de acesso
        mock_channel_repo.is_authorized.assert_called_once()

        # Assert - mensagem salva
        mock_message_repo.save.assert_called_once()
        saved_message = mock_message_repo.save.call_args[0][0]
        assert isinstance(saved_message, Message)

        # Assert - evento publicado
        mock_event_publisher.assert_called_once()
        published_event = mock_event_publisher.call_args[0][0]
        assert isinstance(published_event, MessageSentEvent)

        # Assert - resultado
        assert result.success is True
        assert result.message_id is not None

    @pytest.mark.asyncio
    async def test_handle_rejeita_canal_nao_autorizado(self, handler, mock_channel_repo, mock_message_repo):
        """
        DOC: specs/discord-application/spec.md
        Scenario: Handler valida permissões

        WHEN handler.handle(command) é chamado com canal NÃO autorizado
        THEN SHALL lançar exceção e NÃO salvar mensagem
        """
        mock_channel_repo.is_authorized = AsyncMock(return_value=False)

        command = SendMenuCommand.create(
            channel_id="999999999",
            text="Não autorizado",
            placeholder="Não autorizado",
            options=[{"label": "X", "value": "x"}],
        )

        # Act & Assert
        with pytest.raises(PermissionError, match="não está autorizado"):
            await handler.handle(command)

        # Assert - mensagem NÃO foi salva
        mock_message_repo.save.assert_not_called()

    @pytest.mark.asyncio
    async def test_handle_rejeita_placeholder_vazio(self, handler):
        """
        DOC: specs/discord-presentation/spec.md
        Scenario: SendMenuCommand com placeholder vazio

        WHEN command.placeholder está vazio
        THEN SHALL lançar ValueError
        """
        command = SendMenuCommand.create(
            channel_id="123456789",
            text="Teste",
            placeholder="",  # Vazio
            options=[{"label": "X", "value": "x"}],
        )

        with pytest.raises(ValueError, match="placeholder.*vazio"):
            await handler.handle(command)

    @pytest.mark.asyncio
    async def test_handle_rejeita_sem_opcoes(self, handler):
        """
        DOC: specs/discord-presentation/spec.md
        Scenario: SendMenuCommand sem opções

        WHEN command.options está vazio
        THEN SHALL lançar ValueError na criação do command
        NOTA: A validação ocorre no SendMenuCommand.__post_init__, não no handler
        """
        # O Command valida na criação, antes de chegar ao handler
        with pytest.raises(ValueError, match="max_values.*não pode exceder"):
            SendMenuCommand.create(
                channel_id="123456789",
                text="Sem opções",
                placeholder="Sem opções",
                options=[],  # Vazio - max_values=1 > len(options)=0
            )

    @pytest.mark.asyncio
    async def test_handle_suporta_varias_opcoes(self, handler, mock_message_repo):
        """
        DOC: specs/discord-presentation/spec.md
        Scenario: Menu com múltiplas opções

        WHEN options tem até 25 itens
        THEN SHALL processar todas corretamente
        """
        options = [
            {"label": f"Opção {i}", "value": f"opt{i}"}
            for i in range(10)
        ]

        command = SendMenuCommand.create(
            channel_id="123456789",
            text="Escolha:",
            placeholder="Escolha:",
            options=options,
        )

        result = await handler.handle(command)

        assert result.success is True
        mock_message_repo.save.assert_called_once()

    @pytest.mark.asyncio
    async def test_handle_suporta_opcoes_com_emoji(self, handler):
        """
        DOC: specs/discord-presentation/spec.md
        Scenario: Opções com emoji

        WHEN option tem emoji definido
        THEN SHALL incluir emoji na formatação
        """
        command = SendMenuCommand.create(
            channel_id="123456789",
            text="Escolha:",
            placeholder="Escolha:",
            options=[
                {"label": "🍕 Pizza", "value": "pizza", "emoji": "🍕"},
                {"label": "🍔 Burger", "value": "burger", "emoji": "🍔"},
            ],
        )

        result = await handler.handle(command)

        assert result.success is True
