"""
Testes unitários para ConsultarPortfolioHandler com suporte multi-moeda.

DOC: src/core/paper/application/handlers/consultar_portfolio_handler.py - Handler com base_currency.

Cenários:
- Consultar portfolio em moeda nativa (sem conversão)
- Consultar portfolio com conversão para outra moeda
- PnL calculado com conversão
"""
import pytest
from decimal import Decimal
from unittest.mock import AsyncMock, MagicMock, patch

from src.core.paper.application.queries.consultar_portfolio import (
    ConsultarPortfolioQuery,
)
from src.core.paper.domain.currency import Currency
from src.core.paper.domain.money import Money


class TestConsultarPortfolioHandler:
    """Testes para ConsultarPortfolioHandler com suporte multi-moeda."""

    @pytest.fixture
    def broker(self):
        """Broker mock."""
        broker = MagicMock()
        broker.saldo_inicial = Decimal("100000")
        broker.obter_saldo = AsyncMock(return_value=Decimal("50000"))
        broker.listar_posicoes_marcadas = AsyncMock(return_value=[
            {
                "ticker": "PETR4.SA",
                "quantidade": 100,
                "preco_medio": 30.00,
                "preco_atual": 35.50,
                "custo_total": 3000.0,
                "valor_atual": 3550.0,
                "pnl": 550.0,
                "pnl_percentual": 18.33,
            }
        ])
        return broker

    @pytest.fixture
    def feed(self):
        """DataFeed mock."""
        return MagicMock()

    @pytest.fixture
    def converter(self):
        """CurrencyConverter mock."""
        converter = AsyncMock()

        async def mock_convert(money: Money, to: Currency) -> Money:
            if money.currency == to:
                return money
            if money.currency == Currency.BRL and to == Currency.USD:
                return Money(money.amount * Decimal("0.2"), Currency.USD)
            if money.currency == Currency.USD and to == Currency.BRL:
                return Money(money.amount * Decimal("5.0"), Currency.BRL)
            return money

        converter.convert.side_effect = mock_convert
        return converter

    @pytest.mark.asyncio
    async def test_handle_sem_base_currency_retorna_em_moeda_nativa(
        self, broker, feed, converter
    ):
        """Sem base_currency, deve retornar valores em moeda nativa."""
        from src.core.paper.application.handlers.consultar_portfolio_handler import (
            ConsultarPortfolioHandler,
        )

        handler = ConsultarPortfolioHandler(broker, feed, converter)
        query = ConsultarPortfolioQuery(portfolio_id="test")

        result = await handler.handle(query)

        # saldo_atual = 50000 (saldo) + 3550 (posições) = 53550
        assert result.saldo_atual == pytest.approx(53550.0, rel=0.01)

    @pytest.mark.asyncio
    async def test_handle_com_base_currency_converte(
        self, broker, feed, converter
    ):
        """Com base_currency USD, deve converter BRL para USD."""
        from src.core.paper.application.handlers.consultar_portfolio_handler import (
            ConsultarPortfolioHandler,
        )

        handler = ConsultarPortfolioHandler(broker, feed, converter)
        query = ConsultarPortfolioQuery(
            portfolio_id="test",
            base_currency=Currency.USD,
        )

        result = await handler.handle(query)

        # saldo_atual = 53550 BRL * 0.2 = 10710 USD
        assert result.currency == Currency.USD
        assert result.saldo_atual == pytest.approx(10710.0, rel=1.0)

    @pytest.mark.asyncio
    async def test_pnl_com_conversao(
        self, broker, feed, converter
    ):
        """PnL deve ser calculado na moeda alvo."""
        from src.core.paper.application.handlers.consultar_portfolio_handler import (
            ConsultarPortfolioHandler,
        )

        # Setup: saldo 110000 BRL = 10% de lucro sobre 100000
        broker.obter_saldo = AsyncMock(return_value=Decimal("110000"))
        broker.listar_posicoes_marcadas = AsyncMock(return_value=[])

        handler = ConsultarPortfolioHandler(broker, feed, converter)
        query = ConsultarPortfolioQuery(
            portfolio_id="test",
            base_currency=Currency.USD,
        )

        result = await handler.handle(query)

        # saldo_inicial: 100000 BRL = 20000 USD
        # saldo_atual: 110000 BRL = 22000 USD
        # pnl: 2000 USD (10%)
        assert result.currency == Currency.USD
        assert result.pnl == pytest.approx(2000.0, rel=1.0)
        assert result.pnl_percentual == pytest.approx(10.0, rel=0.1)
