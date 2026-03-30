# -*- coding: utf-8 -*-
"""
Testes unitários para SendButtonsHandler.

DOC: openspec/changes/discord-ddd-migration/specs/discord-application/spec.md
- Handler valida permissões
- Handler cria Message com botões
- Handler valida limite de 5 botões
- Handler publica MessageSentEvent
"""

from __future__ import annotations

from unittest.mock import AsyncMock

import pytest

from src.core.discord.application.commands import SendButtonsCommand
from src.core.discord.domain.entities import Message
from src.core.discord.domain.events import MessageSentEvent
from src.core.discord.domain.repositories import ChannelRepository, MessageRepository


class TestSendButtonsHandler:
    """
    Testa SendButtonsHandler.process().

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
        Cria instância do SendButtonsHandler.

        TODO: Implementar handler após teste falhar (RED).
        """
        from src.core.discord.application.handlers import send_buttons_handler

        return send_buttons_handler.SendButtonsHandler(
            channel_repository=mock_channel_repo,
            message_repository=mock_message_repo,
            event_publisher=mock_event_publisher,
        )

    @pytest.mark.asyncio
    async def test_handle_envia_mensagem_com_botoes(
        self,
        handler,
        mock_channel_repo: ChannelRepository,
        mock_message_repo: MessageRepository,
        mock_event_publisher: AsyncMock,
    ):
        """
        DOC: specs/discord-application/spec.md
        Scenario: SendButtonsHandler executa comando

        WHEN handler.handle(command) é chamado com botões válidos
        THEN SHALL:
          - validar acesso via ChannelRepository.is_authorized()
          - criar Message com texto e botões
          - salvar via MessageRepository.save()
          - publicar MessageSentEvent
        """
        # Setup - command válido
        command = SendButtonsCommand.create(
            channel_id="123456789",
            text="Selecione uma opção:",
            buttons=[
                {"id": "btn_confirm", "label": "Confirmar"},
                {"id": "btn_cancel", "label": "Cancelar", "style": "danger"},
            ],
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

        command = SendButtonsCommand.create(
            channel_id="999999999",
            text="Botões não autorizados",
            buttons=[{"id": "btn1", "label": "Botão 1"}],
        )

        # Act & Assert
        with pytest.raises(PermissionError, match="não está autorizado"):
            await handler.handle(command)

        # Assert - mensagem NÃO foi salva
        mock_message_repo.save.assert_not_called()

    @pytest.mark.asyncio
    async def test_handle_rejeita_texto_vazio(
        self,
        handler,
        mock_channel_repo: ChannelRepository,
    ):
        """
        DOC: specs/discord-presentation/spec.md
        Scenario: SendButtonsCommand com texto vazio

        WHEN command.text está vazio
        THEN SHALL lançar ValueError
        """
        command = SendButtonsCommand.create(
            channel_id="123456789",
            text="",  # Vazio
            buttons=[{"id": "btn1", "label": "Botão 1"}],
        )

        with pytest.raises(ValueError, match="texto.*vazio"):
            await handler.handle(command)

    @pytest.mark.asyncio
    async def test_handle_rejeita_mais_de_5_botoes(
        self,
        handler,
        mock_channel_repo: ChannelRepository,
        mock_message_repo: MessageRepository,
    ):
        """
        DOC: specs/discord-presentation/spec.md
        Scenario: Limite de 5 botões do Discord

        WHEN command.buttons tem mais de 5 itens
        THEN SHALL lançar ValueError na criação do Command
        """
        # Criar 6 botões (limite excedido)
        buttons = [{"id": f"btn{i}", "label": f"Botão {i}"} for i in range(6)]

        with pytest.raises(ValueError, match="máximo 5 botões"):
            SendButtonsCommand.create(
                channel_id="123456789",
                text="Muitos botões",
                buttons=buttons,
            )

    @pytest.mark.asyncio
    async def test_handle_suporta_varios_estilos_de_botao(
        self,
        handler,
        mock_channel_repo: ChannelRepository,
        mock_message_repo: MessageRepository,
    ):
        """
        DOC: specs/discord-presentation/spec.md
        Scenario: Estilos de botão suportados

        WHEN buttons têm diferentes estilos (primary, secondary, danger, etc)
        THEN SHALL processar todos corretamente
        """
        command = SendButtonsCommand.create(
            channel_id="123456789",
            text="Escolha o estilo:",
            buttons=[
                {"id": "btn_primary", "label": "Primário", "style": "primary"},
                {"id": "btn_secondary", "label": "Secundário", "style": "secondary"},
                {"id": "btn_success", "label": "Sucesso", "style": "success"},
                {"id": "btn_danger", "label": "Perigo", "style": "danger"},
            ],
        )

        result = await handler.handle(command)

        assert result.success is True
        mock_message_repo.save.assert_called_once()

    @pytest.mark.asyncio
    async def test_handle_suporta_botoes_com_emoji(
        self,
        handler,
        mock_channel_repo: ChannelRepository,
        mock_message_repo: MessageRepository,
    ):
        """
        DOC: specs/discord-presentation/spec.md
        Scenario: Botões com emoji

        WHEN button tem emoji definido
        THEN SHALL incluir emoji na formatação
        """
        command = SendButtonsCommand.create(
            channel_id="123456789",
            text="Reaja:",
            buttons=[
                {"id": "btn_yes", "label": "Sim", "emoji": "✅"},
                {"id": "btn_no", "label": "Não", "emoji": "❌"},
            ],
        )

        result = await handler.handle(command)

        assert result.success is True
        saved_message = mock_message_repo.save.call_args[0][0]
        # TODO: Verificar se emoji está incluído na mensagem formatada

    @pytest.mark.asyncio
    async def test_handle_suporta_botoes_desabilitados(
        self,
        handler,
        mock_channel_repo: ChannelRepository,
        mock_message_repo: MessageRepository,
    ):
        """
        DOC: specs/discord-presentation/spec.md
        Scenario: Botões desabilitados

        WHEN button.disabled=True
        THEN SHALL marcar botão como desabilitado
        """
        command = SendButtonsCommand.create(
            channel_id="123456789",
            text="Ação indisponível:",
            buttons=[
                {"id": "btn_disabled", "label": "Indisponível", "disabled": True},
            ],
        )

        result = await handler.handle(command)

        assert result.success is True
