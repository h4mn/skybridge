# -*- coding: utf-8 -*-
"""
Facade MCP - Paper Trading

Facade principal que expõe operações de Paper Trading via MCP
(Model Context Protocol) para integração com LLMs.
"""
from decimal import Decimal
from typing import Optional

from .resources.prompts_resource import create_prompt_resources


class PaperTradingMCP:
    """
    Facade para operações de Paper Trading via MCP.

    Tools disponíveis:
    - paper_criar_ordem: Criar nova ordem
    - paper_consultar_portfolio: Consultar portfolio
    - paper_cotacao_ticker: Consultar cotação

    Resources disponíveis:
    - paper://portfolio: Estado do portfolio
    - paper://prompts/guide: Guia geral
    - paper://prompts/operations: Referência de operações
    - paper://prompts/troubleshooting: Guia de problemas
    - paper://prompts/all: Todos os prompts
    """

    def __init__(self):
        """Inicializa a facade."""
        self._prompt_resources = create_prompt_resources()

    def get_resources(self) -> list:
        """Retorna todos os recursos MCP disponíveis."""
        return self._prompt_resources

    # ==================== Tools ====================

    async def criar_ordem(
        self,
        ticker: str,
        lado: str,
        quantidade: int,
        preco_limite: Optional[Decimal] = None,
        portfolio_id: str = "default",
    ) -> dict:
        """
        Tool: paper_criar_ordem

        Cria uma nova ordem de compra ou venda.

        Args:
            ticker: Código do ativo (ex: "PETR4")
            lado: Direção da operação ("COMPRA" ou "VENDA")
            quantidade: Número de unidades
            preco_limite: Preço limite (None = ordem a mercado)
            portfolio_id: ID do portfolio

        Returns:
            Dicionário com dados da ordem criada
        """
        # TODO: Implementar via CriarOrdemCommand
        raise NotImplementedError("Implementar via CriarOrdemCommand")

    async def consultar_portfolio(self, portfolio_id: str = "default") -> dict:
        """
        Tool: paper_consultar_portfolio

        Consulta estado atual do portfolio.

        Args:
            portfolio_id: ID do portfolio

        Returns:
            Dicionário com saldo, posições, PL, etc.
        """
        # TODO: Implementar via ConsultarPortfolioQuery
        raise NotImplementedError("Implementar via ConsultarPortfolioQuery")

    async def avaliar_risco(self, portfolio_id: str = "default") -> dict:
        """
        Tool: paper_avaliar_risco

        Avalia métricas de risco do portfolio.

        Args:
            portfolio_id: ID do portfolio

        Returns:
            Dicionário com métricas de risco (VaR, exposição, etc.)
        """
        # TODO: Implementar via ConsultarRiscoQuery
        raise NotImplementedError("Implementar via ConsultarRiscoQuery")

    async def cancelar_ordem(self, ordem_id: str) -> dict:
        """
        Tool: paper_cancelar_ordem

        Cancela uma ordem existente.

        Args:
            ordem_id: ID da ordem a cancelar

        Returns:
            Dicionário com status do cancelamento
        """
        # TODO: Implementar via CancelarOrdemCommand
        raise NotImplementedError("Implementar via CancelarOrdemCommand")

    # ==================== Resources ====================

    async def get_portfolio_resource(self, portfolio_id: str = "default") -> str:
        """
        Resource: paper://portfolio

        Retorna representação do portfolio como recurso MCP.

        Args:
            portfolio_id: ID do portfolio

        Returns:
            String formatada com estado do portfolio
        """
        # TODO: Implementar consulta de portfolio
        raise NotImplementedError("Implementar consulta de portfolio")

    async def get_ordens_resource(
        self,
        portfolio_id: str = "default",
        status: Optional[str] = None,
    ) -> str:
        """
        Resource: paper://ordens

        Retorna representação das ordens como recurso MCP.

        Args:
            portfolio_id: ID do portfolio
            status: Filtro opcional por status

        Returns:
            String formatada com lista de ordens
        """
        # TODO: Implementar consulta de ordens
        raise NotImplementedError("Implementar consulta de ordens")
