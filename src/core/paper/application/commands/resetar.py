# -*- coding: utf-8 -*-
"""Command para resetar o portfolio para estado inicial."""
from dataclasses import dataclass
from decimal import Decimal
from typing import Optional


@dataclass
class ResetarCommand:
    """Command: intenção de resetar o portfolio.

    Limpa todas as ordens, posições e redefine saldo.

    Attributes:
        saldo_inicial: Novo saldo inicial (opcional, mantém atual se None)
        portfolio_id: ID do portfolio (opcional, usa default se None)
    """
    saldo_inicial: Optional[Decimal] = None
    portfolio_id: Optional[str] = None
