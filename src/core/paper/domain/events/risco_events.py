"""
Eventos de Risco e Posição - Stop loss e mudanças de posição.
"""

from __future__ import annotations

from dataclasses import dataclass

from .base_event import DomainEvent


@dataclass(frozen=True, kw_only=True)
class StopLossAcionado(DomainEvent):
    """
    Evento disparado quando um stop loss é disparado.

    Trigger: Preço atinge nível de stop loss
    """

    ticker: str
    preco_trigger: float
    perda_percentual: float
    quantidade: int
    posicao_id: str | None = None


@dataclass(frozen=True, kw_only=True)
class PosicaoAtualizada(DomainEvent):
    """
    Evento disparado quando uma posição é modificada.

    Trigger: Execução de ordem altera posição
    """

    ticker: str
    quantidade_anterior: int
    quantidade_nova: int
    preco_medio_novo: float
    preco_atual: float
    pnl_nao_realizado: float | None = None


__all__ = ["StopLossAcionado", "PosicaoAtualizada"]
