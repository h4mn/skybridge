# -*- coding: utf-8 -*-
"""
Presentation Layer - Camada de apresentação do módulo Discord.

Exporta Views e componentes para integração com bot Discord.
"""

from .portfolio_views import (
    PortfolioMainView,
    PortfolioWelcomeView,
    PortfolioColors,
    PortfolioReadModel,
    AssetCardReadModel,
)

from .chart_helper import (
    QuickChartHelper,
    ChartColors,
    create_alocacao_chart,
    create_pnl_chart,
)

__all__ = [
    # Views
    "PortfolioMainView",
    "PortfolioWelcomeView",
    "PortfolioColors",
    # Read Models
    "PortfolioReadModel",
    "AssetCardReadModel",
    # Charts
    "QuickChartHelper",
    "ChartColors",
    "create_alocacao_chart",
    "create_pnl_chart",
]
