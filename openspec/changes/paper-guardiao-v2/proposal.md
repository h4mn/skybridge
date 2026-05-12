## Why

O Guardião Conservador v1 entra apenas uma vez por ciclo de tendência via DI crossover. Após SL, o +DI já está dominante — não há novo crossover para re-entrada. Em backtest de 7 dias (9.685 candles 1m BTC-USD), 65% dos sinais COMPRA ocorrem com ADX 25-30 (zona fraca), gerando whipsaws. O SL fixo de -0.20% é muito apertado — o mercado rallied +1.44% após parar o Guardião num trade que teria sobrevivido com SL fixo de 0.50%.

## What Changes

- **SL fixo 0.50%**: Substituir SL -0.20% por SL fixo 0.50% validado pelo ML como ponto doce.
- **Breakeven Standalone**: Ao atingir +0.10% de lucro, mover SL para o ponto de entrada (0%). Protege o capital eliminando risco de perda em trades que já deram retorno mínimo. Independente do trailing stop (que ativa em +0.20%).
- **Multi-Entry Strategy**: Duas estratégias de entrada independentes:
  - **Entrada 1 (DI cross)**: +DI cruza acima de -DI, com ADX acima do limite e -DI abaixo do ADX. "Compra quando a tendência se confirma com força — ADX domina o -DI".
  - **Entrada 2 (ADX surge)**: ADX cruza de abaixo para acima do limite, com +DI dominante e -DI abaixo do +DI. "Compra quando a força da tendência dispara — +DI já domina".
- **Swing Low Lookback**: Calcular o último fundo em 100 períodos quando DI crossover dispara, estabelecendo referência de preço para entradas derivadas.
- **Dual Entry System**: Após crossover, gerar duas oportunidades de entrada via Orders pendentes:
  - **Entry 1 (Pullback)**: Buy Limit no 61.8% Fibonacci da distância fundo→crossover. "Compra na retração".
  - **Entry 2 (Breakout + ADX)**: Após rompimento do nível do crossover + ADX cruzando acima do threshold. "Compra na confirmação".
- **Arquitetura forward-compatible (MT5)**: Evoluir PositionTracker para PositionTrackerPort + SimpleTracker (netting), preparando caminho pra HedgeTracker (hedging) e integração com brokers reais. Nomenclatura MT5-compatible (`ticket`, `position_type`).

## Capabilities

### New Capabilities
- `dual-entry-system`: Sistema de dupla entrada com pullback Fibonacci e breakout + confirmação ADX. Gera Orders pendentes gerenciadas pelo re-entry state.
- `position-tracker-port`: Interface abstrata PositionTrackerPort com implementação SimpleTracker (netting, 1 posição/ticker). Nomenclatura MT5-compatible para futura integração.

### Modified Capabilities
- `guardiao-conservador`: Multi-entry strategy (DI cross + ADX surge) com filtros condicionais. Exposição do `swing_low` no resultado do evaluate.
- `strategy-worker`: SL fixo 0.50% na abertura + breakeven standalone (+0.10% → SL na entrada) + lógica de re-entrada (Eventos 3-6) via PositionTrackerPort.

## Impact

- `src/core/paper/domain/strategies/guardiao_conservador.py` — cálculo de swing low
- `src/core/paper/domain/strategies/position_tracker.py` — refatorar para PositionTrackerPort + SimpleTracker
- `src/core/paper/facade/sandbox/workers/strategy_worker.py` — SL fixo 0.50% + re-entry logic via port
- `tests/unit/paper/domain/strategies/test_position_tracker.py` — testes da port + SimpleTracker + re-entry state

> "Duas chances por ciclo de tendência — o SL vira signal" – made by Sky ⚔️
