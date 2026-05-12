# -*- coding: utf-8 -*-
"""@deprecated CalibradorDinamico — legado da versão v1 (SMA crossover).

Substituído pelo TP dinâmico por faixa ADX no Guardião Conservador v2.
Mantido como referência para estudo comparativo entre ATR-based e ADX-based.
Não é mais importado no pipeline ativo.
"""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal


@dataclass(frozen=True)
class ParametrosCalibrados:
    sl_pct: Decimal
    tp_pct: Decimal
    range_min: bool


class CalibradorDinamico:
    """Calcula SL/TP dinamicamente via volatilidade média de preço (NVR).

    NVR = Normalized Volatility Range — média das variações absolutas
    entre closes consecutivos, normalizada pelo último preço.
    """

    def __init__(
        self,
        periodo: int = 14,
        k_sl: Decimal = Decimal("1.5"),
        k_tp: Decimal = Decimal("2.0"),
        min_atr_pct: Decimal = Decimal("0.0001"),
    ):
        self._periodo = periodo
        self._k_sl = k_sl
        self._k_tp = k_tp
        self._min_atr_pct = min_atr_pct

    def calibrar(self, precos: list[Decimal]) -> ParametrosCalibrados:
        if len(precos) < self._periodo + 1:
            return ParametrosCalibrados(
                sl_pct=Decimal("0.003"),
                tp_pct=Decimal("0.005"),
                range_min=True,
            )

        ranges = self._calc_price_ranges(precos)
        avg_range = sum(ranges[-self._periodo:]) / self._periodo
        ultimo = precos[-1]

        if ultimo == 0:
            return ParametrosCalibrados(
                sl_pct=Decimal("0.003"),
                tp_pct=Decimal("0.005"),
                range_min=True,
            )

        range_pct = avg_range / ultimo

        if range_pct < self._min_atr_pct:
            return ParametrosCalibrados(
                sl_pct=Decimal("0.003"),
                tp_pct=Decimal("0.005"),
                range_min=True,
            )

        sl_pct = self._k_sl * range_pct
        tp_pct = self._k_tp * range_pct

        return ParametrosCalibrados(
            sl_pct=sl_pct,
            tp_pct=tp_pct,
            range_min=False,
        )

    def _calc_price_ranges(self, precos: list[Decimal]) -> list[Decimal]:
        """Variação absoluta entre closes consecutivos."""
        return [abs(precos[i] - precos[i - 1]) for i in range(1, len(precos))]


__all__ = ["CalibradorDinamico", "ParametrosCalibrados"]
