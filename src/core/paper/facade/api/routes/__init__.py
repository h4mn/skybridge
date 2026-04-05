# -*- coding: utf-8 -*-
"""
Routes - Paper Trading API

Rotas FastAPI organizadas por domínio de negócio.

Módulos:
- mercado: Rotas para cotações e histórico
- ordens: Rotas para gerenciamento de ordens
- portfolio: Rotas para consulta de portfolio
- risco: Rotas para avaliação de risco (futuro)
"""

from . import mercado
from . import ordens
from . import portfolio
from . import risco

__all__ = ["mercado", "ordens", "portfolio", "risco"]
