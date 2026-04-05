"""
Porta do Repository - Paper Trading

Define a interface para persistência de dados do paper trading.
Implementações podem ser SQLite, PostgreSQL, etc.
"""

from abc import ABC, abstractmethod
from decimal import Decimal
from typing import Optional


class RepositoryPort(ABC):
    """
    Interface para persistência de dados.

    Implementações:
    - SQLiteRepository: Persistência em SQLite
    - PostgreSQLRepository: Persistência em PostgreSQL
    - InMemoryRepository: Persistência em memória (testes)
    """

    # ==================== Portfolio ====================

    @abstractmethod
    async def salvar_portfolio(
        self,
        portfolio_id: str,
        saldo: Decimal,
        usuario_id: str,
    ) -> None:
        """
        Salva/atualiza um portfolio.

        Args:
            portfolio_id: ID único do portfolio
            saldo: Saldo disponível
            usuario_id: ID do usuário proprietário
        """
        pass

    @abstractmethod
    async def carregar_portfolio(self, portfolio_id: str) -> dict:
        """
        Carrega um portfolio pelo ID.

        Args:
            portfolio_id: ID do portfolio

        Returns:
            Dicionário com dados do portfolio

        Raises:
            PortfolioNaoEncontradoError: Se portfolio não existir
        """
        pass

    # ==================== Ordens ====================

    @abstractmethod
    async def salvar_ordem(self, ordem: dict) -> str:
        """
        Salva uma nova ordem.

        Args:
            ordem: Dicionário com dados da ordem

        Returns:
            ID da ordem criada
        """
        pass

    @abstractmethod
    async def atualizar_ordem(self, ordem_id: str, dados: dict) -> None:
        """
        Atualiza dados de uma ordem existente.

        Args:
            ordem_id: ID da ordem
            dados: Campos a atualizar
        """
        pass

    @abstractmethod
    async def carregar_ordem(self, ordem_id: str) -> dict:
        """
        Carrega uma ordem pelo ID.

        Args:
            ordem_id: ID da ordem

        Returns:
            Dicionário com dados da ordem
        """
        pass

    @abstractmethod
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
        pass

    # ==================== Posições ====================

    @abstractmethod
    async def salvar_posicao(self, posicao: dict) -> None:
        """
        Salva/atualiza uma posição.

        Args:
            posicao: Dicionário com dados da posição
        """
        pass

    @abstractmethod
    async def listar_posicoes(self, portfolio_id: str) -> list[dict]:
        """
        Lista posições de um portfolio.

        Args:
            portfolio_id: ID do portfolio

        Returns:
            Lista de posições
        """
        pass

    # ==================== Histórico ====================

    @abstractmethod
    async def registrar_operacao(self, operacao: dict) -> None:
        """
        Registra uma operação no histórico.

        Args:
            operacao: Dicionário com dados da operação
        """
        pass

    @abstractmethod
    async def listar_historico(
        self,
        portfolio_id: str,
        limite: int = 100,
    ) -> list[dict]:
        """
        Lista histórico de operações.

        Args:
            portfolio_id: ID do portfolio
            limite: Número máximo de registros

        Returns:
            Lista de operações
        """
        pass


# ==================== Portfolio Repository Port (Simplificado) ====================

class PortfolioRepositoryPort(ABC):
    """Interface para repositório de Portfolio.
    
    Define o contrato para persistência de portfolios,
    permitindo diferentes implementações (memória, SQLite, etc).
    """
    
    @abstractmethod
    def find_by_id(self, portfolio_id: str) -> "Portfolio":
        """Busca portfolio por ID."""
        pass
    
    @abstractmethod
    def find_default(self) -> "Portfolio":
        """Retorna o portfolio padrão."""
        pass
    
    @abstractmethod
    def save(self, portfolio: "Portfolio") -> None:
        """Salva o portfolio."""
        pass


# Importação para type hint
from ..domain.entities.portfolio import Portfolio
