# -*- coding: utf-8 -*-
"""
Testes unitários para ButtonClickHandler.

DOC: openspec/changes/discord-ddd-migration/specs/discord-application/spec.md
- Handler valida button_custom_id
- Handler valida channel_id
- Handler publica ButtonClickedEvent
- Handler retorna HandlerResult com dados
"""

from __future__ import annotations

from unittest.mock import AsyncMock

import pytest

from src.core.discord.application.commands import HandleButtonClickCommand
from src.core.discord.application.handlers.handler_result import HandlerResult


class TestButtonClickHandler:
    """
    Testa ButtonClickHandler.handle().

    Especificação: Application Layer - Command Handlers
    """

    @pytest.fixture
    def mock_event_publisher(self):
        """Mock de EventPublisher."""
        return AsyncMock()

    @pytest.fixture
    def handler(self, mock_event_publisher):
        """Cria instância do ButtonClickHandler."""
        from src.core.discord.application.handlers import button_click_handler

        return button_click_handler.ButtonClickHandler(
            event_publisher=mock_event_publisher
        )

    @pytest.mark.asyncio
    async def test_handle_processa_clique_valido(self, handler, mock_event_publisher):
        """
        DOC: specs/discord-application/spec.md
        Scenario: Processar clique válido

        WHEN handler.handle(command) é chamado com dados válidos
        THEN SHALL publicar evento e retornar sucesso
        """
        command = HandleButtonClickCommand(
            interaction_id="interaction_123",
            button_custom_id="confirm_btn",
            button_label="Confirmar",
            user_id="111111111",
            user_name="UsuarioTest",
            channel_id="123456789",
            message_id="987654321",
        )

        result = await handler.handle(command)

        # Assert - evento publicado
        mock_event_publisher.publish.assert_called_once()
        published_event = mock_event_publisher.publish.call_args[0][0]
        assert published_event.button_custom_id == "confirm_btn"

        # Assert - resultado sucesso (HandlerResult tem success, message_id, error)
        assert result.success is True
        assert result.message_id is not None  # event_id é armazenado em message_id
        assert result.error is None

    @pytest.mark.asyncio
    async def test_handle_rejeita_button_custom_id_vazio(self, handler, mock_event_publisher):
        """
        DOC: specs/discord-application/spec.md
        Scenario: button_custom_id vazio

        WHEN handler.handle(command) é chamado com button_custom_id vazio
        THEN SHALL retornar erro sem publicar evento
        """
        command = HandleButtonClickCommand(
            interaction_id="interaction_123",
            button_custom_id="",  # Vazio
            button_label="Botão",
            user_id="111111111",
            user_name="UsuarioTest",
            channel_id="123456789",
            message_id="987654321",
        )

        result = await handler.handle(command)

        # Assert - evento NÃO publicado
        mock_event_publisher.publish.assert_not_called()

        # Assert - erro
        assert result.success is False
        assert "button_custom_id" in result.error.lower()

    @pytest.mark.asyncio
    async def test_handle_rejeita_channel_id_vazio(self, handler, mock_event_publisher):
        """
        DOC: specs/discord-application/spec.md
        Scenario: channel_id vazio

        WHEN handler.handle(command) é chamado com channel_id vazio
        THEN SHALL retornar erro sem publicar evento
        """
        command = HandleButtonClickCommand(
            interaction_id="interaction_123",
            button_custom_id="btn",
            button_label="Botão",
            user_id="111111111",
            user_name="UsuarioTest",
            channel_id="",  # Vazio
            message_id="987654321",
        )

        result = await handler.handle(command)

        # Assert - evento NÃO publicado
        mock_event_publisher.publish.assert_not_called()

        # Assert - erro
        assert result.success is False
        assert "channel_id" in result.error.lower()

    @pytest.mark.asyncio
    async def test_handle_inclui_event_id_no_resultado(self, handler, mock_event_publisher):
        """
        DOC: specs/discord-application/spec.md
        Scenario: Event ID no resultado

        WHEN handler.handle(command) processa com sucesso
        THEN SHALL incluir event_id no message_id do resultado
        """
        command = HandleButtonClickCommand(
            interaction_id="interaction_123",
            button_custom_id="action_btn",
            button_label="Ação",
            user_id="111111111",
            user_name="UsuarioTest",
            channel_id="123456789",
            message_id="987654321",
        )

        result = await handler.handle(command)

        # Assert - event_id presente (armazenado em message_id)
        assert result.success is True
        assert result.message_id is not None

    @pytest.mark.asyncio
    async def test_handle_retorna_erro_em_excecao(self, handler, mock_event_publisher):
        """
        DOC: specs/discord-application/spec.md
        Scenario: Exceção durante processamento

        WHEN event_publisher.publish() lança exceção
        THEN SHALL retornar HandlerResult.failure
        """
        # Setup - publisher lança exceção
        mock_event_publisher.publish = AsyncMock(side_effect=Exception("Falha no publisher"))

        command = HandleButtonClickCommand(
            interaction_id="interaction_123",
            button_custom_id="btn",
            button_label="Botão",
            user_id="111111111",
            user_name="UsuarioTest",
            channel_id="123456789",
            message_id="987654321",
        )

        result = await handler.handle(command)

        # Assert - erro retornado
        assert result.success is False
        assert "Erro ao processar clique" in result.error

    @pytest.mark.asyncio
    async def test_handle_suporta_varios_nomes_usuario(self, handler, mock_event_publisher):
        """
        DOC: specs/discord-application/spec.md
        Scenario: Diferentes nomes de usuário

        WHEN handler.handle(command) é chamado com user_name variado
        THEN SHALL processar corretamente
        """
        for username in ["User123", "João Silva", "Test_User#9999", "ユーザー"]:
            command = HandleButtonClickCommand(
                interaction_id="interaction_123",
                button_custom_id="btn",
                button_label="Botão",
                user_id="111111111",
                user_name=username,
                channel_id="123456789",
                message_id="987654321",
            )

            result = await handler.handle(command)

            assert result.success is True
