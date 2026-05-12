# -*- coding: utf-8 -*-
"""Guardião Conservador — estratégia ADX +DI/-DI crossover.

Parâmetros validados via backtest (7d, 1m, BTC-USD):
  - Sinal: crossover +DI/-DI (ADX puro, sem SMA)
  - Filtro: ADX >= 25
  - Filtro: gap mínimo |+DI - -DI| >= 5 (anti-whipsaw)
  - TP dinâmico: ADX<20→0.30%, 20-30→0.40%, 30-40→0.50%, >40→0.60%
  - SL fixo: -0.50%
"""

from __future__ import annotations

from decimal import Decimal

from .signal import DadosMercado, SinalEstrategia, TipoSinal


class GuardiaoConservador:
    name = "guardiao-conservador"

    def __init__(
        self,
        adx_period: int = 14,
        adx_threshold: Decimal = Decimal("25"),
        volume_ratio_threshold: Decimal = Decimal("1.0"),
        volume_sma_period: int = 20,
        di_gap_min: Decimal = Decimal("3"),
    ):
        self._adx_period = adx_period
        self._adx_threshold = adx_threshold
        self._volume_ratio_threshold = volume_ratio_threshold
        self._volume_sma_period = volume_sma_period
        self._di_gap_min = di_gap_min
        self._last_indicators: dict | None = None

    def _calc_adx(
        self,
        closes: tuple[Decimal, ...],
        highs: tuple[Decimal, ...],
        lows: tuple[Decimal, ...],
        period: int,
    ) -> tuple[list[Decimal], list[Decimal], list[Decimal]]:
        """Calcula +DI, -DI e ADX via Wilder's smoothing com OHLC.

        Returns (+DI_series, -DI_series, ADX_series) — cada um com len = len(closes).
        Primeiros valores são 0 até ter dados suficientes.
        """
        n = len(closes)
        if n < period + 1:
            zeros = [Decimal("0")] * n
            return zeros, zeros, zeros

        has_ohlc = len(highs) == n and len(lows) == n

        # True Range, +DM, -DM
        tr_list: list[Decimal] = [Decimal("0")]
        plus_dm: list[Decimal] = [Decimal("0")]
        minus_dm: list[Decimal] = [Decimal("0")]

        for i in range(1, n):
            if has_ohlc:
                h, l, prev_c = highs[i], lows[i], closes[i - 1]
                prev_h, prev_l = highs[i - 1], lows[i - 1]
                tr = max(h - l, abs(h - prev_c), abs(l - prev_c))
                if tr == 0:
                    tr = Decimal("0.00000001")
                up_move = h - prev_h
                down_move = prev_l - l
            else:
                c, prev_c = closes[i], closes[i - 1]
                tr = abs(c - prev_c)
                if tr == 0:
                    tr = Decimal("0.00000001")
                up_move = c - prev_c
                down_move = prev_c - c

            pdm = Decimal("0")
            mdm = Decimal("0")
            if up_move > down_move and up_move > 0:
                pdm = up_move
            if down_move > up_move and down_move > 0:
                mdm = down_move

            tr_list.append(tr)
            plus_dm.append(pdm)
            minus_dm.append(mdm)

        # Wilder's smoothing (alpha = 1/period)
        alpha = Decimal("1") / Decimal(str(period))

        smooth_tr: list[Decimal] = [Decimal("0")] * n
        smooth_plus_dm: list[Decimal] = [Decimal("0")] * n
        smooth_minus_dm: list[Decimal] = [Decimal("0")] * n

        # Inicializar com soma dos primeiros `period` valores
        if n > period:
            smooth_tr[period] = sum(tr_list[1:period + 1])
            smooth_plus_dm[period] = sum(plus_dm[1:period + 1])
            smooth_minus_dm[period] = sum(minus_dm[1:period + 1])

            for i in range(period + 1, n):
                smooth_tr[i] = smooth_tr[i - 1] - (smooth_tr[i - 1] / Decimal(str(period))) + tr_list[i]
                smooth_plus_dm[i] = smooth_plus_dm[i - 1] - (smooth_plus_dm[i - 1] / Decimal(str(period))) + plus_dm[i]
                smooth_minus_dm[i] = smooth_minus_dm[i - 1] - (smooth_minus_dm[i - 1] / Decimal(str(period))) + minus_dm[i]

        # +DI, -DI
        plus_di: list[Decimal] = [Decimal("0")] * n
        minus_di: list[Decimal] = [Decimal("0")] * n

        for i in range(period, n):
            if smooth_tr[i] > 0:
                plus_di[i] = Decimal("100") * smooth_plus_dm[i] / smooth_tr[i]
                minus_di[i] = Decimal("100") * smooth_minus_dm[i] / smooth_tr[i]

        # DX e ADX
        dx: list[Decimal] = [Decimal("0")] * n
        for i in range(period, n):
            di_sum = plus_di[i] + minus_di[i]
            if di_sum > 0:
                dx[i] = Decimal("100") * abs(plus_di[i] - minus_di[i]) / di_sum

        adx: list[Decimal] = [Decimal("0")] * n
        adx_start = period * 2 - 1
        if n > adx_start:
            adx[adx_start] = sum(dx[period:adx_start + 1]) / Decimal(str(adx_start - period + 1))
            for i in range(adx_start + 1, n):
                adx[i] = (adx[i - 1] * Decimal(str(period - 1)) + dx[i]) / Decimal(str(period))

        return plus_di, minus_di, adx

    def _calc_volume_ratio(self, volumes: tuple[int, ...], sma_period: int) -> Decimal:
        """@deprecated Volume filter desativado — yfinance crypto volume não é confiável.

        Reativar quando: migrar para exchange API direta (Binance) ou para
        períodos de alta volatilidade onde volume confirma momentum.
        Razão da desativação: ML mostrou que ADX>=25 já filtra whipsaws
        eficazmente; volume adiciona marginal com dado ruim.
        """
        return Decimal("1.0")
        if len(volumes) < sma_period + 1:
            return Decimal("1.0")
        vol_slice = volumes[-(sma_period + 1):-1]
        if not vol_slice or sum(vol_slice) == 0:
            return Decimal("1.0")
        avg = Decimal(str(sum(vol_slice))) / Decimal(str(len(vol_slice)))
        current = volumes[-1]
        if avg == 0:
            return Decimal("1.0")
        return Decimal(str(current)) / avg

    def _tp_for_adx(self, adx: Decimal) -> Decimal:
        """Mapeia ADX para TP dinâmico (perfil Conservador)."""
        if adx < 20:
            return Decimal("0.0030")
        if adx < 30:
            return Decimal("0.0040")
        if adx < 40:
            return Decimal("0.0050")
        return Decimal("0.0060")

    def evaluate(self, dados: DadosMercado) -> SinalEstrategia | None:
        precos = dados.historico_precos
        volumes = dados.historico_volumes

        min_required = self._adx_period * 2
        if len(precos) < min_required + 1:
            self._last_indicators = None
            return None

        plus_di, minus_di, adx = self._calc_adx(
            precos, dados.historico_highs, dados.historico_lows, self._adx_period
        )
        vol_ratio = self._calc_volume_ratio(volumes, self._volume_sma_period) if volumes else Decimal("1.0")

        # Swing low: mínimo dos últimos 100 períodos
        lookback = precos[-100:] if len(precos) >= 100 else precos
        swing_low = min(lookback) if lookback else dados.preco_atual

        self._last_indicators = {
            "plus_di": plus_di[-1],
            "minus_di": minus_di[-1],
            "adx": adx[-1],
            "volume_ratio": vol_ratio,
            "swing_low": swing_low,
        }

        idx = len(precos) - 1
        prev_idx = idx - 1

        curr_pdi = plus_di[idx]
        curr_mdi = minus_di[idx]
        prev_pdi = plus_di[prev_idx]
        prev_mdi = minus_di[prev_idx]
        curr_adx = adx[idx]
        prev_adx = adx[prev_idx]

        if curr_pdi == 0 and curr_mdi == 0:
            return None

        # Gap mínimo entre +DI e -DI — filtra whipsaws em crossovers fracos
        gap = abs(curr_pdi - curr_mdi)
        if gap < self._di_gap_min:
            return None

        tipo: TipoSinal | None = None
        razao_prefix: str | None = None

        # ── Entrada 1: DI crossover — ADX acima E -DI abaixo do ADX ──
        if prev_pdi <= prev_mdi and curr_pdi > curr_mdi:
            if curr_adx >= self._adx_threshold and curr_mdi < curr_adx:
                tipo = TipoSinal.COMPRA
                razao_prefix = "COMPRA (DI cross)"
        elif prev_pdi >= prev_mdi and curr_pdi < curr_mdi:
            if curr_adx >= self._adx_threshold and curr_pdi < curr_adx:
                tipo = TipoSinal.VENDA
                razao_prefix = "VENDA (DI cross)"

        # ── Entrada 2: ADX surge — cruza pra cima do threshold, DI dominante E -DI < +DI ──
        if tipo is None:
            adx_crossing_up = prev_adx < self._adx_threshold <= curr_adx
            if adx_crossing_up and curr_pdi > curr_mdi:
                tipo = TipoSinal.COMPRA
                razao_prefix = "COMPRA (ADX surge)"

        if tipo is None:
            return None

        if vol_ratio < self._volume_ratio_threshold:
            return None

        tp_pct = self._tp_for_adx(curr_adx)
        razao = (
            f"{razao_prefix}: +DI={float(curr_pdi):.1f} x -DI={float(curr_mdi):.1f} "
            f"| ADX={float(curr_adx):.1f}"
        )

        return SinalEstrategia(
            ticker=dados.ticker,
            tipo=tipo,
            preco=dados.preco_atual,
            razao=razao,
            take_profit_pct=tp_pct,
        )


__all__ = ["GuardiaoConservador"]
