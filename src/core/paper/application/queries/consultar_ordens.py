# -*- coding: utf-8 -*-
"""Query para consultar ordens do portfolio."""
from dataclasses import dataclass
from typing import Optional, List


@dataclass
class ConsultarOrdensQuery:
    """Query: consulta de ordens do portfolio.

    Attributes:
        ticker: Filtrar por ticker (opcional)
        lado: Filtrar por lado "COMPRA" ou "VENDA" (opcional)
        status: Filtrar por status (opcional)
        limite: Limite de resultados (opcional)
    """
    ticker: Optional[str] = None
    lado: Optional[str] = None
    status: Optional[str] = None
    limite: Optional[int] = None

    def __post_init__(self):
        if self.lado and self.lado not in ("COMPRA", "VENDA"):
            raise ValueError(f"lado deve ser 'COMPRA' ou 'VENDA', recebido: {self.lado}")
        if self.limite is not None and self.limite <= 0:
            raise ValueError(f"limite deve ser positivo, recebido: {self.limite}")


@dataclass
class OrdemItem:
    """Item de ordem no resultado."""
    id: str
    ticker: str
    lado: str
    quantidade: int
    preco_execucao: float
    valor_total: float
    status: str
    timestamp: str


@dataclass
class OrdensResult:
    """Resultado da consulta de ordens."""
    ordens: List[OrdemItem]
    total: int
