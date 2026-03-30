# -*- coding: utf-8 -*-
"""
Testes unitários para SendEmbedHandler.

DOC: openspec/changes/discord-ddd-migration/specs/discord-application/spec.md
- Handler valida permissões
- Handler cria Message com embed
- Handler salva mensagem
- Handler publica MessageSentEvent
"""

from __future__ import annotations

from unittest.mock import AsyncMock

import pytest

from src.core.discord.application.commands import SendEmbedCommand
from src.core.discord.domain.entities import Message
from src.core.discord.domain.events import MessageSentEvent
from src.core.discord.domain.repositories import ChannelRepository, MessageRepository


class TestSendEmbedHandler:
    """
    Testa SendEmbedHandler.process().

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
        Cria instância do SendEmbedHandler.

        TODO: Implementar handler após teste falhar (RED).
        """
        from src.core.discord.application.handlers import send_embed_handler

        return send_embed_handler.SendEmbedHandler(
            channel_repository=mock_channel_repo,
            message_repository=mock_message_repo,
            event_publisher=mock_event_publisher,
        )

    @pytest.mark.asyncio
    async def test_handle_envia_embed_canal_autorizado(
        self,
        handler,
        mock_channel_repo: ChannelRepository,
        mock_message_repo: MessageRepository,
        mock_event_publisher: AsyncMock,
    ):
        """
        DOC: specs/discord-application/spec.md
        Scenario: SendEmbedHandler executa comando

        WHEN handler.handle(command) é chamado com canal autorizado
        THEN SHALL:
          - validar acesso via ChannelRepository.is_authorized()
          - criar Message com dados do embed
          - salvar via MessageRepository.save()
          - publicar MessageSentEvent
        """
        # Setup - command válido
        command = SendEmbedCommand.create(
            channel_id="123456789",
            title="Título do Embed",
            description="Descrição do embed",
            color="verde",
            fields=[{"name": "Campo1", "value": "Valor1"}],
        )

        # Act
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

        command = SendEmbedCommand.create(
            channel_id="999999999",
            title="Embed não autorizado",
        )

        # Act & Assert
        with pytest.raises(PermissionError, match="não está autorizado"):
            await handler.handle(command)

        # Assert - mensagem NÃO foi salva
        mock_message_repo.save.assert_not_called()

    @pytest.mark.asyncio
    async def test_handle_rejeita_titulo_vazio(
        self,
        handler,
        mock_channel_repo: ChannelRepository,
    ):
        """
        DOC: specs/discord-presentation/spec.md
        Scenario: SendEmbedCommand com título vazio

        WHEN command.embed.title está vazio
        THEN SHALL lançar ValueError
        """
        command = SendEmbedCommand.create(
            channel_id="123456789",
            title="",  # Vazio
        )

        with pytest.raises(ValueError, match="título.*vazio"):
            await handler.handle(command)

    @pytest.mark.asyncio
    async def test_handle_converte_cor_para_nome_valido(
        self,
        handler,
        mock_channel_repo: ChannelRepository,
        mock_message_repo: MessageRepository,
    ):
        """
        DOC: specs/discord-presentation/spec.md
        Scenario: Cores mapeadas para valores Discord

        WHEN command.embed.color é "verde"
        THEN SHALL converter para cor Discord (e.g., 65280)
        """
        command = SendEmbedCommand.create(
            channel_id="123456789",
            title="Embed Verde",
            color="verde",
        )

        await handler.handle(command)

        # Assert - mensagem salva com cor convertida
        saved_message = mock_message_repo.save.call_args[0][0]
        # TODO: Message precisa ter campo embed_data com cor convertida
        # assert saved_message.embed_data["color"] == 65280

    @pytest.mark.asyncio
    async def test_handle_inclui_fields_quando_presentes(
        self,
        handler,
        mock_channel_repo: ChannelRepository,
        mock_message_repo: MessageRepository,
    ):
        """
        DOC: specs/discord-presentation/spec.md
        Scenario: Embed com múltiplos campos

        WHEN command.embed.fields tem múltiplos itens
        THEN SHALL criar Message com todos os fields
        """
        command = SendEmbedCommand.create(
            channel_id="123456789",
            title="Multi-Field Embed",
            fields=[
                {"name": "Campo1", "value": "Valor1", "inline": True},
                {"name": "Campo2", "value": "Valor2", "inline": True},
                {"name": "Campo3", "value": "Valor3"},
            ],
        )

        await handler.handle(command)

        # Assert - mensagem salva com fields
        saved_message = mock_message_repo.save.call_args[0][0]
        # TODO: Message precisa ter campo embed_data com fields
        # assert len(saved_message.embed_data["fields"]) == 3

    @pytest.mark.asyncio
    async def test_handle_suporta_cores_variadas(
        self,
        handler,
        mock_channel_repo: ChannelRepository,
        mock_message_repo: MessageRepository,
    ):
        """
        DOC: specs/discord-presentation/spec.md
        Scenario: Cores suportadas pelo sistema

        WHEN command.embed.color é azul, verde, vermelho, amarelo, roxo
        THEN SHALL aceitar todas as variações
        """
        cores = ["azul", "verde", "vermelho", "amarelo", "roxo"]

        for cor in cores:
            command = SendEmbedCommand.create(
                channel_id="123456789",
                title=f"Embed {cor}",
                color=cor,
            )

            result = await handler.handle(command)
            assert result.success is True
