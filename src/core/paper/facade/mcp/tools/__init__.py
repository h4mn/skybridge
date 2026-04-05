# -*- coding: utf-8 -*-
"""
MCP Tools - Paper Trading

Ferramentas MCP (Model Context Protocol) para integração com LLMs.

Tools implementadas:
- CriarOrdemTool: Criar nova ordem de compra/venda
- ConsultarPortfolioTool: Consultar estado do portfolio com PnL
- CotacaoTickerTool: Consultar cotação atual de um ativo

Tools planejadas (futuro):
- AvaliarRiscoTool: Avaliar métricas de risco
"""

from .criar_ordem import CriarOrdemTool
from .consultar_portfolio import ConsultarPortfolioTool
from .cotacao_ticker import CotacaoTickerTool

# AvaliarRiscoTool ainda não implementado
try:
    from .avaliar_risco import AvaliarRiscoTool
except ImportError:
    AvaliarRiscoTool = None

__all__ = [
    "CriarOrdemTool",
    "ConsultarPortfolioTool",
    "CotacaoTickerTool",
    "AvaliarRiscoTool",
]
