# -*- coding: utf-8 -*-
"""
Queries - Paper Trading

Queries representam consultas de dados que não modificam estado.
Seguem o padrão Query para encapsular operações de leitura.

Queries implementadas:
- ConsultarPortfolioQuery: Obter estado atual do portfolio com PnL
- ConsultarCotacaoQuery: Obter cotação atual de um ticker
- ConsultarHistoricoQuery: Obter histórico de preços
- ConsultarOrdensQuery: Listar ordens com filtros

Queries planejadas (futuro):
- ConsultarPosicoesQuery: Listar posições detidas
- ConsultarRiscoQuery: Obter métricas de risco

Exemplo:
    query = ConsultarCotacaoQuery(ticker="PETR4.SA")
    resultado = await handler.handle(query)
    print(resultado.preco)
"""

from .consultar_portfolio import ConsultarPortfolioQuery, PortfolioResult
from .consultar_cotacao import ConsultarCotacaoQuery, CotacaoResult
from .consultar_historico import ConsultarHistoricoQuery, CandleData, HistoricoResult
from .consultar_ordens import ConsultarOrdensQuery, OrdemItem, OrdensResult

__all__ = [
    'ConsultarPortfolioQuery',
    'PortfolioResult',
    'ConsultarCotacaoQuery',
    'CotacaoResult',
    'ConsultarHistoricoQuery',
    'CandleData',
    'HistoricoResult',
    'ConsultarOrdensQuery',
    'OrdemItem',
    'OrdensResult',
]
