## ADDED Requirements

### Requirement: WriteQueue é o single writer
Todo write no SQLite SHALL passar pela `WriteQueue`. Nenhum componente grava direto.

#### Scenario: Broker enfileira ordem
- **WHEN** broker executa ordem COMPRA
- **THEN** SHALL chamar `await queue.enqueue(SaveOrder(...))` ao invés de `salvar()`

#### Scenario: Tracker enfileira posição
- **WHEN** PositionTracker atualiza trailing stop
- **THEN** SHALL chamar `await queue.enqueue(UpdatePosition(...))`

#### Scenario: Worker enfileira sinal
- **WHEN** StrategyWorker recebe sinal COMPRA
- **THEN** SHALL chamar `await queue.enqueue(SaveSignal(...))`

### Requirement: Batch flush em transação única
O flush SHALL drenar múltiplas operações em 1 transação SQLite.

#### Scenario: 10 operações em 1 transação
- **WHEN** enfileirar 3 SaveTick + 2 SaveOrder + 5 SavePnl
- **THEN** flush SHALL executar 1 BEGIN...COMMIT com 10 INSERTs

### Requirement: Flush periódico automático
O WriteQueue SHALL executar flush a cada `flush_interval` ms ou quando `max_batch` acumular.

#### Scenario: Flush por tempo
- **WHEN** 1 operação na fila e flush_interval=500ms
- **THEN** flush SHALL executar após 500ms

#### Scenario: Flush por batch size
- **WHEN** 50 operações na fila e max_batch=50
- **THEN** flush SHALL executar imediatamente

#### Scenario: Flush agressivo para ticks
- **WHEN** fila contém SaveTick e depth > 20
- **THEN** flush SHALL executar antes do intervalo padrão

### Requirement: Concurrent enqueue
Múltiplas coroutines SHALL poder enfileirar simultaneamente.

#### Scenario: 3 workers enfileiram ao mesmo tempo
- **WHEN** Worker A, B, C enfileiram operações simultaneamente
- **THEN** todas SHALL ser adicionadas à fila sem erro

### Requirement: Close drena fila
O `close()` SHALL executar flush final antes de parar.

#### Scenario: Flush final no shutdown
- **WHEN** chamar `await queue.close()` com 5 operações pendentes
- **THEN** SHALL executar flush final com as 5 operações

### Requirement: Tipos de operação
O `WriteQueue` SHALL suportar: SaveOrder, UpdatePosition, SavePnl, SaveSignal, SaveTick, SaveOhlcv.

#### Scenario: SaveOrder com FK para position
- **WHEN** enfileirar `SaveOrder` com position_id
- **THEN** flush SHALL gravar em `orders` com FK preenchida

#### Scenario: UpdatePosition com PK composta
- **WHEN** enfileirar `UpdatePosition(ticker="BTC-USD", strategy_name="guardiao")`
- **THEN** flush SHALL upsert em `positions` pela PK (ticker, strategy_name)

### Requirement: Crash consistency
Operações não-commitadas são aceitavelmente perdidas; database fica consistente.

#### Scenario: Crash com fila pendente
- **WHEN** processo morre com 3 operações na fila
- **THEN** database SHALL estar no estado do último flush commitado

> "A fila serializa o caos em ordem" – made by Sky ⚡
