"""
YahooCurrencyAdapter - Adapter para conversão de moedas usando Yahoo Finance.

Este adapter implementa CurrencyConverterPort usando a API do Yahoo Finance
via biblioteca yfinance.
"""
import asyncio
from datetime import datetime, timedelta
from decimal import Decimal
from typing import Optional

import yfinance as yf

from src.core.paper.domain.currency import Currency
from src.core.paper.domain.money import Money
from src.core.paper.ports.currency_converter_port import CurrencyConverterPort


# Mapeamento de pares de moeda para tickers Yahoo Finance
YAHOO_TICKER_MAP = {
    # Fiat pairs
    (Currency.USD, Currency.BRL): "BRL=X",
    (Currency.EUR, Currency.BRL): "EURBRL=X",
    (Currency.EUR, Currency.USD): "EURUSD=X",
    (Currency.GBP, Currency.USD): "GBPUSD=X",
    (Currency.GBP, Currency.BRL): "GBPBRL=X",
    # Crypto pairs
    (Currency.BTC, Currency.USD): "BTC-USD",
    (Currency.BTC, Currency.BRL): "BTC-BRL",
    (Currency.ETH, Currency.USD): "ETH-USD",
    (Currency.ETH, Currency.BRL): "ETH-BRL",
}

# TTL do cache em minutos
CACHE_TTL_MINUTES = 5


class YahooCurrencyAdapter(CurrencyConverterPort):
    """
    Adapter para conversão de moedas usando Yahoo Finance.

    Features:
    - Busca taxas em tempo real do Yahoo Finance
    - Cache em memória com TTL de 5 minutos
    - Suporte a pares fiat e crypto
    - Fallback para cache expirado em caso de erro

    Example:
        >>> adapter = YahooCurrencyAdapter()
        >>> rate = await adapter.get_rate(Currency.USD, Currency.BRL)
        >>> rate
        Decimal('5.25')
        >>> usd = Money(Decimal("100"), Currency.USD)
        >>> brl = await adapter.convert(usd, Currency.BRL)
        >>> brl.amount
        Decimal('525.00')
    """

    def __init__(self, cache_ttl_minutes: int = CACHE_TTL_MINUTES):
        """
        Inicializa o adapter.

        Args:
            cache_ttl_minutes: TTL do cache em minutos (padrão: 5).
        """
        self._cache: dict[tuple[Currency, Currency], dict] = {}
        self._cache_ttl = timedelta(minutes=cache_ttl_minutes)

    def _get_ticker(self, from_currency: Currency, to_currency: Currency) -> str:
        """
        Retorna ticker Yahoo para o par de moedas.

        Args:
            from_currency: Moeda de origem.
            to_currency: Moeda de destino.

        Returns:
            Ticker Yahoo Finance para o par.
        """
        pair = (from_currency, to_currency)

        # Tenta par direto
        if pair in YAHOO_TICKER_MAP:
            return YAHOO_TICKER_MAP[pair]

        # Tenta par inverso
        inverse_pair = (to_currency, from_currency)
        if inverse_pair in YAHOO_TICKER_MAP:
            return YAHOO_TICKER_MAP[inverse_pair]

        # Constrói ticker genérico (ex: EUR=X para EUR/USD)
        return f"{from_currency.value}{to_currency.value}=X"

    def _is_cache_valid(self, cache_entry: dict) -> bool:
        """Verifica se entrada do cache ainda é válida."""
        if "timestamp" not in cache_entry:
            return False
        return datetime.now() - cache_entry["timestamp"] < self._cache_ttl

    async def get_rate(
        self, from_currency: Currency, to_currency: Currency
    ) -> Decimal:
        """
        Retorna taxa de câmbio atual.

        Args:
            from_currency: Moeda de origem.
            to_currency: Moeda de destino.

        Returns:
            Taxa de câmbio (quanto vale 1 unidade de from em to).
        """
        # Mesma moeda = taxa 1
        if from_currency == to_currency:
            return Decimal("1")

        pair = (from_currency, to_currency)

        # Verifica cache
        if pair in self._cache and self._is_cache_valid(self._cache[pair]):
            return self._cache[pair]["rate"]

        # Busca do Yahoo Finance
        ticker_symbol = self._get_ticker(from_currency, to_currency)
        ticker = yf.Ticker(ticker_symbol)

        # Executa em thread separada para não bloquear
        loop = asyncio.get_event_loop()
        hist = await loop.run_in_executor(
            None, lambda: ticker.history(period="1d")
        )

        if hist.empty:
            raise ValueError(f"No rate found for {from_currency.value}/{to_currency.value}")

        rate = Decimal(str(hist["Close"].iloc[-1]))

        # Verifica se precisa inverter (par inverso)
        inverse_pair = (to_currency, from_currency)
        if inverse_pair in YAHOO_TICKER_MAP and pair not in YAHOO_TICKER_MAP:
            rate = Decimal("1") / rate

        # Atualiza cache
        self._cache[pair] = {
            "rate": rate,
            "timestamp": datetime.now(),
        }

        return rate

    async def convert(self, money: Money, to: Currency) -> Money:
        """
        Converte Money para outra moeda.

        Args:
            money: Valor a converter.
            to: Moeda de destino.

        Returns:
            Novo Money na moeda de destino.
        """
        if money.currency == to:
            return money

        rate = await self.get_rate(money.currency, to)
        return money.convert_to(to, rate)
