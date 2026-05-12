# Tasks: Guardião Conservador v2

## P1 — Bug Fixes + Observabilidade

- [x] test_position_guard_rejeita_compra_duplicada — RED
- [x] test_position_guard_rejeita_venda_fantasma — RED
- [x] Implementar position guard no `strategy_worker.py::_do_tick()` — GREEN
- [x] test_tp_executes_at_threshold_price — RED
- [x] test_sl_executes_at_threshold_price — RED
- [x] Implementar preço de threshold no `position_tracker.py::check_price()` — GREEN
- [x] Implementar `preco_limite` no `paper_broker.py` — GREEN
- [x] Implementar log verde/vermelho ao fechar posição em `strategy_worker.py`
- [x] Implementar `_closed_pnl` tracking e heartbeat enriquecido (60 ticks) em `strategy_worker.py`

## P2 — Calibração Dinâmica

- [x] test_calibrador_atr_baixa_volatilidade — RED
- [x] test_calibrador_atr_alta_volatilidade — RED
- [x] Criar `calibrador_dinamico.py` com `calibrar() -> ParametrosCalibrados` — GREEN
- [x] Integrar calibrador no StrategyWorker (início de sessão)
- [x] Atualizar CSV diário com colunas: melhorias_impl, range_filter_on, tp_pct_config, sl_pct_config, calibrador_on, avg_holding_min

## P3 — Trailing Stop + Coleta

- [x] test_trailing_stop_apos_020 — RED
- [x] test_trailing_stop_sobe_com_preco — RED
- [x] test_trailing_stop_nunca_abaixo_breakeven — RED
- [x] Implementar trailing stop no `position_tracker.py` — GREEN
- [x] Criar `reversal_collector.py` — coleta dados pós-entrada (SKY-136)
- [x] Registrar dados em `estudo-reversao.csv`

## P4 — Rate Limiting + Stale Guard

- [x] test_stale_guard_nao_operar — RED
- [x] test_stale_guard_retoma_com_dados_frescos — RED
- [x] Implementar stale guard no `strategy_worker.py::_do_tick()` — GREEN
- [x] Implementar TTL cache (30s por ticker) + backoff exponencial no fetch

## P5 — ML Validation → ADX Puro (validado em notebook 14 células)

- [x] ML: comparar SMA crossover vs ADX puro → ADX venceu em todos combos
- [x] ML: testar TP dinâmico por faixa ADX → Conservador ADX>=25 melhor (+2.141%)
- [x] ML: scorecard completo (PnL, WR, Sharpe, MaxDD, PF) → campeão definido
- [x] ML: testar breakeven → não melhora Sharpe, descartado
- [x] ML: testar volume filter → ratio > 1.0x melhora qualidade, incluído
- [x] ML: registrar janela WFO no history → infra criada

## P6 — Implementação ADX +DI/-DI (baseado no ML)

- [x] Adicionar `historico_volumes` em DadosMercado + `take_profit_pct` em SinalEstrategia
- [x] Reescrever `guardiao_conservador.py`: ADX crossover + filtro ADX>=25 + filtro volume + TP dinâmico
- [x] PositionTracker com TP dinâmico por posição (`open_position` aceita `take_profit_pct`)
- [x] StrategyWorker passa volumes e usa TP dinâmico do sinal
- [x] Atualizar `run_orchestrator.py`: SL=0.20%, remover CalibradorDinamico, ADX puro
- [x] Testes: ADX calculation, crossover, ADX filter, volume filter, dynamic TP, per-position TP
- [x] Tick colorido: +DI/-DI/ADX/gap com cores ANSI por proximidade
- [x] Heartbeat com trades, WR% e PnL% aberto

## P7 — TradingView Indicadores

- [x] Guardião ADX Filter v2 (overlay) — +DI/-DI crossover, sinais filtrados, info box
- [x] Guardião ADX Panel v2 (painel separado) — +DI/-DI/ADX com cores dinâmicas, gap HOT, TP dinâmico

## Verificação

- [x] `pytest tests/unit/paper/ -v` — 83 testes verdes
- [x] Rodar orchestrator: zero duplicadas, zero fantasmas, TP no threshold, indicadores visíveis
