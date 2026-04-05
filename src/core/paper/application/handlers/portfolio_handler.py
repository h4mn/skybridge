"""Handler para queries do portfolio."""
from ..queries.consultar_portfolio import ConsultarPortfolioQuery, PortfolioResult
from ...ports.repository_port import PortfolioRepositoryPort


class PortfolioQueryHandler:
    """Handler para consultas do portfolio."""
    
    def __init__(self, repository: PortfolioRepositoryPort):
        self.repository = repository
    
    def handle_consultar(self, query: ConsultarPortfolioQuery) -> PortfolioResult:
        """Processa a query de consulta do portfolio."""
        if query.portfolio_id:
            portfolio = self.repository.find_by_id(query.portfolio_id)
        else:
            portfolio = self.repository.find_default()
        
        return PortfolioResult(
            id=portfolio.id,
            nome=portfolio.nome,
            saldo_inicial=portfolio.saldo_inicial,
            saldo_atual=portfolio.saldo_atual,
            pnl=portfolio.pnl(),
            pnl_percentual=portfolio.pnl_percentual()
        )
