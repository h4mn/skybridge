"""
Resource: Portfolio - Paper Trading MCP

Recurso MCP para expor estado do portfolio como URI.
"""



class PortfolioResource:
    """
    Resource MCP para consulta de portfolio.

    URI: paper://portfolio

    Descrição para LLM:
        Recurso que representa o estado atual do portfolio de paper trading.
        Pode ser consultado para obter informações completas do portfolio.

    Formato de resposta:
        Texto formatado com:
        - Saldo disponível
        - Lista de posições
        - Lucro/prejuízo total
        - Valor total do portfolio

    Exemplo de uso pelo LLM:
        <resource_read uri="paper://portfolio" />
    """

    uri = "paper://portfolio"
    name = "Portfolio de Paper Trading"
    description = """
    Recurso que representa o estado atual do portfolio de paper trading.

    Informações disponíveis:
    - Saldo disponível para novas operações
    - Posições detidas com detalhes
    - Lucro/prejuízo total
    - Valor total do portfolio

    Use este recurso quando precisar de uma visão geral do portfolio.
    """
    mime_type = "text/plain"

    def __init__(self, portfolio_id: str = "default"):
        """
        Inicializa o recurso.

        Args:
            portfolio_id: ID do portfolio a ser consultado
        """
        self.portfolio_id = portfolio_id

    async def read(self) -> str:
        """
        Lê o conteúdo do recurso.

        Returns:
            String formatada com estado do portfolio
        """
        # TODO: Implementar consulta real
        portfolio_data = await self._get_portfolio_data()
        return self._format_response(portfolio_data)

    async def _get_portfolio_data(self) -> dict:
        """
        Obtém dados do portfolio.

        Returns:
            Dicionário com dados do portfolio
        """
        # TODO: Implementar via facade
        return {
            "saldo_disponivel": 0,
            "valor_total": 0,
            "pl_total": 0,
            "posicoes": [],
        }

    def _format_response(self, data: dict) -> str:
        """
        Formata resposta como texto legível.

        Args:
            data: Dados do portfolio

        Returns:
            String formatada
        """
        lines = [
            "# Portfolio de Paper Trading",
            "",
            f"**Saldo Disponível:** R$ {data['saldo_disponivel']:,.2f}",
            f"**Valor Total:** R$ {data['valor_total']:,.2f}",
            f"**PL Total:** R$ {data['pl_total']:,.2f}",
            "",
            "## Posições",
            "",
        ]

        if data["posicoes"]:
            for pos in data["posicoes"]:
                lines.append(
                    f"- **{pos['ticker']}**: {pos['quantidade']} unidades "
                    f"@ R$ {pos['preco_medio']:.2f} "
                    f"(PL: R$ {pos['pl']:.2f})"
                )
        else:
            lines.append("_Nenhuma posição aberta_")

        return "\n".join(lines)

    def get_template(self) -> dict:
        """Retorna template do recurso para registro no MCP."""
        return {
            "uri": self.uri,
            "name": self.name,
            "description": self.description,
            "mimeType": self.mime_type,
        }
