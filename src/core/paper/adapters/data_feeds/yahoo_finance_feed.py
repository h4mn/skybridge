"""Adapter - Yahoo Finance Feed.

Implementa DataFeedPort usando yfinance (gratuito, sem API key).
Suporta ativos da B3 (PETR4.SA), cripto (BTC-USD) e mercado americano.
"""
from decimal import Decimal
from typing import AsyncIterator
import asyncio

import yfinance as yf

from ...ports.data_feed_port import DataFeedPort, Cotacao


class YahooFinanceFeed(DataFeedPort):
    """Feed de dados via Yahoo Finance.

    Não requer autenticação. Dados com delay de ~15min para B3,
    próximo de real-time para cripto.

    Exemplos de tickers:
        B3:    PETR4.SA, VALE3.SA, ITUB4.SA, BBDC4.SA
        Cripto: BTC-USD, ETH-USD, SOL-USD
        EUA:   AAPL, MSFT, TSLA
    """

    def __init__(self, intervalo_stream_segundos: int = 5):
        self._intervalo = intervalo_stream_segundos
        self._conectado = False

    async def conectar(self) -> None:
        self._conectado = True

    async def desconectar(self) -> None:
        self._conectado = False

    async def obter_cotacao(self, ticker: str) -> Cotacao:
        """Retorna a cotação mais recente do ativo.

        Usa o período de 1 dia com intervalo de 1 minuto para
        pegar o preço mais atual disponível.
        """
        loop = asyncio.get_event_loop()
        cotacao = await loop.run_in_executor(None, self._buscar_cotacao, ticker)
        return cotacao

    def _buscar_cotacao(self, ticker: str) -> Cotacao:
        ativo = yf.Ticker(ticker)
        hist = ativo.history(period="1d", interval="1m")

        if hist.empty:
            raise ValueError(f"Ticker '{ticker}' não encontrado ou sem dados.")

        ultimo = hist.iloc[-1]
        preco = Decimal(str(round(float(ultimo["Close"]), 2)))
        volume = int(ultimo.get("Volume", 0))
        timestamp = ultimo.name.isoformat() if hasattr(ultimo.name, "isoformat") else str(ultimo.name)

        return Cotacao(
            ticker=ticker.upper(),
            preco=preco,
            volume=volume,
            timestamp=timestamp,
        )

    async def obter_historico(
        self,
        ticker: str,
        periodo_dias: int = 30,
        intervalo: str = "1d",
    ) -> list[Cotacao]:
        """Retorna histórico de cotações no intervalo especificado."""
        loop = asyncio.get_event_loop()
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
            cotacoes.append(
                Cotacao(
                    ticker=ticker.upper(),
                    preco=preco,
                    volume=volume,
                    timestamp=ts,
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
            loop = asyncio.get_event_loop()
            valido = await loop.run_in_executor(None, self._checar_ticker, ticker)
            return valido
        except Exception:
            return False

    def _checar_ticker(self, ticker: str) -> bool:
        ativo = yf.Ticker(ticker)
        hist = ativo.history(period="5d")
        return not hist.empty
