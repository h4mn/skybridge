"""ReversalCollector — coleta dados pós-entrada para estudo estatístico (SKY-136)."""

from __future__ import annotations

import csv
import logging
import os
from decimal import Decimal
from pathlib import Path

logger = logging.getLogger(__name__)

_DEFAULT_CSV = str(
    Path(__file__).resolve().parents[4] / "data" / "estudo-reversao.csv"
)

_FIELDS = [
    "ticker",
    "preco_entrada",
    "preco_saida",
    "pico",
    "variacao_max_pct",
    "reversao_pct",
    "drawdown_max_pct",
    "tempo_ate_pico_ticks",
    "duracao_ticks",
]


class ReversalCollector:
    """Coleta dados de preço pós-entrada para calibrar trailing stop.

    Ciclo de vida:
        start_tracking() → update() [N ticks] → stop_tracking()
    """

    def __init__(self, csv_path: str = _DEFAULT_CSV):
        self._csv_path = csv_path
        self._tracking: dict[str, dict] = {}

    def is_tracking(self, ticker: str) -> bool:
        return ticker in self._tracking

    def start_tracking(
        self, ticker: str, preco_entrada: Decimal, timestamp: str
    ) -> None:
        self._tracking[ticker] = {
            "ticker": ticker,
            "preco_entrada": preco_entrada,
            "timestamp_entrada": timestamp,
            "pico": preco_entrada,
            "tempo_ate_pico_ticks": 0,
            "drawdown_max": Decimal("0"),
            "tick_count": 0,
        }

    def update(self, ticker: str, preco_atual: Decimal) -> None:
        t = self._tracking.get(ticker)
        if t is None:
            return

        t["tick_count"] += 1

        if preco_atual > t["pico"]:
            t["pico"] = preco_atual
            t["tempo_ate_pico_ticks"] = t["tick_count"]

        if t["pico"] != Decimal("0"):
            drawdown = (t["pico"] - preco_atual) / t["pico"]
            if drawdown > t["drawdown_max"]:
                t["drawdown_max"] = drawdown

    def stop_tracking(
        self, ticker: str, preco_saida: Decimal
    ) -> dict | None:
        t = self._tracking.pop(ticker, None)
        if t is None:
            return None

        pico = t["pico"]
        entrada = t["preco_entrada"]

        reversao = (
            (pico - preco_saida) / pico
            if pico != Decimal("0")
            else Decimal("0")
        )

        record = {
            "ticker": ticker,
            "preco_entrada": float(entrada),
            "preco_saida": float(preco_saida),
            "pico": float(pico),
            "variacao_max_pct": round(
                float((pico - entrada) / entrada * 100), 4
            ),
            "reversao_pct": round(float(reversao * 100), 4),
            "drawdown_max_pct": round(float(t["drawdown_max"] * 100), 4),
            "tempo_ate_pico_ticks": t["tempo_ate_pico_ticks"],
            "duracao_ticks": t["tick_count"],
        }

        self._save(record)
        return record

    def _save(self, record: dict) -> None:
        os.makedirs(os.path.dirname(self._csv_path) or ".", exist_ok=True)
        file_exists = os.path.isfile(self._csv_path)

        with open(self._csv_path, "a", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=_FIELDS)
            if not file_exists:
                writer.writeheader()
            writer.writerow(record)

        logger.debug(f"[REVERSAL] {record['ticker']} salvo em {self._csv_path}")


__all__ = ["ReversalCollector"]
