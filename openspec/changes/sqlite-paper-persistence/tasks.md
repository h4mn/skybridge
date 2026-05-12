## 1. Schema Foundation

- [x] 1.1 Criar `schema.sql` com todas as tabelas (state_meta, cashbook_entries, orders com FK+order_type+broker+strategy_name, positions com PK composta+broker+side, strategy_positions com PK composta+broker, closed_pnl com broker+strategy_name+pnl_value_display, signals com broker+strategy_name, ticks_raw, ohlcv, portfolios com portfolio_type, schema_version) e indexes
- [x] 1.2 Criar `test_sqlite_schema.py` — tabelas existem, indexes, idempotência, WAL, NUMERIC vs REAL

## 2. SQLitePaperState CQS

- [x] 2.1 Criar `sqlite_paper_state.py` com `__init__` (WAL tuning, schema init, auto-detecção JSON)
- [x] 2.2 Implementar Queries: `get_position(ticker, strategy_name)`, `list_orders(ticker, status)`, `get_cashbook()`, `get_closed_pnl(ticker)`
- [x] 2.3 Implementar Commands: `save_order()`, `update_position()`, `save_pnl()`, `save_signal()`, `save_tick()`, `save_ohlcv()`
- [x] 2.4 Criar `test_sqlite_paper_state.py` — queries em DB vazio retornam defaults/None
- [x] 2.5 Teste: cada command grava só sua tabela (save_order não toca positions)
- [x] 2.6 Teste: get_position com PK composta (guardiao vs sniper em BTC-USD)
- [x] 2.7 Teste: list_orders com filtros (ticker, status, broker)
- [x] 2.8 Implementar compat legado: `carregar()` monta PaperStateData, `salvar()` reescreve tudo
- [x] 2.9 Teste: roundtrip legado (carregar/salvar PaperStateData)
- [x] 2.10 Teste: atomicidade (rollback em erro, dados anteriores intactos)
- [x] 2.11 Teste: crash recovery (kill, dados intactos)

## 3. Migração JSON → SQLite

- [x] 3.1 Criar `migrations.py` com `import_json_to_sqlite()` — mapeia JSON v3 para tabelas com strategy_name default
- [x] 3.2 Criar `test_sqlite_migrations.py` — import JSON v3 (cashbook, ordens com broker, posições com PK composta)
- [x] 3.3 Implementar importação de `guardiao-state.json` (strategy_positions + closed_pnl)
- [x] 3.4 Teste: import guardiao-state com TP e trailing preservados
- [x] 3.5 Teste: migração idempotente (rodar 2x não duplica)
- [x] 3.6 Teste: JSON renomeado para `.v3.migrated.json`
- [x] 3.7 Integrar auto-detecção no `__init__()` (detecta .json ausente de .db)

## 4. DI Wiring

- [x] 4.1 Modificar `facade/api/dependencies.py` — trocar `JsonFilePaperState` por `SQLitePaperState`
- [x] 4.2 Verificar testes existentes da API passam (compat legado)
- [x] 4.3 Modificar `run_orchestrator.py` — injetar SQLitePaperState + WriteQueue

## 5. Write Queue (Single Writer)

- [x] 5.1 Criar `sqlite_write_queue.py` com `WriteQueue` (asyncio.Queue + flush loop)
- [x] 5.2 Implementar tipos: SaveOrder, UpdatePosition, SavePnl, SaveSignal, SaveTick, SaveOhlcv
- [x] 5.3 Criar `test_sqlite_write_queue.py` — batch flush (10 ops em 1 txn)
- [x] 5.4 Teste: concurrent enqueue (3 workers simultâneos)
- [x] 5.5 Teste: close drena fila (flush final)
- [x] 5.6 Teste: crash consistency (dados do último flush intactos)
- [x] 5.7 Wire WriteQueue no orchestrator — broker, tracker e workers enfileiram
- [x] 5.8 Remover chamadas diretas a `salvar()` do broker — passar pela Queue

## 6. Signals + Ticks Raw + OHLCV

- [x] 6.1 Adicionar persistência de sinais no StrategyWorker via WriteQueue
- [x] 6.2 Teste: sinal COMPRA/VENDA persistido com strategy_name e broker
- [x] 6.3 Adicionar persistência de ticks raw no datafeed via WriteQueue
- [x] 6.4 Teste: tick raw persistido em ticks_raw com preço exato
- [x] 6.5 Implementar agregação OHLCV em memória + persistência via WriteQueue
- [x] 6.6 Teste: candle 1m persistido em ohlcv
- [x] 6.7 Teste: DuckDB `sqlite_scan()` lê database (teste criado, skip se DuckDB não instalado)

## 7. Backup Temporal

- [x] 7.1 Implementar backup mensal automático (copia .db para backups/paper_state-YYYY-MM.db)
- [x] 7.2 Teste: backup criado na primeira execução do mês
- [x] 7.3 Teste: backup não duplica no mesmo mês

> "34 tarefas, SOLID, CQS, single writer, ML-ready" – made by Sky 🗄️
