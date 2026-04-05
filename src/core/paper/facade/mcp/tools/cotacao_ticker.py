# -*- coding: utf-8 -*-
"""Tool: Cotação Ticker - Paper Trading MCP.

Ferramenta MCP para consultar cotação atual de um ticker via LLM.
"""
from ....application.queries.consultar_cotacao import ConsultarCotacaoQuery
from ....application.handlers.consultar_cotacao_handler import ConsultarCotacaoHandler


class CotacaoTickerTool:
    """Tool MCP para consulta de cotação.

    Nome da tool: paper_cotacao_ticker
    """

    name = "paper_cotacao_ticker"
    description = """
    Consulta a cotação atual de um ativo.

    Use esta ferramenta quando o usuário quiser saber:
    - Preço atual de uma ação, cripto ou ETF
    - Última cotação de um ticker

    **Tickers suportados:**
    - B3: PETR4.SA, VALE3.SA, ITUB4.SA
    - Cripto: BTC-USD, ETH-USD
    - EUA: AAPL, TSLA, MSFT
    """

    def __init__(self, handler: ConsultarCotacaoHandler):
        self._handler = handler

    async def execute(self, ticker: str) -> dict:
        """Executa a consulta de cotação."""
        try:
            query = ConsultarCotacaoQuery(ticker=ticker.upper())
            result = await self._handler.handle(query)

            return {
                "sucesso": True,
                "ticker": result.ticker,
                "preco": float(result.preco),
                "variacao": float(result.variacao) if result.variacao else None,
                "timestamp": result.timestamp,
            }
        except ValueError as e:
            return {"sucesso": False, "erro": str(e), "ticker": ticker}
        except Exception as e:
            return {"sucesso": False, "erro": f"Erro ao buscar cotação: {e}"}

    def get_schema(self) -> dict:
        """Retorna schema JSON para validação de parâmetros."""
        return {
            "type": "object",
            "properties": {
                "ticker": {
                    "type": "string",
                    "description": "Código do ativo (ex: PETR4.SA, BTC-USD)",
                },
            },
            "required": ["ticker"],
        }
