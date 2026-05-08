# -*- coding: utf-8 -*-
"""Estratégias de trading — domain objects puros."""

from .protocol import StrategyProtocol
from .signal import DadosMercado, SinalEstrategia, TipoSinal

__all__ = [
    "TipoSinal",
    "DadosMercado",
    "SinalEstrategia",
    "StrategyProtocol",
]
