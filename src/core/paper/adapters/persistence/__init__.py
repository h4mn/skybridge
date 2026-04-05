"""
Persistence Adapters - Paper Trading

Implementações concretas em RepositoryPort para diferentes bancos de dados.
Adapters planejados:
- SQLiteRepository: Persistência em SQLite (desenvolvimento)
- PostgreSQLRepository: Persistência em PostgreSQL (produção)
- InMemoryRepository: Persistência em memória (testes)
Exemplo de usage:
    from src.core.paper.adapters.persistence import SQLiteRepository
    repo = SQLiteRepository("paper_trading.db")
    await repo.salvar_portfolio("portfolio-001", Decimal("10000"), "user-001")
    portfolio = await repo.carregar_portfolio("portfolio-001")
"""
from .in_memory_repository import InMemoryPortfolioRepository
from .json_file_repository import JsonFilePortfolioRepository
from .json_file_paper_state import JsonFilePaperState
__all__ = [
    "InMemoryPortfolioRepository",
    "JsonFilePortfolioRepository",
    "JsonFilePaperState",
]
