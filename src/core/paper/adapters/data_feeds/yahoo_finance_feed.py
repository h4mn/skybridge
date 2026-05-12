"""Adapter - Yahoo Finance Feed.

Implementa DataFeedPort usando yfinance (gratuito, sem API key).
Suporta ativos da B3 (PETR4.SA), cripto (BTC-USD) e mercado americano.
"""
from decimal import Decimal
from typing import AsyncIterator
import asyncio
import logging
import time

import yfinance as yf

from ...ports.data_feed_port import DataFeedPort, Cotacao

logger = logging.getLogger(__name__)


class YahooFinanceFeed(DataFeedPort):
    """Feed de dados via Yahoo Finance.

    Não requer autenticação. Dados com delay de ~15min para B3,
    próximo de real-time para cripto.

    Exemplos de tickers:
        B3:    PETR4.SA, VALE3.SA, ITUB4.SA, BBDC4.SA
        Cripto: BTC-USD, ETH-USD, SOL-USD
        EUA:   AAPL, MSFT, TSLA
    """

    def __init__(self, intervalo_stream_segundos: int = 5, ttl_seconds: float = 30.0):
        self._intervalo = intervalo_stream_segundos
        self._conectado = False
        self._ttl = ttl_seconds
        self._cache: dict[str, tuple[float, Cotacao]] = {}

    async def conectar(self) -> None:
        self._conectado = True

    async def desconectar(self) -> None:
        self._conectado = False

    async def obter_cotacao(self, ticker: str) -> Cotacao:
        """Retorna a cotação mais recente do ativo com TTL cache e backoff."""
        ticker_key = ticker.upper()
        now = time.monotonic()

        cached = self._cache.get(ticker_key)
        if cached and (now - cached[0]) < self._ttl:
            return cached[1]

        for attempt in range(3):
            try:
                loop = asyncio.get_running_loop()
                cotacao = await loop.run_in_executor(None, self._buscar_cotacao, ticker)
                self._cache[ticker_key] = (now, cotacao)
                return cotacao
            except Exception as e:
                if attempt < 2:
                    wait = 2 ** attempt
                    logger.warning(f"[RATE-LIMIT] {ticker}: retry em {wait}s ({e})")
                    await asyncio.sleep(wait)
                else:
                    raise

    def _buscar_cotacao(self, ticker: str) -> Cotacao:
        ativo = yf.Ticker(ticker)
        hist = ativo.history(period="1d", interval="1m")

        if hist.empty:
            raise ValueError(f"Ticker '{ticker}' não encontrado ou sem dados.")

        ultimo = hist.iloc[-1]
        preco = Decimal(str(round(float(ultimo["Close"]), 2)))
        volume = int(ultimo.get("Volume", 0))
        timestamp = ultimo.name.isoformat() if hasattr(ultimo.name, "isoformat") else str(ultimo.name)
        high = Decimal(str(round(float(ultimo["High"]), 2)))
        low = Decimal(str(round(float(ultimo["Low"]), 2)))
        open_ = Decimal(str(round(float(ultimo["Open"]), 2)))

        return Cotacao(
            ticker=ticker.upper(),
            preco=preco,
            volume=volume,
            timestamp=timestamp,
            high=high,
            low=low,
            open=open_,
        )

    async def obter_historico(
        self,
        ticker: str,
        periodo_dias: int = 30,
        intervalo: str = "1d",
    ) -> list[Cotacao]:
        """Retorna histórico de cotações no intervalo especificado."""
        loop = asyncio.get_running_loop()
        historico = await loop.run_in_executor(
            None, self._buscar_historico, ticker, periodo_dias, intervalo
        )
        return historico

    def _buscar_historico(self, ticker: str, periodo_dias: int, intervalo: str = "1d") -> list[Cotacao]:
        periodo = f"{periodo_dias}d"
        ativo = yf.Ticker(ticker)
        hist = ativo.history(period=periodo, interval=intervalo)

        if hist.empty:
            raise ValueError(f"Ticker '{ticker}' não encontrado ou sem histórico.")

        cotacoes = []
        for timestamp, row in hist.iterrows():
            preco = Decimal(str(round(float(row["Close"]), 2)))
            volume = int(row.get("Volume", 0))
            ts = timestamp.isoformat() if hasattr(timestamp, "isoformat") else str(timestamp)
            high = Decimal(str(round(float(row["High"]), 2)))
            low = Decimal(str(round(float(row["Low"]), 2)))
            open_ = Decimal(str(round(float(row["Open"]), 2)))
            cotacoes.append(
                Cotacao(
                    ticker=ticker.upper(),
                    preco=preco,
                    volume=volume,
                    timestamp=ts,
                    high=high,
                    low=low,
                    open=open_,
                )
            )
        return cotacoes

    async def stream_cotacoes(
        self,
        tickers: list[str],
    ) -> AsyncIterator[Cotacao]:
        """Polling a cada N segundos simulando stream."""
        while True:
            for ticker in tickers:
                try:
                    cotacao = await self.obter_cotacao(ticker)
                    yield cotacao
                except Exception:
                    pass
            await asyncio.sleep(self._intervalo)

    async def validar_ticker(self, ticker: str) -> bool:
        """Verifica se o ticker existe no Yahoo Finance."""
        try:
            loop = asyncio.get_running_loop()
            valido = await loop.run_in_executor(None, self._checar_ticker, ticker)
            return valido
        except Exception:
            return False

    def _checar_ticker(self, ticker: str) -> bool:
        ativo = yf.Ticker(ticker)
        hist = ativo.history(period="5d")
        return not hist.empty
