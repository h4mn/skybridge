# -*- coding: utf-8 -*-
"""
Teste de compatibilidade DuckDB → SQLite.

Task 6.7: DuckDB sqlite_scan() lê database gerado pelo SQLitePaperState.
"""

import sqlite3
from pathlib import Path

import pytest

from src.core.paper.adapters.persistence.sqlite_paper_state import SQLitePaperState

try:
    import duckdb
    HAS_DUCKDB = True
except ImportError:
    HAS_DUCKDB = False


@pytest.mark.skipif(not HAS_DUCKDB, reason="DuckDB não instalado")
class TestDuckDBCompat:
    def test_sqlite_scan_le_database(self, tmp_path):
        """Scenario: DuckDB consegue ler database SQLite."""
        db_path = tmp_path / "test.db"
        state = SQLitePaperState(str(db_path))
        state.save_order({
            "created_at": "2026-01-01T00:00:00", "id": "ord-1",
            "ticker": "BTC-USD", "side": "buy", "quantity": 1,
            "price": "50000", "total_value": "50000", "status": "EXECUTADA",
            "order_type": "open", "broker": "binance", "strategy_name": "guardiao",
        })
        state.save_tick({
            "time": "2026-01-01T10:00:00", "symbol": "BTC-USD",
            "broker": "binance", "price": "50000.12", "volume": 100,
        })
        state.close()

        con = duckdb.connect()
        result = con.execute(
            f"SELECT * FROM sqlite_scan('{db_path}', 'orders')"
        ).fetchall()
        assert len(result) == 1
        assert result[0][1] == "ord-1"  # id column

        ticks = con.execute(
            f"SELECT * FROM sqlite_scan('{db_path}', 'ticks_raw')"
        ).fetchall()
        assert len(ticks) == 1
        con.close()
