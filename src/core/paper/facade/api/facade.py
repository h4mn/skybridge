"""
DEPRECATED - Esta classe NÃO é usada.

Esta facade foi substituída pela arquitetura CQRS com FastAPI.

Use:
- FastAPI app: src.core.paper.facade.api.app:create_app()
- Routes: src.core.paper.facade.api.routes.*
- Handlers: src.core.paper.application.handlers.*

Mantido apenas para referência histórica.
Remover em futura versão após confirmação de que não há dependências.

---
Facade API - Paper Trading (ORIGINAL)

Facade principal que expõe operações de alto nível para o sistema
de paper trading via REST/HTTP.

Esta classe encapsula a complexidade de coordenar commands, queries
e handlers, fornecendo uma interface simples para o cliente.
"""

from decimal import Decimal
from typing import Optional


class PaperTradingAPI:
    """
    Facade para operações de Paper Trading via API REST.

    Responsabilidades:
    - Expor operações de alto nível
    - Coordenar commands e queries
    - Gerenciar ciclo de vida dos handlers
    """

    def __init__(self):
        """Inicializa a facade com dependências padrão."""
        # TODO: Injetar dependências via DI
        pass

    # ==================== Ordens ====================

    async def criar_ordem(
        self,
        ticker: str,
        lado: str,
        quantidade: int,
        preco_limite: Optional[Decimal] = None,
        portfolio_id: str = "default",
    ) -> dict:
        """
        Cria uma nova ordem de compra ou venda.

        Args:
            ticker: Código do ativo (ex: "PETR4")
            lado: Direção da operação ("COMPRA" ou "VENDA")
            quantidade: Número de unidades
            preco_limite: Preço limite (None = ordem a mercado)
            portfolio_id: ID do portfolio

        Returns:
            Dicionário com dados da ordem criada

        Raises:
            ValidationError: Se parâmetros inválidos
            SaldoInsuficienteError: Se saldo insuficiente para compra
        """
        # TODO: Implementar via CriarOrdemCommand
        raise NotImplementedError("Implementar via CriarOrdemCommand")

    async def cancelar_ordem(self, ordem_id: str) -> bool:
        """
        Cancela uma ordem existente.

        Args:
            ordem_id: ID da ordem a cancelar

        Returns:
            True se cancelada com sucesso
        """
        # TODO: Implementar via CancelarOrdemCommand
        raise NotImplementedError("Implementar via CancelarOrdemCommand")

    async def listar_ordens(
        self,
        portfolio_id: str,
        status: Optional[str] = None,
    ) -> list[dict]:
        """
        Lista ordens de um portfolio.

        Args:
            portfolio_id: ID do portfolio
            status: Filtro opcional por status

        Returns:
            Lista de ordens
        """
        # TODO: Implementar via ConsultarOrdensQuery
        raise NotImplementedError("Implementar via ConsultarOrdensQuery")

    # ==================== Portfolio ====================

    async def consultar_portfolio(self, portfolio_id: str) -> dict:
        """
        Consulta estado atual do portfolio.

        Args:
            portfolio_id: ID do portfolio

        Returns:
            Dicionário com saldo, posições, PL, etc.
        """
        # TODO: Implementar via ConsultarPortfolioQuery
        raise NotImplementedError("Implementar via ConsultarPortfolioQuery")

    async def resetar_portfolio(
        self,
        portfolio_id: str,
        saldo_inicial: Decimal = Decimal("100000"),
    ) -> dict:
        """
        Reseta portfolio para estado inicial.

        Args:
            portfolio_id: ID do portfolio
            saldo_inicial: Saldo inicial após reset

        Returns:
            Dicionário com dados do portfolio resetado
        """
        # TODO: Implementar via ResetarPortfolioCommand
        raise NotImplementedError("Implementar via ResetarPortfolioCommand")

    # ==================== Risco ====================

    async def avaliar_risco(self, portfolio_id: str) -> dict:
        """
        Avalia métricas de risco do portfolio.

        Args:
            portfolio_id: ID do portfolio

        Returns:
            Dicionário com métricas de risco (VaR, exposição, etc.)
        """
        # TODO: Implementar via ConsultarRiscoQuery
        raise NotImplementedError("Implementar via ConsultarRiscoQuery")

    async def configurar_stop_loss(
        self,
        ticker: str,
        percentual: Decimal,
        portfolio_id: str = "default",
    ) -> dict:
        """
        Configura stop loss para uma posição.

        Args:
            ticker: Código do ativo
            percentual: Percentual de perda para acionar stop
            portfolio_id: ID do portfolio

        Returns:
            Dicionário com configuração de stop loss
        """
        # TODO: Implementar via AtualizarStopLossCommand
        raise NotImplementedError("Implementar via AtualizarStopLossCommand")
