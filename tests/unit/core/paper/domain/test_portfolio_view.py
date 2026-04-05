"""
Testes unitários para PortfolioView e PositionView.

DOC: src/core/paper/domain/portfolio_view.py - Views de portfolio multi-moeda.

Cenários:
- Criar PositionView com ticker, quantity, market_price
- Criar PortfolioView com múltiplas posições em moedas diferentes
- Calcular total por moeda (total_by_currency)
- Calcular total convertido para moeda alvo (total_converted)
"""
import pytest
from decimal import Decimal
from unittest.mock import AsyncMock

from src.core.paper.domain.currency import Currency
from src.core.paper.domain.money import Money
from src.core.paper.domain.quantity import Quantity, AssetType
from src.core.paper.domain.portfolio_view import PositionView, PortfolioView
from src.core.paper.ports.currency_converter_port import CurrencyConverterPort


class TestPositionView:
    """Testes para PositionView."""

    def test_cria_position_view_com_todos_campos(self):
        """PositionView deve ser criada com ticker, quantity, market_price."""
        position = PositionView(
            ticker="PETR4.SA",
            quantity=Quantity(
                value=Decimal("100"),
                precision=0,
                min_tick=Decimal("1"),
                asset_type=AssetType.STOCK,
            ),
            market_price=Money(Decimal("35.50"), Currency.BRL),
        )
        assert position.ticker == "PETR4.SA"
        assert position.quantity.value == Decimal("100")
        assert position.market_price.amount == Decimal("35.50")
        assert position.market_price.currency == Currency.BRL

    def test_market_value_calculado_automaticamente(self):
        """market_value deve ser quantity * market_price."""
        position = PositionView(
            ticker="PETR4.SA",
            quantity=Quantity(
                value=Decimal("100"),
                precision=0,
                min_tick=Decimal("1"),
                asset_type=AssetType.STOCK,
            ),
            market_price=Money(Decimal("35.50"), Currency.BRL),
        )
        # 100 * 35.50 = 3550.00
        assert position.market_value.amount == Decimal("3550.00")
        assert position.market_value.currency == Currency.BRL

    def test_cost_basis_opcional(self):
        """cost_basis deve ser opcional."""
        position = PositionView(
            ticker="PETR4.SA",
            quantity=Quantity(
                value=Decimal("100"),
                precision=0,
                min_tick=Decimal("1"),
                asset_type=AssetType.STOCK,
            ),
            market_price=Money(Decimal("35.50"), Currency.BRL),
            cost_basis=Money(Decimal("30.00"), Currency.BRL),
        )
        assert position.cost_basis is not None
        assert position.cost_basis.amount == Decimal("30.00")

    def test_pnl_calculado_se_cost_basis_presente(self):
        """pnl deve ser calculado se cost_basis presente."""
        position = PositionView(
            ticker="PETR4.SA",
            quantity=Quantity(
                value=Decimal("100"),
                precision=0,
                min_tick=Decimal("1"),
                asset_type=AssetType.STOCK,
            ),
            market_price=Money(Decimal("35.50"), Currency.BRL),
            cost_basis=Money(Decimal("30.00"), Currency.BRL),  # 100 * 30 = 3000
        )
        # market_value = 3550, cost = 3000, pnl = 550
        assert position.pnl is not None
        assert position.pnl.amount == Decimal("550.00")


class TestPortfolioView:
    """Testes para PortfolioView."""

    def test_cria_portfolio_view_com_posicoes(self):
        """PortfolioView deve ser criado com lista de posições."""
        positions = [
            PositionView(
                ticker="PETR4.SA",
                quantity=Quantity(
                    value=Decimal("100"),
                    precision=0,
                    min_tick=Decimal("1"),
                    asset_type=AssetType.STOCK,
                ),
                market_price=Money(Decimal("35.50"), Currency.BRL),
            ),
        ]
        portfolio = PortfolioView(positions=positions, base_currency=Currency.BRL)
        assert len(portfolio.positions) == 1
        assert portfolio.base_currency == Currency.BRL

    def test_total_by_currency_soma_por_moeda(self):
        """total_by_currency deve somar market_values por moeda."""
        positions = [
            PositionView(
                ticker="PETR4.SA",
                quantity=Quantity(
                    value=Decimal("100"),
                    precision=0,
                    min_tick=Decimal("1"),
                    asset_type=AssetType.STOCK,
                ),
                market_price=Money(Decimal("35.50"), Currency.BRL),  # 3550 BRL
            ),
            PositionView(
                ticker="VALE3.SA",
                quantity=Quantity(
                    value=Decimal("50"),
                    precision=0,
                    min_tick=Decimal("1"),
                    asset_type=AssetType.STOCK,
                ),
                market_price=Money(Decimal("70.00"), Currency.BRL),  # 3500 BRL
            ),
        ]
        portfolio = PortfolioView(positions=positions, base_currency=Currency.BRL)

        totals = portfolio.total_by_currency()
        assert Currency.BRL in totals
        assert totals[Currency.BRL].amount == Decimal("7050.00")

    @pytest.mark.asyncio
    async def test_total_converted_converte_tudo_para_moeda_alvo(self):
        """total_converted deve converter todas posições para moeda alvo."""
        positions = [
            PositionView(
                ticker="BTC-USD",
                quantity=Quantity(
                    value=Decimal("0.5"),
                    precision=8,
                    min_tick=Decimal("0.00000001"),
                    asset_type=AssetType.CRYPTO,
                ),
                market_price=Money(Decimal("85000"), Currency.USD),  # 42500 USD
            ),
            PositionView(
                ticker="PETR4.SA",
                quantity=Quantity(
                    value=Decimal("100"),
                    precision=0,
                    min_tick=Decimal("1"),
                    asset_type=AssetType.STOCK,
                ),
                market_price=Money(Decimal("35.50"), Currency.BRL),  # 3550 BRL
            ),
        ]
        portfolio = PortfolioView(positions=positions, base_currency=Currency.BRL)

        # Mock converter.convert() para retornar Money apropriado
        converter = AsyncMock(spec=CurrencyConverterPort)

        async def mock_convert(money: Money, to: Currency) -> Money:
            if money.currency == to:
                return money
            if money.currency == Currency.USD and to == Currency.BRL:
                return Money(money.amount * Decimal("5.0"), Currency.BRL)
            return money

        converter.convert.side_effect = mock_convert

        total_brl = await portfolio.total_converted(converter, Currency.BRL)

        # 42500 USD * 5 = 212500 BRL + 3550 BRL = 216050 BRL
        assert total_brl.currency == Currency.BRL
        assert total_brl.amount == Decimal("216050")

    @pytest.mark.asyncio
    async def test_total_converted_mesma_moeda_nao_converte(self):
        """total_converted para mesma moeda não deve chamar converter."""
        positions = [
            PositionView(
                ticker="PETR4.SA",
                quantity=Quantity(
                    value=Decimal("100"),
                    precision=0,
                    min_tick=Decimal("1"),
                    asset_type=AssetType.STOCK,
                ),
                market_price=Money(Decimal("35.50"), Currency.BRL),
            ),
        ]
        portfolio = PortfolioView(positions=positions, base_currency=Currency.BRL)

        converter = AsyncMock(spec=CurrencyConverterPort)

        # Mock convert para retornar mesmo money se mesma moeda
        async def mock_convert(money: Money, to: Currency) -> Money:
            if money.currency == to:
                return money
            raise ValueError("Should not convert same currency")

        converter.convert.side_effect = mock_convert

        total_brl = await portfolio.total_converted(converter, Currency.BRL)

        # Não deve chamar get_rate pois tudo já está em BRL
        converter.get_rate.assert_not_called()
        assert total_brl.amount == Decimal("3550.00")
