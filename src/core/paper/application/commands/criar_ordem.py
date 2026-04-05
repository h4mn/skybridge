# -*- coding: utf-8 -*-
"""Command para criar uma ordem de compra/venda."""
from dataclasses import dataclass
from decimal import Decimal
from typing import Optional


@dataclass
class CriarOrdemCommand:
    """Command: intenção de criar uma nova ordem.

    Attributes:
        ticker: Código do ativo (ex: "PETR4.SA")
        lado: Direção da operação ("COMPRA" ou "VENDA")
        quantidade: Número de unidades
        preco_limite: Preço limite (None = ordem a mercado)
        portfolio_id: ID do portfolio (opcional, usa default se None)
    """
    ticker: str
    lado: str  # "COMPRA" ou "VENDA"
    quantidade: int
    preco_limite: Optional[Decimal] = None
    portfolio_id: Optional[str] = None

    def __post_init__(self):
        """Validação básica do command."""
        if not self.ticker:
            raise ValueError("ticker é obrigatório")
        if self.lado not in ("COMPRA", "VENDA"):
            raise ValueError(f"lado deve ser 'COMPRA' ou 'VENDA', recebido: {self.lado}")
        if self.quantidade <= 0:
            raise ValueError(f"quantidade deve ser positiva, recebido: {self.quantidade}")
