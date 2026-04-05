"""
API Facade - Paper Trading

Interface REST/HTTP para integração externa do sistema de paper trading.

Componentes:
- facade: Facade principal que expõe operações de alto nível
- routes: Rotas FastAPI organizadas por domínio
- schemas: Modelos Pydantic para validação
- dependencies: Injeção de dependências do FastAPI

Exemplo de uso:
    from src.core.paper.facade.api.facade import PaperTradingAPI

    api = PaperTradingAPI()
    await api.criar_ordem(ticker="PETR4", lado="COMPRA", quantidade=100)
"""

from .facade import PaperTradingAPI

__all__ = ["PaperTradingAPI"]
