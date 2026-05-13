# Plano: SQLite+WAL para Paper Trading (SKY-39)

**Data:** 2026-05-09 | **Issue:** SKY-39 | **Referência:** `comparativo-banco-dados.md`

## Contexto

O Paper Trading Bot persiste estado em `paper_state.json` (single file, read-modify-write completo a cada operação). A issue SKY-39 pede SQLite para persistência. SQLite+WAL hoje, com **schema pronto para TimescaleDB** no futuro (ML evolutivo, multi-corretora, tick raw).

A arquitetura hexagonal existente (`PaperStatePort` → adapters) permite trocar o adapter sem mexer em consumidores.

---

## Schema (hypertable-ready)

Todas as tabelas time-series com timestamp na primeira coluna, tipos compatíveis com PostgreSQL.

```sql
-- Metadados do estado (version, base_currency, etc.)
CREATE TABLE IF NOT EXISTS state_meta (
    key   TEXT PRIMARY KEY,
    value TEXT NOT NULL
);

-- CashBook multi-moeda
CREATE TABLE IF NOT EXISTS cashbook_entries (
    currency        TEXT PRIMARY KEY,
    amount          TEXT NOT NULL,
    conversion_rate TEXT NOT NULL
);

-- Ordens (hypertable-ready: timestamp first)
CREATE TABLE IF NOT EXISTS orders (
    created_at      TEXT NOT NULL,
    id              TEXT PRIMARY KEY,
    portfolio_id    TEXT,
    ticker          TEXT NOT NULL,
    side            TEXT NOT NULL,
    quantity        INTEGER NOT NULL,
    price           TEXT NOT NULL,
    total_value     TEXT NOT NULL,
    currency        TEXT NOT NULL DEFAULT 'USD',
    status          TEXT NOT NULL DEFAULT 'PENDING',
    executed_at     TEXT
);
CREATE INDEX IF NOT EXISTS idx_orders_ticker ON orders(ticker);
CREATE INDEX IF NOT EXISTS idx_orders_status ON orders(status);
CREATE INDEX IF NOT EXISTS idx_orders_created_at ON orders(created_at);

-- Posições do broker
CREATE TABLE IF NOT EXISTS positions (
    ticker          TEXT PRIMARY KEY,
    quantity        INTEGER NOT NULL,
    avg_price       TEXT NOT NULL,
    currency        TEXT NOT NULL DEFAULT 'USD',
    status          TEXT NOT NULL DEFAULT 'open',
    opened_at       TEXT NOT NULL,
    closed_at       TEXT
);

-- Posições do PositionTracker (SL/TP/trailing)
CREATE TABLE IF NOT EXISTS strategy_positions (
    ticker              TEXT PRIMARY KEY,
    entry_price         TEXT NOT NULL,
    status              TEXT NOT NULL DEFAULT 'open',
    take_profit_pct     TEXT,
    stop_loss_pct       TEXT,
    trailing_pico       TEXT,
    trailing_stop       TEXT,
    opened_at           TEXT NOT NULL
);

-- PnL fechado (hypertable-ready)
CREATE TABLE IF NOT EXISTS closed_pnl (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    closed_at       TEXT NOT NULL,
    ticker          TEXT NOT NULL,
    entry_price     TEXT NOT NULL,
    exit_price      TEXT NOT NULL,
    quantity        INTEGER NOT NULL,
    pnl_value       REAL NOT NULL,
    pnl_pct         REAL NOT NULL,
    reason          TEXT,
    strategy_name   TEXT
);
CREATE INDEX IF NOT EXISTS idx_closed_pnl_ticker ON closed_pnl(ticker);
CREATE INDEX IF NOT EXISTS idx_closed_pnl_closed_at ON closed_pnl(closed_at);

-- Sinais de estratégia (hypertable-ready, hoje não é persistido)
CREATE TABLE IF NOT EXISTS signals (
    created_at      TEXT NOT NULL,
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    ticker          TEXT NOT NULL,
    signal_type     TEXT NOT NULL,
    price           TEXT NOT NULL,
    reason          TEXT,
    take_profit_pct TEXT,
    strategy_name   TEXT
);
CREATE INDEX IF NOT EXISTS idx_signals_ticker ON signals(ticker);
CREATE INDEX IF NOT EXISTS idx_signals_created_at ON signals(created_at);

-- OHLCV / Ticks (hypertable-ready, futuro ML)
CREATE TABLE IF NOT EXISTS ticks (
    time            TEXT NOT NULL,
    symbol          TEXT NOT NULL,
    broker          TEXT NOT NULL DEFAULT 'yahoo',
    open            TEXT,
    high            TEXT,
    low             TEXT,
    close           TEXT NOT NULL,
    volume          INTEGER,
    interval        TEXT NOT NULL DEFAULT '1m'
);
CREATE INDEX IF NOT EXISTS idx_ticks_symbol_time ON ticks(symbol, time);
CREATE INDEX IF NOT EXISTS idx_ticks_time ON ticks(time);

-- Portfólios
CREATE TABLE IF NOT EXISTS portfolios (
    id              TEXT PRIMARY KEY,
    name            TEXT,
    initial_balance REAL NOT NULL,
    current_balance REAL NOT NULL,
    created_at      TEXT NOT NULL
);

-- Versionamento do schema
CREATE TABLE IF NOT EXISTS schema_version (
    version         INTEGER PRIMARY KEY,
    applied_at      TEXT NOT NULL DEFAULT (datetime('now')),
    description     TEXT
);
```

**Migração para TimescaleDB:** `SELECT create_hypertable('ticks', 'time')` + cast `TEXT`→`TIMESTAMPTZ` + `TEXT`→`NUMERIC`. Indexes permanecem.

---

## Novos Arquivos

```
src/core/paper/adapters/persistence/
    sqlite_paper_state.py          # SQLitePaperState(PaperStatePort)
    sqlite_write_queue.py          # WriteQueue para batch writes
    sqlite_portfolio_repository.py # SQLitePortfolioRepository(RepositoryPort)
    schema.sql                     # DDL completo
    migrations.py                  # JSON→SQLite + versionamento

tests/unit/core/paper/
    test_sqlite_schema.py
    test_sqlite_paper_state.py
    test_sqlite_write_queue.py
    test_sqlite_migrations.py
```

**Sem modificação** em ports, brokers, handlers, strategies — o adapter troca por baixo dos panos.

---

## Classes

### SQLitePaperState(PaperStatePort)

- `__init__(db_path)`: abre conexão, WAL mode, `synchronous=NORMAL`, `busy_timeout=5000`, roda `schema.sql`
- `carregar()` → lê tabelas → monta `PaperStateData` (mesmo dataclass de hoje)
- `salvar(estado)` → escreve todas as tabelas em 1 transação
- `resetar()` → truncate + inserts defaults
- Auto-detecção: se `.db` não existe mas `.json` existe → importa via migrations

### WriteQueue

- `asyncio.Queue` + flush loop (500ms ou max_batch=50)
- Workers enfileiram `WriteOperation` (SavePosition, SavePnl, SaveSignal, SaveTick)
- Flush drena fila → 1 transação SQLite com N operações
- Crash recovery: WAL garante consistência. Operações não-commitadas na fila são perdidas (aceitável — estado é re-derivado pelo PositionTracker)

### SQLitePortfolioRepository(RepositoryPort)

- Reimplementa `find_by_id`, `find_default`, `save` contra tabelas `portfolios`
- Mais simples que `JsonFilePortfolioRepository` (não precisa read-modify-write do blob inteiro)

---

## Migração JSON → SQLite

1. `SQLitePaperState.__init__()` detecta `.db` ausente + `.json` presente
2. `migrations.import_json_to_sqlite()`:
   - Lê `paper_state.json` v3
   - Mapeia campos para tabelas relacionais
   - Importa `guardiao-state.json` (positions + closed_pnl)
   - Tudo em 1 transação
   - Renomeia `.json` para `.v3.migrated.json`
3. Schema version = 4 (era SQLite)

---

## Arquivos Modificados

| Arquivo | Mudança |
|---|---|
| `facade/api/dependencies.py` | Swap `JsonFilePaperState` → `SQLitePaperState` |
| `facade/sandbox/run_orchestrator.py` | Substitui `_save_state()` por WriteQueue |

---

## Fases de Implementação

### Fase 1: Schema + Adapter Core
1. Criar `schema.sql`
2. Implementar `SQLitePaperState.__init__` (WAL, schema init)
3. Implementar `carregar()` + `salvar()` + `resetar()`
4. Testes: schema, roundtrip save/load, reset, WAL mode

### Fase 2: Migração
5. Implementar `migrations.py` (JSON v3 → SQLite)
6. Testes: import JSON, import guardiao-state, idempotência

### Fase 3: Wiring
7. Trocar DI em `dependencies.py`
8. Ajustar `run_orchestrator.py`
9. Verificar testes existentes passam

### Fase 4: Write Queue
10. Implementar `WriteQueue`
11. Testes: batch flush, concurrent enqueue, crash recovery

### Fase 5: Signals + Ticks (extensão)
12. Persistir sinais de estratégia
13. Persistir OHLCV aggregates
14. Testes: signal/tick storage, DuckDB `sqlite_scan()`

---

## Verificação

1. `pytest tests/unit/core/paper/ -v` — todos os testes novos + existentes passam
2. `python -m apps.api.main` — API sobe sem erro
3. Verificar `paper_state.db` criado com WAL mode ativo
4. DuckDB consegue ler: `duckdb.sql("SELECT * FROM sqlite_scan('paper_state.db', 'orders')")`
5. Migração JSON: renomear `.json` existente, rodar init, verificar dados importados

> "SQLite hoje, TimescaleDB amanhã, o port nunca muda" – made by Sky 🗄️
