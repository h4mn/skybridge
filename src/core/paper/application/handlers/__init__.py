# -*- coding: utf-8 -*-
"""
Handlers - Paper Trading

Handlers orquestram a execução de Commands e Queries,
coordenando domain services e repositories.

Command Handlers:
- CriarOrdemHandler: Processa CriarOrdemCommand
- DepositarHandler: Processa DepositarCommand
- ResetarHandler: Processa ResetarCommand

Query Handlers:
- ConsultarCotacaoHandler: Processa ConsultarCotacaoQuery
- ConsultarHistoricoHandler: Processa ConsultarHistoricoQuery
- ConsultarPortfolioHandler: Processa ConsultarPortfolioQuery
- ConsultarOrdensHandler: Processa ConsultarOrdensQuery

Handlers planejados (futuro):
- CancelarOrdemHandler: Processa CancelarOrdemCommand
- ConsultarRiscoHandler: Processa ConsultarRiscoQuery

Responsabilidades:
- Validar input
- Carregar agregados do repositório
- Delegar lógica de negócio para domain services
- Persistir mudanças
- Publicar eventos de domínio

Exemplo:
    handler = CriarOrdemHandler(broker)
    result = await handler.handle(command)
"""

# Command Handlers
from .criar_ordem_handler import CriarOrdemHandler, OrdemResult
from .depositar_handler import DepositarHandler, DepositoResult
from .resetar_handler import ResetarHandler, ResetarResult

# Query Handlers
from .consultar_cotacao_handler import ConsultarCotacaoHandler
from .consultar_historico_handler import ConsultarHistoricoHandler
from .consultar_portfolio_handler import ConsultarPortfolioHandler
from .consultar_ordens_handler import ConsultarOrdensHandler

# Legacy (manter compatibilidade)
from .portfolio_handler import PortfolioQueryHandler

__all__ = [
    # Command Handlers
    'CriarOrdemHandler',
    'OrdemResult',
    'DepositarHandler',
    'DepositoResult',
    'ResetarHandler',
    'ResetarResult',
    # Query Handlers
    'ConsultarCotacaoHandler',
    'ConsultarHistoricoHandler',
    'ConsultarPortfolioHandler',
    'ConsultarOrdensHandler',
    # Legacy
    'PortfolioQueryHandler',
]
