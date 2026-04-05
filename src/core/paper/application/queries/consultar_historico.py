# -*- coding: utf-8 -*-
"""Query para consultar histórico de preços de um ticker."""
from dataclasses import dataclass
from decimal import Decimal
from typing import List, Optional


@dataclass
class ConsultarHistoricoQuery:
    """Query: consulta de histórico de preços.

    Attributes:
        ticker: Código do ativo (ex: "PETR4.SA")
        dias: Número de dias para buscar (padrão: 30)
    """
    ticker: str
    dias: int = 30

    def __post_init__(self):
        if not self.ticker:
            raise ValueError("ticker é obrigatório")
        if self.dias <= 0:
            raise ValueError(f"dias deve ser positivo, recebido: {self.dias}")


@dataclass
class CandleData:
    """Dados de um candle (OHLCV)."""
    timestamp: str
    abertura: Decimal
    alta: Decimal
    baixa: Decimal
    fechamento: Decimal
    volume: Optional[int] = None


@dataclass
class HistoricoResult:
    """Resultado da consulta de histórico."""
    ticker: str
    candles: List[CandleData]
