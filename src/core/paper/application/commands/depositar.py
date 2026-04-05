# -*- coding: utf-8 -*-
"""Command para depositar saldo no portfolio."""
from dataclasses import dataclass
from decimal import Decimal
from typing import Optional


@dataclass
class DepositarCommand:
    """Command: intenção de depositar saldo no portfolio.

    Attributes:
        valor: Valor a depositar (deve ser positivo)
        portfolio_id: ID do portfolio (opcional, usa default se None)
    """
    valor: Decimal
    portfolio_id: Optional[str] = None

    def __post_init__(self):
        """Validação básica do command."""
        if self.valor <= 0:
            raise ValueError(f"valor deve ser positivo, recebido: {self.valor}")
