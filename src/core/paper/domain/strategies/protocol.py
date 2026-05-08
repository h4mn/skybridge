# -*- coding: utf-8 -*-
"""StrategyProtocol — contrato para estratégias de trading."""

from __future__ import annotations

from typing import Protocol, runtime_checkable

from .signal import DadosMercado, SinalEstrategia


@runtime_checkable
class StrategyProtocol(Protocol):
    name: str

    def evaluate(self, dados: DadosMercado) -> SinalEstrategia | None: ...


__all__ = ["StrategyProtocol"]
