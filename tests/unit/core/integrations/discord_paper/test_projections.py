# -*- coding: utf-8 -*-
"""
Testes de Projections - Discord → Paper Integration.

Valida projections de portfolio e ordens.
"""

import pytest
from decimal import Decimal

from src.core.integrations.discord_paper.projections.portfolio_projection import (
    PortfolioProjection,
    PortfolioEmbed,
    PortfolioMenuOptions,
)
from src.core.integrations.discord_paper.projections.ordem_projection import (
    OrdemProjection,
    OrdemEmbed,
    OrdemStatus,
)


class TestPortfolioProjection:
    """Testes de projection de portfolio."""

    def test_project_embed_cria_instancia(self):
        """Testa que projection cria embed válido."""
        projection = PortfolioProjection()

        embed = projection.project_embed(
            balance_btc=Decimal("1.5"),
            balance_usd=Decimal("50000"),
            positions=[],
            pnl_percent=15.5
        )

        assert isinstance(embed, PortfolioEmbed)
        assert embed.balance_btc == Decimal("1.5")
        assert embed.pnl_percent == 15.5

    def test_project_embed_cor_verde_para_lucro(self):
        """Testa que lucro usa cor verde."""
        projection = PortfolioProjection()

        embed = projection.project_embed(
            balance_btc=Decimal("1.0"),
            balance_usd=Decimal("50000"),
            positions=[],
            pnl_percent=10.0
        )

        assert embed.color == 3066993  # Verde

    def test_project_embed_cor_vermelha_para_prejuizo(self):
        """Testa que prejuízo usa cor vermelha."""
        projection = PortfolioProjection()

        embed = projection.project_embed(
            balance_btc=Decimal("1.0"),
            balance_usd=Decimal("50000"),
            positions=[],
            pnl_percent=-5.0
        )

        assert embed.color == 15158332  # Vermelho

    def test_project_menu_com_posicoes(self):
        """Testa que menu com posições tem mais opções."""
        projection = PortfolioProjection()

        menu = projection.project_menu(has_positions=True)

        assert len(menu.options) >= 4
        opcoes_values = [opt["value"] for opt in menu.options]
        assert "portfolio_positions" in opcoes_values
        assert "close_position" in opcoes_values

    def test_project_menu_sem_posicoes(self):
        """Testa que menu sem posições tem opções básicas."""
        projection = PortfolioProjection()

        menu = projection.project_menu(has_positions=False)

        opcoes_values = [opt["value"] for opt in menu.options]
        assert "portfolio_positions" not in opcoes_values
        assert "close_position" not in opcoes_values


class TestOrdemProjection:
    """Testes de projection de ordens."""

    def test_project_ordem_confirmacao(self):
        """Testa projection de ordem pendente de confirmação."""
        projection = OrdemProjection()

        embed, buttons = projection.project_ordem_confirmacao(
            symbol="BTCUSD",
            side="buy",
            quantity=Decimal("0.5"),
            price=Decimal("50000"),
            order_id="ord123"
        )

        assert isinstance(embed, OrdemEmbed)
        assert embed.symbol == "BTCUSD"
        assert embed.status == OrdemStatus.PENDENTE
        assert len(buttons.buttons) == 2  # Confirmar e Cancelar

    def test_project_ordem_executada(self):
        """Testa projection de ordem executada."""
        projection = OrdemProjection()

        embed = projection.project_ordem_executada(
            symbol="ETHUSD",
            side="sell",
            quantity=Decimal("2.0"),
            price=Decimal("3000"),
            order_id="ord456"
        )

        assert embed.status == OrdemStatus.EXECUTADA
        assert embed.color == 3066993  # Verde

    def test_project_ordem_cancelada(self):
        """Testa projection de ordem cancelada."""
        projection = OrdemProjection()

        embed = projection.project_ordem_cancelada(
            order_id="ord789",
            reason="Usuário cancelou"
        )

        assert embed.status == OrdemStatus.CANCELADA
        assert embed.color == 15158332  # Vermelho

    def test_ordem_embed_to_dict(self):
        """Testa conversão de embed para dict."""
        projection = OrdemProjection()

        embed, _ = projection.project_ordem_confirmacao(
            symbol="BTCUSD",
            side="buy",
            quantity=Decimal("1.0"),
            price=Decimal("50000"),
            order_id="ord123"
        )

        embed_dict = embed.to_embed_dict()

        assert "title" in embed_dict
        assert "color" in embed_dict
        assert "fields" in embed_dict
        assert len(embed_dict["fields"]) > 0
