# -*- coding: utf-8 -*-
"""Testes unitários para CriarOrdemHandler."""
from decimal import Decimal
from unittest.mock import AsyncMock, MagicMock
import pytest

from src.core.paper.application.commands.criar_ordem import CriarOrdemCommand
from src.core.paper.application.handlers.criar_ordem_handler import CriarOrdemHandler, OrdemResult
from src.core.paper.adapters.brokers import SaldoInsuficienteError


class TestCriarOrdemHandler:
    """Testes para o handler de criação de ordens."""

    @pytest.fixture
    def broker_mock(self):
        """Broker mock para testes."""
        broker = AsyncMock()
        broker.enviar_ordem = AsyncMock(return_value="ordem-001")
        broker.consultar_ordem = AsyncMock(return_value={
            "id": "ordem-001",
            "ticker": "PETR4.SA",
            "lado": "COMPRA",
            "quantidade": 100,
            "preco_execucao": 30.50,
            "valor_total": 3050.0,
            "status": "EXECUTADA",
            "timestamp": "2026-03-27T10:00:00",
        })
        return broker

    @pytest.mark.asyncio
    async def test_ordem_compra_executada(self, broker_mock):
        """Teste: ordem de compra é executada com sucesso."""
        handler = CriarOrdemHandler(broker_mock)
        command = CriarOrdemCommand(
            ticker="PETR4.SA",
            lado="COMPRA",
            quantidade=100,
        )

        result = await handler.handle(command)

        assert isinstance(result, OrdemResult)
        assert result.id == "ordem-001"
        assert result.ticker == "PETR4.SA"
        assert result.lado == "COMPRA"
        assert result.quantidade == 100
        assert result.preco_execucao == 30.50
        assert result.status == "EXECUTADA"

        # Verifica que o broker foi chamado corretamente
        broker_mock.enviar_ordem.assert_called_once_with(
            ticker="PETR4.SA",
            lado="COMPRA",
            quantidade=100,
            preco_limite=None,
        )

    @pytest.mark.asyncio
    async def test_ordem_com_preco_limite(self, broker_mock):
        """Teste: ordem com preço limite é passada ao broker."""
        handler = CriarOrdemHandler(broker_mock)
        command = CriarOrdemCommand(
            ticker="VALE3.SA",
            lado="COMPRA",
            quantidade=50,
            preco_limite=Decimal("65.00"),
        )

        await handler.handle(command)

        broker_mock.enviar_ordem.assert_called_once_with(
            ticker="VALE3.SA",
            lado="COMPRA",
            quantidade=50,
            preco_limite=Decimal("65.00"),
        )

    @pytest.mark.asyncio
    async def test_saldo_insuficiente_rejeita(self, broker_mock):
        """Teste: saldo insuficiente lança exceção."""
        broker_mock.enviar_ordem = AsyncMock(
            side_effect=SaldoInsuficienteError("Saldo insuficiente")
        )
        handler = CriarOrdemHandler(broker_mock)
        command = CriarOrdemCommand(
            ticker="PETR4.SA",
            lado="COMPRA",
            quantidade=10000,  # Quantidade alta para causar saldo insuficiente
        )

        with pytest.raises(SaldoInsuficienteError, match="Saldo insuficiente"):
            await handler.handle(command)

    @pytest.mark.asyncio
    async def test_ordem_venda_executada(self, broker_mock):
        """Teste: ordem de venda é executada com sucesso."""
        broker_mock.consultar_ordem = AsyncMock(return_value={
            "id": "ordem-002",
            "ticker": "PETR4.SA",
            "lado": "VENDA",
            "quantidade": 100,
            "preco_execucao": 31.00,
            "valor_total": 3100.0,
            "status": "EXECUTADA",
            "timestamp": "2026-03-27T11:00:00",
        })
        handler = CriarOrdemHandler(broker_mock)
        command = CriarOrdemCommand(
            ticker="PETR4.SA",
            lado="VENDA",
            quantidade=100,
        )

        result = await handler.handle(command)

        assert result.lado == "VENDA"
        assert result.preco_execucao == 31.00


class TestConsultarCotacaoHandler:
    """Testes para o handler de consulta de cotação."""

    @pytest.fixture
    def feed_mock(self):
        """Feed mock para testes."""
        from src.core.paper.ports.data_feed_port import Cotacao
        feed = AsyncMock()
        feed.obter_cotacao = AsyncMock(return_value=Cotacao(
            ticker="PETR4.SA",
            preco=Decimal("30.50"),
            volume=1000000,
            timestamp="2026-03-27T10:00:00",
        ))
        return feed

    @pytest.mark.asyncio
    async def test_consulta_cotacao_retorna_dados(self, feed_mock):
        """Teste: consulta de cotação retorna dados."""
        from src.core.paper.application.queries.consultar_cotacao import ConsultarCotacaoQuery
        from src.core.paper.application.handlers.consultar_cotacao_handler import ConsultarCotacaoHandler

        handler = ConsultarCotacaoHandler(feed_mock)
        query = ConsultarCotacaoQuery(ticker="PETR4.SA")

        result = await handler.handle(query)

        assert result.ticker == "PETR4.SA"
        assert result.preco == Decimal("30.50")
        assert result.timestamp == "2026-03-27T10:00:00"


class TestConsultarPortfolioHandler:
    """Testes para o handler de consulta de portfolio."""

    @pytest.fixture
    def broker_mock(self):
        """Broker mock para testes."""
        from src.core.paper.domain.cashbook import CashBook
        from src.core.paper.domain.currency import Currency

        cashbook = CashBook.from_single_currency(Currency.BRL, Decimal("50000"))

        broker = AsyncMock()
        broker.cashbook = cashbook
        broker.saldo_inicial = Decimal("100000")
        broker.listar_posicoes_marcadas = AsyncMock(return_value=[
            {
                "ticker": "PETR4.SA",
                "quantidade": 100,
                "preco_medio": 30.0,
                "preco_atual": 32.0,
                "custo_total": 3000.0,
                "valor_atual": 3200.0,
                "pnl": 200.0,
                "pnl_percentual": 6.67,
            }
        ])
        return broker

    @pytest.fixture
    def feed_mock(self):
        """Feed mock para testes."""
        return AsyncMock()

    @pytest.mark.asyncio
    async def test_portfolio_com_pnl_calculado(self, broker_mock, feed_mock):
        """Teste: portfolio retorna PnL calculado."""
        from src.core.paper.application.queries.consultar_portfolio import ConsultarPortfolioQuery
        from src.core.paper.application.handlers.consultar_portfolio_handler import ConsultarPortfolioHandler
        from src.core.paper.ports.currency_converter_port import CurrencyConverterPort

        # Converter mock
        converter = AsyncMock(spec=CurrencyConverterPort)

        handler = ConsultarPortfolioHandler(broker_mock, feed_mock, converter)
        query = ConsultarPortfolioQuery()

        result = await handler.handle(query)

        # Saldo: 50000 + valor_posicoes: 3200 = 53200
        # PnL: 53200 - 100000 = -46800
        assert result.saldo_atual == 53200.0
        assert result.pnl == -46800.0
