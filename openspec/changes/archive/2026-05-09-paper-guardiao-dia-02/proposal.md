# Guardião Conservador v2 — Bug Fixes + Observabilidade + ML Validation

## Why

O Guardião Conservador completou seu primeiro dia de operação (08/05/2026) com 14 bugs de execução críticos: compras duplicadas, vendas fantasma, TP com slippage de +0.84% ao invés de +0.50%, e falta de observabilidade no heartbeat e logs. Sem essas correções, o paper trading produz métricas não-confiáveis.

Após correções, sessão de ML (14 células de análise, 7 dias, 1m BTC-USD) validou que ADX puro +DI/-DI crossover supera SMA crossover em todos os combos testados.

## What Changes

### P1 — Bug Fixes + Observabilidade
- **Position Guard**: Eliminar compras duplicadas e vendas fantasma
- **TP/SL Threshold Price**: Executar no preço exato do threshold
- **Log Verde/Vermelho**: Diferenciar lucro/prejuízo com cores ANSI
- **Heartbeat Enriquecido**: PnL, trades, WR%, PnL% aberto a cada 60 ticks

### P2 — Calibração Dinâmica (substituída pelo ML)
- **Calibrador ATR**: Criado e integrado, posteriormente substituído por TP dinâmico ADX via ML

### P3 — Trailing Stop + Coleta
- **Trailing Stop**: Após +0.20%, trailing a 0.15% do pico, nunca abaixo breakeven
- **Coletor de Dados**: Registro pós-entrada para estudo estatístico (SKY-136)

### P4 — Rate Limiting + Stale Guard
- **TTL Cache + Backoff**: Limite de 1 req/s ao Yahoo com retry exponencial
- **Stale Guard**: Bloqueia novos sinais com dados defasados (silencioso)

### P5 — ML Validation (14 células notebook)
- **ADX vs SMA**: ADX puro venceu em todos os combos (+2.141% vs negativo)
- **TP Dinâmico**: Conservador ADX>=25 com TP 0.30-0.60% por faixa ADX
- **Breakeven**: Testado e descartado (não melhora Sharpe)
- **Volume**: ratio > 1.0x incluído como filtro

### P6 — Implementação ADX (baseada no ML)
- **Estratégia**: +DI/-DI crossover com ADX>=25 + volume filter + TP dinâmico
- **PositionTracker**: TP dinâmico por posição
- **Tick Colorido**: Indicadores +DI/-DI/ADX/gap com cores por proximidade
- **Parâmetros**: SL=-0.20%, TP=0.30-0.60% dinâmico, ADX>=25, vol>=1.0x

### P7 — TradingView Indicadores
- **Filter (overlay)**: Sinais filtrados com background por zona ADX
- **Panel (separado)**: +DI/-DI/ADX com cores dinâmicas, gap HOT, TP info box

## KPIs Validados

| KPI | Valor |
|---|---|
| PnL | +2.141% |
| Win Rate | 31.9% |
| Sharpe | +0.090 |
| MaxDD | -1.600% |
| Profit Factor | 1.23 |

## Out of Scope
- Cooldown entre sinais (position guard + filtros bastam)
- Velas 5min (futuro: módulo multi-timeframe)
- Comparação de estratégias (futuro: módulo de criação)
