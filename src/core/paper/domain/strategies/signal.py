# -*- coding: utf-8 -*-
"""Value Objects de sinal para estratégias de trading."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from decimal import Decimal
from enum import Enum


class TipoSinal(str, Enum):
    COMPRA = "compra"
    VENDA = "venda"
    NEUTRO = "neutro"


@dataclass(frozen=True)
class DadosMercado:
    ticker: str
    preco_atual: Decimal
    historico_precos: tuple[Decimal, ...] = ()
    historico_volumes: tuple[int, ...] = ()
    historico_highs: tuple[Decimal, ...] = ()
    historico_lows: tuple[Decimal, ...] = ()

    def __post_init__(self):
        if not isinstance(self.historico_precos, tuple):
            object.__setattr__(self, "historico_precos", tuple(self.historico_precos))
        if not isinstance(self.historico_volumes, tuple):
            object.__setattr__(self, "historico_volumes", tuple(self.historico_volumes))
        if not isinstance(self.historico_highs, tuple):
            object.__setattr__(self, "historico_highs", tuple(self.historico_highs))
        if not isinstance(self.historico_lows, tuple):
            object.__setattr__(self, "historico_lows", tuple(self.historico_lows))


@dataclass(frozen=True, kw_only=True)
class SinalEstrategia:
    ticker: str
    tipo: TipoSinal
    preco: Decimal
    razao: str
    timestamp: datetime = field(default_factory=datetime.now)
    take_profit_pct: Decimal | None = None

    def to_dict(self) -> dict:
        return {
            "ticker": self.ticker,
            "tipo": self.tipo.value,
            "preco": str(self.preco),
            "razao": self.razao,
            "timestamp": self.timestamp.isoformat(),
        }


__all__ = ["TipoSinal", "DadosMercado", "SinalEstrategia"]
