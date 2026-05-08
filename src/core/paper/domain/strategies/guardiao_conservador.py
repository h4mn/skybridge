# -*- coding: utf-8 -*-
"""Guardião Conservador — estratégia SMA crossover conservadora."""

from __future__ import annotations

from decimal import Decimal

from .signal import DadosMercado, SinalEstrategia, TipoSinal


class GuardiaoConservador:
    name = "guardiao-conservador"

    def __init__(self, short_period: int = 5, long_period: int = 15):
        self._short_period = short_period
        self._long_period = long_period

    def _calculate_sma(
        self, prices: tuple[Decimal, ...], period: int
    ) -> Decimal | None:
        if len(prices) < period:
            return None
        window = prices[-period:]
        return sum(window) / Decimal(period)

    def _detect_crossover(
        self,
        short_sma: Decimal,
        long_sma: Decimal,
        prev_short_sma: Decimal,
        prev_long_sma: Decimal,
    ) -> TipoSinal | None:
        if prev_short_sma is None or prev_long_sma is None:
            return None
        if prev_short_sma <= prev_long_sma and short_sma > long_sma:
            return TipoSinal.COMPRA
        if prev_short_sma >= prev_long_sma and short_sma < long_sma:
            return TipoSinal.VENDA
        return None

    def evaluate(self, dados: DadosMercado) -> SinalEstrategia | None:
        precos = dados.historico_precos

        if len(precos) < self._long_period + 1:
            return None

        short_sma = self._calculate_sma(precos, self._short_period)
        long_sma = self._calculate_sma(precos, self._long_period)

        if short_sma is None or long_sma is None:
            return None

        prev_precos = precos[:-1]
        prev_short_sma = self._calculate_sma(prev_precos, self._short_period)
        prev_long_sma = self._calculate_sma(prev_precos, self._long_period)

        tipo = self._detect_crossover(short_sma, long_sma, prev_short_sma, prev_long_sma)

        if tipo is None:
            return None

        if tipo == TipoSinal.COMPRA:
            razao = f"SMA{self._short_period} cruzou acima de SMA{self._long_period}"
        else:
            razao = f"SMA{self._short_period} cruzou abaixo de SMA{self._long_period}"

        return SinalEstrategia(
            ticker=dados.ticker,
            tipo=tipo,
            preco=dados.preco_atual,
            razao=razao,
        )


__all__ = ["GuardiaoConservador"]
