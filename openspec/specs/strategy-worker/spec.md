## MODIFIED Requirements

### Requirement: StrategyWorker com injeção de dependências
O StrategyWorker SHALL aceitar via construtor: `strategy`, `datafeed`, `executor`, `position_tracker`, `tickers`, `periodo_historico`, `intervalo_historico`, `quantity`, `reversal_collector`, `stale_threshold`.

> **Nota:** Para crypto 1min, recomenda-se `periodo_historico=30` com `intervalo_historico="1m"`.

#### Scenario: Criar worker com dependências
- **WHEN** criar `StrategyWorker(strategy, datafeed, executor, tracker, tickers=["BTC-USD"])`
- **THEN** SHALL inicializar com todas as dependências

### Requirement: Worker usa PositionTrackerPort
O worker SHALL depender de PositionTrackerPort (interface), não de SimpleTracker diretamente.

#### Scenario: Worker funciona com qualquer tracker
- **WHEN** worker recebe SimpleTracker ou HedgeTracker
- **THEN** SHALL operar normalmente via interface da port

### Requirement: Position Guard
O `_do_tick()` SHALL rejeitar compras duplicadas (já posicionado) e vendas fantasmas (sem posição).

#### Scenario: Compra duplicada rejeitada
- **WHEN** sinal COMPRA para ticker já posicionado
- **THEN** SHALL logar "compra rejeitada" e NÃO executar ordem

#### Scenario: Venda fantasma rejeitada
- **WHEN** sinal VENDA para ticker sem posição
- **THEN** SHALL logar "venda rejeitada" e NÃO executar ordem

### Requirement: Stale Guard
O `_do_tick()` SHALL bloquear novos sinais quando preço não muda por `stale_threshold` ticks (default 2). SL/TP continuam funcionando.

#### Scenario: Dados stale bloqueiam sinais
- **WHEN** preço idêntico por 2+ ticks
- **THEN** NENHUMA operação de compra/venda é executada

#### Scenario: SL/TP não bloqueados por stale
- **WHEN** dados stale E SL/TP acionado
- **THEN** SL/TP SHALL executar normalmente

#### Scenario: Dados frescos retornam
- **WHEN** preço muda após stale
- **THEN** operações retomam

### Requirement: SL fixo 0.50% na abertura de posição
O worker SHALL passar SL fixo de 0.50% ao abrir posição via PositionTrackerPort (usa default do tracker).

#### Scenario: SL fixo na entrada
- **WHEN** COMPRA executada
- **THEN** `open_position()` SHALL ser chamada sem `stop_loss_pct` (usa default 0.005)

### Requirement: TP dinâmico reavaliado a cada tick
O `_do_tick()` SHALL reavaliar TP da posição aberta pelo ADX atual a cada tick.

#### Scenario: TP atualizado por ADX
- **WHEN** posição aberta E strategy._last_indicators disponível
- **THEN** SHALL chamar `position_tracker.update_take_profit()` com novo TP

### Requirement: Dual Entry System — re-entry check
O worker SHALL verificar condições de re-entrada (Entry 1 e Entry 2) antes de avaliar estratégia, usando re-entry state do PositionTrackerPort.

#### Scenario: Entry 1 — Pullback Fibonacci (Buy Limit)
- **WHEN** sem posição E reentry_state existe E preco_atual <= fib_level E ticks >= cooldown
- **THEN** SHALL executar COMPRA com razao "Pullback Fib 61.8%"

#### Scenario: Entry 2 — Breakout + ADX confirm
- **WHEN** sem posição E reentry_state existe E preco_atual > crossover_price E +DI > -DI E ADX anterior < threshold E ADX atual >= threshold E ticks >= cooldown
- **THEN** SHALL executar COMPRA com razao "Breakout + ADX confirm"

#### Scenario: Re-entrada bloqueada por cooldown
- **WHEN** SL acionado há < 3 ticks
- **THEN** SHALL NÃO executar re-entrada

#### Scenario: Re-entry state criado após DI crossover
- **WHEN** DI crossover gera COMPRA
- **THEN** SHALL criar reentry_state com crossover_price e swing_low

#### Scenario: Re-entry state expirado
- **WHEN** reentry_state existe há 200+ ticks
- **THEN** SHALL limpar estado sem executar re-entrada

### Requirement: Cooldown rastreado por SL
O worker SHALL rastrear `_ticks_since_sl` por ticker, incrementando a cada tick após SL.

### Requirement: Log Verde/Vermelho
O worker SHALL logar fechamentos com tag LUCRO (verde) ou PERDA (vermelho) e ANSI colors.

#### Scenario: Fechamento em lucro
- **WHEN** posição fechada com PnL >= 0
- **THEN** log SHALL conter "LUCRO" em verde

#### Scenario: Fechamento em prejuízo
- **WHEN** posição fechada com PnL < 0
- **THEN** log SHALL conter "PERDA" em vermelho

### Requirement: Heartbeat Enriquecido
O worker SHALL logar heartbeat a cada 60 ticks com: trades, WR%, PnL fechado, PnL aberto (%), posições.

#### Scenario: Heartbeat a cada 60 ticks
- **WHEN** tick_count é múltiplo de 60
- **THEN** log SHALL conter "HEARTBEAT" com trades, WR%, Fechados, Aberto, Posições

### Requirement: Tick com indicadores coloridos
O worker SHALL logar +DI/-DI/ADX/gap/vol com cores ANSI quando evaluate() retorna None.

#### Scenario: Indicadores logados em tick neutro
- **WHEN** evaluate() retorna None e _last_indicators disponível
- **THEN** log SHALL conter +DI, -DI, ADX, gap, vol com cores por proximidade

### Requirement: PnL tracking
O worker SHALL manter `_closed_pnl` (lista de PnL fechado) para persistência.

### Requirement: ReversalCollector integração
O worker SHALL integrar ReversalCollector: start_tracking na compra, update a cada tick, stop_tracking no fechamento.

### Requirement: Construtor backward-compatible
O StrategyWorker SHALL manter compatibilidade com construtor antigo (strategy_name, on_suggestion).

> "O worker é a ponte entre a estratégia e o mercado" – made by Sky 🔗
