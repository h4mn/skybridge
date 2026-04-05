"""
Tool: Avaliar Risco - Paper Trading MCP

Ferramenta MCP para avaliar métricas de risco do portfolio via LLM.
"""



class AvaliarRiscoTool:
    """
    Tool MCP para avaliação de risco.

    Nome da tool: paper_avaliar_risco

    Descrição para LLM:
        Avalia as métricas de risco do portfolio de paper trading.
        Use esta ferramenta quando o usuário quiser saber:
        - Nível de risco do portfolio
        - Exposição total
        - Concentração por ativo

    Parâmetros:
        portfolio_id (str, opcional): ID do portfolio (padrão: "default")

    Exemplo de uso pelo LLM:
        <tool_call name="paper_avaliar_risco">
        {
            "portfolio_id": "default"
        }
        </tool_call
    """

    name = "paper_avaliar_risco"
    description = """
    Avalia as métricas de risco do portfolio de paper trading.

    Use esta ferramenta quando o usuário quiser saber:
    - Qual é o nível de risco atual do portfolio
    - Se está muito concentrado em algum ativo
    - Qual é a exposição total ao mercado
    - Se há necessidade de diversificação

    Retorna métricas como:
    - VaR (Value at Risk)
    - Exposição total
    - Concentração por ativo
    - Recomendações de ajuste
    """

    async def execute(
        self,
        portfolio_id: str = "default",
    ) -> dict:
        """
        Executa a avaliação de risco.

        Args:
            portfolio_id: ID do portfolio

        Returns:
            Dicionário com métricas de risco:
            - var: Value at Risk
            - exposicao_total: Exposição ao mercado
            - concentracao: Concentração por ativo
            - recomendacoes: Lista de recomendações
        """
        # TODO: Implementar via facade
        raise NotImplementedError("Implementar via PaperTradingMCP facade")

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
