# -*- coding: utf-8 -*-
"""PositionTracker — rastreamento de posição com Stop Loss / Take Profit.

PositionTrackerPort define a interface abstrata.
SimpleTracker é a implementação netting (1 posição/ticker).
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from decimal import Decimal


class PositionTrackerPort(ABC):
    """Interface abstrata para rastreamento de posição (nomenclatura MT5-compatible)."""

    @abstractmethod
    def open_position(self, ticker: str, preco_entrada: Decimal,
                      take_profit_pct: Decimal | None = None,
                      stop_loss_pct: Decimal | None = None) -> None: ...

    @abstractmethod
    def close_position(self, ticker: str) -> None: ...

    @abstractmethod
    def get_position(self, ticker: str) -> dict | None: ...

    @abstractmethod
    def check_price(self, ticker: str, preco_atual: Decimal): ...

    @abstractmethod
    def list_positions(self) -> list[dict]: ...

    @abstractmethod
    def restore_positions(self, positions: list[dict]) -> None: ...

    @abstractmethod
    def set_reentry_state(self, ticker: str, *, crossover_price: Decimal,
                          swing_low: Decimal | None) -> None: ...

    @abstractmethod
    def get_reentry_state(self, ticker: str) -> dict | None: ...

    @abstractmethod
    def tick_reentry(self, ticker: str) -> None: ...

    @abstractmethod
    def clear_reentry_state(self, ticker: str) -> None: ...


class SimpleTracker(PositionTrackerPort):
    """Implementação netting — 1 posição por ticker. Nomenclatura MT5-compatible."""

    REENTRY_MAX_TICKS = 200
    FIB_LEVEL = Decimal("0.618")

    def __init__(
        self,
        stop_loss_pct: Decimal = Decimal("0.005"),
        take_profit_pct: Decimal = Decimal("0.10"),
        trailing_activation_pct: Decimal = Decimal("0.002"),
        trailing_distance_pct: Decimal = Decimal("0.0015"),
        breakeven_activation_pct: Decimal = Decimal("0.001"),
    ):
        self._stop_loss_pct = stop_loss_pct
        self._take_profit_pct = take_profit_pct
        self._trailing_activation_pct = trailing_activation_pct
        self._trailing_distance_pct = trailing_distance_pct
        self._breakeven_activation_pct = breakeven_activation_pct
        self._positions: dict[str, dict] = {}
        self._trailing: dict[str, dict] = {}
        self._reentry: dict[str, dict] = {}
        self._next_ticket = 1

    def open_position(self, ticker: str, preco_entrada: Decimal,
                      take_profit_pct: Decimal | None = None,
                      stop_loss_pct: Decimal | None = None) -> None:
        ticket = self._next_ticket
        self._next_ticket += 1
        self._positions[ticker] = {
            "ticker": ticker,
            "ticket": ticket,
            "preco_entrada": preco_entrada,
            "status": "aberta",
            "position_type": "BUY",
            "take_profit_pct": take_profit_pct or self._take_profit_pct,
            "stop_loss_pct": stop_loss_pct or self._stop_loss_pct,
            "breakeven_activated": False,
        }

    def close_position(self, ticker: str) -> None:
        self._positions.pop(ticker, None)
        self._trailing.pop(ticker, None)

    def get_position(self, ticker: str) -> dict | None:
        return self._positions.get(ticker)

    def check_price(self, ticker: str, preco_atual: Decimal):
        from .signal import SinalEstrategia, TipoSinal

        pos = self._positions.get(ticker)
        if pos is None:
            return None

        entrada = pos["preco_entrada"]
        tp_pct = pos.get("take_profit_pct", self._take_profit_pct)
        sl_pct = pos.get("stop_loss_pct", self._stop_loss_pct)
        variacao = (preco_atual - entrada) / entrada

        if variacao <= -sl_pct:
            if pos.get("breakeven_activated"):
                return SinalEstrategia(
                    ticker=ticker,
                    tipo=TipoSinal.VENDA,
                    preco=entrada,
                    razao=f"Breakeven acionado ({variacao * 100:.1f}%)",
                )
            preco_threshold = entrada * (Decimal("1") - sl_pct)
            return SinalEstrategia(
                ticker=ticker,
                tipo=TipoSinal.VENDA,
                preco=preco_threshold,
                razao=f"Stop Loss acionado (-{abs(variacao) * 100:.1f}%)",
            )

        if variacao >= tp_pct:
            preco_threshold = entrada * (Decimal("1") + tp_pct)
            return SinalEstrategia(
                ticker=ticker,
                tipo=TipoSinal.VENDA,
                preco=preco_threshold,
                razao=f"Take Profit acionado (+{variacao * 100:.1f}%)",
            )

        trailing_stop = self.get_trailing_stop(ticker)
        if trailing_stop is not None and preco_atual <= trailing_stop:
            return SinalEstrategia(
                ticker=ticker,
                tipo=TipoSinal.VENDA,
                preco=trailing_stop,
                razao=f"Trailing Stop acionado (+{variacao * 100:.1f}%)",
            )

        return None

    def list_positions(self) -> list[dict]:
        return list(self._positions.values())

    def restore_positions(self, positions: list[dict]) -> None:
        """Restaura posições salvas (facade persistence)."""
        for pos in positions:
            ticker = pos["ticker"]
            tp_raw = pos.get("take_profit_pct")
            tp_pct = Decimal(str(tp_raw)) if tp_raw is not None else self._take_profit_pct
            sl_raw = pos.get("stop_loss_pct")
            sl_pct = Decimal(str(sl_raw)) if sl_raw is not None else self._stop_loss_pct
            ticket = pos.get("ticket", self._next_ticket)
            if isinstance(ticket, int):
                self._next_ticket = max(self._next_ticket, ticket + 1)
            else:
                ticket = self._next_ticket
                self._next_ticket += 1
            self._positions[ticker] = {
                "ticker": ticker,
                "ticket": ticket,
                "preco_entrada": Decimal(str(pos["preco_entrada"])),
                "status": "aberta",
                "position_type": "BUY",
                "take_profit_pct": tp_pct,
                "stop_loss_pct": sl_pct,
                "breakeven_activated": bool(pos.get("breakeven_activated")),
            }
            trailing_pico = pos.get("trailing_pico")
            trailing_stop = pos.get("trailing_stop")
            if trailing_pico is not None and trailing_stop is not None:
                self._trailing[ticker] = {
                    "pico": Decimal(str(trailing_pico)),
                    "stop": Decimal(str(trailing_stop)),
                }

    def update_trailing(self, ticker: str, preco_atual: Decimal) -> None:
        pos = self._positions.get(ticker)
        if pos is None:
            return

        entrada = pos["preco_entrada"]
        variacao = (preco_atual - entrada) / entrada

        if variacao < self._trailing_activation_pct:
            return

        novo_pico = max(preco_atual, self._trailing.get(ticker, {}).get("pico", Decimal("0")))
        novo_stop = novo_pico * (Decimal("1") - self._trailing_distance_pct)

        breakeven = entrada
        if novo_stop < breakeven:
            novo_stop = breakeven

        self._trailing[ticker] = {"pico": novo_pico, "stop": novo_stop}

    def get_trailing_stop(self, ticker: str) -> Decimal | None:
        t = self._trailing.get(ticker)
        return t["stop"] if t else None

    def update_breakeven(self, ticker: str, preco_atual: Decimal) -> dict | None:
        """Breakeven standalone: ao atingir +0.10%, move SL para o preço de entrada.

        Returns dict with trigger_price e breakeven_price quando ativado, None caso contrário.
        """
        pos = self._positions.get(ticker)
        if pos is None or pos.get("breakeven_activated"):
            return None

        entrada = pos["preco_entrada"]
        variacao = (preco_atual - entrada) / entrada

        if variacao >= self._breakeven_activation_pct:
            pos["stop_loss_pct"] = Decimal("0")
            pos["breakeven_activated"] = True
            return {"trigger_price": preco_atual, "breakeven_price": entrada}
        return None

    def update_take_profit(self, ticker: str, new_tp_pct: Decimal) -> bool:
        """Atualiza TP de uma posição aberta (TP dinâmico reavaliado a cada tick)."""
        pos = self._positions.get(ticker)
        if pos is None:
            return False
        pos["take_profit_pct"] = new_tp_pct
        return True

    # ── Re-entry state ──

    def set_reentry_state(self, ticker: str, *, crossover_price: Decimal,
                          swing_low: Decimal | None) -> None:
        fib_level = None
        if swing_low is not None:
            distance = crossover_price - swing_low
            fib_level = swing_low + distance * self.FIB_LEVEL
        self._reentry[ticker] = {
            "crossover_price": crossover_price,
            "swing_low": swing_low,
            "fib_level": fib_level,
            "ticks_since_signal": 0,
        }

    def get_reentry_state(self, ticker: str) -> dict | None:
        return self._reentry.get(ticker)

    def tick_reentry(self, ticker: str) -> None:
        state = self._reentry.get(ticker)
        if state is None:
            return
        state["ticks_since_signal"] += 1
        if state["ticks_since_signal"] >= self.REENTRY_MAX_TICKS:
            del self._reentry[ticker]

    def clear_reentry_state(self, ticker: str) -> None:
        self._reentry.pop(ticker, None)


# Backward-compatible alias
PositionTracker = SimpleTracker

__all__ = ["PositionTrackerPort", "SimpleTracker", "PositionTracker"]
