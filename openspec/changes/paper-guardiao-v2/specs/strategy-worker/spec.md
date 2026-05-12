## ADDED Requirements

### Requirement: SL fixo 0.50% na abertura de posição
O worker SHALL passar SL fixo de 0.50% ao abrir posição via PositionTrackerPort.

#### Scenario: SL fixo na entrada
- **WHEN** COMPRA executada
- **THEN** `open_position()` SHALL ser chamada com `stop_loss_pct=0.005`

### Requirement: Worker usa PositionTrackerPort (não implementação concreta)
O worker SHALL depender de PositionTrackerPort (interface), não de SimpleTracker diretamente.

#### Scenario: Worker funciona com qualquer tracker
- **WHEN** worker recebe SimpleTracker ou HedgeTracker
- **THEN** SHALL operar normalmente via interface da port

### Requirement: Wire do Dual Entry System via Orders pendentes
O worker SHALL implementar verificação de re-entrada (Eventos 3-6) consultando re-entry state do PositionTrackerPort.

#### Scenario: Entry 1 — Pullback Fibonacci (Buy Limit)
- **WHEN** sem posição E reentry_state existe E preco_atual <= fib_level E ticks >= cooldown
- **THEN** SHALL executar COMPRA com razao "Pullback Fib 61.8%"

#### Scenario: Entry 2 — Breakout + ADX confirm
- **WHEN** sem posição E reentry_state existe E preco_atual > crossover_price E ADX anterior < threshold E ADX atual >= threshold E ticks >= cooldown
- **THEN** SHALL executar COMPRA com razao "Breakout + ADX confirm"

#### Scenario: Re-entrada bloqueada por cooldown
- **WHEN** SL acionado há < 3 ticks
- **THEN** SHALL NÃO executar re-entrada

#### Scenario: Re-entry state criado após DI crossover
- **WHEN** DI crossover gera COMPRA mas sem posição (entrada normal ou já posicionado)
- **THEN** SHALL criar reentry_state com crossover_price e swing_low

#### Scenario: Re-entry state expirado
- **WHEN** reentry_state existe há 200+ ticks
- **THEN** SHALL limpar estado sem executar re-entrada

> "O worker é a ponte entre a estratégia e o mercado" – made by Sky 🔗
