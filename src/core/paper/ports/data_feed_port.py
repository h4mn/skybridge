"""
Porta do Data Feed - Paper Trading

Define a interface para obtenção de dados de mercado.
Implementações podem ser Yahoo Finance, Alpha Vantage, etc.
"""

from abc import ABC, abstractmethod
from decimal import Decimal
from typing import AsyncIterator


class Cotacao:
    """Representa uma cotação de mercado."""

    def __init__(
        self,
        ticker: str,
        preco: Decimal,
        volume: int,
        timestamp: str,
        high: Decimal | None = None,
        low: Decimal | None = None,
        open: Decimal | None = None,
    ):
        self.ticker = ticker
        self.preco = preco
        self.volume = volume
        self.timestamp = timestamp
        self.high = high
        self.low = low
        self.open = open


class DataFeedPort(ABC):
    """
    Interface para feeds de dados de mercado.

    Implementações:
    - YahooFinanceFeed: Dados do Yahoo Finance
    - AlphaVantageFeed: Dados do Alpha Vantage
    - BinanceFeed: Dados da Binance
    """

    @abstractmethod
    async def conectar(self) -> None:
        """Estabelece conexão com o feed de dados."""
        pass

    @abstractmethod
    async def desconectar(self) -> None:
        """Encerra conexão com o feed de dados."""
        pass

    @abstractmethod
    async def obter_cotacao(self, ticker: str) -> Cotacao:
        """
        Obtém cotação atual de um ativo.

        Args:
            ticker: Código do ativo (ex: "PETR4.SA")

        Returns:
            Cotacao com preço, volume e timestamp

        Raises:
            TickerNaoEncontradoError: Se ticker não existir
        """
        pass

    @abstractmethod
    async def obter_historico(
        self,
        ticker: str,
        periodo_dias: int = 30,
        intervalo: str = "1d",
    ) -> list[Cotacao]:
        """
        Obtém histórico de cotações.

        Args:
            ticker: Código do ativo
            periodo_dias: Número de dias de histórico
            intervalo: Intervalo das velas ("1d", "1h", "1m", etc.)

        Returns:
            Lista de cotações históricas
        """
        pass

    @abstractmethod
    async def stream_cotacoes(
        self,
        tickers: list[str],
    ) -> AsyncIterator[Cotacao]:
        """
        Stream de cotações em tempo real.

        Args:
            tickers: Lista de códigos de ativos

        Yields:
            Cotacao a cada atualização
        """
        pass

    @abstractmethod
    async def validar_ticker(self, ticker: str) -> bool:
        """
        Verifica se um ticker é válido.

        Args:
            ticker: Código do ativo

        Returns:
            True se o ticker existe e está ativo
        """
        pass
