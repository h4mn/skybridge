# -*- coding: utf-8 -*-
"""Query para consultar cotação de um ticker."""
from dataclasses import dataclass
from decimal import Decimal
from typing import Optional


@dataclass
class ConsultarCotacaoQuery:
    """Query: consulta de cotação atual de um ativo.

    Attributes:
        ticker: Código do ativo (ex: "PETR4.SA")
    """
    ticker: str

    def __post_init__(self):
        if not self.ticker:
            raise ValueError("ticker é obrigatório")


@dataclass
class CotacaoResult:
    """Resultado da consulta de cotação."""
    ticker: str
    preco: Decimal
    variacao: Optional[Decimal] = None  # Variação percentual do dia
    timestamp: Optional[str] = None
