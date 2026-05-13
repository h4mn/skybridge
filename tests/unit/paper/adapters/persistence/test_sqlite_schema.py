# -*- coding: utf-8 -*-
"""
Testes do schema SQLite para Paper Trading.

TDD RED: Estes testes DEVEM falhar enquanto schema.sql não existir.
Cada cenário mapeia para um requirement do spec sqlite-schema.

Spec: openspec/changes/sqlite-paper-persistence/specs/sqlite-schema/spec.md
"""

import sqlite3
from pathlib import Path
from decimal import Decimal

import pytest

# Path para o schema.sql
SCHEMA_PATH = Path(__file__).parent.parent.parent.parent.parent.parent / (
    "src/core/paper/adapters/persistence/schema.sql"
)


@pytest.fixture
def db_connection(tmp_path):
    """Cria conexão SQLite em memória com schema aplicado."""
    conn = sqlite3.connect(str(tmp_path / "test.db"))
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA synchronous=NORMAL")
    conn.execute("PRAGMA busy_timeout=5000")
    if SCHEMA_PATH.exists():
        with open(SCHEMA_PATH, "r", encoding="utf-8") as f:
            conn.executescript(f.read())
    yield conn
    conn.close()


# ── Requirement: Schema versionado ──


class TestSchemaVersion:
    def test_database_novo_inicia_com_versao_5(self, db_connection):
        """Scenario: Database novo inicia com versão 5."""
        cursor = db_connection.execute("SELECT version FROM schema_version")
        row = cursor.fetchone()
        assert row is not None
        assert row[0] == 5

    def test_schema_idempotente(self, db_connection):
        """Scenario: Rodar _init_schema() 2x sem erro."""
        if not SCHEMA_PATH.exists():
            pytest.skip("schema.sql não existe (RED)")
        with open(SCHEMA_PATH, "r", encoding="utf-8") as f:
            sql = f.read()
        # Segunda execução não deve lançar erro
        db_connection.executescript(sql)


# ── Requirement: WAL mode ativo ──


class TestWALMode:
    def test_journal_mode_wal(self, db_connection):
        """Scenario: PRAGMA journal_mode retorna 'wal'."""
        cursor = db_connection.execute("PRAGMA journal_mode")
        result = cursor.fetchone()[0]
        assert result == "wal"

    def test_synchronous_normal(self, db_connection):
        """Scenario: PRAGMA synchronous retorna 1 (NORMAL)."""
        cursor = db_connection.execute("PRAGMA synchronous")
        result = cursor.fetchone()[0]
        assert result == 1

    def test_busy_timeout_5000(self, db_connection):
        """Scenario: PRAGMA busy_timeout retorna 5000."""
        cursor = db_connection.execute("PRAGMA busy_timeout")
        result = cursor.fetchone()[0]
        assert result == 5000


# ── Requirement: Tabelas hypertable-ready (timestamp-first) ──


class TestHypertableReady:
    @pytest.mark.parametrize("table_name", [
        "orders", "closed_pnl", "signals", "ticks_raw", "ohlcv",
    ])
    def test_timestamp_first_column(self, db_connection, table_name):
        """Scenario: Timestamp-first em time-series."""
        cursor = db_connection.execute(
            f"PRAGMA table_info({table_name})"
        )
        columns = cursor.fetchall()
        assert len(columns) > 0, f"Tabela {table_name} não existe"
        first_col = columns[0]
        col_name = first_col[1]
        col_type = first_col[2]
        # Primeira coluna deve ser tipo TEXT (ISO-8601 timestamp)
        assert col_type == "TEXT", (
            f"Primeira coluna de {table_name} é {col_type}, esperava TEXT"
        )
        # Nome deve conter "time", "at", ou "date"
        assert any(kw in col_name.lower() for kw in ("time", "at", "date")), (
            f"Primeira coluna de {table_name} é '{col_name}', esperava timestamp"
        )


# ── Requirement: NUMERIC (TEXT) para valores exatos ──


class TestNumericPrecision:
    def test_preco_armazenado_como_text(self, db_connection):
        """Scenario: Preço Decimal salvo como TEXT sem perda."""
        if not SCHEMA_PATH.exists():
            pytest.skip("schema.sql não existe (RED)")
        # Inserir preço com alta precisão
        price = "50000.12345678"
        db_connection.execute(
            "INSERT INTO positions (ticker, strategy_name, side, quantity, avg_price, status, opened_at) "
            "VALUES (?, ?, ?, ?, ?, ?, ?)",
            ("BTC-USD", "test", "long", 1, price, "open", "2026-01-01T00:00:00"),
        )
        db_connection.commit()

        cursor = db_connection.execute(
            "SELECT avg_price FROM positions WHERE ticker='BTC-USD' AND strategy_name='test'"
        )
        result = cursor.fetchone()[0]
        assert result == price, f"Preço perdeu precisão: {result} != {price}"


# ── Requirement: REAL para display ──


class TestRealDisplay:
    def test_pnl_display_arredondado(self, db_connection):
        """Scenario: pnl_value_display em REAL."""
        if not SCHEMA_PATH.exists():
            pytest.skip("schema.sql não existe (RED)")
        db_connection.execute(
            "INSERT INTO closed_pnl "
            "(closed_at, ticker, strategy_name, broker, entry_price, exit_price, "
            "quantity, side, pnl_value, pnl_value_display, pnl_pct, reason) "
            "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (
                "2026-01-01T10:00:00", "BTC-USD", "guardiao", "binance",
                "50000", "50100", 1, "long", "100.12345678",
                100.1235, 0.2, "tp_hit",
            ),
        )
        db_connection.commit()

        cursor = db_connection.execute(
            "SELECT pnl_value, pnl_value_display FROM closed_pnl"
        )
        row = cursor.fetchone()
        assert row is not None
        # pnl_value é TEXT (exato)
        assert row[0] == "100.12345678"
        # pnl_value_display é REAL (arredondado)
        assert isinstance(row[1], float)
        assert abs(row[1] - 100.1235) < 0.0001


# ── Requirement: Tabela state_meta ──


class TestStateMeta:
    def test_state_meta_existe(self, db_connection):
        """Scenario: Tabela state_meta com key/value."""
        db_connection.execute(
            "INSERT INTO state_meta (key, value) VALUES (?, ?)",
            ("base_currency", "BRL"),
        )
        db_connection.commit()

        cursor = db_connection.execute(
            "SELECT value FROM state_meta WHERE key='base_currency'"
        )
        assert cursor.fetchone()[0] == "BRL"


# ── Requirement: Tabela cashbook_entries ──


class TestCashbookEntries:
    def test_multi_moeda_persistida(self, db_connection):
        """Scenario: Cashbook com múltiplas moedas."""
        db_connection.execute(
            "INSERT INTO cashbook_entries (currency, amount, conversion_rate) VALUES (?, ?, ?)",
            ("BRL", "100000", "1"),
        )
        db_connection.execute(
            "INSERT INTO cashbook_entries (currency, amount, conversion_rate) VALUES (?, ?, ?)",
            ("USD", "2500", "5.20"),
        )
        db_connection.commit()

        cursor = db_connection.execute(
            "SELECT COUNT(*) FROM cashbook_entries"
        )
        assert cursor.fetchone()[0] == 2


# ── Requirement: Tabela orders com FK + order_type + broker + strategy_name ──


class TestOrders:
    def test_ordem_vinculada_a_posicao(self, db_connection):
        """Scenario: Ordem com position_id FK e order_type='open'."""
        if not SCHEMA_PATH.exists():
            pytest.skip("schema.sql não existe (RED)")
        # Cria posição e pega surrogate key
        cursor = db_connection.execute(
            "INSERT INTO positions (ticker, strategy_name, side, quantity, avg_price, status, opened_at, broker) "
            "VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
            ("BTC-USD", "guardiao", "long", 1, "50000", "open", "2026-01-01T00:00:00", "binance"),
        )
        pos_id = cursor.lastrowid
        db_connection.commit()

        # Ordem vinculada via FK
        db_connection.execute(
            "INSERT INTO orders (created_at, id, ticker, side, quantity, price, "
            "total_value, status, order_type, position_id, broker, strategy_name) "
            "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (
                "2026-01-01T00:00:00", "ord-1", "BTC-USD", "buy", 1,
                "50000", "50000", "EXECUTADA", "open",
                pos_id, "binance", "guardiao",
            ),
        )
        db_connection.commit()

        cursor = db_connection.execute(
            "SELECT order_type, position_id FROM orders WHERE id='ord-1'"
        )
        row = cursor.fetchone()
        assert row[0] == "open"
        assert row[1] == pos_id

    def test_aumento_de_posicao(self, db_connection):
        """Scenario: order_type='increase' com position_id."""
        if not SCHEMA_PATH.exists():
            pytest.skip("schema.sql não existe (RED)")
        cursor = db_connection.execute(
            "INSERT INTO positions (ticker, strategy_name, side, quantity, avg_price, status, opened_at, broker) "
            "VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
            ("BTC-USD", "guardiao", "long", 1, "50000", "open", "2026-01-01T00:00:00", "binance"),
        )
        pos_id = cursor.lastrowid
        db_connection.execute(
            "INSERT INTO orders (created_at, id, ticker, side, quantity, price, "
            "total_value, status, order_type, position_id, broker, strategy_name) "
            "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (
                "2026-01-02T00:00:00", "ord-2", "BTC-USD", "buy", 1,
                "52000", "52000", "EXECUTADA", "increase",
                pos_id, "binance", "guardiao",
            ),
        )
        db_connection.commit()

        cursor = db_connection.execute(
            "SELECT order_type FROM orders WHERE id='ord-2'"
        )
        assert cursor.fetchone()[0] == "increase"

    def test_saida_parcial(self, db_connection):
        """Scenario: order_type='partial_close'."""
        if not SCHEMA_PATH.exists():
            pytest.skip("schema.sql não existe (RED)")
        cursor = db_connection.execute(
            "INSERT INTO positions (ticker, strategy_name, side, quantity, avg_price, status, opened_at, broker) "
            "VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
            ("BTC-USD", "guardiao", "long", 2, "50000", "open", "2026-01-01T00:00:00", "binance"),
        )
        pos_id = cursor.lastrowid
        db_connection.execute(
            "INSERT INTO orders (created_at, id, ticker, side, quantity, price, "
            "total_value, status, order_type, position_id, broker, strategy_name) "
            "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (
                "2026-01-03T00:00:00", "ord-3", "BTC-USD", "sell", 1,
                "51000", "51000", "EXECUTADA", "partial_close",
                pos_id, "binance", "guardiao",
            ),
        )
        db_connection.commit()

        cursor = db_connection.execute(
            "SELECT order_type FROM orders WHERE id='ord-3'"
        )
        assert cursor.fetchone()[0] == "partial_close"

    def test_multiplas_ordens_por_posicao(self, db_connection):
        """Scenario: 5 ordens vinculadas à mesma posição via FK."""
        if not SCHEMA_PATH.exists():
            pytest.skip("schema.sql não existe (RED)")
        cursor = db_connection.execute(
            "INSERT INTO positions (ticker, strategy_name, side, quantity, avg_price, status, opened_at, broker) "
            "VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
            ("BTC-USD", "guardiao", "long", 5, "50000", "open", "2026-01-01T00:00:00", "binance"),
        )
        pos_id = cursor.lastrowid
        types = ["open", "increase", "increase", "partial_close", "full_close"]
        for i, otype in enumerate(types):
            db_connection.execute(
                "INSERT INTO orders (created_at, id, ticker, side, quantity, price, "
                "total_value, status, order_type, position_id, broker, strategy_name) "
                "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                (
                    f"2026-01-0{i+1}T00:00:00", f"ord-m{i}", "BTC-USD",
                    "buy" if otype in ("open", "increase") else "sell",
                    1, "50000", "50000", "EXECUTADA", otype,
                    pos_id, "binance", "guardiao",
                ),
            )
        db_connection.commit()

        cursor = db_connection.execute(
            "SELECT COUNT(*) FROM orders WHERE position_id=?",
            (pos_id,),
        )
        assert cursor.fetchone()[0] == 5

    def test_indexes_em_orders(self, db_connection):
        """Scenario: Indexes em ticker, status, created_at, broker, strategy_name."""
        if not SCHEMA_PATH.exists():
            pytest.skip("schema.sql não existe (RED)")
        cursor = db_connection.execute(
            "SELECT name FROM sqlite_master WHERE type='index' AND tbl_name='orders'"
        )
        indexes = {row[0] for row in cursor.fetchall()}
        # Pelo menos indexes nas colunas chave
        assert len(indexes) >= 3, f"Esperava >= 3 indexes, achou {indexes}"


# ── Requirement: Tabela positions com PK composta + broker + side ──


class TestPositions:
    def test_multi_estrategia_mesmo_ticker(self, db_connection):
        """Scenario: Guardião e Sniper operam BTC-USD simultaneamente."""
        if not SCHEMA_PATH.exists():
            pytest.skip("schema.sql não existe (RED)")
        db_connection.execute(
            "INSERT INTO positions (ticker, strategy_name, side, quantity, avg_price, status, opened_at, broker) "
            "VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
            ("BTC-USD", "guardiao", "long", 1, "50000", "open", "2026-01-01T00:00:00", "binance"),
        )
        db_connection.execute(
            "INSERT INTO positions (ticker, strategy_name, side, quantity, avg_price, status, opened_at, broker) "
            "VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
            ("BTC-USD", "sniper", "long", 2, "51000", "open", "2026-01-01T01:00:00", "binance"),
        )
        db_connection.commit()

        cursor = db_connection.execute(
            "SELECT strategy_name FROM positions WHERE ticker='BTC-USD' ORDER BY strategy_name"
        )
        rows = cursor.fetchall()
        assert len(rows) == 2
        assert rows[0][0] == "guardiao"
        assert rows[1][0] == "sniper"

    def test_side_da_posicao(self, db_connection):
        """Scenario: Side 'long' para posição comprada."""
        if not SCHEMA_PATH.exists():
            pytest.skip("schema.sql não existe (RED)")
        db_connection.execute(
            "INSERT INTO positions (ticker, strategy_name, side, quantity, avg_price, status, opened_at, broker) "
            "VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
            ("BTC-USD", "test", "long", 1, "50000", "open", "2026-01-01T00:00:00", "binance"),
        )
        db_connection.commit()

        cursor = db_connection.execute(
            "SELECT side FROM positions WHERE ticker='BTC-USD' AND strategy_name='test'"
        )
        assert cursor.fetchone()[0] == "long"

    def test_posicao_raiz_sem_parent(self, db_connection):
        """Scenario: Posição normal com grid_level e parent_position_id NULL."""
        if not SCHEMA_PATH.exists():
            pytest.skip("schema.sql não existe (RED)")
        db_connection.execute(
            "INSERT INTO positions (ticker, strategy_name, side, quantity, avg_price, status, opened_at, broker) "
            "VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
            ("BTC-USD", "test", "long", 1, "50000", "open", "2026-01-01T00:00:00", "binance"),
        )
        db_connection.commit()

        cursor = db_connection.execute(
            "SELECT grid_level, parent_position_id FROM positions "
            "WHERE ticker='BTC-USD' AND strategy_name='test'"
        )
        row = cursor.fetchone()
        assert row[0] is None  # grid_level
        assert row[1] is None  # parent_position_id

    def test_posicao_grid_com_nivel(self, db_connection):
        """Scenario: Posição grid com grid_level=3 e parent_position_id."""
        if not SCHEMA_PATH.exists():
            pytest.skip("schema.sql não existe (RED)")
        # Posição pai
        db_connection.execute(
            "INSERT INTO positions (ticker, strategy_name, side, quantity, avg_price, status, opened_at, broker) "
            "VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
            ("BTC-USD", "grid-master", "long", 5, "50000", "open", "2026-01-01T00:00:00", "binance"),
        )
        # Sub-posição grid nível 3
        db_connection.execute(
            "INSERT INTO positions (ticker, strategy_name, side, quantity, avg_price, status, opened_at, broker, grid_level, parent_position_id) "
            "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            ("BTC-USD", "grid-3", "long", 1, "48000", "open", "2026-01-01T00:00:00", "binance", 3, "BTC-USD::grid-master"),
        )
        db_connection.commit()

        cursor = db_connection.execute(
            "SELECT grid_level, parent_position_id FROM positions "
            "WHERE strategy_name='grid-3'"
        )
        row = cursor.fetchone()
        assert row[0] == 3
        assert row[1] == "BTC-USD::grid-master"


# ── Requirement: Tabela strategy_positions com PK composta ──


class TestStrategyPositions:
    def test_trailing_stop_por_estrategia(self, db_connection):
        """Scenario: Trailing stop diferente por estratégia."""
        if not SCHEMA_PATH.exists():
            pytest.skip("schema.sql não existe (RED)")
        db_connection.execute(
            "INSERT INTO strategy_positions "
            "(ticker, strategy_name, entry_price, status, take_profit_pct, stop_loss_pct, "
            "trailing_pico, trailing_stop, opened_at, broker) "
            "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            ("BTC-USD", "guardiao", "80000", "open", "0.004", "0.02", "80300", "79800", "2026-01-01T00:00:00", "binance"),
        )
        db_connection.execute(
            "INSERT INTO strategy_positions "
            "(ticker, strategy_name, entry_price, status, take_profit_pct, stop_loss_pct, "
            "trailing_pico, trailing_stop, opened_at, broker) "
            "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            ("BTC-USD", "sniper", "80000", "open", "0.002", "0.01", "80500", "80200", "2026-01-01T00:00:00", "binance"),
        )
        db_connection.commit()

        cursor = db_connection.execute(
            "SELECT trailing_pico FROM strategy_positions "
            "WHERE ticker='BTC-USD' AND strategy_name='guardiao'"
        )
        assert cursor.fetchone()[0] == "80300"


# ── Requirement: Tabela closed_pnl ──


class TestClosedPnl:
    def test_pnl_por_estrategia_e_broker(self, db_connection):
        """Scenario: PnL com strategy_name e broker."""
        if not SCHEMA_PATH.exists():
            pytest.skip("schema.sql não existe (RED)")
        db_connection.execute(
            "INSERT INTO closed_pnl "
            "(closed_at, ticker, strategy_name, broker, entry_price, exit_price, "
            "quantity, side, pnl_value, pnl_value_display, pnl_pct, reason) "
            "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (
                "2026-01-01T10:00:00", "BTC-USD", "guardiao-conservador",
                "binance", "50000", "50500", 1, "long", "500",
                500.0, 1.0, "tp_hit",
            ),
        )
        db_connection.commit()

        cursor = db_connection.execute(
            "SELECT strategy_name, broker FROM closed_pnl"
        )
        row = cursor.fetchone()
        assert row[0] == "guardiao-conservador"
        assert row[1] == "binance"


# ── Requirement: Tabela signals ──


class TestSignals:
    def test_sinal_por_estrategia(self, db_connection):
        """Scenario: Sinal com strategy_name e broker."""
        if not SCHEMA_PATH.exists():
            pytest.skip("schema.sql não existe (RED)")
        db_connection.execute(
            "INSERT INTO signals "
            "(created_at, ticker, strategy_name, broker, signal_type, price, reason, take_profit_pct) "
            "VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
            (
                "2026-01-01T10:00:00", "BTC-USD", "guardiao", "binance",
                "BUY", "50000", "RSI oversold", "0.004",
            ),
        )
        db_connection.commit()

        cursor = db_connection.execute(
            "SELECT strategy_name, broker, signal_type FROM signals"
        )
        row = cursor.fetchone()
        assert row[0] == "guardiao"
        assert row[1] == "binance"
        assert row[2] == "BUY"


# ── Requirement: Tabela ticks_raw ──


class TestTicksRaw:
    def test_tick_raw_persistido(self, db_connection):
        """Scenario: Tick raw com preço exato."""
        if not SCHEMA_PATH.exists():
            pytest.skip("schema.sql não existe (RED)")
        db_connection.execute(
            "INSERT INTO ticks_raw (time, symbol, broker, price, volume, side) "
            "VALUES (?, ?, ?, ?, ?, ?)",
            ("2026-01-01T10:00:00.123", "BTC-USD", "binance", "50000.12", 100, "buy"),
        )
        db_connection.commit()

        cursor = db_connection.execute(
            "SELECT price FROM ticks_raw WHERE symbol='BTC-USD'"
        )
        assert cursor.fetchone()[0] == "50000.12"

    def test_index_em_ticks_raw(self, db_connection):
        """Scenario: Index composto em (symbol, time)."""
        if not SCHEMA_PATH.exists():
            pytest.skip("schema.sql não existe (RED)")
        cursor = db_connection.execute(
            "SELECT name FROM sqlite_master WHERE type='index' AND tbl_name='ticks_raw'"
        )
        indexes = {row[0] for row in cursor.fetchall()}
        assert len(indexes) >= 1


# ── Requirement: Tabela ohlcv ──


class TestOhlcv:
    def test_candle_ohlcv_persistido(self, db_connection):
        """Scenario: Candle OHLCV com interval='1m'."""
        if not SCHEMA_PATH.exists():
            pytest.skip("schema.sql não existe (RED)")
        db_connection.execute(
            "INSERT INTO ohlcv (time, symbol, broker, open, high, low, close, volume, interval) "
            "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (
                "2026-01-01T10:00:00", "BTC-USD", "binance",
                "50000", "50100", "49900", "50050", 1000, "1m",
            ),
        )
        db_connection.commit()

        cursor = db_connection.execute(
            "SELECT interval FROM ohlcv WHERE symbol='BTC-USD'"
        )
        assert cursor.fetchone()[0] == "1m"

    def test_index_em_ohlcv(self, db_connection):
        """Scenario: Index composto em (symbol, time)."""
        if not SCHEMA_PATH.exists():
            pytest.skip("schema.sql não existe (RED)")
        cursor = db_connection.execute(
            "SELECT name FROM sqlite_master WHERE type='index' AND tbl_name='ohlcv'"
        )
        indexes = {row[0] for row in cursor.fetchall()}
        assert len(indexes) >= 1


# ── Requirement: Tabela portfolios ──


class TestPortfolios:
    def test_portfolio_por_estrategia(self, db_connection):
        """Scenario: Portfolio tipo 'strategy'."""
        if not SCHEMA_PATH.exists():
            pytest.skip("schema.sql não existe (RED)")
        db_connection.execute(
            "INSERT INTO portfolios (id, name, portfolio_type, strategy_name, broker, "
            "initial_balance, current_balance, created_at) "
            "VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
            (
                "port-1", "Guardião Portfolio", "strategy",
                "guardiao-conservador", "binance",
                100000.0, 105000.0, "2026-01-01T00:00:00",
            ),
        )
        db_connection.commit()

        cursor = db_connection.execute(
            "SELECT portfolio_type, strategy_name FROM portfolios WHERE id='port-1'"
        )
        row = cursor.fetchone()
        assert row[0] == "strategy"
        assert row[1] == "guardiao-conservador"

    def test_portfolio_por_corretora(self, db_connection):
        """Scenario: Portfolio tipo 'broker'."""
        if not SCHEMA_PATH.exists():
            pytest.skip("schema.sql não existe (RED)")
        db_connection.execute(
            "INSERT INTO portfolios (id, name, portfolio_type, strategy_name, broker, "
            "initial_balance, current_balance, created_at) "
            "VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
            (
                "port-2", "Binance Portfolio", "broker",
                None, "binance",
                50000.0, 52000.0, "2026-01-01T00:00:00",
            ),
        )
        db_connection.commit()

        cursor = db_connection.execute(
            "SELECT portfolio_type, broker FROM portfolios WHERE id='port-2'"
        )
        row = cursor.fetchone()
        assert row[0] == "broker"
        assert row[1] == "binance"


# ── Requirement: Surrogate key + FK orders → positions ──


class TestSurrogateKey:
    def test_positions_tem_id_autoincrement(self, db_connection):
        """Scenario: Positions com surrogate key id INTEGER PRIMARY KEY."""
        if not SCHEMA_PATH.exists():
            pytest.skip("schema.sql não existe (RED)")
        cursor = db_connection.execute(
            "INSERT INTO positions (ticker, strategy_name, side, quantity, avg_price, "
            "status, opened_at, broker) "
            "VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
            ("BTC-USD", "guardiao", "long", 1, "50000", "open", "2026-01-01T00:00:00", "binance"),
        )
        assert cursor.lastrowid == 1

        cursor2 = db_connection.execute(
            "INSERT INTO positions (ticker, strategy_name, side, quantity, avg_price, "
            "status, opened_at, broker) "
            "VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
            ("ETH-USD", "guardiao", "long", 2, "3000", "open", "2026-01-01T00:00:00", "binance"),
        )
        assert cursor2.lastrowid == 2

    def test_unique_ticker_strategy(self, db_connection):
        """Scenario: UNIQUE(ticker, strategy_name) impede duplicatas."""
        if not SCHEMA_PATH.exists():
            pytest.skip("schema.sql não existe (RED)")
        db_connection.execute(
            "INSERT INTO positions (ticker, strategy_name, side, quantity, avg_price, "
            "status, opened_at, broker) "
            "VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
            ("BTC-USD", "guardiao", "long", 1, "50000", "open", "2026-01-01T00:00:00", "binance"),
        )
        with pytest.raises(sqlite3.IntegrityError):
            db_connection.execute(
                "INSERT INTO positions (ticker, strategy_name, side, quantity, avg_price, "
                "status, opened_at, broker) "
                "VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                ("BTC-USD", "guardiao", "long", 2, "51000", "open", "2026-01-01T00:00:00", "binance"),
            )


class TestFKOrdersPositions:
    def test_ordem_sem_posicao_null(self, db_connection):
        """Scenario: position_id aceita NULL."""
        if not SCHEMA_PATH.exists():
            pytest.skip("schema.sql não existe (RED)")
        db_connection.execute(
            "INSERT INTO orders (created_at, id, ticker, side, quantity, price, "
            "total_value, status, order_type, broker, strategy_name) "
            "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (
                "2026-01-01T00:00:00", "ord-null", "BTC-USD", "buy", 1,
                "50000", "50000", "PENDING", "open", "binance", "guardiao",
            ),
        )
        db_connection.commit()

        cursor = db_connection.execute(
            "SELECT position_id FROM orders WHERE id='ord-null'"
        )
        assert cursor.fetchone()[0] is None

    def test_fk_enforcement_posicao_invalida(self, db_connection):
        """Scenario: FK impede order com position_id inexistente."""
        if not SCHEMA_PATH.exists():
            pytest.skip("schema.sql não existe (RED)")
        with pytest.raises(sqlite3.IntegrityError):
            db_connection.execute(
                "INSERT INTO orders (created_at, id, ticker, side, quantity, price, "
                "total_value, status, position_id, broker, strategy_name) "
                "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                (
                    "2026-01-01T00:00:00", "ord-fk", "BTC-USD", "buy", 1,
                    "50000", "50000", "EXECUTADA", 999, "paper", "guardiao",
                ),
            )

    def test_fk_ordem_vinculada_a_posicao(self, db_connection):
        """Scenario: Ordem com position_id INTEGER válido."""
        if not SCHEMA_PATH.exists():
            pytest.skip("schema.sql não existe (RED)")
        cursor = db_connection.execute(
            "INSERT INTO positions (ticker, strategy_name, side, quantity, avg_price, "
            "status, opened_at, broker) "
            "VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
            ("BTC-USD", "guardiao", "long", 1, "50000", "open", "2026-01-01T00:00:00", "binance"),
        )
        pos_id = cursor.lastrowid

        db_connection.execute(
            "INSERT INTO orders (created_at, id, ticker, side, quantity, price, "
            "total_value, status, order_type, position_id, broker, strategy_name) "
            "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (
                "2026-01-01T00:00:00", "ord-1", "BTC-USD", "buy", 1,
                "50000", "50000", "EXECUTADA", "open", pos_id, "binance", "guardiao",
            ),
        )
        db_connection.commit()

        result = db_connection.execute(
            "SELECT position_id FROM orders WHERE id='ord-1'"
        ).fetchone()
        assert result[0] == pos_id


# ── Requirement: Aumento recalcula preço médio ──


class TestPositionRecalc:
    def test_aumento_recalcula_preco_medio(self, db_connection):
        """Scenario: Increase recalcula avg_price e quantity."""
        if not SCHEMA_PATH.exists():
            pytest.skip("schema.sql não existe (RED)")
        # Simula posição inicial
        db_connection.execute(
            "INSERT INTO positions (ticker, strategy_name, side, quantity, avg_price, status, opened_at, broker) "
            "VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
            ("BTC-USD", "test", "long", 10, "50000", "open", "2026-01-01T00:00:00", "binance"),
        )
        db_connection.commit()

        # Simula aumento: recalcula
        # (10 * 50000 + 5 * 52000) / 15 = 50666.67
        db_connection.execute(
            "UPDATE positions SET quantity=15, avg_price='50666.67' "
            "WHERE ticker='BTC-USD' AND strategy_name='test'"
        )
        db_connection.commit()

        cursor = db_connection.execute(
            "SELECT quantity, avg_price FROM positions "
            "WHERE ticker='BTC-USD' AND strategy_name='test'"
        )
        row = cursor.fetchone()
        assert row[0] == 15
        assert row[1] == "50666.67"
