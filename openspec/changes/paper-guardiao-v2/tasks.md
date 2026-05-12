## 1. Swing Low — GuardiaoConservador

- [x] 1.1 RED: Testes para `swing_low` em `_last_indicators`
- [x] 1.2 GREEN: Adicionar cálculo de swing low (min 100 períodos) em `evaluate()`

## 2. PositionTrackerPort + SimpleTracker

- [x] 2.1 RED: Testes da PositionTrackerPort (interface abstrata)
- [x] 2.2 GREEN: Extrair interface PositionTrackerPort de position_tracker.py
- [x] 2.3 GREEN: Renomear PositionTracker para SimpleTracker (manter alias backward-compatible)
- [x] 2.4 GREEN: Adicionar `ticket` sequencial nas posições (nomenclatura MT5)
- [x] 2.5 RED: Teste que SimpleTracker rejeita posição duplicada (netting)
- [x] 2.6 GREEN: Implementar netting mode (substitui posição existente)

## 3. Remover SL Dinâmico + SL Fixo 0.50%

- [x] 3.1 Remover `_sl_for_adx()` de `guardiao_conservador.py` (linhas 159-167)
- [x] 3.2 Remover `update_stop_loss()` de `position_tracker.py` (linhas 140-146)
- [x] 3.3 Remover reavaliação tick a tick de SL em `strategy_worker.py` (linhas 320-321)
- [x] 3.4 Remover `_sl_for_adx()` da abertura de posição em `strategy_worker.py` (linha 415)
- [x] 3.5 Limpar mock de `_sl_for_adx` em `test_order_position_pnl_persistence.py` (linha 36)
- [x] 3.6 GREEN: Ajustar default `stop_loss_pct` para `Decimal("0.005")` em position_tracker.py
- [x] 3.7 GREEN: Ajustar `stop_loss_pct` em `run_orchestrator.py` (linha 115, atual 0.002 → 0.005)
- [x] 3.8 RED: Teste que `open_position()` usa SL default 0.005
- [x] 3.9 Rodar testes existentes e corrigir quebras

## 4. Estado de Re-entrada — SimpleTracker

- [x] 4.1 RED: Testes para `set_reentry_state()`, `get_reentry_state()`, `tick_reentry()`, `clear_reentry_state()`
- [x] 4.2 GREEN: Implementar estado de re-entrada em `_reentry` dict
- [x] 4.3 RED: Teste de expiração automática (200 ticks)
- [x] 4.4 GREEN: Implementar expiração no `tick_reentry()`

## 5. Wire StrategyWorker — SL Fixo + Re-entry

- [x] 5.1 RED: Teste que worker abre posição com SL default do tracker (sem passar stop_loss_pct)
- [x] 5.2 GREEN: Simplificar abertura de posição — usar SL do tracker, sem `_sl_for_adx`
- [x] 5.3 GREEN: Worker recebe PositionTrackerPort (não SimpleTracker diretamente)

## 6. Dual Entry System — StrategyWorker

- [x] 6.1 RED: Teste Entry 1 — Pullback Fibonacci (Buy Limit)
- [x] 6.2 GREEN: Implementar verificação de pullback no `_do_tick()`
- [x] 6.3 RED: Teste Entry 2 — Breakout + ADX confirm
- [x] 6.4 GREEN: Implementar verificação de breakout + ADX no `_do_tick()`
- [x] 6.5 RED: Teste cooldown (bloqueia re-entrada < 3 ticks)
- [x] 6.6 GREEN: Implementar verificação de cooldown
- [x] 6.7 RED: Teste expiração (200 ticks sem execução)
- [x] 6.8 GREEN: Implementar expiração de re-entrada
- [x] 6.9 Criar reentry_state após DI crossover

## 7. Validação Final

- [x] 7.1 Rodar todos os testes (target: 210+ passando)
- [x] 7.2 Verificar zero regressão nos testes existentes
- [x] 7.3 Atualizar spec openspec/specs/ com novos requisitos

## 8. Breakeven Standalone (+0.10% → SL na entrada)

- [x] 8.1 RED: Testes para `update_breakeven()` — ativa em +0.10%, move SL para 0%, idempotente
- [x] 8.2 GREEN: Implementar `update_breakeven()` no SimpleTracker (gatilho `breakeven_activation_pct=0.001`)
- [x] 8.3 GREEN: Modificar `check_price()` — quando breakeven ativado e preço <= entrada, executar no preço de entrada com razão "Breakeven"
- [x] 8.4 GREEN: Wire `update_breakeven()` no StrategyWorker `_do_tick()` (antes de `check_price`)
- [x] 8.5 GREEN: Adicionar `breakeven_activated` ao `open_position()` e `restore_positions()`
- [x] 8.6 Documentar na change (proposal + design + tasks)

## 9. Multi-Entry Strategy (DI cross + ADX surge)

- [x] 9.1 RED: Teste Entrada 1 — DI crossover com ADX acima e -DI abaixo do ADX
- [x] 9.2 RED: Teste Entrada 1 — DI crossover bloqueado quando -DI >= ADX
- [x] 9.3 RED: Teste Entrada 2 — ADX cruza pra cima com +DI dominante e -DI < +DI
- [x] 9.4 RED: Teste Entrada 2 — ADX surge bloqueado quando -DI >= +DI
- [x] 9.5 RED: Teste Entrada 2 — ADX já acima não dispara como surge
- [x] 9.6 RED: Teste Entrada 2 — ADX cruza pra baixo não dispara
- [x] 9.7 RED: Teste gap DI respeitado em ambas as entradas
- [x] 9.8 GREEN: Refatorar `evaluate()` — separar Entrada 1 (DI cross com filtros) e Entrada 2 (ADX surge com filtros)
- [x] 9.9 Corrigir testes existentes afetados (DIGapFilter — ADX > -DI necessário)
- [x] 9.10 Verificar zero regressão (158 passed)
- [x] 9.11 Documentar na change (proposal + design D7 + tasks)

## 10. Ajustes Pós-Implementação

- [x] 10.1 Reduzir di_gap_min default de 5 para 3 (guardiao_conservador.py + teste)
- [x] 10.2 Simplificar Dual Entry Entry 2 — ADX >= threshold sem cruzamento (strategy_worker.py)
- [x] 10.3 Atualizar testes do dual entry (test_strategy_worker.py)
- [x] 10.4 Documentar D8 no design.md
- [x] 10.5 Verificar zero regressão (158 passed)
