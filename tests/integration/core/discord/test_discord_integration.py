# -*- coding: utf-8 -*-
"""
Testes de Integração - Discord DDD Module.

Testes de integração entre as camadas DDD.
"""

import pytest
from decimal import Decimal

from src.core.discord.presentation.dto.tool_schemas import (
    SendEmbedInput,
    SendProgressInput,
    CreateThreadInput,
)
from src.core.integrations.discord_paper.projections.portfolio_projection import (
    PortfolioProjection,
)
from src.core.integrations.discord_paper.handlers.portfolio_ui_handler import (
    PortfolioUIHandler,
)


class TestPresentationLayerIntegration:
    """Testes de integração da Presentation Layer."""

    def test_tool_schema_validacao_reply(self):
        """Testa validação de schema de reply."""
        data = {
            "chat_id": "123456",
            "title": "Teste",
        }
        schema = SendEmbedInput.model_validate(data)
        assert schema.chat_id == "123456"

    def test_tool_schema_erro_sem_chat_id(self):
        """Testa erro quando chat_id não fornecido."""
        with pytest.raises(Exception):
            SendEmbedInput.model_validate({"title": "Teste"})


class TestIntegrationLayerIntegration:
    """Testes de integração da Integration Layer."""

    def test_portfolio_projection_para_dict(self):
        """Testa conversão de projection para dict Discord."""
        projection = PortfolioProjection()

        embed = projection.project_embed(
            balance_btc=Decimal("2.5"),
            balance_usd=Decimal("75000"),
            positions=[
                {"symbol": "BTC", "side": "long", "pnl_percent": 10.0},
                {"symbol": "ETH", "side": "short", "pnl_percent": -5.0}
            ],
            pnl_percent=7.5
        )

        embed_dict = embed.to_embed_dict()

        assert embed_dict["title"] == "📊 Portfolio Paper Trading"
        assert len(embed_dict["fields"]) >= 3  # Saldo BTC, USD, P&L
        assert embed_dict["color"] == 3066993  # Verde (lucro)

    def test_portfolio_menu_opcoes_dinamicas(self):
        """Testa opções dinâmicas de menu baseadas em estado."""
        projection = PortfolioProjection()

        # Sem posições
        menu_vazio = projection.project_menu(has_positions=False)
        valores_vazio = [opt["value"] for opt in menu_vazio.options]
        assert "close_position" not in valores_vazio

        # Com posições
        menu_com_pos = projection.project_menu(has_positions=True)
        valores_com = [opt["value"] for opt in menu_com_pos.options]
        assert "close_position" in valores_com


class TestEndToEndFlow:
    """Testes de fluxo completo DDD."""

    def test_fluxo_portfolio_embed(self):
        """Testa fluxo completo de geração de embed de portfolio."""
        # 1. Dados do domínio (Paper Trading)
        balance_btc = 1.5
        balance_usd = 50000
        positions = [{"symbol": "BTC", "side": "long", "pnl_percent": 15.0}]
        pnl = 15.0

        # 2. Projection (Integration Layer)
        projection = PortfolioProjection()
        embed = projection.project_embed(
            balance_btc=Decimal(str(balance_btc)),
            balance_usd=Decimal(str(balance_usd)),
            positions=positions,
            pnl_percent=pnl
        )

        # 3. Conversão para formato Discord (Presentation Layer)
        embed_dict = embed.to_embed_dict()

        # Validação
        assert embed.balance_btc == Decimal("1.5")
        assert embed_dict["title"] == "📊 Portfolio Paper Trading"
        assert embed_dict["color"] == 3066993  # Verde

    def test_fluxo_ordem_confirmacao(self):
        """Testa fluxo completo de confirmação de ordem."""
        from src.core.integrations.discord_paper.projections.ordem_projection import (
            OrdemProjection,
        )

        # 1. Dados da ordem (Paper Trading)
        symbol = "BTCUSD"
        side = "buy"
        quantity = 1.0
        price = 50000
        order_id = "ord123"

        # 2. Projection
        projection = OrdemProjection()
        embed, buttons = projection.project_ordem_confirmacao(
            symbol=symbol,
            side=side,
            quantity=Decimal(str(quantity)),
            price=Decimal(str(price)),
            order_id=order_id
        )

        # Validação
        assert embed.symbol == "BTCUSD"
        assert embed.status.name == "PENDENTE"
        assert len(buttons.buttons) == 2
        assert buttons.buttons[0]["label"] == "✅ Confirmar"
        assert buttons.buttons[1]["label"] == "❌ Cancelar"
