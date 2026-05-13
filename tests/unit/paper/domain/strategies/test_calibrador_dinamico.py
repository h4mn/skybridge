# -*- coding: utf-8 -*-
"""Testes para CalibradorDinamico — calibração ATR(14) para SL/TP."""

from decimal import Decimal

import pytest


class TestCalibradorATRBaixaVolatilidade:
    """DOC: specs/paper-guardiao-v2 — Volatilidade muito baixa: range_min = True."""

    def test_calibrador_atr_baixa_volatilidade(self):
        """WHEN ATR normalizado < 0.01% THEN range_min = True."""
        from src.core.paper.domain.strategies.calibrador_dinamico import (
            CalibradorDinamico,
            ParametrosCalibrados,
        )

        calibrador = CalibradorDinamico()
        precos = [Decimal("100000") + Decimal(i) for i in range(20)]

        resultado = calibrador.calibrar(precos)

        assert resultado.range_min is True


class TestCalibradorATRAltaVolatilidade:
    """DOC: specs/paper-guardiao-v2 — Volatilidade normal: retorna sl_pct e tp_pct."""

    def test_calibrador_atr_alta_volatilidade(self):
        """WHEN ATR normalizado > 0.01% THEN retorna sl_pct e tp_pct calculados."""
        from src.core.paper.domain.strategies.calibrador_dinamico import (
            CalibradorDinamico,
            ParametrosCalibrados,
        )

        calibrador = CalibradorDinamico()
        precos = [
            Decimal("80000") + Decimal(str(200 * (i % 5 - 2)))
            for i in range(30)
        ]

        resultado = calibrador.calibrar(precos)

        assert resultado.range_min is False
        assert resultado.sl_pct > 0
        assert resultado.tp_pct > resultado.sl_pct
        assert resultado.tp_pct > resultado.sl_pct
