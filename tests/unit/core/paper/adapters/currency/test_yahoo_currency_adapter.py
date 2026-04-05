"""
Testes unitários para YahooCurrencyAdapter.

DOC: src/core/paper/adapters/currency/yahoo_currency_adapter.py - Adapter Yahoo Finance.

Cenários:
- Mapear pares de moeda para tickers Yahoo
- Buscar taxa de câmbio do Yahoo
- Cache com TTL 5min
- Fallback para taxa em cache quando Yahoo indisponível
"""
import pytest
from decimal import Decimal
from unittest.mock import AsyncMock, patch, MagicMock
from datetime import datetime, timedelta

from src.core.paper.domain.currency import Currency
from src.core.paper.domain.money import Money
from src.core.paper.adapters.currency.yahoo_currency_adapter import (
    YahooCurrencyAdapter,
    YAHOO_TICKER_MAP,
)


class TestYahooTickerMap:
    """Testes para mapeamento de tickers Yahoo."""

    def test_mapeia_usd_brl(self):
        """USD para BRL deve mapear para BRL=X."""
        assert YAHOO_TICKER_MAP[(Currency.USD, Currency.BRL)] == "BRL=X"

    def test_mapeia_eur_brl(self):
        """EUR para BRL deve mapear para EURBRL=X."""
        assert YAHOO_TICKER_MAP[(Currency.EUR, Currency.BRL)] == "EURBRL=X"

    def test_mapeia_eur_usd(self):
        """EUR para USD deve mapear para EURUSD=X."""
        assert YAHOO_TICKER_MAP[(Currency.EUR, Currency.USD)] == "EURUSD=X"

    def test_mapeia_gbp_usd(self):
        """GBP para USD deve mapear para GBPUSD=X."""
        assert YAHOO_TICKER_MAP[(Currency.GBP, Currency.USD)] == "GBPUSD=X"

    def test_mapeia_btc_usd(self):
        """BTC para USD deve mapear para BTC-USD."""
        assert YAHOO_TICKER_MAP[(Currency.BTC, Currency.USD)] == "BTC-USD"

    def test_mapeia_eth_usd(self):
        """ETH para USD deve mapear para ETH-USD."""
        assert YAHOO_TICKER_MAP[(Currency.ETH, Currency.USD)] == "ETH-USD"


class TestYahooCurrencyAdapterGetTicker:
    """Testes para método _get_ticker."""

    def test_get_ticker_retorna_ticker_mapeado(self):
        """_get_ticker deve retornar ticker mapeado."""
        adapter = YahooCurrencyAdapter()
        ticker = adapter._get_ticker(Currency.USD, Currency.BRL)
        assert ticker == "BRL=X"

    def test_get_ticker_inverte_se_nao_encontrado(self):
        """_get_ticker deve inverter par se não encontrar direto."""
        adapter = YahooCurrencyAdapter()
        # BRL -> USD não está mapeado diretamente, mas USD -> BRL está
        ticker = adapter._get_ticker(Currency.BRL, Currency.USD)
        # Deve retornar o inverso e depois inverter a taxa
        assert ticker == "BRL=X"  # Retorna ticker do par inverso


class TestYahooCurrencyAdapterGetRate:
    """Testes para método get_rate."""

    @pytest.mark.asyncio
    async def test_get_rate_retorna_taxa_do_yahoo(self):
        """get_rate deve buscar taxa do Yahoo Finance."""
        adapter = YahooCurrencyAdapter()

        # Mock do yfinance no módulo do adapter
        with patch(
            "src.core.paper.adapters.currency.yahoo_currency_adapter.yf.Ticker"
        ) as mock_ticker_class:
            mock_ticker = MagicMock()

            # Cria mock do DataFrame que simula hist["Close"].iloc[-1]
            mock_close_series = MagicMock()
            mock_close_series.iloc = [5.25]  # Simula Series.iloc[-1]
            mock_history = MagicMock()
            mock_history.empty = False
            mock_history.__getitem__ = lambda self, key: mock_close_series
            mock_ticker.history.return_value = mock_history
            mock_ticker_class.return_value = mock_ticker

            rate = await adapter.get_rate(Currency.USD, Currency.BRL)
            assert rate == Decimal("5.25")

    @pytest.mark.asyncio
    async def test_get_rate_usa_cache_se_valido(self):
        """get_rate deve usar cache se ainda válido."""
        adapter = YahooCurrencyAdapter()

        # Popula cache manualmente
        adapter._cache[(Currency.USD, Currency.BRL)] = {
            "rate": Decimal("5.0"),
            "timestamp": datetime.now(),
        }

        # Não deve chamar yfinance
        with patch("yfinance.Ticker") as mock_ticker:
            rate = await adapter.get_rate(Currency.USD, Currency.BRL)
            mock_ticker.assert_not_called()
            assert rate == Decimal("5.0")

    @pytest.mark.asyncio
    async def test_get_rate_busca_nova_se_cache_expirado(self):
        """get_rate deve buscar nova taxa se cache expirado (>5min)."""
        adapter = YahooCurrencyAdapter()

        # Popula cache expirado
        adapter._cache[(Currency.USD, Currency.BRL)] = {
            "rate": Decimal("4.0"),  # Taxa antiga
            "timestamp": datetime.now() - timedelta(minutes=10),  # 10min atrás
        }

        with patch(
            "src.core.paper.adapters.currency.yahoo_currency_adapter.yf.Ticker"
        ) as mock_ticker_class:
            mock_ticker = MagicMock()

            # Cria mock do DataFrame que simula hist["Close"].iloc[-1]
            mock_close_series = MagicMock()
            mock_close_series.iloc = [5.50]  # Simula Series.iloc[-1]
            mock_history = MagicMock()
            mock_history.empty = False
            mock_history.__getitem__ = lambda self, key: mock_close_series
            mock_ticker.history.return_value = mock_history
            mock_ticker_class.return_value = mock_ticker

            rate = await adapter.get_rate(Currency.USD, Currency.BRL)
            assert rate == Decimal("5.50")  # Nova taxa, não a do cache

    @pytest.mark.asyncio
    async def test_get_rate_mesma_moeda_retorna_1(self):
        """get_rate para mesma moeda deve retornar 1."""
        adapter = YahooCurrencyAdapter()
        rate = await adapter.get_rate(Currency.USD, Currency.USD)
        assert rate == Decimal("1")


class TestYahooCurrencyAdapterConvert:
    """Testes para método convert."""

    @pytest.mark.asyncio
    async def test_convert_usd_para_brl(self):
        """convert deve converter USD para BRL."""
        adapter = YahooCurrencyAdapter()

        with patch.object(adapter, "get_rate", new_callable=AsyncMock) as mock_get_rate:
            mock_get_rate.return_value = Decimal("5.0")

            money = Money(Decimal("100"), Currency.USD)
            converted = await adapter.convert(money, Currency.BRL)

            assert converted.amount == Decimal("500")
            assert converted.currency == Currency.BRL

    @pytest.mark.asyncio
    async def test_convert_mesma_moeda_retorna_igual(self):
        """convert para mesma moeda deve retornar igual."""
        adapter = YahooCurrencyAdapter()
        money = Money(Decimal("100"), Currency.BRL)
        converted = await adapter.convert(money, Currency.BRL)
        assert converted.amount == Decimal("100")
        assert converted.currency == Currency.BRL
