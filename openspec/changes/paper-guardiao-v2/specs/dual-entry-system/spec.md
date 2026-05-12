## ADDED Requirements

### Requirement: Cálculo de nível Fibonacci 61.8%
O sistema SHALL calcular o nível 61.8% (golden ratio) da distância entre o swing low e o preço do DI crossover.

#### Scenario: Cálculo do nível 61.8%
- **WHEN** swing_low = $80,279 e crossover_price = $80,830 (distância = $551)
- **THEN** fib_level SHALL ser $80,279 + ($551 × 0.618) = $80,619.5

#### Scenario: Nível Fibonacci sem swing low
- **WHEN** swing_low não está disponível (dados insuficientes)
- **THEN** fib_level SHALL ser `None` e Entry 1 SHALL ser desabilitada

### Requirement: Entry 1 — Buy Limit no Pullback Fibonacci
O sistema SHALL gerar uma Order pendente do tipo Buy Limit no nível 61.8% após DI crossover, quando não há posição aberta.

#### Scenario: Buy Limit executado no nível Fibonacci
- **WHEN** reentry_state existe E preço atual <= fib_level E sem posição E cooldown OK
- **THEN** SHALL executar COMPRA com razao "Pullback Fib 61.8%"

#### Scenario: Buy Limit não executado (preço não chegou)
- **WHEN** reentry_state existe E preço atual > fib_level
- **THEN** SHALL NÃO executar (aguardar)

#### Scenario: Buy Limit ignorado se posição já existe (SimpleTracker netting)
- **WHEN** posição já está aberta para o ticker
- **THEN** Entry 1 SHALL ser ignorada

### Requirement: Entry 2 — Breakout + Confirmação ADX
O sistema SHALL gerar COMPRA quando: vela fecha acima do preço do DI crossover, +DI > -DI, ADX cruza acima do threshold. Sem posição aberta.

#### Scenario: Breakout com confirmação ADX
- **WHEN** reentry_state existe E preço > crossover_price E +DI > -DI E ADX anterior < threshold E ADX atual >= threshold E sem posição E cooldown OK
- **THEN** SHALL executar COMPRA com razao "Breakout + ADX confirm"

#### Scenario: Breakout sem ADX (adiado)
- **WHEN** preço > crossover_price E ADX < threshold
- **THEN** SHALL NÃO executar (aguardar ADX confirmar)

#### Scenario: Breakout ignorado se posição existe (SimpleTracker netting)
- **WHEN** posição já está aberta para o ticker
- **THEN** Entry 2 SHALL ser ignorada

### Requirement: Cooldown de re-entrada
O sistema SHALL exigir mínimo de 3 ticks entre SL exit e qualquer re-entrada.

#### Scenario: Re-entrada antes do cooldown
- **WHEN** SL acionado há < 3 ticks
- **THEN** SHALL NÃO gerar re-entrada

#### Scenario: Re-entrada após cooldown
- **WHEN** SL acionado há >= 3 ticks E condições de Entry 1 ou 2 atendidas
- **THEN** SHALL gerar re-entrada normalmente

### Requirement: Re-entry state como Orders pendentes
O sistema SHALL manter estado de re-entrada representando Orders pendentes, isolado das posições.

#### Scenario: Re-entry state criado após DI crossover
- **WHEN** DI crossover detectado E sem posição
- **THEN** SHALL criar re-entry state com `crossover_price`, `swing_low`, `fib_level` (Buy Limit level), `ticks_since_signal=0`

#### Scenario: Re-entry state limpo após execução
- **WHEN** Entry 1 ou Entry 2 executa COMPRA
- **THEN** SHALL limpar re-entry state

#### Scenario: Re-entry state expirado
- **WHEN** re-entry state existe há 200+ ticks sem execução
- **THEN** SHALL limpar sem executar

> "Orders pendentes são promessas de entrada" – made by Sky ⚔️
