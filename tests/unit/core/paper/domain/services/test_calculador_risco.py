"""
Testes unitários para CalculadorDeRisco.

Testa cálculo de métricas de risco:
- VaR (Value at Risk 95%)
- Exposição total
- Concentração por ativo
- Drawdown
"""

from decimal import Decimal
from datetime import datetime, timedelta

import pytest

from src.core.paper.domain.currency import Currency
from src.core.paper.domain.money import Money
from src.core.paper.domain.portfolio_view import PortfolioView, PositionView
from src.core.paper.domain.quantity import Quantity, AssetType
from src.core.paper.domain.services.calculador_risco import (
    CalculadorDeRisco,
    MetricasRisco,
)


class TestCalculadorDeRisco:
    """Testes para CalculadorDeRisco."""

    @pytest.fixture
    def calculador(self):
        """Cria calculador de risco."""
        return CalculadorDeRisco()

    @pytest.fixture
    def portfolio_simples(self):
        """Portfolio com 2 posições."""
        return PortfolioView(
            positions=[
                PositionView(
                    ticker="PETR4.SA",
                    quantity=Quantity(Decimal("100"), precision=0, min_tick=Decimal("1"), asset_type=AssetType.STOCK),
                    market_price=Money(Decimal("30.00"), Currency.BRL),
                    cost_basis=Money(Decimal("25.00"), Currency.BRL),
                ),
                PositionView(
                    ticker="VALE3.SA",
                    quantity=Quantity(Decimal("200"), precision=0, min_tick=Decimal("1"), asset_type=AssetType.STOCK),
                    market_price=Money(Decimal("70.00"), Currency.BRL),
                    cost_basis=Money(Decimal("65.00"), Currency.BRL),
                ),
            ],
            base_currency=Currency.BRL,
            cash=Money(Decimal("10000"), Currency.BRL),
        )

    def test_calcular_exposicao_total(self, calculador, portfolio_simples):
        """Exposição total = soma dos market_values."""
        metricas = calculador.calcular(portfolio_simples)

        # PETR4: 100 * 30 = 3000
        # VALE3: 200 * 70 = 14000
        # Total posições: 17000
        assert metricas.exposicao_total == Decimal("17000")

    def test_calcular_concentracao_por_ativo(self, calculador, portfolio_simples):
        """Concentração = % de cada ativo na exposição total."""
        metricas = calculador.calcular(portfolio_simples)

        # PETR4: 3000 / 17000 = 17.65%
        # VALE3: 14000 / 17000 = 82.35%
        assert metricas.concentracao["PETR4.SA"] == pytest.approx(Decimal("0.1765"), rel=Decimal("0.001"))
        assert metricas.concentracao["VALE3.SA"] == pytest.approx(Decimal("0.8235"), rel=Decimal("0.001"))

    def test_calcular_var_95_simples(self, calculador, portfolio_simples):
        """VaR 95% - simplificado (5% de perda máxima estimada)."""
        metricas = calculador.calcular(portfolio_simples)

        # VaR simplificado: 5% da exposição como risco máximo
        # 17000 * 0.05 = 850
        assert metricas.var_95 == pytest.approx(Decimal("850"), rel=Decimal("0.01"))

    def test_calcular_drawdown_simples(self, calculador, portfolio_simples):
        """Drawdown = queda desde o topo (pico)."""
        metricas = calculador.calcular(portfolio_simples)

        # Sem histórico de pico, drawdown é 0
        assert metricas.drawdown == Decimal("0")

    def test_calcular_drawdown_com_pico(self, calculador):
        """Drawdown com pico histórico definido."""
        portfolio = PortfolioView(
            positions=[
                PositionView(
                    ticker="PETR4.SA",
                    quantity=Quantity(Decimal("100"), precision=0, min_tick=Decimal("1"), asset_type=AssetType.STOCK),
                    market_price=Money(Decimal("30.00"), Currency.BRL),
                    cost_basis=Money(Decimal("25.00"), Currency.BRL),
                ),
            ],
            base_currency=Currency.BRL,
        )

        # Definir pico histórico
        metricas = calculador.calcular(
            portfolio,
            pico_historico=Decimal("4000")  # Pico foi 4000
        )

        # Valor atual: 3000
        # Drawdown: (4000 - 3000) / 4000 = 25%
        assert metricas.drawdown == pytest.approx(Decimal("0.25"), rel=Decimal("0.01"))

    def test_portfolio_vazio_retorna_metricas_zero(self, calculador):
        """Portfolio vazio deve ter exposição zero."""
        portfolio = PortfolioView(
            positions=[],
            base_currency=Currency.BRL,
            cash=Money(Decimal("10000"), Currency.BRL),
        )

        metricas = calculador.calcular(portfolio)

        assert metricas.exposicao_total == Decimal("0")
        assert metricas.var_95 == Decimal("0")
        assert len(metricas.concentracao) == 0

    def test_calcular_com_multi_moeda(self, calculador):
        """Portfolio com múltiplas moedas."""
        portfolio = PortfolioView(
            positions=[
                PositionView(
                    ticker="BTC-USD",
                    quantity=Quantity(Decimal("1"), precision=8, min_tick=Decimal("0.00000001"), asset_type=AssetType.CRYPTO),
                    market_price=Money(Decimal("50000"), Currency.USD),
                    cost_basis=Money(Decimal("45000"), Currency.USD),
                ),
                PositionView(
                    ticker="PETR4.SA",
                    quantity=Quantity(Decimal("100"), precision=0, min_tick=Decimal("1"), asset_type=AssetType.STOCK),
                    market_price=Money(Decimal("30.00"), Currency.BRL),
                    cost_basis=Money(Decimal("25.00"), Currency.BRL),
                ),
            ],
            base_currency=Currency.BRL,
        )

        metricas = calculador.calcular(portfolio)

        # Exposição total (soma simplificada, sem conversão)
        # 50000 USD + 3000 BRL
        # Nota: em produção precisaria converter para moeda base
        assert metricas.exposicao_total > 0
        assert len(metricas.concentracao) == 2


class TestMetricasRisco:
    """Testes para value object MetricasRisco."""

    def test_metricas_risco_imutavel(self):
        """MetricasRisco deve ser imutável (frozen)."""
        from dataclasses import FrozenInstanceError

        metricas = MetricasRisco(
            exposicao_total=Decimal("1000"),
            var_95=Decimal("50"),
            drawdown=Decimal("0.10"),
            concentracao={"ATIVO": Decimal("0.5")},
        )

        # Tentar modificar deve levantar erro
        with pytest.raises(FrozenInstanceError):
            metricas.exposicao_total = Decimal("2000")
