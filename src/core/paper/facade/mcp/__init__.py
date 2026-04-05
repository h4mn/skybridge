"""
MCP Facade - Paper Trading

Interface Model Context Protocol (MCP) para integração com LLMs.

Componentes:
- facade: Facade principal que expõe operações via MCP
- tools: Ferramentas MCP para LLMs
- resources: Recursos MCP para consulta

Exemplo de uso:
    from src.core.paper.facade.mcp.facade import PaperTradingMCP

    mcp = PaperTradingMCP()
    # Tools: paper_criar_ordem, paper_consultar_portfolio
    # Resources: paper://portfolio
"""

from .facade import PaperTradingMCP

__all__ = ["PaperTradingMCP"]
