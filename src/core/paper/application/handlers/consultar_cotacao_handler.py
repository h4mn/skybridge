# -*- coding: utf-8 -*-
"""Handler para processar ConsultarCotacaoQuery."""
from ..queries.consultar_cotacao import ConsultarCotacaoQuery, CotacaoResult
from ...ports.data_feed_port import DataFeedPort


class ConsultarCotacaoHandler:
    """Handler para consultas de cotação.

    Delega a obtenção de dados para o DataFeedPort.
    """

    def __init__(self, feed: DataFeedPort):
        self._feed = feed

    async def handle(self, query: ConsultarCotacaoQuery) -> CotacaoResult:
        """Processa a query de cotação.

        Args:
            query: Query com ticker a consultar

        Returns:
            CotacaoResult com preço atual
        """
        cotacao = await self._feed.obter_cotacao(query.ticker)

        return CotacaoResult(
            ticker=cotacao.ticker,
            preco=cotacao.preco,
            variacao=None,  # TODO: calcular variação percentual
            timestamp=cotacao.timestamp,
        )
