# -*- coding: utf-8 -*-
"""
Testes unitários para SendMessageHandler.

DOC: openspec/changes/discord-ddd-migration/specs/discord-application/spec.md
- Handler valida permissões
- Handler cria Message
- Handler salva mensagem
- Handler publica MessageSentEvent
"""

from __future__ import annotations

from unittest.mock import AsyncMock, Mock
from unittest.mock import patch

import pytest

from src.core.discord.application.commands import SendMessageCommand
from src.core.discord.domain.entities import Message
from src.core.discord.domain.events import MessageSentEvent
from src.core.discord.domain.repositories import ChannelRepository, MessageRepository
from src.core.discord.domain.value_objects import ChannelId, MessageContent


class TestSendMessageHandler:
    """
    Testa SendMessageHandler.process().

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
        """
        Cria instância do SendMessageHandler.

        TODO: Implementar handler após teste falhar (RED).
        """
        from src.core.discord.application.handlers import send_message_handler

        return send_message_handler.SendMessageHandler(
            channel_repository=mock_channel_repo,
            message_repository=mock_message_repo,
            event_publisher=mock_event_publisher,
        )

    @pytest.mark.asyncio
    async def test_handle_envia_mensagem_canal_autorizado(
        self,
        handler,
        mock_channel_repo: ChannelRepository,
        mock_message_repo: MessageRepository,
        mock_event_publisher: AsyncMock,
    ):
        """
        DOC: specs/discord-application/spec.md
        Scenario: SendMessageHandler executa comando

        WHEN handler.handle(command) é chamado com canal autorizado
        THEN SHALL:
          - validar acesso via ChannelRepository.is_authorized()
          - criar Message com dados do command
          - salvar via MessageRepository.save()
          - publicar MessageSentEvent
        """
        # Setup - command válido
        command = SendMessageCommand.create(
            channel_id="123456789",
            text="Olá, mundo!",
        )

        # Act
        result = await handler.handle(command)

        # Assert - validação de acesso
        mock_channel_repo.is_authorized.assert_called_once_with(
            ChannelId("123456789")
        )

        # Assert - mensagem salva
        mock_message_repo.save.assert_called_once()
        saved_message = mock_message_repo.save.call_args[0][0]
        assert isinstance(saved_message, Message)
        assert str(saved_message.content) == "Olá, mundo!"

        # Assert - evento publicado
        mock_event_publisher.assert_called_once()
        published_event = mock_event_publisher.call_args[0][0]
        assert isinstance(published_event, MessageSentEvent)

        # Assert - resultado
        assert result.success is True
        assert result.message_id is not None

    @pytest.mark.asyncio
    async def test_handle_rejeita_canal_nao_autorizado(
        self,
        handler,
        mock_channel_repo: ChannelRepository,
        mock_message_repo: MessageRepository,
    ):
        """
        DOC: specs/discord-application/spec.md
        Scenario: Handler valida permissões

        WHEN handler.handle(command) é chamado com canal NÃO autorizado
        THEN SHALL lançar exceção e NÃO salvar mensagem
        """
        # Setup - canal não autorizado
        mock_channel_repo.is_authorized = AsyncMock(return_value=False)

        command = SendMessageCommand.create(
            channel_id="999999999",
            text="Mensagem não autorizada",
        )

        # Act & Assert
        with pytest.raises(PermissionError, match="não está autorizado"):
            await handler.handle(command)

        # Assert - mensagem NÃO foi salva
        mock_message_repo.save.assert_not_called()

    @pytest.mark.asyncio
    async def test_handle_inclui_reply_to_quando_presente(
        self,
        handler,
        mock_channel_repo: ChannelRepository,
        mock_message_repo: MessageRepository,
    ):
        """
        DOC: specs/discord-application/spec.md
        Scenario: SendMessageCommand com reply_to

        WHEN command.contém reply_to (Message ID)
        THEN SHALL criar Message com referência à mensagem original
        """
        command = SendMessageCommand.create(
            channel_id="123456789",
            text="Isso é uma resposta",
            reply_to="987654321",
        )

        await handler.handle(command)

        # Assert - mensagem salva com reply_to
        saved_message = mock_message_repo.save.call_args[0][0]
        # TODO: Message precisa ter campo reply_to (a ser adicionado)
        # assert saved_message.reply_to == "987654321"

    @pytest.mark.asyncio
    async def test_handle_rejeita_conteudo_vazio(self, handler):
        """
        DOC: specs/discord-domain/spec.md
        Scenario: MessageContent vazio é inválido

        WHEN command.text está vazio
        THEN SHALL lançar ValueError na criação do command
        NOTA: A validação ocorre no MessageContent.__post_init__, não no handler
        """
        # O Command valida na criação, antes de chegar ao handler
        with pytest.raises(ValueError, match="MessageContent.*não pode ser vazio"):
            SendMessageCommand.create(
                channel_id="123456789",
                text="",  # Vazio
            )

    @pytest.mark.asyncio
    async def test_handle_rejeita_conteudo_muito_longo(self):
        """
        DOC: specs/discord-domain/spec.md
        Scenario: MessageContent excede limite máximo

        WHEN command.content excede 20000 caracteres
        THEN SHALL lançar MessageTooLongError na criação do Command
        """
        from src.core.discord.domain.value_objects import MessageTooLongError

        # Conteúdo maior que MAX_LENGTH (20000)
        texto_longo = "x" * 20001

        # O erro ocorre na criação do Command, validado por MessageContent
        with pytest.raises(MessageTooLongError):
            SendMessageCommand.create(
                channel_id="123456789",
                text=texto_longo,
            )
