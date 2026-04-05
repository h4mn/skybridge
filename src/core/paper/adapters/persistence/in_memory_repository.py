"""Adapter - Repositório em memória para desenvolvimento/testes."""
from typing import Dict
from ...ports.repository_port import PortfolioRepositoryPort
from ...domain.entities.portfolio import Portfolio


class InMemoryPortfolioRepository(PortfolioRepositoryPort):
    """Repositório em memória para Portfolio.
    
    Implementação simples que mantém portfolios em memória.
    Útil para desenvolvimento e testes.
    """
    
    def __init__(self):
        self._portfolios: Dict[str, Portfolio] = {}
        # Cria portfolio padrão
        default = Portfolio()
        self._portfolios[default.id] = default
        self._default_id = default.id
    
    def find_by_id(self, portfolio_id: str) -> Portfolio:
        if portfolio_id not in self._portfolios:
            raise ValueError(f"Portfolio {portfolio_id} não encontrado")
        return self._portfolios[portfolio_id]
    
    def find_default(self) -> Portfolio:
        return self._portfolios[self._default_id]
    
    def save(self, portfolio: Portfolio) -> None:
        self._portfolios[portfolio.id] = portfolio
