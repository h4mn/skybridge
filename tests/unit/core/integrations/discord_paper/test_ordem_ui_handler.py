# -*- coding: utf-8 -*-
"""
Testes unitários para OrdemUIHandler.

DOC: openspec/changes/discord-ddd-migration/specs/discord-paper-integration/spec.md
- Handler envia confirmação de ordem
- Handler envia notificação de ordem executada
- Handler envia notificação de ordem cancelada
- Handler roteia respostas de confirmação
"""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock

import pytest

from src.core.integrations.discord_paper.handlers.ordem_ui_handler import OrdemUIHandler


class TestOrdemUIHandler:
    """
    Testa OrdemUIHandler.

    Especificação: Integration Layer - Handlers
    """

    @pytest.fixture
    def mock_discord_service(self):
        """Mock de DiscordService."""
        service = AsyncMock()
        service.send_buttons = AsyncMock(return_value=MagicMock(id="msg123"))
        service.send_embed = AsyncMock(return_value=MagicMock(id="msg456"))
        service.send_message = AsyncMock()
        service.edit_message = AsyncMock()
        return service

    @pytest.fixture
    def handler(self, mock_discord_service):
        """Cria instância do OrdemUIHandler."""
        return OrdemUIHandler(discord_service=mock_discord_service)

    @pytest.mark.asyncio
    async def test_send_ordem_confirmancia_chama_projection(self, handler, mock_discord_service):
        """
        DOC: specs/discord-paper-integration/spec.md
        Scenario: Enviar confirmação de ordem

        WHEN send_ordem_confirmacao() é chamado
        THEN SHALL usar projection e chamar send_buttons()
        """
        message_id = await handler.send_ordem_confirmacao(
            channel_id="123456789",
            symbol="BTCUSD",
            side="buy",
            quantity=0.5,
            price=50000.0,
            order_id="ord123"
        )

        # Assert - send_buttons foi chamado
        mock_discord_service.send_buttons.assert_called_once()
        call_kwargs = mock_discord_service.send_buttons.call_args[1]

        assert call_kwargs["channel_id"] == "123456789"
        assert "BTCUSD" in call_kwargs["title"]
        assert len(call_kwargs["buttons"]) == 2  # Confirmar e Cancelar

        # Assert - confirmação guardada
        pending = handler.get_pending_confirmation("ord123")
        assert pending is not None
        assert pending["symbol"] == "BTCUSD"
        assert pending["side"] == "buy"

        # Assert - retorna message_id
        assert message_id == "msg123"

    @pytest.mark.asyncio
    async def test_send_ordem_executada_remove_pendente(self, handler, mock_discord_service):
        """
        DOC: specs/discord-paper-integration/spec.md
        Scenario: Enviar ordem executada

        WHEN send_ordem_executada() é chamado
        THEN SHALL remover confirmação pendente e enviar embed
        """
        # Primeiro adiciona uma confirmação pendente
        handler._pending_confirmations["ord123"] = {"symbol": "BTC"}

        message_id = await handler.send_ordem_executada(
            channel_id="123456789",
            symbol="BTCUSD",
            side="buy",
            quantity=0.5,
            price=50000.0,
            order_id="ord123"
        )

        # Assert - pendente removido
        assert handler.get_pending_confirmation("ord123") is None

        # Assert - send_embed foi chamado
        mock_discord_service.send_embed.assert_called_once()
        call_kwargs = mock_discord_service.send_embed.call_args[1]

        assert call_kwargs["color"] == 3066993  # Verde para executada
        assert "executada" in call_kwargs["title"].lower()

    @pytest.mark.asyncio
    async def test_send_ordem_cancelada(self, handler, mock_discord_service):
        """
        DOC: specs/discord-paper-integration/spec.md
        Scenario: Enviar ordem cancelada

        WHEN send_ordem_cancelada() é chamado
        THEN SHALL enviar embed com status cancelada
        """
        # Primeiro adiciona uma confirmação pendente
        handler._pending_confirmations["ord123"] = {"symbol": "BTC"}

        message_id = await handler.send_ordem_cancelada(
            channel_id="123456789",
            order_id="ord123",
            reason="Usuário cancelou"
        )

        # Assert - send_embed foi chamado
        mock_discord_service.send_embed.assert_called_once()
        call_kwargs = mock_discord_service.send_embed.call_args[1]

        assert call_kwargs["color"] == 15158332  # Vermelho para cancelada
        assert "cancelada" in call_kwargs["title"].lower()

    @pytest.mark.asyncio
    async def test_handle_ordem_confirmation_confirmada(self, handler, mock_discord_service):
        """
        DOC: specs/discord-paper-integration/spec.md
        Scenario: Confirmar ordem

        WHEN handle_ordem_confirmation() é chamado com confirmed=True
        THEN SHALL processar ordem confirmada
        """
        # Adiciona confirmação pendente
        handler._pending_confirmations["ord123"] = {
            "channel_id": "123456789",
            "message_id": "msg456",
            "symbol": "BTCUSD",
            "side": "buy"
        }

        await handler.handle_ordem_confirmation(
            custom_id="confirm_order_ord123",
            confirmed=True
        )

        # Assert - send_message foi chamado confirmando
        mock_discord_service.send_message.assert_called_once()
        call_kwargs = mock_discord_service.send_message.call_args[1]

        assert "confirmada" in call_kwargs["content"].lower()

    @pytest.mark.asyncio
    async def test_handle_ordem_confirmation_rejeitada(self, handler, mock_discord_service):
        """
        DOC: specs/discord-paper-integration/spec.md
        Scenario: Rejeitar ordem

        WHEN handle_ordem_confirmation() é chamado com confirmed=False
        THEN SHALL processar ordem rejeitada
        """
        # Adiciona confirmação pendente
        handler._pending_confirmations["ord123"] = {
            "channel_id": "123456789",
            "message_id": "msg456",
            "symbol": "BTCUSD",
            "side": "buy"
        }

        await handler.handle_ordem_confirmation(
            custom_id="cancel_order_ord123",
            confirmed=False
        )

        # Assert - send_embed foi chamado (cancelada)
        mock_discord_service.send_embed.assert_called_once()
        # Assert - edit_message foi chamado (desabilitar botões)
        mock_discord_service.edit_message.assert_called_once()

    @pytest.mark.asyncio
    async def test_handle_ordem_confirmation_custom_id_invalido(self, handler, mock_discord_service):
        """
        DOC: specs/discord-paper-integration/spec.md
        Scenario: Custom ID inválido

        WHEN handle_ordem_confirmation() é chamado com custom_id malformado
        THEN SHALL não processar (log warning)
        """
        await handler.handle_ordem_confirmation(
            custom_id="invalid_id",
            confirmed=True
        )

        # Assert - nenhum método foi chamado
        mock_discord_service.send_message.assert_not_called()
        mock_discord_service.send_embed.assert_not_called()

    @pytest.mark.asyncio
    async def test_handle_ordem_confirmation_sem_pendente(self, handler, mock_discord_service):
        """
        DOC: specs/discord-paper-integration/spec.md
        Scenario: Confirmação sem pendência

        WHEN handle_ordem_confirmation() é chamado mas não há pendência
        THEN SHALL não processar
        """
        await handler.handle_ordem_confirmation(
            custom_id="confirm_order_ord999",
            confirmed=True
        )

        # Assert - nenhum método foi chamado
        mock_discord_service.send_message.assert_not_called()

    @pytest.mark.asyncio
    async def test_get_pending_confirmation_retorna_dados(self, handler):
        """
        DOC: specs/discord-paper-integration/spec.md
        Scenario: Buscar confirmação pendente

        WHEN get_pending_confirmation() é chamado com order_id válido
        THEN SHALL retornar dados pendentes
        """
        handler._pending_confirmations["ord123"] = {
            "symbol": "BTCUSD",
            "side": "buy"
        }

        pending = handler.get_pending_confirmation("ord123")

        assert pending is not None
        assert pending["symbol"] == "BTCUSD"

    @pytest.mark.asyncio
    async def test_clear_pending_confirmation_remove_dados(self, handler):
        """
        DOC: specs/discord-paper-integration/spec.md
        Scenario: Limpar confirmação pendente

        WHEN clear_pending_confirmation() é chamado
        THEN SHALL remover dados pendentes
        """
        handler._pending_confirmations["ord123"] = {"symbol": "BTC"}

        handler.clear_pending_confirmation("ord123")

        assert handler.get_pending_confirmation("ord123") is None

    @pytest.mark.asyncio
    async def test_send_ordem_confirmancia_sem_preco(self, handler, mock_discord_service):
        """
        DOC: specs/discord-paper-integration/spec.md
        Scenario: Ordem a mercado (sem preço)

        WHEN send_ordem_confirmacao() é chamado com price=None
        THEN SHALL processar corretamente
        """
        message_id = await handler.send_ordem_confirmacao(
            channel_id="123456789",
            symbol="BTCUSD",
            side="buy",
            quantity=0.5,
            price=None,  # Ordem a mercado
            order_id="ord123"
        )

        # Assert - processou com sucesso
        assert message_id == "msg123"
        assert handler.get_pending_confirmation("ord123") is not None
