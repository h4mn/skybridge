## ADDED Requirements

### Requirement: Schema versionado
O SQLite SHALL ter tabela `schema_version` que registra a versão atual do schema.

#### Scenario: Database novo inicia com versão 4
- **WHEN** criar database novo via `SQLitePaperState(db_path)`
- **THEN** tabela `schema_version` SHALL conter version=4

#### Scenario: Schema idempotente
- **WHEN** rodar `_init_schema()` 2 vezes seguidas
- **THEN** SHALL criar tabelas sem erro (IF NOT EXISTS)

### Requirement: WAL mode ativo
O SQLite SHALL usar WAL mode com tuning para trading.

#### Scenario: WAL configurado
- **WHEN** abrir conexão via `SQLitePaperState`
- **THEN** `PRAGMA journal_mode` SHALL retornar 'wal'
- **AND** `PRAGMA synchronous` SHALL retornar 1 (NORMAL)
- **AND** `PRAGMA busy_timeout` SHALL retornar 5000

### Requirement: Tabelas hypertable-ready
O schema SHALL ter tabelas time-series com timestamp na primeira coluna.

#### Scenario: Timestamp-first em time-series
- **WHEN** inspecionar DDL das tabelas orders, closed_pnl, signals, ticks_raw, ohlcv
- **THEN** primeira coluna SHALL ser tipo TEXT (ISO-8601 timestamp)

### Requirement: NUMERIC (TEXT) para valores exatos
Colunas financeiras SHALL usar TEXT para preservar precisão Decimal.

#### Scenario: Preço armazenado como TEXT
- **WHEN** salvar preço Decimal("50000.12345678")
- **THEN** SHALL armazenar como TEXT "50000.12345678" (sem perda)

### Requirement: REAL para display
Colunas de exibição SHALL usar REAL para cálculos agregados rápidos.

#### Scenario: PnL display arredondado
- **WHEN** salvar closed_pnl com pnl_value=50.12345678
- **THEN** pnl_value SHALL ser TEXT "50.12345678"
- **AND** pnl_value_display SHALL ser REAL 50.1235

### Requirement: Tabela state_meta
O schema SHALL ter tabela `state_meta` (key TEXT PK, value TEXT).

#### Scenario: Metadados persistidos
- **WHEN** salvar estado com base_currency='BRL' e version=4
- **THEN** state_meta SHALL conter key='base_currency' com value='BRL'

### Requirement: Tabela cashbook_entries
O schema SHALL ter tabela `cashbook_entries` (currency TEXT PK, amount TEXT, conversion_rate TEXT).

#### Scenario: Multi-moeda persistida
- **WHEN** salvar cashbook com BRL=100000 e USD=2500
- **THEN** cashbook_entries SHALL conter 2 rows com valores exatos

### Requirement: Tabela orders com FK para position
O schema SHALL ter tabela `orders` com FK `position_id` e coluna `order_type` ('open', 'increase', 'partial_close', 'full_close'), `broker`, `strategy_name`.

#### Scenario: Ordem vinculada a posição
- **WHEN** salvar ordem COMPRA BTC-USD que abre posição
- **THEN** orders SHALL conter position_id vinculado e order_type='open'

#### Scenario: Aumento de posição
- **WHEN** estratégia compra mais BTC-USD em posição já aberta
- **THEN** orders SHALL ter order_type='increase' e position_id da posição existente

#### Scenario: Saída parcial
- **WHEN** estratégia vende 50% da posição BTC-USD
- **THEN** orders SHALL ter order_type='partial_close' e quantity correspondente à metade

#### Scenario: Múltiplas ordens por posição
- **WHEN** posição tem 1 abertura + 2 aumentos + 1 saída parcial + 1 fechamento total
- **THEN** orders SHALL ter 5 registros com mesmo position_id e tipos distintos

#### Scenario: Ordem indexada
- **WHEN** salvar ordem
- **THEN** indexes SHALL existir em ticker, status, created_at, broker, strategy_name

### Requirement: Tabela positions com PK composta e broker
O schema SHALL ter tabela `positions` com PK `(ticker, strategy_name)`, colunas `broker`, `side`, `quantity`, `avg_price`, `status`, `opened_at`, `closed_at`, `grid_level INTEGER`, `parent_position_id TEXT`. O `avg_price` e `quantity` são recalculados a cada ordem do tipo 'increase'.

#### Scenario: Aumento recalcula preço médio
- **WHEN** posição long BTC-USD com avg_price=50000, qty=10 recebe ordem increase de qty=5 a price=52000
- **THEN** avg_price SHALL ser atualizado para 50666.67 e quantity para 15

#### Scenario: Posição raiz sem parent
- **WHEN** criar posição de abertura normal
- **THEN** grid_level SHALL ser NULL e parent_position_id SHALL ser NULL

#### Scenario: Posição grid com nível
- **WHEN** estratégia de grid cria sub-posição nível 3 vinculada à posição pai
- **THEN** grid_level SHALL ser 3 e parent_position_id SHALL ter o ID da posição pai

#### Scenario: Hierarquia de posições
- **WHEN** posição pai tem 5 sub-posições de grid (níveis 1-5)
- **THEN** todas SHALL ter mesmo parent_position_id com grid_level 1-5

#### Scenario: Multi-estratégia mesmo ticker
- **WHEN** Guardião e Sniper operam BTC-USD simultaneamente
- **THEN** positions SHALL ter 2 registros: (BTC-USD, guardiao) e (BTC-USD, sniper)

#### Scenario: Side da posição
- **WHEN** abrir posição comprada
- **THEN** side SHALL ser 'long'

#### Scenario: Broker distinto
- **WHEN** posição aberta na Binance e outra na Coinbase
- **THEN** broker SHALL distinguir as duas posições

### Requirement: Tabela strategy_positions com PK composta
O schema SHALL ter tabela `strategy_positions` com PK `(ticker, strategy_name)`, colunas `broker`, `entry_price`, `side`, `status`, `take_profit_pct`, `stop_loss_pct`, `trailing_pico`, `trailing_stop`, `opened_at`.

#### Scenario: Trailing stop por estratégia
- **WHEN** Guardião tem trailing pico=80300 e Sniper tem trailing pico=80500
- **THEN** strategy_positions SHALL ter 2 registros com trailings distintos

### Requirement: Tabela closed_pnl com broker e strategy_name
O schema SHALL ter tabela `closed_pnl` (id autoincrement, closed_at, ticker, strategy_name, broker, entry_price, exit_price, quantity, side, pnl_value TEXT, pnl_value_display REAL, pnl_pct REAL, reason).

#### Scenario: PnL por estratégia e broker
- **WHEN** Guardião fecha posição BTC-USD na Binance com lucro
- **THEN** closed_pnl SHALL ter strategy_name='guardiao-conservador' e broker='binance'

### Requirement: Tabela signals com broker e strategy_name
O schema SHALL ter tabela `signals` (created_at, id autoincrement, ticker, strategy_name, broker, signal_type, price, reason, take_profit_pct).

#### Scenario: Sinal por estratégia
- **WHEN** Guardião gera sinal COMPRA BTC-USD
- **THEN** signals SHALL ter strategy_name e broker preenchidos

### Requirement: Tabela ticks_raw
O schema SHALL ter tabela `ticks_raw` (time, symbol, broker, price TEXT, volume INTEGER, side TEXT).

#### Scenario: Tick raw persistido
- **WHEN** receber tick BTC-USD price=50000.12
- **THEN** ticks_raw SHALL conter o registro com timestamp e preço exato

#### Scenario: Index para queries por symbol
- **WHEN** criar tabela ticks_raw
- **THEN** index composto SHALL existir em (symbol, time)

### Requirement: Tabela ohlcv
O schema SHALL ter tabela `ohlcv` (time, symbol, broker, open TEXT, high TEXT, low TEXT, close TEXT, volume INTEGER, interval TEXT).

#### Scenario: Candle OHLCV persistido
- **WHEN** agregar ticks em candle 1m
- **THEN** ohlcv SHALL conter o registro com interval='1m'

#### Scenario: Index para time-series queries
- **WHEN** criar tabela ohlcv
- **THEN** index composto SHALL existir em (symbol, time)

### Requirement: Tabela portfolios com agrupamento
O schema SHALL ter tabela `portfolios` (id TEXT PK, name TEXT, portfolio_type TEXT, strategy_name TEXT, broker TEXT, initial_balance REAL, current_balance REAL, created_at TEXT).

#### Scenario: Portfolio agrupado por estratégia
- **WHEN** criar portfolio tipo 'strategy' para guardiao-conservador
- **THEN** portfolio_type SHALL ser 'strategy' e strategy_name preenchido

#### Scenario: Portfolio agrupado por corretora
- **WHEN** criar portfolio tipo 'broker' para Binance
- **THEN** portfolio_type SHALL ser 'broker' e broker='binance'

### Requirement: FK orders → positions
O schema SHALL ter constraint FK `position_id` em `orders` referenciando `positions`.

#### Scenario: Ordem sem posição (abertura)
- **WHEN** ordem COMPRA cria nova posição
- **THEN** position_id SHALL ser preenchido com o ID da posição criada

#### Scenario: Ordem sem posição é válida
- **WHEN** ordem é registrada antes da posição existir
- **THEN** position_id SHALL aceitar NULL

> "O schema é o contrato entre hoje e amanhã" – made by Sky 🗄️
