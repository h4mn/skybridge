# -*- coding: utf-8 -*-
"""Handler para processar ConsultarHistoricoQuery."""
from ..queries.consultar_historico import ConsultarHistoricoQuery, HistoricoResult, CandleData
from ...ports.data_feed_port import DataFeedPort


class ConsultarHistoricoHandler:
    """Handler para consultas de histórico de preços.

    Delega a obtenção de dados para o DataFeedPort.
    """

    def __init__(self, feed: DataFeedPort):
        self._feed = feed

    async def handle(self, query: ConsultarHistoricoQuery) -> HistoricoResult:
        """Processa a query de histórico.

        Args:
            query: Query com ticker e período

        Returns:
            HistoricoResult com lista de candles
        """
        cotacoes = await self._feed.obter_historico(
            ticker=query.ticker,
            periodo_dias=query.dias,
        )

        candles = [
            CandleData(
                timestamp=cotacao.timestamp,
                abertura=cotacao.preco,  # YahooFeed retorna apenas preço de fechamento
                alta=cotacao.preco,
                baixa=cotacao.preco,
                fechamento=cotacao.preco,
                volume=cotacao.volume,
            )
            for cotacao in cotacoes
        ]

        return HistoricoResult(
            ticker=query.ticker,
            candles=candles,
        )
