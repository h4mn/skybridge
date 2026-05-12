-- Paper Trading Schema v4 (SQLite+WAL, hypertable-ready)
-- Compatível com migração futura para TimescaleDB.

PRAGMA journal_mode=WAL;
PRAGMA synchronous=NORMAL;
PRAGMA busy_timeout=5000;
PRAGMA foreign_keys=ON;

-- Schema version
CREATE TABLE IF NOT EXISTS schema_version (
    version INTEGER PRIMARY KEY,
    applied_at TEXT NOT NULL DEFAULT (datetime('now')),
    description TEXT
);

-- State metadata (key-value)
CREATE TABLE IF NOT EXISTS state_meta (
    key TEXT PRIMARY KEY NOT NULL,
    value TEXT NOT NULL
);

-- CashBook multi-moeda
CREATE TABLE IF NOT EXISTS cashbook_entries (
    currency TEXT PRIMARY KEY NOT NULL,
    amount TEXT NOT NULL,
    conversion_rate TEXT NOT NULL
);

-- Posições do broker (surrogate key id + UNIQUE ticker+strategy_name)
CREATE TABLE IF NOT EXISTS positions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    ticker TEXT NOT NULL,
    strategy_name TEXT NOT NULL,
    broker TEXT NOT NULL DEFAULT 'paper',
    side TEXT NOT NULL DEFAULT 'long',
    quantity INTEGER NOT NULL DEFAULT 0,
    avg_price TEXT NOT NULL DEFAULT '0',
    currency TEXT NOT NULL DEFAULT 'USD',
    status TEXT NOT NULL DEFAULT 'open',
    opened_at TEXT NOT NULL,
    closed_at TEXT,
    grid_level INTEGER,
    parent_position_id TEXT,
    UNIQUE(ticker, strategy_name)
);

-- Ordens (hypertable-ready: timestamp-first, FK → positions)
CREATE TABLE IF NOT EXISTS orders (
    created_at TEXT NOT NULL,
    id TEXT PRIMARY KEY NOT NULL,
    portfolio_id TEXT,
    ticker TEXT NOT NULL,
    side TEXT NOT NULL,
    quantity INTEGER NOT NULL,
    price TEXT NOT NULL,
    total_value TEXT NOT NULL,
    currency TEXT NOT NULL DEFAULT 'USD',
    status TEXT NOT NULL DEFAULT 'PENDING',
    executed_at TEXT,
    order_type TEXT NOT NULL DEFAULT 'open',
    position_id INTEGER REFERENCES positions(id) ON DELETE SET NULL,
    broker TEXT NOT NULL DEFAULT 'paper',
    strategy_name TEXT NOT NULL DEFAULT 'default'
);

-- Posições do PositionTracker (SL/TP/trailing)
CREATE TABLE IF NOT EXISTS strategy_positions (
    ticker TEXT NOT NULL,
    strategy_name TEXT NOT NULL,
    broker TEXT NOT NULL DEFAULT 'paper',
    entry_price TEXT NOT NULL,
    side TEXT NOT NULL DEFAULT 'long',
    status TEXT NOT NULL DEFAULT 'open',
    take_profit_pct TEXT,
    stop_loss_pct TEXT,
    trailing_pico TEXT,
    trailing_stop TEXT,
    opened_at TEXT NOT NULL,
    closed_at TEXT,
    PRIMARY KEY (ticker, strategy_name)
);

-- PnL fechado (hypertable-ready: timestamp-first)
CREATE TABLE IF NOT EXISTS closed_pnl (
    closed_at TEXT NOT NULL,
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    ticker TEXT NOT NULL,
    strategy_name TEXT NOT NULL DEFAULT 'default',
    broker TEXT NOT NULL DEFAULT 'paper',
    entry_price TEXT NOT NULL,
    exit_price TEXT NOT NULL,
    quantity INTEGER NOT NULL,
    side TEXT NOT NULL DEFAULT 'long',
    pnl_value TEXT NOT NULL,
    pnl_value_display REAL NOT NULL,
    pnl_pct REAL NOT NULL,
    reason TEXT
);

-- Sinais de estratégia (hypertable-ready: timestamp-first)
CREATE TABLE IF NOT EXISTS signals (
    created_at TEXT NOT NULL,
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    ticker TEXT NOT NULL,
    strategy_name TEXT NOT NULL DEFAULT 'default',
    broker TEXT NOT NULL DEFAULT 'paper',
    signal_type TEXT NOT NULL,
    price TEXT NOT NULL,
    reason TEXT,
    take_profit_pct TEXT
);

-- Ticks raw (hypertable-ready: timestamp-first, ML evolutivo)
CREATE TABLE IF NOT EXISTS ticks_raw (
    time TEXT NOT NULL,
    symbol TEXT NOT NULL,
    broker TEXT NOT NULL DEFAULT 'paper',
    price TEXT NOT NULL,
    volume INTEGER,
    side TEXT
);

-- OHLCV / Candles (hypertable-ready: timestamp-first)
CREATE TABLE IF NOT EXISTS ohlcv (
    time TEXT NOT NULL,
    symbol TEXT NOT NULL,
    broker TEXT NOT NULL DEFAULT 'paper',
    open TEXT NOT NULL,
    high TEXT NOT NULL,
    low TEXT NOT NULL,
    close TEXT NOT NULL,
    volume INTEGER,
    interval TEXT NOT NULL DEFAULT '1m'
);

-- Portfólios com agrupamento por tipo
CREATE TABLE IF NOT EXISTS portfolios (
    id TEXT PRIMARY KEY NOT NULL,
    name TEXT,
    portfolio_type TEXT,
    strategy_name TEXT,
    broker TEXT,
    initial_balance REAL,
    current_balance REAL,
    created_at TEXT
);

-- Indexes
CREATE INDEX IF NOT EXISTS idx_orders_ticker ON orders(ticker);
CREATE INDEX IF NOT EXISTS idx_orders_status ON orders(status);
CREATE INDEX IF NOT EXISTS idx_orders_created_at ON orders(created_at);
CREATE INDEX IF NOT EXISTS idx_orders_broker ON orders(broker);
CREATE INDEX IF NOT EXISTS idx_orders_strategy ON orders(strategy_name);

CREATE INDEX IF NOT EXISTS idx_ticks_raw_symbol_time ON ticks_raw(symbol, time);
CREATE INDEX IF NOT EXISTS idx_ohlcv_symbol_time ON ohlcv(symbol, time);

CREATE INDEX IF NOT EXISTS idx_closed_pnl_ticker ON closed_pnl(ticker);
CREATE INDEX IF NOT EXISTS idx_closed_pnl_strategy ON closed_pnl(strategy_name);

CREATE INDEX IF NOT EXISTS idx_signals_ticker ON signals(ticker);
CREATE INDEX IF NOT EXISTS idx_signals_strategy ON signals(strategy_name);

-- Inicialização do schema version
INSERT OR IGNORE INTO schema_version (version, description)
VALUES (5, 'Surrogate key + FK orders→positions');
