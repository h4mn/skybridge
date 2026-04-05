# -*- coding: utf-8 -*-
"""Testes de integração multi-moeda para PaperBroker."""
import pytest
from decimal import Decimal
from unittest.mock import AsyncMock, MagicMock

from src.core.paper.adapters.brokers.paper_broker import PaperBroker
from src.core.paper.adapters.data_feeds.yahoo_finance_feed import YahooFinanceFeed
from src.core.paper.adapters.currency.yahoo_currency_adapter import YahooCurrencyAdapter
from src.core.paper.domain.currency import Currency
from src.core.paper.domain.cashbook import CashBook


@pytest.fixture
def mock_feed():
    """Feed mock que retorna cotações."""
    feed = MagicMock(spec=YahooFinanceFeed)
    feed.conectar = AsyncMock()
    feed.desconectar = AsyncMock()

    async def mock_obter_cotacao(ticker: str):
        """Retorna cotação mockada."""
        from src.core.paper.ports.data_feed_port import Cotacao

        if ticker == "AAPL":
            return Cotacao(
                ticker="AAPL",
                preco=Decimal("175.50"),
                volume=1000000,
                timestamp="2026-03-29T20:00:00",
            )
        elif ticker == "PETR4.SA":
            return Cotacao(
                ticker="PETR4.SA",
                preco=Decimal("35.20"),
                volume=5000000,
                timestamp="2026-03-29T20:00:00",
            )
        elif ticker == "BTC-USD":
            return Cotacao(
                ticker="BTC-USD",
                preco=Decimal("85000"),
                volume=10000,
                timestamp="2026-03-29T20:00:00",
            )
        return Cotacao(ticker, Decimal("100"), 1000, "2026-03-29T20:00:00")

    feed.obter_cotacao = mock_obter_cotacao
    return feed


@pytest.fixture
def mock_converter():
    """Converter mock que retorna taxas fixas."""
    converter = MagicMock(spec=YahooCurrencyAdapter)
    converter.get_rate = AsyncMock()

    async def mock_get_rate(from_currency: Currency, to_currency: Currency) -> Decimal:
        """Retorna taxa de conversão mockada."""
        if from_currency == Currency.USD and to_currency == Currency.BRL:
            return Decimal("5.0")  # 1 USD = 5 BRL
        elif from_currency == Currency.BRL and to_currency == Currency.USD:
            return Decimal("0.2")  # 1 BRL = 0.2 USD
        return Decimal("1.0")

    converter.get_rate = mock_get_rate
    return converter


@pytest.fixture
def broker(mock_feed, mock_converter):
    """Broker configurado com cashbook multi-moeda."""
    cashbook = CashBook.from_single_currency(Currency.BRL, Decimal("100000"))
    broker = PaperBroker(
        feed=mock_feed,
        converter=mock_converter,
        cashbook=cashbook,
    )
    return broker


@pytest.mark.asyncio
async def test_comprar_ativo_usd_com_saldo_brl_converte(broker):
    """
    Dado: CashBook com BRL=100000, rate=1.0
    Quando: Comprar 10 AAPL a $175.50 USD ($1755 total)
    Então: Deve converter USD→BRL (5.0) e debitar BRL corretamente
    """
    # WHEN: Comprar AAPL (ativo em USD)
    ordem_id = await broker.enviar_ordem("AAPL", "COMPRA", 10)

    # THEN: Ordem executada
    assert ordem_id is not None

    # Cashbook deve ter:
    # - BRL reduzido de 100000 para (100000 - 1755*5.0) = 91225
    brl_entry = broker.cashbook.get(Currency.BRL)
    assert brl_entry.amount == Decimal("91225")  # 100000 - 1755*5.0

    # USD adicionado com conversão (1755 USD, rate 5.0)
    usd_entry = broker.cashbook.get(Currency.USD)
    assert usd_entry.amount == Decimal("1755")
    assert usd_entry.conversion_rate == Decimal("5.0")

    # Posição criada
    posicoes = broker.listar_posicoes()
    assert len(posicoes) == 1
    assert posicoes[0]["ticker"] == "AAPL"
    assert posicoes[0]["quantidade"] == 10


@pytest.mark.asyncio
async def test_vender_ativo_usd_creditaria_usd(broker):
    """
    Dado: CashBook com BRL=100000 e posição AAPL=10
    Quando: Vender 5 AAPL a $175.50 USD
    Então: Creditar USD no cashbook (não BRL)
    """
    # SETUP: Comprar AAPL primeiro
    await broker.enviar_ordem("AAPL", "COMPRA", 10)
    broker.cashbook.add(Currency.USD, Decimal("5000"), Decimal("5.0"))

    # WHEN: Vender metade das ações
    await broker.enviar_ordem("AAPL", "VENDA", 5)

    # THEN: USD creditado (5 * 175.50 = 877.50)
    # Total USD = 1755 (compra) + 5000 (extra) + 877.50 (venda) = 7632.50
    usd_entry = broker.cashbook.get(Currency.USD)
    assert usd_entry.amount == Decimal("7632.50")

    # Posição reduzida
    posicoes = broker.listar_posicoes()
    assert posicoes[0]["quantidade"] == 5


@pytest.mark.asyncio
async def test_comprar_ativo_brl_nao_converte(broker):
    """
    Dado: CashBook com BRL=100000
    Quando: Comprar PETR4.SA (ativo em BRL)
    Então: Debitar BRL diretamente, sem conversão
    """
    # WHEN: Comprar PETR4.SA
    await broker.enviar_ordem("PETR4.SA", "COMPRA", 100)

    # THEN: BRL debitado (100 * 35.20 = 3520)
    brl_entry = broker.cashbook.get(Currency.BRL)
    assert brl_entry.amount == Decimal("96480")  # 100000 - 3520

    # USD não deve ter sido tocado
    usd_entry = broker.cashbook.get(Currency.USD)
    assert usd_entry.amount == Decimal("0")


@pytest.mark.asyncio
async def test_saldo_insuficiente_mesmo_com_conversao(broker):
    """
    Dado: CashBook com BRL=1000 (insuficiente)
    Quando: Tentar comprar 10 BTC a $85000 USD ($850000 total)
    Então: Deve lançar SaldoInsuficienteError (mesmo com conversão)
    """
    # SETUP: Reduzir saldo
    broker.cashbook.subtract(Currency.BRL, Decimal("99000"))

    # WHEN/THEN: Tentar comprar BTC deve falhar
    from src.core.paper.adapters.brokers.paper_broker import SaldoInsuficienteError

    with pytest.raises(SaldoInsuficienteError):
        await broker.enviar_ordem("BTC-USD", "COMPRA", 10)


@pytest.mark.asyncio
async def test_total_em_base_currency_soma_todas_moedas(broker):
    """
    Dado: CashBook com BRL=50000 (rate=1.0) e USD=1000 (rate=5.0)
    Quando: Calcular total_in_base_currency
    Então: Deve retornar 50000 + (1000 * 5.0) = 55000
    """
    # SETUP: Configurar cashbook com duas moedas
    broker.cashbook = CashBook.from_single_currency(Currency.BRL, Decimal("50000"))
    broker.cashbook.add(Currency.USD, Decimal("1000"), Decimal("5.0"))

    # THEN: Total em base currency
    assert broker.cashbook.total_in_base_currency == Decimal("55000")


@pytest.mark.asyncio
async def test_posicoes_marcadas_mo_moneda_correta(broker):
    """
    Dado: Posições em AAPL (USD) e PETR4 (BRL)
    Quando: Listar posições marcadas
    Então: Cada posição deve ter campo 'currency' correto
    """
    # SETUP: Criar posições
    await broker.enviar_ordem("AAPL", "COMPRA", 10)
    await broker.enviar_ordem("PETR4.SA", "COMPRA", 100)

    # WHEN: Listar posições marcadas
    posicoes = await broker.listar_posicoes_marcadas()

    # THEN: Verificar moedas
    aapl_pos = next(p for p in posicoes if p["ticker"] == "AAPL")
    assert aapl_pos["currency"] == "USD"

    petr4_pos = next(p for p in posicoes if p["ticker"] == "PETR4.SA")
    assert petr4_pos["currency"] == "BRL"


@pytest.mark.asyncio
async def test_pnl_calculado_na_moeda_do_ativo(broker):
    """
    Dado: Posição em AAPL (USD) com preço médio $175.50
    Quando: Preço atual é $175.50 (sem variação)
    Então: PnL deve ser 0 (comprei e vendi pelo mesmo preço)
    """
    # SETUP: Comprar AAPL
    await broker.enviar_ordem("AAPL", "COMPRA", 10)

    # WHEN: Listar posições marcadas
    posicoes = await broker.listar_posicoes_marcadas()
    aapl_pos = next(p for p in posicoes if p["ticker"] == "AAPL")

    # THEN: PnL em USD (sem variação de preço)
    assert aapl_pos["pnl"] == 0.0  # Preço de compra = preço atual
    assert aapl_pos["currency"] == "USD"


@pytest.mark.asyncio
async def test_conversao_rate_atualizada_em_operacoes(broker):
    """
    Dado: Taxa de conversão 5.0 BRL/USD
    Quando: Comprar ativo USD com saldo BRL
    Então: Cashbook deve ter entrada USD criada com conversion_rate
    """
    # WHEN: Comprar AAPL (ativo em USD)
    await broker.enviar_ordem("AAPL", "COMPRA", 5)

    # THEN: Entry USD criada com rate correto
    usd_entry = broker.cashbook.get(Currency.USD)
    assert usd_entry.amount > 0  # Deve ter saldo USD
    assert usd_entry.conversion_rate == Decimal("5.0")  # Rate aplicada

    # BRL foi debitado (convertido)
    brl_entry = broker.cashbook.get(Currency.BRL)
    # BRL inicial 100000 - (5 * 175.50 * 5.0) = 95612.5
    assert brl_entry.amount < Decimal("100000")  # Foi debitado
