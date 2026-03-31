# -*- coding: utf-8 -*-
"""
Testes unitários para PortfolioUIHandler.

DOC: openspec/changes/discord-ddd-migration/specs/discord-paper-integration/spec.md
- Handler envia embed de portfolio via DiscordService
- Handler envia menu de opções
- Handler atualiza barra de progresso
- Handler roteia seleções do menu
"""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock

import pytest

from src.core.integrations.discord_paper.handlers.portfolio_ui_handler import PortfolioUIHandler


class TestPortfolioUIHandler:
    """
    Testa PortfolioUIHandler.

    Especificação: Integration Layer - Handlers
    """

    @pytest.fixture
    def mock_discord_service(self):
        """Mock de DiscordService."""
        service = AsyncMock()
        service.send_embed = AsyncMock(return_value=MagicMock(id="msg123"))
        service.send_buttons = AsyncMock(return_value=MagicMock(id="msg456"))
        service.send_message = AsyncMock()
        service.send_progress = AsyncMock()
        return service

    @pytest.fixture
    def handler(self, mock_discord_service):
        """Cria instância do PortfolioUIHandler."""
        return PortfolioUIHandler(discord_service=mock_discord_service)

    @pytest.mark.asyncio
    async def test_send_portfolio_embed_chama_projection(self, handler, mock_discord_service):
        """
        DOC: specs/discord-paper-integration/spec.md
        Scenario: Enviar embed de portfolio

        WHEN send_portfolio_embed() é chamado
        THEN SHALL usar projection e chamar send_embed()
        """
        message_id = await handler.send_portfolio_embed(
            channel_id="123456789",
            balance_btc=1.5,
            balance_usd=50000.0,
            positions=[],
            pnl_percent=15.5
        )

        # Assert - send_embed foi chamado
        mock_discord_service.send_embed.assert_called_once()
        call_kwargs = mock_discord_service.send_embed.call_args[1]

        assert call_kwargs["channel_id"] == "123456789"
        assert call_kwargs["title"] is not None
        assert call_kwargs["color"] == 3066993  # Verde para lucro

        # Assert - retorna message_id
        assert message_id == "msg123"

    @pytest.mark.asyncio
    async def test_send_portfolio_embed_cor_vermelha_prejuizo(self, handler, mock_discord_service):
        """
        DOC: specs/discord-paper-integration/spec.md
        Scenario: Embed com prejuízo

        WHEN send_portfolio_embed() é chamado com pnl_percent negativo
        THEN SHALL usar cor vermelha
        """
        await handler.send_portfolio_embed(
            channel_id="123456789",
            balance_btc=1.0,
            balance_usd=45000.0,
            positions=[],
            pnl_percent=-5.0
        )

        call_kwargs = mock_discord_service.send_embed.call_args[1]
        assert call_kwargs["color"] == 15158332  # Vermelho para prejuízo

    @pytest.mark.asyncio
    async def test_send_portfolio_menu_com_posicoes(self, handler, mock_discord_service):
        """
        DOC: specs/discord-paper-integration/spec.md
        Scenario: Menu com posições

        WHEN send_portfolio_menu() é chamado com has_positions=True
        THEN SHALL incluir opções de posições
        """
        message_id = await handler.send_portfolio_menu(
            channel_id="123456789",
            has_positions=True
        )

        # Assert - send_buttons foi chamado
        mock_discord_service.send_buttons.assert_called_once()
        call_kwargs = mock_discord_service.send_buttons.call_args[1]

        assert call_kwargs["channel_id"] == "123456789"
        assert len(call_kwargs["buttons"]) >= 4  # Inclui opções de posições

        # Verifica que existe botão de fechar posição
        button_ids = [btn.custom_id for btn in call_kwargs["buttons"]]
        assert "close_position" in button_ids

    @pytest.mark.asyncio
    async def test_send_portfolio_menu_sem_posicoes(self, handler, mock_discord_service):
        """
        DOC: specs/discord-paper-integration/spec.md
        Scenario: Menu sem posições

        WHEN send_portfolio_menu() é chamado com has_positions=False
        THEN SHALL não incluir opções de posições
        """
        await handler.send_portfolio_menu(
            channel_id="123456789",
            has_positions=False
        )

        call_kwargs = mock_discord_service.send_buttons.call_args[1]
        button_ids = [btn.custom_id for btn in call_kwargs["buttons"]]

        assert "portfolio_positions" not in button_ids
        assert "close_position" not in button_ids

    @pytest.mark.asyncio
    async def test_update_portfolio_progress(self, handler, mock_discord_service):
        """
        DOC: specs/discord-paper-integration/spec.md
        Scenario: Atualizar progresso

        WHEN update_portfolio_progress() é chamado
        THEN SHALL chamar send_progress com parâmetros corretos
        """
        await handler.update_portfolio_progress(
            channel_id="123456789",
            tracking_id="track123",
            current=50,
            total=100,
            status="running"
        )

        # Assert - send_progress foi chamado
        mock_discord_service.send_progress.assert_called_once()
        call_kwargs = mock_discord_service.send_progress.call_args[1]

        assert call_kwargs["channel_id"] == "123456789"
        assert call_kwargs["current"] == 50
        assert call_kwargs["total"] == 100
        assert call_kwargs["status"] == "running"
        assert call_kwargs["tracking_id"] == "track123"

    @pytest.mark.asyncio
    async def test_handle_portfolio_selection_summary(self, handler, mock_discord_service):
        """
        DOC: specs/discord-paper-integration/spec.md
        Scenario: Seleção summary

        WHEN handle_portfolio_selection() é chamado com "portfolio_summary"
        THEN SHALL enviar mensagem de resumo
        """
        await handler.handle_portfolio_selection(
            selection="portfolio_summary",
            channel_id="123456789"
        )

        # Assert - send_message foi chamado
        mock_discord_service.send_message.assert_called_once()
        call_kwargs = mock_discord_service.send_message.call_args[1]

        assert "Resumo" in call_kwargs["content"]

    @pytest.mark.asyncio
    async def test_handle_portfolio_selection_positions(self, handler, mock_discord_service):
        """
        DOC: specs/discord-paper-integration/spec.md
        Scenario: Seleção positions

        WHEN handle_portfolio_selection() é chamado com "portfolio_positions"
        THEN SHALL enviar mensagem de posições
        """
        await handler.handle_portfolio_selection(
            selection="portfolio_positions",
            channel_id="123456789"
        )

        call_kwargs = mock_discord_service.send_message.call_args[1]
        assert "Posições" in call_kwargs["content"]

    @pytest.mark.asyncio
    async def test_handle_portfolio_selection_desconhecida(self, handler, mock_discord_service):
        """
        DOC: specs/discord-paper-integration/spec.md
        Scenario: Seleção desconhecida

        WHEN handle_portfolio_selection() é chamado com seleção inválida
        THEN SHALL não enviar mensagem (log warning)
        """
        await handler.handle_portfolio_selection(
            selection="unknown_option",
            channel_id="123456789"
        )

        # Assert - send_message NÃO foi chamado
        mock_discord_service.send_message.assert_not_called()

    @pytest.mark.asyncio
    async def test_handle_portfolio_selection_close_position(self, handler, mock_discord_service):
        """
        DOC: specs/discord-paper-integration/spec.md
        Scenario: Seleção close_position

        WHEN handle_portfolio_selection() é chamado com "close_position"
        THEN SHALL enviar mensagem de fechar posição
        """
        await handler.handle_portfolio_selection(
            selection="close_position",
            channel_id="123456789"
        )

        call_kwargs = mock_discord_service.send_message.call_args[1]
        assert "Fechar" in call_kwargs["content"]
