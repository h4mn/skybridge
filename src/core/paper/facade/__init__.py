"""
Facades - Paper Trading

Agrupa as facades de integração externa do sistema de paper trading.

Esta pasta centraliza todas as interfaces de entrada do sistema:
- API: Interface REST/HTTP para integração com sistemas externos
- MCP: Interface Model Context Protocol para integração com LLMs

O padrão Facade fornece uma interface simplificada para subsistemas complexos,
escondendo a complexidade interna do domain/application/ports/adapters.

Exemplo de uso:

    # Via API REST
    from src.core.paper.facade.api import PaperTradingAPI
    api = PaperTradingAPI()
    await api.criar_ordem(ticker="PETR4", lado="COMPRA", quantidade=100)

    # Via MCP (para LLMs)
    from src.core.paper.facade.mcp import PaperTradingMCP
    mcp = PaperTradingMCP()
    # Tools: paper_criar_ordem, paper_consultar_portfolio
    # Resources: paper://portfolio
"""

from .api import PaperTradingAPI
from .mcp import PaperTradingMCP

__all__ = ["PaperTradingAPI", "PaperTradingMCP"]
