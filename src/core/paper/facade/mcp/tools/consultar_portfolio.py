# -*- coding: utf-8 -*-
"""Tool: Consultar Portfolio - Paper Trading MCP.

Ferramenta MCP para consultar estado do portfolio via LLM.
"""

from ....application.queries.consultar_portfolio import ConsultarPortfolioQuery
from ....application.handlers.consultar_portfolio_handler import ConsultarPortfolioHandler


class ConsultarPortfolioTool:
    """Tool MCP para consulta de portfolio.

    Nome da tool: paper_consultar_portfolio
    """

    name = "paper_consultar_portfolio"
    description = """
    Consulta o estado atual do portfolio de paper trading.

    Use esta ferramenta quando o usuário quiser saber:
    - Qual é o saldo disponível
    - Quais posições estão abertas
    - Qual é o lucro ou prejuízo total
    - Qual é o valor total do portfolio
    """

    def __init__(self, handler: ConsultarPortfolioHandler):
        self._handler = handler

    async def execute(
        self,
        portfolio_id: str = "default",
    ) -> dict:
        """Executa a consulta do portfolio."""
        try:
            query = ConsultarPortfolioQuery(portfolio_id=portfolio_id)
            result = await self._handler.handle(query)

            return {
                "sucesso": True,
                "portfolio_id": result.id,
                "nome": result.nome,
                "saldo_inicial": result.saldo_inicial,
                "saldo_atual": result.saldo_atual,
                "pnl": result.pnl,
                "pnl_percentual": result.pnl_percentual,
            }
        except Exception as e:
            return {"sucesso": False, "erro": str(e)}

    def get_schema(self) -> dict:
        """Retorna schema JSON para validação de parâmetros."""
        return {
            "type": "object",
            "properties": {
                "portfolio_id": {
                    "type": "string",
                    "default": "default",
                    "description": "ID do portfolio",
                },
            },
            "required": [],
        }
