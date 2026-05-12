## Context

O Paper Trading Module usa `PaperStatePort` como interface de persistência, com `JsonFilePaperState` como implementação. Toda operação faz read-modify-write completo do arquivo JSON. O sistema já provou funcionar para paper trading single-estratégia (Guardião Conservador), mas precisa evoluir para multi-estratégia e multi-corretora.

Referência arquitetural: `comparativo-banco-dados.md` (Anexos A-C) e `plano-sqlite-wal.md`.

## Goals / Non-Goals

**Goals:**
- Substituir JSON por SQLite+WAL como adapter padrão de persistência
- Interface CQS granular (commands e queries separados, SOLID)
- Schema relacional hypertable-ready para migração futura a TimescaleDB
- Single writer via Write Queue — broker, tracker e workers passam pela fila
- Persistir ticks raw + OHLCV + sinais para ML evolutivo (janelas deslizantes)
- Backup temporal mensal automático
- Migração transparente JSON → SQLite

**Non-Goals:**
- TimescaleDB (futuro — schema é preparado, implementação não)
- DuckDB como dependência obrigatória (opcional para analytics)
- Remover `carregar()`/`salvar()` do port (mantidos deprecated para compat)

## Decisions

### D1: CQS no adapter — Commands e Queries separados

**Decisão:** `SQLitePaperState` oferece métodos granulares:
- **Queries**: `get_position(ticker, strategy)`, `list_orders(ticker)`, `get_cashbook()`, `get_closed_pnl(ticker)`
- **Commands**: `save_order(order)`, `update_position(ticker, ...)`, `save_pnl(pnl)`, `save_tick(tick)`, `save_signal(signal)`

`carregar()`/`salvar(PaperStateData)` mantidos como deprecated para transição suave, mas novos consumidores usam métodos granulares.

**Rationale:** Evita reescrever tabelas inteiras a cada operação. Cada método toca só a tabela relevante. Separa leitura de escrita (CQS).

### D2: Single writer via WriteQueue

**Decisão:** Todo write (broker, tracker, workers) passa pela `WriteQueue`. Nenhum componente grava direto no SQLite.

**Alternativas consideradas:**
- Broker grava direto, queue só para workers → rejeitado: conflito de transações concorrentes
- Múltiplas conexões com busy_timeout → rejeitado: contenção e latência imprevisível

**Rationale:** 1 writer = 0 contention. WriteQueue batchifica em transações únicas. Flush periódico (500ms ou max_batch=50).

### D3: PK composta (ticker, strategy_name) para posições

**Decisão:** `positions` e `strategy_positions` usam PK `(ticker, strategy_name)`. Suporta múltiplas estratégias no mesmo ativo simultaneamente.

**Rationale:** Produção prevê 5+ estratégias por ativo. PK só em ticker colide.

### D4: FK orders → positions com tipo de ordem

**Decisão:** Tabela `orders` tem FK `position_id` + coluna `order_type` ('open', 'increase', 'partial_close', 'full_close'). Uma posição pode ter N ordens. A posição recalcula `avg_price` e `quantity` a cada ordem de aumento.

**Rationale:** Rastreabilidade total: qual ordem abriu, quais aumentaram, quais fecharam parcialmente, qual fechou totalmente. Suporta DCA, pyramiding, saída parcial. Analytics de win rate por trade completo.

### D5: NUMERIC (TEXT) para exato + REAL para display

**Decisão:** Valores financeiros em `TEXT` (Decimal exato). Colunas de exibição/arredondamento em `REAL` quando necessário (pnl_value_display).

**Rationale:** `TEXT` preserva precisão Decimal. `SUM(CAST(pnl_value AS REAL))` para agregações rápidas. Cast em query > perda de precisão em storage.

### D6: Ticks raw + OHLCV em tabelas separadas

**Decisão:** Tabela `ticks_raw` (cada tick individual) + tabela `ohlcv` (candles agregados). Ambas hypertable-ready.

**Rationale:** ML evolutivo precisa de ticks raw para janelas deslizantes. OHLCV serve para display e estratégias. TimescaleDB fará Continuous Aggregates da raw para OHLCV.

### D7: Coluna broker em orders, positions, signals

**Decisão:** Todas as tabelas de trading incluem `broker TEXT`. Distingue operações entre corretoras.

**Rationale:** Produção com 5-10 corretoras. Uma posição BTC-USD na Binance ≠ Coinbase.

### D8: Grid trading — hierarquia de posições

**Decisão:** Tabela `positions` inclui `grid_level INTEGER` e `parent_position_id TEXT`. Posições raiz (não-grid) têm ambos NULL. Posições de grid referenciam a posição pai e indicam o nível.

**Rationale:** Sistema de grid cria múltiplas sub-posições em níveis de preço diferentes, todas vinculadas a uma posição coordenadora. Permite rastrear hierarquia, calcular PnL por grid level, e identificar posição pai para fechamento coordenado.

### D9: Backup temporal mensal

**Decisão:** Backup automático mensal: copia `.db` para `backups/paper_state-YYYY-MM.db`. Usa SQLite Online Backup API (`sqlite3_backup_init`).

**Rationale:** SKY-39 pede backup. Mensal é suficiente para paper trading. Recuperação = substituir `.db` ativo pelo backup.

### D10: Migração automática na inicialização

**Decisão:** `SQLitePaperState.__init__()` detecta `.db` ausente + `.json` presente → importa automaticamente.

**Rationale:** Zero downtime. Primeiro boot com novo adapter já funciona.

## Risks / Trade-offs

- **[Single writer]** Tudo passa pela WriteQueue. Se a queue travar, nada é gravado. Mitigação: flush com timeout + fallback para `salvar()` direto em caso de falha da queue.
- **[Ticks raw volume]** 10 futuros a 1-5sec = ~650K ticks/dia. SQLite+WAL aguenta em batch, mas single writer pode acumular fila. Mitigação: flush agressivo (200ms ou batch=20) para ticks. Monitorar queue depth.
- **[TEXT vs NUMERIC]** `ORDER BY price` ordena lexicograficamente. Mitigação: indexes em timestamp, não em preço. Analytics via DuckDB com cast automático.
- **[Migração irreversível]** JSON renomeado para `.v3.migrated.json`. Mitigação: arquivo preservado, rollback = apagar `.db` e renomear `.json`.
- **[Backup mensal pode ser pouco]** Se DB corrompe no dia 30, perde-se até 30 dias. Mitigação: WAL mode é resistente a corrupção. Futuro: backup semanal ou diário.
