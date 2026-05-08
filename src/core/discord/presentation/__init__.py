# -*- coding: utf-8 -*-
"""
Presentation Layer - Camada de apresentação do módulo Discord.

Exporta Views e componentes para integração com bot Discord.

NOTA: portfolio_views depende de discord.py (View, Button, Embed) e nao e
importado no nivel do modulo para evitar colisao de namespace durante
coleta do pytest. Importar diretamente do submodulo:
    from src.core.discord.presentation.portfolio_views import PortfolioMainView
"""

from .chart_helper import (
    QuickChartHelper,
    ChartColors,
    create_alocacao_chart,
    create_pnl_chart,
)

__all__ = [
    # Charts
    "QuickChartHelper",
    "ChartColors",
    "create_alocacao_chart",
    "create_pnl_chart",
]
