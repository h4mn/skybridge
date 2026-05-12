# Design: Guardião Conservador v2

## Arquitetura

```
StrategyWorker._do_tick()
  │
  ├─ 1. Cotação              ← datafeed.obter_cotacao()
  │     └─ TTL cache 30s + backoff exponencial (3 retries)
  │
  ├─ 2. Trailing Stop        ← position_tracker.update_trailing()
  │     └─ Após +0.20%, trailing a 0.15% do pico, nunca abaixo breakeven
  │
  ├─ 3. SL/TP Check          ← position_tracker.check_price()
  │     ├─ SEMPRE verifica (mesmo com dados stale)
  │     ├─ Usa TP dinâmico por posição (definido na abertura)
  │     └─ Executa no preço do threshold, não do mercado
  │
  ├─ 4. Stale Guard          ← bloqueia apenas novos sinais (silencioso)
  │     └─ Se preço idêntico por 2 ticks → skip estratégia
  │
  ├─ 5. Dados de Mercado     ← datafeed.obter_historico()
  │     ├─ historico_precos → ADX +DI/-DI
  │     └─ historico_volumes → volume_ratio
  │
  ├─ 6. Estratégia ADX       ← GuardiaoConservador.evaluate()
  │     ├─ Crossover +DI/-DI (ADX puro, sem SMA)
  │     ├─ Filtro ADX >= 25 (remove whipsaws)
  │     ├─ Filtro volume_ratio >= 1.0 (confirmação)
  │     ├─ TP dinâmico por faixa ADX (0.30-0.60%)
  │     └─ Guarda indicadores em _last_indicators
  │
  ├─ 7. Position Guard       ← rejeita duplicadas e fantasmas
  │     ├─ Compra: rejeitar se já posicionado
  │     └─ Venda: rejeitar se não posicionado
  │
  ├─ 8. Execução
  │     ├─ COMPRA → open_position(ticker, preco, take_profit_pct=tp_dinamico)
  │     └─ VENDA → close_position + registra PnL
  │
  └─ 9. Observabilidade
        ├─ Tick colorido: +DI/-DI/ADX/gap/vol com cores ANSI
        ├─ Fechamento: LUCRO verde / PERDA vermelho
        ├─ _closed_pnl tracking
        └─ Heartbeat: trades, WR%, PnL fechado/aberto (%)
```

## Parâmetros Validados (backtest 7d 1m BTC-USD)

| Parâmetro | Valor | KPI Resultante |
|---|---|---|
| Sinal | +DI/-DI crossover | PnL +2.141% |
| Filtro ADX | >= 25 | WR 31.9% |
| Filtro Volume | ratio >= 1.0 | Sharpe +0.090 |
| SL | -0.20% fixo | MaxDD -1.600% |
| TP dinâmico | 0.30-0.60% por ADX | PF 1.23 |
| Trailing | +0.20% ativa, 0.15% dist | — |
| Breakeven | Não (não melhora Sharpe) | — |

## Componentes

### Guardião Conservador (estratégia)
- `guardiao_conservador.py` — domain object puro
- Sinal: crossover +DI/-DI (Wilder's smoothed ADX 14)
- Filtros: ADX >= 25, volume_ratio >= 1.0
- TP dinâmico: mapeado por faixa ADX na abertura da posição
- Expõe `_last_indicators` para log colorido no worker

### Position Tracker
- `position_tracker.py` — rastreamento com SL/TP/trailing
- TP dinâmico por posição (recebe na abertura)
- Persiste TP customizado no state JSON

### Strategy Worker
- `strategy_worker.py` — orquestra tick cycle
- Tick colorido com +DI/-DI/ADX/gap/vol
- Heartbeat com trades, WR%, PnL% aberto
- Stale guard silencioso (bloqueia apenas sinais, não SL/TP)

### Data Feed
- `yahoo_finance_feed.py` — TTL cache 30s + backoff exponencial

## Dependências
- `yfinance >= 0.2.40` (já instalado)
- Sem novas dependências externas
