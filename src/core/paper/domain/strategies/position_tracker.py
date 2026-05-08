# -*- coding: utf-8 -*-
"""PositionTracker — rastreamento de posição com Stop Loss / Take Profit."""

from __future__ import annotations

from decimal import Decimal


class PositionTracker:
    def __init__(
        self,
        stop_loss_pct: Decimal = Decimal("0.05"),
        take_profit_pct: Decimal = Decimal("0.10"),
    ):
        self._stop_loss_pct = stop_loss_pct
        self._take_profit_pct = take_profit_pct
        self._positions: dict[str, dict] = {}

    def open_position(self, ticker: str, preco_entrada: Decimal) -> None:
        if ticker not in self._positions:
            self._positions[ticker] = {
                "ticker": ticker,
                "preco_entrada": preco_entrada,
                "status": "aberta",
            }

    def close_position(self, ticker: str) -> None:
        self._positions.pop(ticker, None)

    def get_position(self, ticker: str) -> dict | None:
        return self._positions.get(ticker)

    def check_price(self, ticker: str, preco_atual: Decimal):
        from .signal import SinalEstrategia, TipoSinal

        pos = self._positions.get(ticker)
        if pos is None:
            return None

        entrada = pos["preco_entrada"]
        variacao = (preco_atual - entrada) / entrada

        if variacao <= -self._stop_loss_pct:
            return SinalEstrategia(
                ticker=ticker,
                tipo=TipoSinal.VENDA,
                preco=preco_atual,
                razao=f"Stop Loss acionado (-{abs(variacao) * 100:.1f}%)",
            )

        if variacao >= self._take_profit_pct:
            return SinalEstrategia(
                ticker=ticker,
                tipo=TipoSinal.VENDA,
                preco=preco_atual,
                razao=f"Take Profit acionado (+{variacao * 100:.1f}%)",
            )

        return None

    def list_positions(self) -> list[dict]:
        return list(self._positions.values())


__all__ = ["PositionTracker"]
