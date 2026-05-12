# -*- coding: utf-8 -*-
"""
Adapter - Paper State com persistência em SQLite+WAL.

Implementa PaperStatePort com CQS (Command-Query Separation):
- Queries granulares: get_position, list_orders, get_cashbook, get_closed_pnl
- Commands granulares: save_order, update_position, save_pnl, save_signal, save_tick, save_ohlcv
- Compat legado: carregar(), salvar(PaperStateData), resetar()
"""

import json
import sqlite3
from datetime import datetime
from decimal import Decimal
from pathlib import Path
from typing import Any, Dict, List, Optional

from ...ports.paper_state_port import PaperStateData, PaperStatePort

SCHEMA_PATH = Path(__file__).parent / "schema.sql"


class SQLitePaperState(PaperStatePort):
    """
    Persistência SQLite+WAL com CQS granular.

    Single connection reutilizada entre operações.
    WAL mode para concorrência read/write sem contenção.
    """

    def __init__(self, db_path: str):
        self._db_path = Path(db_path)
        self._db_path.parent.mkdir(parents=True, exist_ok=True)

        self._conn = sqlite3.connect(str(self._db_path))
        self._conn.row_factory = sqlite3.Row
        self._conn.execute("PRAGMA journal_mode=WAL")
        self._conn.execute("PRAGMA synchronous=NORMAL")
        self._conn.execute("PRAGMA busy_timeout=5000")
        self._conn.execute("PRAGMA foreign_keys=ON")
        self._init_schema()

    def _init_schema(self):
        with open(SCHEMA_PATH, "r", encoding="utf-8") as f:
            self._conn.executescript(f.read())
        self._migrate_missing_columns()
        self._conn.commit()

    def _migrate_missing_columns(self):
        """Adiciona colunas que faltam em tabelas existentes (ALTER TABLE)."""
        required = {
            "strategy_positions": ["opened_at TEXT", "closed_at TEXT"],
            "positions": ["opened_at TEXT", "closed_at TEXT", "grid_level INTEGER", "parent_position_id TEXT"],
            "orders": ["portfolio_id TEXT", "position_id INTEGER", "strategy_name TEXT"],
            "closed_pnl": ["reason TEXT"],
        }
        for table, columns in required.items():
            existing = {row[1] for row in self._conn.execute(f"PRAGMA table_info({table})").fetchall()}
            for col_def in columns:
                col_name = col_def.split()[0]
                if col_name not in existing:
                    self._conn.execute(f"ALTER TABLE {table} ADD COLUMN {col_def}")

    def close(self):
        if self._conn:
            self._conn.close()
            self._conn = None

    def create_backup(self, backup_dir: Path) -> Path:
        """Cria backup mensal via sqlite3 Online Backup API."""
        backup_dir = Path(backup_dir)
        backup_dir.mkdir(parents=True, exist_ok=True)
        now = datetime.now()
        backup_name = f"paper_state-{now.strftime('%Y-%m')}.db"
        backup_path = backup_dir / backup_name

        if backup_path.exists():
            return backup_path

        self._conn.commit()  # Flush antes do backup
        dest = sqlite3.connect(str(backup_path))
        try:
            self._conn.backup(dest)
        finally:
            dest.close()
        return backup_path

    # ── Queries ──

    def get_position(self, ticker: str, strategy_name: str) -> Optional[Dict[str, Any]]:
        cursor = self._conn.execute(
            "SELECT * FROM positions WHERE ticker=? AND strategy_name=?",
            (ticker, strategy_name),
        )
        row = cursor.fetchone()
        return dict(row) if row else None

    def list_orders(
        self,
        ticker: str,
        status: Optional[str] = None,
        broker: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        query = "SELECT * FROM orders WHERE ticker=?"
        params: list = [ticker]

        if status:
            query += " AND status=?"
            params.append(status)
        if broker:
            query += " AND broker=?"
            params.append(broker)

        query += " ORDER BY created_at"
        cursor = self._conn.execute(query, params)
        return [dict(row) for row in cursor.fetchall()]

    def get_cashbook(self) -> Dict[str, Any]:
        cursor = self._conn.execute("SELECT currency, amount, conversion_rate FROM cashbook_entries")
        return {row["currency"]: {"amount": row["amount"], "conversion_rate": row["conversion_rate"]} for row in cursor.fetchall()}

    def get_closed_pnl(self, ticker: str) -> List[Dict[str, Any]]:
        cursor = self._conn.execute(
            "SELECT * FROM closed_pnl WHERE ticker=? ORDER BY closed_at",
            (ticker,),
        )
        return [dict(row) for row in cursor.fetchall()]

    # ── Commands (públicos com commit) ──

    def save_order(self, order: Dict[str, Any]) -> None:
        self._insert_order(order)
        self._conn.commit()

    def _insert_order(self, order: Dict[str, Any]) -> None:
        self._conn.execute(
            "INSERT INTO orders "
            "(created_at, id, portfolio_id, ticker, side, quantity, price, "
            "total_value, currency, status, executed_at, order_type, position_id, "
            "broker, strategy_name) "
            "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (
                order.get("created_at", ""),
                order["id"],
                order.get("portfolio_id"),
                order["ticker"],
                order["side"],
                order["quantity"],
                order["price"],
                order["total_value"],
                order.get("currency", "USD"),
                order.get("status", "PENDING"),
                order.get("executed_at"),
                order.get("order_type", "open"),
                order.get("position_id"),
                order.get("broker", "paper"),
                order.get("strategy_name", "default"),
            ),
        )

    def update_position(self, ticker: str, strategy_name: str, data: Dict[str, Any]) -> None:
        self._upsert_position(ticker, strategy_name, data)
        self._conn.commit()

    def _upsert_position(self, ticker: str, strategy_name: str, data: Dict[str, Any]) -> None:
        existing = self.get_position(ticker, strategy_name)
        if existing:
            sets = []
            params: list = []
            for key, value in data.items():
                sets.append(f"{key}=?")
                params.append(value)
            params.extend([ticker, strategy_name])
            self._conn.execute(
                f"UPDATE positions SET {', '.join(sets)} WHERE ticker=? AND strategy_name=?",
                params,
            )
        else:
            self._conn.execute(
                "INSERT INTO positions "
                "(ticker, strategy_name, broker, side, quantity, avg_price, "
                "currency, status, opened_at, closed_at, grid_level, parent_position_id) "
                "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                (
                    ticker,
                    strategy_name,
                    data.get("broker", "paper"),
                    data.get("side", "long"),
                    data.get("quantity", 0),
                    data.get("avg_price", "0"),
                    data.get("currency", "USD"),
                    data.get("status", "open"),
                    data.get("opened_at", datetime.now().isoformat()),
                    data.get("closed_at"),
                    data.get("grid_level"),
                    data.get("parent_position_id"),
                ),
            )

    def save_pnl(self, pnl: Dict[str, Any]) -> None:
        self._insert_pnl(pnl)
        self._conn.commit()

    def _insert_pnl(self, pnl: Dict[str, Any]) -> None:
        self._conn.execute(
            "INSERT INTO closed_pnl "
            "(closed_at, ticker, strategy_name, broker, entry_price, exit_price, "
            "quantity, side, pnl_value, pnl_value_display, pnl_pct, reason) "
            "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (
                pnl["closed_at"],
                pnl["ticker"],
                pnl.get("strategy_name", "default"),
                pnl.get("broker", "paper"),
                pnl["entry_price"],
                pnl["exit_price"],
                pnl["quantity"],
                pnl.get("side", "long"),
                pnl["pnl_value"],
                pnl["pnl_value_display"],
                pnl["pnl_pct"],
                pnl.get("reason"),
            ),
        )

    def save_signal(self, signal: Dict[str, Any]) -> None:
        self._insert_signal(signal)
        self._conn.commit()

    def _insert_signal(self, signal: Dict[str, Any]) -> None:
        self._conn.execute(
            "INSERT INTO signals "
            "(created_at, ticker, strategy_name, broker, signal_type, price, "
            "reason, take_profit_pct) "
            "VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
            (
                signal["created_at"],
                signal["ticker"],
                signal.get("strategy_name", "default"),
                signal.get("broker", "paper"),
                signal["signal_type"],
                signal["price"],
                signal.get("reason"),
                signal.get("take_profit_pct"),
            ),
        )

    def save_tick(self, tick: Dict[str, Any]) -> None:
        self._insert_tick(tick)
        self._conn.commit()

    def _insert_tick(self, tick: Dict[str, Any]) -> None:
        self._conn.execute(
            "INSERT INTO ticks_raw (time, symbol, broker, price, volume, side) "
            "VALUES (?, ?, ?, ?, ?, ?)",
            (
                tick["time"],
                tick["symbol"],
                tick.get("broker", "paper"),
                tick["price"],
                tick.get("volume"),
                tick.get("side"),
            ),
        )

    def save_ohlcv(self, candle: Dict[str, Any]) -> None:
        self._insert_ohlcv(candle)
        self._conn.commit()

    def _insert_ohlcv(self, candle: Dict[str, Any]) -> None:
        self._conn.execute(
            "INSERT INTO ohlcv (time, symbol, broker, open, high, low, close, volume, interval) "
            "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (
                candle["time"],
                candle["symbol"],
                candle.get("broker", "paper"),
                candle["open"],
                candle["high"],
                candle["low"],
                candle["close"],
                candle.get("volume"),
                candle.get("interval", "1m"),
            ),
        )

    # ── Strategy Positions (PositionTracker) ──

    def _upsert_strategy_position(self, ticker: str, strategy_name: str, data: Dict[str, Any]) -> None:
        existing = self._conn.execute(
            "SELECT 1 FROM strategy_positions WHERE ticker=? AND strategy_name=?",
            (ticker, strategy_name),
        ).fetchone()
        if existing:
            sets = []
            params: list = []
            for key, value in data.items():
                sets.append(f"{key}=?")
                params.append(value)
            params.extend([ticker, strategy_name])
            self._conn.execute(
                f"UPDATE strategy_positions SET {', '.join(sets)} WHERE ticker=? AND strategy_name=?",
                params,
            )
        else:
            self._conn.execute(
                "INSERT INTO strategy_positions "
                "(ticker, strategy_name, broker, entry_price, side, status, "
                "take_profit_pct, stop_loss_pct, trailing_pico, trailing_stop, opened_at) "
                "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                (
                    ticker,
                    strategy_name,
                    data.get("broker", "paper"),
                    data.get("entry_price", "0"),
                    data.get("side", "long"),
                    data.get("status", "open"),
                    data.get("take_profit_pct"),
                    data.get("stop_loss_pct"),
                    data.get("trailing_pico"),
                    data.get("trailing_stop"),
                    data.get("opened_at", datetime.now().isoformat()),
                ),
            )

    def _close_strategy_position(self, ticker: str, strategy_name: str, data: Dict[str, Any]) -> None:
        self._conn.execute(
            "UPDATE strategy_positions SET status='closed', closed_at=? "
            "WHERE ticker=? AND strategy_name=?",
            (data.get("closed_at", datetime.now().isoformat()), ticker, strategy_name),
        )

    def get_strategy_position(self, ticker: str, strategy_name: str) -> Optional[Dict[str, Any]]:
        cursor = self._conn.execute(
            "SELECT * FROM strategy_positions WHERE ticker=? AND strategy_name=? AND status='open'",
            (ticker, strategy_name),
        )
        row = cursor.fetchone()
        return dict(row) if row else None

    def list_open_strategy_positions(self, strategy_name: str = "") -> List[Dict[str, Any]]:
        query = "SELECT * FROM strategy_positions WHERE status='open'"
        params: list = []
        if strategy_name:
            query += " AND strategy_name=?"
            params.append(strategy_name)
        cursor = self._conn.execute(query, params)
        return [dict(row) for row in cursor.fetchall()]

    def get_all_closed_pnl(self) -> List[Dict[str, Any]]:
        cursor = self._conn.execute(
            "SELECT * FROM closed_pnl ORDER BY closed_at"
        )
        return [dict(row) for row in cursor.fetchall()]

    # ── Legacy compat ──

    def carregar(self) -> PaperStateData:
        cursor = self._conn.execute("SELECT key, value FROM state_meta")
        meta = {row["key"]: row["value"] for row in cursor.fetchall()}

        cashbook_data = self.get_cashbook()
        cashbook = {
            "base_currency": meta.get("base_currency", "BRL"),
            "entries": cashbook_data,
        }

        cursor = self._conn.execute("SELECT id, * FROM orders")
        ordens = {}
        for row in cursor.fetchall():
            d = dict(row)
            ordens[d["id"]] = {k: v for k, v in d.items() if k != "id"}

        cursor = self._conn.execute("SELECT * FROM positions")
        posicoes = {}
        for row in cursor.fetchall():
            d = dict(row)
            key = f"{d['ticker']}::{d['strategy_name']}"
            posicoes[key] = {k: v for k, v in d.items() if k not in ("ticker", "strategy_name")}

        cursor = self._conn.execute("SELECT * FROM portfolios")
        portfolios = {}
        for row in cursor.fetchall():
            d = dict(row)
            portfolios[d["id"]] = {k: v for k, v in d.items() if k != "id"}

        saldo_inicial = Decimal(meta.get("saldo_inicial", "100000"))

        return PaperStateData(
            version=3,
            updated_at=meta.get("updated_at", ""),
            saldo_inicial=saldo_inicial,
            base_currency=meta.get("base_currency", "BRL"),
            cashbook=cashbook,
            ordens=ordens,
            posicoes=posicoes,
            portfolios=portfolios,
            default_id=meta.get("default_id"),
        )

    def salvar(self, estado: PaperStateData) -> None:
        now = datetime.now().isoformat()

        self._conn.executescript("DELETE FROM state_meta; DELETE FROM cashbook_entries; DELETE FROM orders; DELETE FROM positions; DELETE FROM portfolios;")

        meta_pairs = [
            ("version", "3"),
            ("updated_at", now),
            ("base_currency", estado.base_currency),
            ("saldo_inicial", str(estado.saldo_inicial)),
        ]
        if estado.default_id:
            meta_pairs.append(("default_id", estado.default_id))
        self._conn.executemany(
            "INSERT INTO state_meta (key, value) VALUES (?, ?)", meta_pairs
        )

        entries = estado.cashbook.get("entries", {})
        cash_rows = [
            (currency, data["amount"], data["conversion_rate"])
            for currency, data in entries.items()
        ]
        if cash_rows:
            self._conn.executemany(
                "INSERT INTO cashbook_entries (currency, amount, conversion_rate) VALUES (?, ?, ?)",
                cash_rows,
            )

        for order_id, order_data in estado.ordens.items():
            self._conn.execute(
                "INSERT INTO orders (created_at, id, ticker, side, quantity, price, "
                "total_value, currency, status, executed_at, order_type, position_id, "
                "broker, strategy_name) "
                "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                (
                    order_data.get("created_at", ""),
                    order_id,
                    order_data.get("ticker", ""),
                    order_data.get("side", ""),
                    order_data.get("quantity", 0),
                    order_data.get("price", "0"),
                    order_data.get("total_value", "0"),
                    order_data.get("currency", "USD"),
                    order_data.get("status", "PENDING"),
                    order_data.get("executed_at"),
                    order_data.get("order_type", "open"),
                    order_data.get("position_id"),
                    order_data.get("broker", "paper"),
                    order_data.get("strategy_name", "default"),
                ),
            )

        for pos_key, pos_data in estado.posicoes.items():
            if "::" in pos_key:
                ticker, strategy = pos_key.split("::", 1)
            else:
                ticker, strategy = pos_key, "default"
            self._conn.execute(
                "INSERT INTO positions (ticker, strategy_name, broker, side, quantity, "
                "avg_price, currency, status, opened_at, closed_at) "
                "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                (
                    ticker,
                    strategy,
                    pos_data.get("broker", "paper"),
                    pos_data.get("side", "long"),
                    pos_data.get("quantity", 0),
                    pos_data.get("avg_price", "0"),
                    pos_data.get("currency", "USD"),
                    pos_data.get("status", "open"),
                    pos_data.get("opened_at", ""),
                    pos_data.get("closed_at"),
                ),
            )

        for pf_id, pf_data in estado.portfolios.items():
            self._conn.execute(
                "INSERT INTO portfolios (id, name, initial_balance, current_balance, created_at) "
                "VALUES (?, ?, ?, ?, ?)",
                (
                    pf_id,
                    pf_data.get("name"),
                    pf_data.get("initial_balance"),
                    pf_data.get("current_balance"),
                    pf_data.get("created_at"),
                ),
            )

        self._conn.commit()

    def resetar(self, saldo_inicial: Optional[Decimal] = None) -> PaperStateData:
        tables = ["state_meta", "cashbook_entries", "orders", "positions",
                   "strategy_positions", "closed_pnl", "signals", "portfolios"]
        for table in tables:
            self._conn.execute(f"DELETE FROM {table}")
        self._conn.commit()

        novo_saldo = saldo_inicial if saldo_inicial is not None else Decimal("100000")
        estado = PaperStateData(
            saldo_inicial=novo_saldo,
            base_currency="BRL",
            cashbook={
                "base_currency": "BRL",
                "entries": {
                    "BRL": {"amount": str(novo_saldo), "conversion_rate": "1"},
                },
            },
        )
        self.salvar(estado)
        return estado
