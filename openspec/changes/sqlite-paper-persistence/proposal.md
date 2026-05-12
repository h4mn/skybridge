## Why

O Paper Trading Bot persiste estado em `paper_state.json` — um único arquivo JSON com read-modify-write completo a cada operação. Isso limita queries analíticas, impede concorrência nativa entre múltiplas estratégias, e não escala para o cenário de produção imaginado (10 futuros, 50 ações, 10 criptos, 5-10 corretoras, 5+ estratégias por ativo). A issue SKY-39 pede SQLite para persistência.

## What Changes

- **Novo adapter SQLite+WAL** com interface CQS (Command/Query separados, SOLID) — sem blob monolítico
- **Schema relacional** hypertable-ready (timestamp-first, tipos compatíveis com PostgreSQL/TimescaleDB)
- **Migração automática** JSON v3 → SQLite (detecta `.json` existente, importa, renomeia)
- **Write Queue como single writer** — todo write passa pela Queue (broker, tracker, workers)
- **Persistência de sinais e ticks raw** — ticks reais armazenados + OHLCV agregado, para ML evolutivo
- **Backup temporal mensal** — snapshot mensal automático
- **Integração DuckDB** via `sqlite_scan()` para analytics

## Capabilities

### New Capabilities
- `sqlite-schema`: Schema SQLite+WAL com tabelas hypertable-ready, NUMERIC para valores, FKs order↔position, broker por tabela, strategy_name em PKs
- `sqlite-paper-state`: Adapter com CQS — queries granulares (`list_orders`, `get_position`) e commands granulares (`save_order`, `update_position`, `save_pnl`). Sem blob `PaperStateData` para writes
- `sqlite-write-queue`: Single writer async — todo write passa pela Queue. Broker, tracker e workers enfileiram
- `sqlite-migration`: Migração automática JSON v3 → SQLite + guardiao-state.json import

### Modified Capabilities
- `paper-state`: `PaperStatePort` ganha métodos granulares CQS. `carregar()`/`salvar()` blob deprecated mas mantido para compat

## Impact

- **Ports**: `PaperStatePort` estendido com CQS methods (non-breaking, métodos antigos mantidos)
- **Adapters**: Novos arquivos em `src/core/paper/adapters/persistence/`
- **DI Wiring**: `facade/api/dependencies.py` troca `JsonFilePaperState` → `SQLitePaperState`
- **Orchestrator**: `run_orchestrator.py` substitui `_save_state()` por WriteQueue
- **Broker**: `JsonFilePaperBroker` passa a enfileirar via WriteQueue ao invés de chamar `salvar()` direto
- **Dependências**: Zero (sqlite3 é stdlib). DuckDB é opcional (analytics)
