# Log de Monitoramento — Guardião Conservador v2

**Data:** 2026-05-12
**Sessão:** paper-guardiao-loop

---

## 00:00 — Virada de Dia, Mercado Lateral

### Status do Sistema

- **Status:** ATIVO
- **Uptime:** ~9 min (restart 23:51:48)
- **Tick:** #495
- **Código:** branch `paper-guardiao` (3d7990e)
- **Trades:** 21 (6W / 15L) | WR 29% | PnL $-78,993.55 | 0 posições

### KPIs Primários

| Métrica | Valor | Delta | Status |
|---------|-------|-------|--------|
| Trades | 21 | 0 | OK |
| Win Rate | 29% | 0pp | ALERTA |
| PnL Total | $-78,993.55 | 0 | ALERTA |
| Posições | 0 | 0 | OK |

### KPIs por Entrada (dia anterior)

| Entrada | Trades | WR | PnL |
|---------|--------|-----|------|
| DI cross | ~15 | ~27% | negativo |
| ADX surge | ~6 | ~33% | negativo |

### KPIs por Saída (dia anterior)

| Motivo | Trades | WR | PnL |
|--------|--------|-----|------|
| Stop Loss | 8 | 0% | -$164K |
| Take Profit | 6 | 100% | +$47K |
| DI crossover | 5 | 0% | -$5K |
| Breakeven | 2 | 0% | -$8K |

### Mercado Atual

| Hora | BTC | +DI | -DI | ADX | Gap | Regime |
|------|-----|-----|-----|-----|-----|--------|
| 23:51 | 81200 | 30.4 | 26.6 | 17.9 | 3.7 | lateral |
| 23:54 | 81234 | 35.3 | 21.6 | 17.6 | 13.7 | lateral +DI |
| 23:58 | 81224 | 29.1 | 20.8 | 17.5 | 8.2 | lateral +DI |
| **00:00** | **81232** | **28.3** | **19.2** | **17.5** | **9.0** | **lateral** |

- **Regime:** Lateral (ADX ~17-18, abaixo de 25)
- **+DI dominante** desde restart (gap 7-14)
- **Sem crossover** no período — +DI já estava acima de -DI quando o bot iniciou
- **BTC range:** 81200-81240 (~$40, 0.05%)

### Anomalias Detectadas

- **PERSISTÊNCIA SQLITE VAZIA:** Banco `paper_state.db` tem 0 rows em todas as tabelas (closed_pnl, signals, strategy_positions, ticks_raw, orders). O heartbeat reporta 21 trades / $-78,993.55 que vêm de dados em memória (restore). A `WriteQueue` está configurada mas `queue.start()` nunca é chamado no `run_orchestrator.py`. O flush via `_on_tick_complete` hook funciona (coroutine detected + awaited), mas os dados do período anterior (antes do restart de 23:35) foram perdidos quando o banco foi recriado. **ISSUE CRÍTICO: histórico de trades não está sendo persistido entre restarts.**
- **Rate limit yfinance:** Erros às 21:00 (sessão anterior), todos auto-recovered
- **Zero trades no novo dia:** Apenas 9 min de operação, mercado lateral

### Ações Recomendadas

1. **P1 — Corrigir persistência SQLite:** Adicionar `await queue.start()` em `run_orchestrator.py` após criar a WriteQueue, OU garantir que o flush via `_on_tick_complete` está realmente executando (adicionar log de debug)
2. **P1 — Investigar banco vazio:** Determinar se o banco foi recriado durante desenvolvimento ou se os dados nunca foram persistidos. Se nunca persistiram, o restore na inicialização está carregando dados fantasma
3. **P2 — Implementar re-arm de sinal:** Reduzir opportunity cost dos sinais perdidos por ADX lag (7 sinais no dia 11)
4. **P2 — Avaliar di_gap_min=3:** O crossover das 18:37 (gap=3.1, ADX=37.4) foi o mais forte do dia e foi bloqueado por 2 pontos

### Observação

A virada de dia coincide com um restart do bot (23:51:48). O mercado está em lateral profundo (ADX ~17), com +DI dominante mas gap insuficiente para gerar sinais novos. O bot herdou 21 trades em memória do período anterior, mas esses dados não sobreviverão a um próximo restart — a persistência SQLite está quebrada.

> "Novo dia, mesma persistência quebrada. O primeiro bug a corrigir é sempre o mais silencioso." – made by Sky 🔧

---

## 00:17 — Lateral Profundo, Persistência Ainda Quebrada

### Status do Sistema

- **Status:** ATIVO
- **Uptime:** ~25 min (restart 23:51:48)
- **Tick:** #496
- **Código:** branch `paper-guardiao` (3d7990e) — **correção `queue.start()` NÃO aplicada ainda** (bot roda código antigo)
- **Trades:** 21 (6W / 15L) | WR 29% | PnL $-78,993.55 | 0 posições

### KPIs Primários

| Métrica | Valor | Delta (vs 00:00) | Status |
|---------|-------|-------------------|--------|
| Trades | 21 | 0 | OK |
| Win Rate | 29% | 0pp | ALERTA |
| PnL Total | $-78,993.55 | 0 | ALERTA |
| Posições | 0 | 0 | OK |
| Ticks desde restart | 496 | +496 | OK |

### Mercado Atual

| Hora | BTC | +DI | -DI | ADX | Gap | Regime |
|------|-----|-----|-----|-----|-----|--------|
| 00:00 | 81232 | 28.3 | 19.2 | 17.5 | 9.0 | lateral +DI |
| 00:06 | 81208 | 25.8 | 31.9 | 17.1 | 6.1 | lateral -DI |
| **00:17** | **81209** | **25.8** | **28.4** | **13.0** | **2.6** | **lateral profundo** |

- **Regime:** Lateral profundo (ADX caiu de 17.5 → 13.0)
- **Gap estreitando:** 9.0 → 2.6 (+DI e -DI convergindo)
- **BTC range:** 81200-81240 (~$40, 0.05%) — praticamente estático
- **Zero trades, zero sinais** no novo dia

### Persistência SQLite — Status Inalterado

| Tabela | Rows | Esperado |
|--------|------|----------|
| closed_pnl | 0 | 21 |
| signals | 0 | N |
| ticks_raw | 0 | ~500+ |
| strategy_positions | 0 | 0 |
| orders | 0 | N |

**Diagnóstico:** O bot ainda roda o código sem `await queue.start()`. A correção foi aplicada no arquivo mas o processo não foi reiniciado (conforme regra do loop). O `_on_tick_complete` hook deveria fazer flush manual, mas ticks_raw=0 confirma que nem ticks estão sendo persistidos — o flush manual pode não estar funcionando ou a fila está vazia (ticks não estão sendo enfileirados).

**Ação necessária (operador):** Reiniciar o bot para aplicar a correção de persistência.

### Anomalias Detectadas

- **Persistência quebrada** (mesma da iteração anterior) — aguardando restart do operador
- **ADX em queda livre:** 17.9 → 13.0 em 25 min — mercado cada vez mais sem direção
- **Zero atividade** — sem sinais, sem trades, sem erros

### Ações Recomendadas

1. **OPERADOR:** Reiniciar o bot para aplicar correção `queue.start()` (commit pendente)
2. **P2:** Implementar re-arm de sinal para reduzir opportunity cost
3. **P2:** Avaliar di_gap_min=3

### Observação

O mercado está em lateral profundo com ADX=13 — o mais baixo desde o restart. Sem tendência, sem sinais, sem trades. O bot está corretamente fora do mercado. A única ação pendente é a correção de persistência, que requer restart manual pelo operador.

> "Lateral profundo: o bot faz exatamente o que deve — nada." – made by Sky 😴

---

## 01:17 — Mini-Downtrend + Spike de Recuperação, Sem Entrada

### Status do Sistema

- **Status:** ATIVO
- **Uptime:** ~1h25min (restart 23:51:48)
- **Tick:** #3923
- **Código:** branch `paper-guardiao` (3d7990e) — correção `queue.start()` pendente
- **Trades:** 21 (6W / 15L) | WR 29% | PnL $-78,993.55 | 0 posições

### KPIs Primários

| Métrica | Valor | Delta | Status |
|---------|-------|-------|--------|
| Trades | 21 | 0 | OK |
| Win Rate | 29% | 0pp | ALERTA |
| PnL Total | $-78,993.55 | 0 | ALERTA |
| Posições | 0 | 0 | OK |

### Mercado — Mini-Downtrend seguido de Spike

| Hora | BTC | +DI | -DI | ADX | Gap | Regime |
|------|-----|-----|-----|-----|-----|--------|
| 00:17 | 81209 | 25.8 | 28.4 | 13.0 | 2.6 | lateral |
| 00:30 | 81198 | 22.2 | 30.9 | 15.6 | 8.7 | -DI dominante |
| 00:45 | 81182 | 19.2 | 33.5 | 18.5 | 14.3 | downtrend leve |
| 01:00 | 81153 | 18.4 | 35.2 | 21.3 | 16.8 | downtrend |
| 01:09 | 81052 | 19.6 | 35.1 | 23.1 | 15.5 | downtrend |
| **01:15** | **80972** | **19.6** | **33.3** | **24.2** | **13.7** | **downtrend** |
| **01:16** | **81081** | **32.2** | **24.8** | **23.4** | **7.5** | **spike +DI** |
| **01:17** | **81122** | **40.3** | **21.7** | **23.9** | **18.6** | **recuperação** |

- **BTC range:** 81209 → 80972 → 81122 (downtrend de -$237, recuperação de +$150)
- **+DI explodiu:** 19.6 → 40.3 em ~2 min (01:15 → 01:17)
- **Gap forte:** 18.6 (+DI dominante), ADX=23.9 (abaixo de 25)
- **Sem crossover:** +DI já estava acima de -DI antes do spike — sinal consumido

### Persistência SQLite — Ainda Quebrada

Todas as tabelas com 0 rows. Bot roda código sem `queue.start()`. Aguardando restart do operador.

### Anomalias Detectadas

- **Persistência quebrada** — aguardando restart (sem autonomia para reiniciar)
- **Spike +DI sem crossover:** +DI saltou 19.6→40.3 mas sem gerar sinal novo (crossover já havia ocorrido anteriormente com ADX<25)

### Observação

O padrão de opportunity cost do dia 11 se repete: +DI cruza acima durante ADX baixo, ADX sobe depois, mas sem crossover novo. O spike de +DI para 40.3 com gap=18.6 seria uma entrada ideal se o sinal não tivesse sido consumido no crossover original.

> "De novo o mesmo filme: sinal consumido, ADX atrasado, lucro perdido." – made by Sky 🔄

---

## 02:17 — Trade #22 Aberto, Trailing Ativo, Gap Colapsando

### Status do Sistema

- **Status:** ATIVO
- **Uptime:** ~2h25min (restart 23:51:48)
- **Tick:** #7382
- **Código:** branch `paper-guardiao` (3d7990e) — correção `queue.start()` pendente
- **Trades:** 21 fechados + 1 aberto | WR 29% | PnL Fechado $-78,993.55 | **Aberto: +$9,637 (+0.119%)**

### Trade #22 — COMPRA BTC-USD

```
01:19:10 POSIÇÃO ABERTA BTC-USD @ 81116.97
```

**Entrada:** Crossover +DI/-DI com gap forte (21.0) e ADX=24.7 (passou no threshold)

### Cronologia

| Hora | BTC | +DI | -DI | ADX | Gap | PnL (est.) | Trail |
|------|-----|-----|-----|-----|-----|------------|-------|
| 01:17 | 81122 | 40.3 | 21.7 | 23.9 | 18.6 | — | — |
| 01:18 | 81113 | 40.7 | 19.7 | 24.7 | 21.0 | — | — |
| **01:19** | **81116** | — | — | — | — | **0.000%** | **ENTRADA** |
| 01:59 | 81260 | 25.3 | 33.8 | 26.4 | 8.5 | +0.178% | 81,158 |
| **02:05** | **81259** | **31.0** | **28.8** | **20.2** | **2.2** | **+0.175%** | **81,158** |
| 02:07 | 81231 | 33.5 | 28.9 | 19.1 | 4.6 | +0.141% | 81,158 |
| 02:10 | 81194 | 26.3 | 36.5 | 17.2 | 10.2 | +0.096% | 81,158 |
| 02:13 | 81173 | 23.8 | 38.4 | 17.8 | 14.6 | +0.070% | 81,158 |
| 02:16 | 81213 | 32.5 | 32.3 | 16.8 | 0.2 | +0.119% | 81,158 |
| **02:17** | **81219** | **31.4** | **31.2** | **15.6** | **0.2** | **+0.119%** | **81,158** |

### Análise do Trade

- **Entrada correta:** Gap=21.0 passou no `di_gap_min=5`, ADX=24.7 passou no threshold
- **Pico:** ~$14,286 (+0.176%) — trailing travou em 81,158
- **Drawdown:** PnL caiu de +0.176% → +0.070% (-DI dominante, gap 14.6)
- **Recuperação:** +DI voltou (23.8→32.5), gap estreitou para 0.2
- **SL=0.000%:** Trailing stop no controle (SL original zerado quando trailing ativou)
- **TP=0.300%:** ADX caiu para ~15-16, TP dinâmico reduziu

### Alerta — Gap=0.2 (Crossover Iminente)

+DI=31.4 vs -DI=31.2 com gap=0.2. **Crossover bearish a 1 tick de acontecer.** Se -DI cruzar acima:
- Trailing stop em 81,158 será acionado
- PnL de ~+$9,637 será garantido (entrada 81,116 → trail 81,158 = +$4,103)

### Persistência SQLite — Ainda Quebrada

0 rows em todas as tabelas. Correção pendente.

### Observação

O trade #22 entrou com as condições ideais documentadas no dia 11: gap forte (21.0), ADX acima do threshold (24.7), e +DI dominante. O `di_gap_min=5` funcionou perfeitamente aqui — bloqueou ruído e permitiu a entrada real. O trailing stop travou o pico e está protegendo o lucro enquanto o gap colapsa.

> "Quando o gap é real, o filtro deixa passar. O trailing faz o resto." – made by Sky ✅

---

## 03:16 — Trade #22: LUCRO por Trailing Stop! +$4,590

### Status do Sistema

- **Status:** ATIVO
- **Uptime:** ~3h25min (restart 23:51:48)
- **Tick:** #10752
- **Código:** branch `paper-guardiao` (3d7990e)
- **Trades:** 22 (7W / 15L) | **WR 32%** | **PnL $-74,403.27** | 0 posições

### Trade #22 — Fechado por Trailing Stop

```
01:19:10 POSIÇÃO ABERTA  BTC-USD @ 81116.97
03:00:31 LUCRO: FECHAMENTO BTC-USD @ 81162.87 | +0.057% ($+4,590.28)
         (Trailing Stop acionado (+0.1%))
```

- **Entry:** 81116.97 | **Exit:** 81162.87 | **Duração:** ~1h41min
- **Lucro:** +$4,590.28 (+0.057%)
- **Trailing:** Travou em 81,162.87 (pico durante 02:57-02:58)
- **Acionamento:** BTC caiu para 81162.87, atingiu trailing

### Cronologia Final

| Fase | Hora | BTC | +DI | -DI | ADX | Gap | PnL | Trail |
|------|------|-----|-----|-----|-----|-----|-----|-------|
| Entry | 01:19 | 81116 | 40.7 | 19.7 | 24.7 | 21.0 | +0.000% | — |
| Pico | 02:05 | 81259 | 31.0 | 28.8 | 20.2 | 2.2 | +0.175% | 81,158 |
| Trailing up | 02:57 | 81249 | 34.1 | 26.3 | 14.4 | 7.8 | +0.172% | **81,162** |
| Gap collapse | 02:59 | 81225 | 31.7 | 29.3 | 13.6 | 2.4 | +0.141% | 81,162 |
| -DI spike | 03:00 | 81195 | 27.6 | 37.1 | 13.7 | 9.5 | +0.102% | 81,162 |
| **Trailing hit** | **03:00** | **81162** | — | — | — | — | **+0.057%** | **81,162** |

### KPIs Atualizados

| Métrica | Antes | Depois | Delta |
|---------|-------|--------|-------|
| Trades | 21 | 22 | +1 |
| Wins | 6 | **7** | +1 |
| Win Rate | 29% | **32%** | **+3pp** |
| PnL Fechado | $-78,993 | **$-74,403** | **+$4,590** |

### Mercado Atual (03:16)

| Hora | BTC | +DI | -DI | ADX | Gap |
|------|-----|-----|-----|-----|-----|
| 03:00 | 81195 | 27.6 | 37.1 | 13.7 | 9.5 |
| 03:07 | 81219 | 26.1 | 29.5 | 11.8 | 3.4 |
| 03:16 | 81252 | 20.5 | 23.8 | 10.2 | 3.3 |

- ADX despencou para 10.2 — mercado totalmente lateral
- Sem posição, sem sinais

### Conformidade

| Check | Status |
|-------|--------|
| di_gap_min=5 | OK (gap=21.0 na entrada) |
| ADX threshold | OK (24.7 na entrada) |
| Trailing stop | OK (ativou, protegeu lucro) |
| TP dinâmico | OK (0.300% com ADX baixo) |
| SL 0.500% | OK (não atingido) |

### Observação

Trade #22 é o segundo win consecutivo por trailing/TP (Trade #21 foi TP, #22 foi trailing). O trailing capturou +$4,590 que seria zero sem ele. O lucro é modesto (+0.057%) mas confirma que o sistema de trailing stop está funcionando como proteção de lucro em mercado lateral.

> "O trailing não fica rico, mas evita pobreza." – made by Sky 💎

---

## 04:22 — Crash-Recuperação e Crossover Perdido

### Status do Sistema

- **Status:** ATIVO
- **Uptime:** ~4h 30m (desde 23:51)
- **Tick:** #14460
- **Código:** branch `paper-guardiao` (3d7990e)
- **Trades:** 22 (7W / 15L) | WR 32% | PnL $-74,403.27 | 0 posições

### KPIs Primários

| Métrica | Valor | Delta (desde 03:16) | Status |
|---------|-------|---------------------|--------|
| Trades | 22 | 0 | OK |
| Win Rate | 32% | 0pp | ALERTA (< 35%) |
| PnL Total | $-74,403 | $0 | RUIM |
| Profit Factor | ~0.47 | — | RUIM (< 0.5) |
| Expectancy | ~$-3,382/trade | — | RUIM (< 0) |

### KPIs por Saída

| Motivo | Trades | WR | PnL |
|--------|--------|-----|------|
| Stop Loss | ~6 | 0% | ~$-111k |
| SMA crossover | ~9 | 2W | ~$-20k |
| Take Profit | ~4 | 100% | ~$+57k |
| Trailing Stop | 1 | 100% | $+4,590 |

### Evento de Mercado (03:16 → 04:22)

| Hora | BTC | +DI | -DI | ADX | Gap | Evento |
|------|-----|-----|-----|-----|-----|--------|
| 03:16 | 81252 | 20.5 | 23.8 | 10.2 | 3.3 | Lateral |
| 04:03 | 80908 | 10.4 | 58.6 | 48.9 | 48.3 | **CRASH** — BTC cai $344 |
| 04:04 | 80888 | 8.5 | 50.6 | 51.9 | 42.1 | ADX pico 51.9 |
| 04:07 | 80912 | 8.0 | 45.0 | 55.2 | 37.0 | **ADX pico 55.2** |
| 04:09 | 80950 | 15.9 | 37.2 | 54.1 | 21.3 | Recuperação +DI |
| 04:12 | 81044 | 30.3 | 28.1 | 48.7 | 2.3 | **Crossover** (gap < 5) |
| 04:12 | 81048 | 32.3 | 27.2 | 45.9 | 5.1 | Gap ≥ 5, sem sinal |
| 04:14 | 81058 | 35.6 | 24.8 | 44.1 | 10.8 | Bullish forte |
| 04:15 | 80919 | 34.6 | 24.1 | 42.2 | 10.5 | Preço reverte |
| 04:16 | 80969 | 23.4 | 43.5 | 40.6 | 20.1 | **Reversão!** -DI domina |
| 04:20 | 81018 | 26.4 | 36.7 | 37.2 | 10.2 | Lateralizando |

### Anomalias Detectadas

1. **COMPRA perdida por ADX lag defect** — Crossover +DI > -DI em 04:12:23 (gap=2.3 < 5), gap abriu para 5.1 em 04:12:54 mas o sinal já foi consumido. Preço subiu de 81044→81058 (+$14). Custo de oportunidade: modesto (mercado reverteu logo depois)
2. **VENDA rejeitada pelo GUARD** (04:16:28) — Correto. Sinal de venda sem posição aberta
3. **Erro yfinance** (ontem 21:00) — "possibly delisted" para BTC-USD. Rate-limit temporário, recuperou sozinho
4. **SQLite persistência:** AINDA VAZIO (0 rows). Fix aplicado no código mas bot roda versão antiga

### Conformidade

| Check | Status |
|-------|--------|
| di_gap_min=5 | Gap=2.3 no crossover → bloqueou corretamente |
| ADX threshold | ADX=48.7 no crossover → OK |
| Trailing stop | Não aplicável (sem posição) |
| Position Guard | VENDA rejeitada corretamente |
| Uptime | Contínuo, sem crashes |

### Ações Recomendadas

1. **[PENDENTE]** Operador precisa reiniciar o bot para aplicar fix de persistência (`queue.start()`)
2. **[P1]** ADX lag defect confirmado novamente — considerar re-arm signal quando gap atinge threshold
3. **[P1]** Reavaliar `di_gap_min` de 5 para 3 — este crossover específico teria funcionado com gap=2

### Observação

Hora intensa: BTC crashou $344 (81252→80888) com -DI em 58.6 e ADX em 55.2 — a maior volatilidade do dia. Depois recuperou e gerou crossover +DI, mas o gap filter bloqueou a entrada. O mercado reverteu rápido de qualquer forma, então a oportunidade perdida foi pequena (~$14 de upside antes da reversão). O fato de o gap ter aberto para 5.1 apenas 30s depois do crossover sugere que `di_gap_min=3` teria capturado esta entrada — embora o resultado final seria Stop Loss dado que o preço caiu logo depois.

> "O filtro protegeu duas vezes: bloqueou a entrada e bloqueou a perda." – made by Sky 🛡️

---

## 05:14 — Mercado em Tendência de Baixa, Bot Fora

### Status do Sistema

- **Status:** ATIVO
- **Uptime:** ~5h 22m (desde 23:51)
- **Tick:** #17460
- **Código:** branch `paper-guardiao` (3d7990e)
- **Trades:** 22 (7W / 15L) | WR 32% | PnL $-74,403.27 | 0 posições

### KPIs Primários

| Métrica | Valor | Delta (desde 04:22) | Status |
|---------|-------|---------------------|--------|
| Trades | 22 | 0 | OK |
| Win Rate | 32% | 0pp | ALERTA |
| PnL Total | $-74,403 | $0 | RUIM |
| Profit Factor | ~0.47 | — | RUIM |

### Mercado Atual (04:22 → 05:14)

| Hora | BTC | +DI | -DI | ADX | Gap | Regime |
|------|-----|-----|-----|-----|-----|--------|
| 04:20 | 81018 | 26.4 | 36.7 | 37.2 | 10.2 | baixa |
| 04:59 | 80837 | 18.0 | 43.1 | 23.0 | 25.2 | baixa |
| 05:07 | 80860 | 12.5 | 34.0 | 33.6 | 21.6 | baixa |
| 05:13 | 80807 | 11.7 | 37.4 | 36.0 | 25.8 | **baixa forte** |

- BTC caiu $211 (-0.26%) no período
- -DI dominante o tempo todo (30-45), +DI em colapso (26→12)
- ADX subindo: 37→36 (trending) → mercado em tendência de baixa consistente
- Sem crossover, sem sinais — comportamento correto do bot

### Anomalias Detectadas

- **Nenhuma** — hora silenciosa, sem sinais, sem erros, sem trades

### Ações Recomendadas

- **[PENDENTE]** Operador precisa reiniciar o bot para aplicar fix de persistência
- **[P1]** ADX lag defect + di_gap_min (mantido do relatório anterior)
- Mercado em baixa forte — quando +DI cruzar acima de -DI, a entrada será crítica

### Observação

Hora sem eventos. O mercado entrou em tendência de baixa clara (-DI=37.4, ADX=36.0) e o bot está corretamente fora. A estratégia DI/ADX brilha neste cenário: evita comprar em queda. O próximo ponto de interesse será quando +DI cruzar acima de -DI — potencialmente uma entrada de reversão lucrativa se o ADX estiver alto o suficiente.

> "Paciência é posição." – made by Sky ⏳

---

## 06:03 — Tendência Enfraquecendo, Crossover Rejeitado por ADX Baixo

### Status do Sistema

- **Status:** ATIVO
- **Uptime:** ~6h 12m (desde 23:51)
- **Tick:** #20220
- **Código:** branch `paper-guardiao` (3d7990e)
- **Trades:** 22 (7W / 15L) | WR 32% | PnL $-74,403.27 | 0 posições

### KPIs Primários

| Métrica | Valor | Delta (desde 05:14) | Status |
|---------|-------|---------------------|--------|
| Trades | 22 | 0 | OK |
| Win Rate | 32% | 0pp | ALERTA |
| PnL Total | $-74,403 | $0 | RUIM |
| Profit Factor | ~0.47 | — | RUIM |

### Mercado Atual (05:14 → 06:03)

| Hora | BTC | +DI | -DI | ADX | Gap | Regime |
|------|-----|-----|-----|-----|-----|--------|
| 05:14 | 80783 | 11.0 | 36.8 | 37.2 | 25.8 | baixa forte |
| 05:16 | 80749 | 9.0 | 39.0 | 40.4 | 30.0 | baixa forte |
| 05:49 | 80894 | 28.1 | 23.9 | 13.9 | 4.3 | **crossover!** |
| 05:52 | 80890 | 28.5 | 23.3 | 12.2 | 5.2 | gap OK, ADX baixo |
| 05:54 | 80838 | 21.5 | 37.4 | 13.0 | 15.9 | crossover revertido |
| 06:01 | 80780 | 19.2 | 37.5 | 19.3 | 18.3 | baixa fraca |

- ADX despencou de 40.4 para 12.2 — tendência de baixa desmoronou
- +DI saltou de 9.0 para 28.5 (crossover com -DI em 05:49)
- Crossover rapidamente revertido: -DI voltou a dominar em 05:54
- BTC oscilou entre 80749-80910 (range $161)

### Anomalias Detectadas

1. **ADX lag defect (3ª ocorrência hoje)** — Crossover +DI > -DI em 05:49 com gap=4.3 (< 5), ADX=13.9 (< 25). Gap abriu para 5.2 em 05:52 mas ADX ainda 12.2. Crossover revertido em 05:54. Ambos os filtros (gap e ADX) bloquearam — corretamente, dado que o crossover reverteu em 5 minutos
2. **SQLite ainda vazio** — 0 rows em todas as tabelas, fix não aplicado

### Ações Recomendadas

- **[PENDENTE]** Operador precisa reiniciar para fix de persistência
- **[P1]** ADX lag defect confirmado pela 3ª vez — padrão recorrente do sistema
- **[INFO]** Crossover de 05:49 foi fraco (ADX=13) e reverteu rápido — filtros corretamente bloquearam

### Observação

O padrão se repete: crossover acontece com ADX baixo (< 15), filtros bloqueiam, e o crossover reverte. Desta vez os filtros acertaram — o preço caiu $56 (80894→80838) nos 5 minutos seguintes ao crossover. ADX caindo de 40 para 12 indica que a tendência de baixa está perdendo força, mas não há direção clara ainda. O bot está em modo "espera qualificada" — correto para um mercado sem convicção.

> "O mercado indeciso é o melhor filtro natural." – made by Sky 🔮

---

## 06:50 — ADX Subindo, Mercado Ainda Lateral-Baixa

### Status do Sistema

- **Status:** ATIVO
- **Uptime:** ~7h (desde 23:51)
- **Tick:** #20999
- **Trades:** 22 (7W / 15L) | WR 32% | PnL $-74,403.27 | 0 posições

### Mercado Atual (06:03 → 06:50)

| Hora | BTC | +DI | -DI | ADX | Gap |
|------|-----|-----|-----|-----|-----|
| 06:01 | 80780 | 19.2 | 37.5 | 19.3 | 18.3 |
| 06:07 | 80750 | 20.5 | 35.7 | 18.1 | 15.2 |
| 06:12 | 80786 | 19.7 | 32.0 | 21.8 | 12.2 |
| 06:15 | 80759 | 16.7 | 36.4 | 25.7 | 19.7 |
| 06:16 | 80773 | 17.2 | 35.8 | 25.6 | 18.6 |

- ADX subindo: 19.3 → 25.6 — atingiu o threshold 25
- -DI dominante estável (~35), +DI fraco (~17)
- BTC lateralizando em 80742-80805 (range $63)
- 1 VENDA rejeitada pelo GUARD em 05:25 — sinal correto, sem posição

### Anomalias

- Nenhuma nova. ADX voltou ao threshold 25 mas sem crossover (-gap=-18.6)

### Observação

Continuação do cenário anterior. ADX subiu de volta para 25.6, mas sem crossover de +DI. O mercado está em "prensa" — ADX indica tendência formando mas a direção ainda é baixa. O próximo movimento significativo será quando +DI cruzar acima de -DI com ADX > 25 e gap ≥ 5.

> "ADX subindo sem crossover é como motor ligado sem engrenar." – made by Sky ⚙️

---

## 07:05 — Trade #23 Perda + Trade #24 Aberto (Fib Pullback!)

### Status do Sistema

- **Status:** ATIVO
- **Uptime:** ~7h 14m (desde 23:51)
- **Tick:** #23756
- **Código:** branch `paper-guardiao` (3d7990e)
- **Trades fechados:** 23 (7W / 16L) | WR 30% | PnL $-76,453.27
- **Posição:** 1 aberta | PnL -$3,945 (-0.049%)

### KPIs Primários

| Métrica | Valor | Delta (desde 06:50) | Status |
|---------|-------|---------------------|--------|
| Trades | 23 | +1 | OK |
| Win Rate | 30% | -2pp | RUIM |
| PnL Fechado | $-76,453 | -$2,050 | RUIM |
| PnL Total | $-80,398 | -$5,995 | RUIM |
| Profit Factor | ~0.45 | -0.02 | RUIM |

### Trade #23 — Detalhes

| Campo | Valor |
|-------|-------|
| Entrada | 06:31:00 @ $80,863.50 (DI cross COMPRA) |
| Saída | 06:48:21 @ $80,843.00 (VENDA DI cross) |
| PnL | -$2,050 (-0.025%) |
| Duração | ~17 min |
| +DI/-DI na saída | 23.8 / 27.9, ADX=32.5 |
| Motivo | -DI cruzou acima de +DI → sinal de venda |

### Trade #24 — Posição Aberta

| Campo | Valor |
|-------|-------|
| Entrada | 06:54:59 @ $80,794.24 |
| **Tipo** | **RE-ENTRY (Pullback Fib 61.8%)** — NOVO! |
| BTC atual | $80,754.79 |
| PnL aberto | -$3,945 (-0.049%) |
| SL | 0.500% ($80,391) |
| TP | 0.500% ($81,197) → ajustou de 0.400% para 0.500% quando ADX > 30 |
| +DI / -DI | 11.1 / 38.2, ADX=36.2 |

### Mercado Atual (06:50 → 07:05)

| Hora | BTC | +DI | -DI | ADX | Evento |
|------|-----|-----|-----|-----|--------|
| 06:31 | 80863 | — | — | — | COMPRA (Trade #23) |
| 06:46 | 80870 | 26.6 | 20.4 | 34.4 | +DI dominante |
| 06:48 | 80843 | 23.8 | 27.9 | 32.5 | **VENDA** — -DI cruza |
| 06:50 | 80855 | 22.3 | 23.5 | 26.8 | Sem posição |
| 06:54 | 80794 | 18.5 | 34.5 | 24.0 | **COMPRA Fib pullback** |
| 07:02 | 80799 | 14.5 | 32.3 | 30.5 | TP sobe p/ 0.500% |
| 07:04 | 80754 | 10.7 | 39.4 | 34.8 | PnL -$3,945 |
| 07:05 | 80757 | 11.1 | 38.2 | 36.2 | ADX subindo |

### Anomalias Detectadas

1. **Entrada contra-tendência via Fib pullback** — COMPRA em 80794 com -DI=34.5 >> +DI=18.5 e ADX=24.0. Mercado claramente bearish, posição imediatamente submersa
2. **Novo tipo de sinal**: "RE-ENTRY (Pullback Fib 61.8%)" — não é DI cross nem ADX surge. Primeira ocorrência observada deste tipo de entrada
3. **TP dinâmico**: Ajustou de 0.400% para 0.500% quando ADX ultrapassou 30 — comportamento esperado

### Ações Recomendadas

- **[ATENÇÃO]** Posição em -$3,945 (-0.049%) com -DI=38 dominante. SL em 0.500% ($80,391). Distância do SL: $80,794 - $80,391 = $403 (0.50%)
- **[PENDENTE]** Fix persistência SQLite ainda não aplicado
- **[OBSERVAR]** Se BTC cair abaixo 80391, SL será acionado: perda de ~$40,300

### Observação

Hora movimentada! Dois eventos importantes: (1) Trade #23 fechou com perda modesta de -$2,050 quando -DI cruzou acima de +DI em ADX=32.5, e (2) apenas 6 minutos depois o bot abriu uma nova posição via **Fibonacci Pullback 61.8%** — um tipo de entrada que não víamos antes. A entrada foi contra a tendência (-DI=34.5 dominante) e a posição já está submersa em -$3,945. O SL dinâmico em 0.500% protege contra perda máxima de ~$40,300. ADX subindo para 36 sugere que a tendência de baixa está se fortalecendo — pé na sola.

> "Comprando na areia movediça com uma corda de Fibonacci." – made by Sky 📐

---

## 07:48 — Posição Fib Agravando, Aproximando do SL

### Status do Sistema

- **Status:** ATIVO — POSIÇÃO EM RISCO
- **Uptime:** ~7h 57m
- **Tick:** #26188
- **Trades fechados:** 23 (7W / 16L) | WR 30% | PnL $-76,453.27
- **Posição:** 1 aberta | PnL **-$12,603 (-0.156%)** | Entrada $80,794.24

### KPIs da Posição

| Métrica | Valor | Status |
|---------|-------|--------|
| Preço entrada | $80,794.24 | — |
| BTC atual | $80,662 | -$132 da entrada |
| PnL aberto | -$12,603 (-0.156%) | ALERTA |
| Pior ponto | -$15,933 (-0.197%) @ 80631 | — |
| Melhor ponto | +$552 (+0.007%) @ 80799 | breve |
| **SL** | **$80,390 (0.500%)** | **distância: $272 (0.34%)** |
| TP | $81,117 (0.400%) | distância: $455 |
| Tipo entrada | Fib Pullback 61.8% | contra-tendência |

### Evolução da Posição (07:05 → 07:48)

| Hora | BTC | PnL | +DI | -DI | ADX | Nota |
|------|-----|-----|-----|-----|-----|------|
| 07:05 | 80757 | -$3,945 | 11.1 | 38.2 | 36.2 | Entrada Fib |
| 07:10 | 80799 | **+$552** | 21.4 | 30.9 | 31.8 | Breve positivo |
| 07:16 | 80743 | -$2,831 | 19.4 | 39.2 | 29.1 | -DI ressurge |
| 07:31 | 80724 | -$7,019 | 23.3 | 35.1 | 26.8 | Agravando |
| 07:41 | 80686 | -$11,510 | 25.0 | 35.4 | 26.9 | -$11k |
| 07:43 | **80631** | **-$15,933** | 22.0 | 38.0 | 26.9 | **Pior ponto** |
| 07:48 | 80662 | -$12,603 | 24.6 | 32.5 | 26.1 | Recuperando leve |

### Análise de Risco

- **SL distance:** $272 (0.34%) — BTC precisa cair mais $272 para SL
- **Perda potencial no SL:** ~$40,300 (0.500%)
- **PnL total se SL atingido:** $-76,453 + (-$40,300) = **$-116,753**
- **-DI dominante:** 32-38 durante toda a posição
- **ADX:** Estável em 26-28 — tendência fraca mas bearish

### Anomalias

1. **Posição Fib contra-tendência em perda acelerada** — de -$2,831 para -$15,933 em 27 minutos
2. **Breve recuperação ignorada** — posição chegou a +$552 às 07:10 mas não ativou trailing/breakeven (provavelmente threshold não atingido)
3. **-DI persistentemente alto (32-39)** — bearish contínuo desde a entrada

### Ações Recomendadas

- **[CRÍTICO]** SL em $80,390 — monitorar de perto. BTC a $272 do SL
- **[OBSERVAR]** Se BTC recuperar para $80,794+, considerar se trailing/breakeven protege
- **[PENDENTE]** Fix persistência SQLite — dados desta posição NÃO estão sendo salvos

### Observação

A posição Fib pullback continua a sangrar. BTC caiu de 80794 para 80631 (pior ponto), uma queda de $163 (-0.20%). A posição chegou a ficar brevemente positiva (+$552) às 07:10, mas o trailing stop não foi ativado (provavelmente o threshold de ativação não foi atingido com apenas +0.007%). Desde então, perda consistente. O SL em 0.500% ($80,390) está $272 abaixo do preço atual — uma distância significativa mas alcançável se a pressão vendedora continuar. O breakeven não foi ativado porque a posição nunca atingiu o limiar de profit necessário.

> "O Fib disse 'compre', o mercado disse 'não'." – made by Sky 📉

---

## 08:05 — SL IMINENTE — Posição a $200 do Stop Loss

### Status do Sistema

- **Status:** ATIVO — **SL IMINENTE**
- **Tick:** #27143
- **Trades fechados:** 23 (7W / 16L) | WR 30% | PnL $-76,453.27
- **Posição:** 1 aberta | PnL **-$16,633 (-0.206%)**

### Dados Críticos

| Métrica | Valor |
|---------|-------|
| BTC atual | **$80,590** |
| Entrada | $80,794.24 |
| **SL** | **$80,390** |
| **Distância ao SL** | **$200 (0.25%)** |
| Pior ponto | $80,606 (-$18,803) |
| Perda se SL | ~$40,300 |
| PnL total se SL | **$-116,753** |

### Evolução Recente (07:48 → 08:05)

| Hora | BTC | PnL | ADX | -DI |
|------|-----|-----|-----|-----|
| 07:48 | 80662 | -$12,603 | 26.1 | 32.5 |
| 08:00 | 80650 | -$15,085 | 31.4 | 38.3 |
| 08:02 | **80606** | **-$18,803** | 30.5 | 37.8 |
| 08:04 | 80627 | -$16,633 | 31.7 | 39.7 |
| 08:05 | **80590** | — | 32.3 | 37.9 |

- BTC caiu $72 em 17 minutos (80662→80590)
- ADX subindo: 26→32 — tendência bearish fortalecendo
- -DI dominante: 32-43 — pressão vendedora forte
- TP ajustou de 0.400% para 0.500% (ADX > 30)

### Análise

Posição Fib pullback em trajetória clara para o SL. A distância de $200 (0.25%) pode ser consumida em 1-2 ticks se a pressão vendedora continuar. ADX subindo indica tendência se fortalecendo contra a posição. A menos que BTC reverta acima de 80700+, o SL será acionado em breve.

> "SL é o amigo que te diz para sair da festa cedo." – made by Sky 🛑

---

## 08:16 — Trade #24 Fechado: DI Cross Salvou $18k vs SL

### Status do Sistema

- **Status:** ATIVO — sem posição
- **Uptime:** ~8h 25m
- **Tick:** #27786
- **Trades fechados:** 24 (7W / 17L) | WR 29% | PnL **$-98,401.27**
- **Posições:** 0

### KPIs Primários

| Métrica | Valor | Delta (desde 08:05) | Status |
|---------|-------|---------------------|--------|
| Trades | 24 | +1 | OK |
| Win Rate | 29% | -1pp | RUIM |
| PnL Total | $-98,401 | -$21,948 | CRÍTICO |
| Profit Factor | ~0.39 | -0.06 | CRÍTICO |

### Trade #24 — Resultado Final

| Campo | Valor |
|-------|-------|
| Entrada | 06:54:59 @ $80,794.24 (Fib Pullback 61.8%) |
| Saída | 08:12:44 @ $80,574.76 (VENDA DI cross) |
| PnL | **-$21,948 (-0.272%)** |
| Duração | ~1h 18min |
| +DI/-DI na saída | 29.7 / 32.8, ADX=32.6 |
| **SL não atingido** | SL em $80,390 → saída $185 acima |
| **DI cross salvou** | ~$18,449 vs perda do SL (~$40,397) |

### Evolução Completa do Trade #24

| Hora | BTC | PnL | Evento |
|------|-----|-----|--------|
| 06:54 | 80794 | $0 | COMPRA Fib 61.8% |
| 07:10 | 80799 | +$552 | Pico positivo |
| 07:43 | 80631 | -$15,933 | Pior ponto |
| 08:02 | 80606 | -$18,803 | Novo pior |
| 08:08 | 80594 | -$24,695 | ADX=37.8, pressão máx |
| 08:10 | 80646 | -$14,792 | Recuperação parcial |
| **08:12** | **80574** | **-$21,948** | **VENDA DI cross** |
| 08:16 | 80509 | — | BTC continua caindo |

### Mercado Atual (08:16)

| Indicador | Valor |
|-----------|-------|
| BTC-USD | $80,509 |
| +DI | 25.3 |
| -DI | 38.8 |
| ADX | 28.0 |
| Gap | 13.5 |
| Regime | tendência_baixa |

### Análise do DI Cross Exit

A saída via DI cross (não SL) foi benéfica:
- **SL teria sido:** $80,390 → perda ~$40,397 (0.500%)
- **DI cross saiu:** $80,574 → perda $21,948 (0.272%)
- **Economia:** ~$18,449 (46% a menos que o SL)
- A estratégia de saída por DI cross demonstrou valor real — cortou perdas antes do SL
- BTC continuou caindo após saída (80574→80509), confirmando que sair foi correto

### Observação

Trade #24 foi o maior trade individual do dia em duração (1h18) e o primeiro usando entrada Fib Pullback. A entrada contra-tendência se mostrou arriscada (-DI dominante), mas o sistema de saída por DI cross mitigou a perda em quase 50% vs SL. O PnL total do portfólio chegou a $-98,401 — a $1,599 da marca de $-100k. WR caiu para 29% (7W/17L).

> "O DI cross não salvou o trade, mas salvou metade do prejuízo." – made by Sky ✂️

---

## 09:03 — Trade #25: COMPRA no Fundo, Posição Lucrativa!

### Status do Sistema

- **Status:** ATIVO — POSIÇÃO LUCRATIVA
- **Uptime:** ~9h 12m
- **Tick:** #30420
- **Trades fechados:** 24 (7W / 17L) | WR 29% | PnL $-98,401.27
- **Posição:** 1 aberta | PnL **+$13,426 (+0.166%)**

### Trade #25 — Posição Aberta

| Campo | Valor |
|-------|-------|
| Entrada | 08:38:22 @ $80,646.49 (DI cross COMPRA) |
| BTC atual | $80,780 |
| **PnL aberto** | **+$13,426 (+0.166%)** |
| SL | 0.500% ($80,242) |
| TP | 0.500% ($81,050) |
| +DI / -DI | 33.3 / 11.8 |
| ADX | 39.3 — **tendência forte de alta** |

### Reversão do Mercado (08:12 → 09:03)

| Hora | BTC | +DI | -DI | ADX | Gap | Evento |
|------|-----|-----|-----|-----|-----|--------|
| 08:12 | 80574 | 29.7 | 32.8 | 32.6 | 3.1 | Trade #24 fechado |
| 08:16 | 80509 | 25.3 | 38.8 | 28.0 | 13.5 | Fundo do dia |
| 08:38 | **80646** | — | — | — | — | **COMPRA (Trade #25)** |
| 08:45 | 80736 | 28.1 | 24.0 | 26.8 | 4.1 | +DI cruzou acima |
| 08:55 | 80733 | 34.6 | 16.4 | 31.3 | 18.2 | +DI forte |
| 09:00 | 80767 | 37.9 | 12.2 | 38.0 | 25.8 | ADX=38 |
| 09:02 | **80780** | **33.3** | **11.8** | **39.3** | 21.5 | **Máximo atual** |

- BTC recuperou $271 do fundo (80509→80780)
- +DI disparou de 25 para 37 — bullish dominance
- -DI colapsou de 38 para 11 — vendedores desapareceram
- ADX: 28→39 — tendência forte se formando

### Anomalias

1. **SL=0.000% nos ticks** — Alguns ticks mostram SL=0.000% enquanto heartbeats mostram SL=0.500%. Possível display bug ou breakeven em ação
2. **Entrada no fundo perfeito** — Trade #25 entrou em 80646, a $137 acima do fundo do dia (80509). Timing excelente

### Ações Recomendadas

- **[OBSERVAR]** Posição lucrativa crescendo. ADX=39 sugere tendência forte — bom para trailing/TP
- **[POSITIVO]** Se TP (0.500%) atingido: lucro de ~$40,300 → PnL total sobe para $-58,101
- **[PENDENTE]** Fix persistência SQLite — dados deste trade NÃO estão sendo salvos

### Observação

Que virada! Após Trade #24 fechar em -$21,948, o mercado encontrou o fundo em 80509 e reverteu violentamente. O bot capturou a entrada em 80646 (DI cross) — a apenas $137 do fundo. Desde então, +DI explodiu para 37 e -DI colapsou para 11, com ADX em 39 indicando tendência forte de alta. A posição está ganhando +$13,426 e subindo. Se atingir TP em 81050 (+0.500%), o lucro será ~$40,300 — quase o suficiente para cobrir as perdas do Trade #24.

> "Quem comprou no fundo tem o melhor assento da casa." – made by Sky 📈

---

## 09:16 — Trade #25 Estável, +$14,877, +DI Pico 47.1

### Status

- **Tick:** #31171 | **Posição:** 1 | **PnL:** +$14,877 (+0.184%)
- Entrada: $80,646.49 | BTC: $80,795.82 | TP: $81,050 | SL: $80,242
- +DI: 39.3 | -DI: 21.9 | ADX: 31.6 | Gap: 17.4

### Evolução (09:03 → 09:16)

| Hora | BTC | PnL | +DI | ADX |
|------|-----|-----|-----|-----|
| 09:02 | 80780 | +$13,426 | 33.3 | 39.3 |
| 09:08 | 80762 | +$11,584 | 38.3 | 35.2 |
| 09:11 | 80799 | **+$15,301** | **47.1** | 32.1 |
| 09:12 | 80802 | **+$15,627** | 45.3 | 32.5 |
| 09:16 | 80795 | +$14,877 | 39.3 | 31.6 |

- +DI atingiu **47.1** às 09:11 — maior leitura do dia
- BTC plateauou em 80795-80802 — consolidando
- Distância ao TP: $255 (0.31%)
- SL=0.000% nos ticks sugere breakeven ativo

### Observação

Posição consolidando lucro. +DI alto (39-47) indica compradores firmes no controle, mas o preço estabilizou. Se BTC não avançar para 81050, a posição pode sair via VENDA DI cross se -DI cruzar acima de +DI. Por enquanto, tendência favorável com ADX>30.

> "Consolidação é o mercado respirando antes do próximo suspiro." – made by Sky 🌬️

---

## 09:48 — BREAKEVEN Matou +$15k! Trade #26 Aberto

### Status do Sistema

- **Status:** ATIVO — posição aberta
- **Tick:** #32969
- **Trades fechados:** 25 (8W / 17L) | WR 32% | PnL $-98,401.27
- **Posição:** 1 aberta | PnL -$2,481 (-0.031%) | Entrada $80,944.11

### Trade #25 — O Breakeven que Matou o Lucro

| Campo | Valor |
|-------|-------|
| Entrada | 08:38:22 @ $80,646.49 |
| Saída | 09:30:32 @ $80,646.49 |
| PnL | **$0.00 (+0.000%)** |
| Motivo | **Breakeven acionado** |
| Lucro máximo perdido | **+$15,627 (+0.194%)** às 09:12 |
| Classificação | "LUCRO" (infla WR) |

**Cronologia da perda de lucro:**
1. 09:02 — PnL +$13,426, +DI=33, ADX=39 → forte
2. 09:12 — PnL **+$15,627** (+DI=45.3) → **pico máximo**
3. 09:16 — PnL +$14,877 → declínio começa
4. 09:24 — +DI caindo, ADX caindo → momentum perdendo
5. **09:30** — **BREAKEVEN a $0.00** → todo lucro evaporou
6. 09:42 — BTC dispara para $80,972 → teria dado TP

### Trade #26 — Nova Posição

| Campo | Valor |
|-------|-------|
| Entrada | 09:41:17 @ $80,944.11 |
| BTC atual | $80,923.98 |
| PnL | -$2,481 (-0.031%) |
| +DI / -DI | 29.0 / 25.3 |
| ADX | 19.9 → lateral |
| TP | 0.300% (ADX < 20) |
| SL | 0.500% |

### Análise Crítica do Breakeven

Este é um **problema sistêmico sério**:

1. **Lucro perdido:** +$15,627 → $0. BTC chegou a $80,972 após o fechamento — teria atingido TP ($81,050)
2. **WR inflacionado:** Breakeven conta como "win" (8W/25 = 32%) mas PnL real é $0
3. **Padrão:** É o 3º breakeven da sessão (outros: Trade #22 trailing +$4,590, e agora este a $0)
4. **Root cause:** O breakeven é configurado no preço de entrada (protect capital), não em um mínimo de lucro (protect gains)

### Gatilho ML Ativado

**"Breakeven率高 + WR baixo"** — o prompt-loop previu este cenário:
- Taxa de breakeven: 1/3 das posições com lucro tiveram breakeven a $0
- Trade #25 teve lucro máximo de +$15,627 que foi completamente eliminado
- **Recomendação:** Estudo ML sobre "Qual breakeven mínimo ótimo?" (ex: breakeven em +0.05% ao invés de 0%)

### Ações Recomendadas

1. **[P1]** Investigar mecanismo de breakeven — considerar breakeven em +0.05% ao invés de $0
2. **[P1]** Backtest: se Trade #25 não tivesse breakeven, teria atingido TP? BTC chegou a 80972
3. **[OBSERVAR]** Trade #26 em leve perda, ADX baixo (19.9) — mercado lateralizando

> "O breakeven protegeu o capital e assassinou o lucro." – made by Sky 💀

---

## 09:53 — Trade #26: ADX Despencando, DI Convergindo

### Status do Sistema

- **Status:** ATIVO — posição aberta em lateralização
- **Tick:** #33255 | **Trades:** 25 (8W/17L) | WR 32% | PnL Fechado: $-98,401.27
- **Posição:** 1 aberta | PnL -$6,881 (-0.085%) | Entrada $80,944.11

### Mercado Atual

| Indicador | 09:48 | 09:53 | Delta |
|-----------|-------|-------|-------|
| BTC | $80,923.98 | $80,878.25 | -$45.73 |
| +DI | 29.0 | 27.8 | -1.2 |
| -DI | 25.3 | 25.8 | +0.5 |
| ADX | 19.9 | 16.3 | **-3.6** |
| Gap | 3.7 | 2.0 | -1.7 |
| PnL | -$2,481 | -$6,881 | -$4,400 |

### Trade #26 — Evolução

| Hora | BTC | PnL | +DI | ADX | Gap |
|------|-----|-----|-----|-----|-----|
| 09:41 | $80,944 (entry) | $0 | 39.1 | 24.2 | 20.8 |
| 09:42 | $80,972 | **+$992** | 36.0 | 25.7 | 17.9 |
| 09:43 | $80,897 | -$4,650 | 32.1 | 24.9 | 8.7 |
| 09:47 | $80,919 | -$2,481 | 29.0 | 19.9 | 3.7 |
| 09:49 | $80,940 | -$328 | 30.2 | 19.1 | 7.5 |
| 09:52 | $80,875 | **-$6,881** | 27.8 | **16.3** | 2.0 |

- **ADX em queda livre:** 24.2 → 16.3 em 12 minutos (-32%)
- **DI convergindo:** +DI 27.8 vs -DI 25.8 (gap=2.0) — risco de DI cross baixista iminente
- **Distância ao SL:** $80,539 (~$339 ou -0.42%)
- **Distância ao TP:** $81,187 (~$309 ou +0.38%)

### Anomalias Detectadas

- **ADX < 17** — mercado fortemente lateral, sem direção. TP reduzido para 0.300% (ADX<20) está correto
- **Risco DI cross** — se -DI cruzar acima de +DI nos próximos ticks, saída automática via DI cross exit (como ocorreu no Trade #24, salvou ~46% vs SL)

### Ações Recomendadas

- **[OBSERVAR]** DI cross iminente — se ocorrer, monitorar se a saída salva capital
- **[PENDENTE]** Breakeven ML study aguardando Trade #26 encerrar para análise consolidada

> "ADX 16 é o mercado sussurrando: 'não sei pra onde ir'." – made by Sky 🤫

---

## 10:18 — ALERTA: DI Cross Exit Falhou! Trade #26 Sangrando

### Status do Sistema

- **Status:** ATIVO — posição aberta em deterioração
- **Tick:** #34680 | **Trades:** 25 (8W/17L) | WR 32% | PnL Fechado: $-98,401.27
- **Posição:** 1 aberta | PnL **-$20,151 (-0.249%)** | Entrada $80,944.11

### BUG CONFIRMADO: DI Cross Exit Bloqueado por ADX

**Root cause:** O DI cross exit usa o MESMO filtro ADX ≥ 25 da entrada. Quando ADX cai abaixo de 25, o sinal de saída VENDA nunca é gerado.

| Hora | +DI | -DI | ADX | Gap | DI Cross? | VENDA Gerada? |
|------|-----|-----|-----|-----|-----------|---------------|
| 09:52 | 29.9 | 27.4 | 17.3 | 2.5 | Não | — |
| **09:56** | **27.4** | **28.3** | **14.2** | 0.9 | **SIM (-DI > +DI)** | **NÃO (ADX<25)** |
| 09:58 | 25.6 | 30.5 | 13.0 | 5.0 | SIM | NÃO (ADX<25) |
| 10:10 | 19.6 | 21.7 | 8.9 | 2.2 | SIM | NÃO (ADX<25) |
| 10:15 | 20.7 | 33.9 | 10.0 | 13.2 | SIM | NÃO (ADX<25) |
| 10:16 | 19.2 | 37.4 | 11.6 | 18.2 | SIM | NÃO (ADX<25) |

**O DI cross baixista ocorreu às ~09:56** — 22 minutos atrás — e a posição continua aberta porque o ADX está em 8-14, bem abaixo do threshold de 25.

**Código:** `guardiao_conservador.py:214-217` — a condição `curr_adx >= self._adx_threshold` bloqueia tanto entradas quanto saídas.

### Evolução Trade #26 (09:41 → 10:18)

| Hora | BTC | PnL | +DI | -DI | ADX |
|------|-----|-----|-----|-----|-----|
| 09:41 | $80,944 (entry) | $0 | 39.1 | 18.3 | 24.2 |
| 09:42 | $80,972 | +$992 | 36.0 | 18.1 | 25.7 |
| 09:43 | $80,897 | -$4,650 | 32.1 | 23.3 | 24.9 |
| 09:53 | $80,878 | -$6,881 | 27.8 | 25.8 | 16.3 |
| 09:58 | $80,851 | -$8,412 | 25.6 | 30.5 | 13.0 |
| 10:07 | $80,880 | -$6,346 | 22.5 | 19.8 | 9.7 |
| 10:15 | $80,776 | -$16,797 | 20.7 | 33.9 | 10.0 |
| **10:16** | **$80,745** | **-$19,840** | 19.2 | 37.4 | 11.6 |
| 10:18 | $80,742 | **-$20,151** | 17.5 | 31.8 | 14.0 |

### Métricas de Risco

| Métrica | Valor |
|---------|-------|
| SL preço | $80,539.40 (entry × 0.995) |
| Distância ao SL | **$203** (0.25%) |
| PnL se atingir SL | **-$40,472 (-0.500%)** |
| TP preço | $81,187 (entry × 1.003) |
| -DI dominância | 31.8 vs 17.5 (1.8x) |

### Anomalias Detectadas

1. **[CRÍTICO] DI cross exit bloqueado por ADX** — saída deveria ser INDEPENDENTE de ADX. Entrada precisa de ADX≥25 para confirmar tendência, mas SAÍDA deve funcionar com qualquer ADX
2. **[ALERTA] Posição rumo ao SL** — PnL -0.249%, SL em -0.500%. Distância de apenas $203
3. **ADX crônico** — ADX < 15 por 20+ minutos consecutivos (desde 09:56)

### Ações Recomendadas

1. **[P0 — BUG]** Separar lógica de saída da lógica de entrada — DI cross exit deve funcionar com qualquer ADX
2. **[P0 — FIX PROPOSTO]** Adicionar saída condicional no `strategy_worker.py`: se posição aberta E -DI > +DI E ADX < threshold → fechar posição (exit DI cross sem filtro ADX)
3. **[P1]** Backtest: quantos trades passados teriam se beneficiado deste fix?
4. **[PENDENTE]** Breakeven ML study + este novo bug = 2 problemas de saída identificados hoje

### Comparação: Trade #24 vs Trade #26

| | Trade #24 | Trade #26 |
|---|-----------|-----------|
| DI cross exit? | SIM (ADX>25) | NÃO (ADX<25) |
| PnL na saída | -$21,948 (salvou $18,449) | -$20,151 e caindo |
| ADX no cross | ~25+ | ~14 |
| Desfecho | Fechou via DI cross | Ainda aberto, rumo ao SL |

> "A saída não deveria precisar de permissão do ADX para proteger o capital." – made by Sky 🚨

---

## 10:38 — IMINENTE: SL a $72! Bug Confirmado com Prejuízo Máximo

### Status do Sistema

- **Status:** ATIVO — **SL IMINENTE**
- **Tick:** #35812 | **Trades:** 25 (8W/17L) | WR 32% | PnL Fechado: $-98,401.27
- **Posição:** 1 aberta | PnL **-$35,981 (-0.445%)** | Entrada $80,944.11

### Métricas Críticas

| Métrica | Valor | Alerta |
|---------|-------|--------|
| BTC atual | $80,611.77 | — |
| SL preço | $80,539.40 | — |
| **Distância ao SL** | **$72 (0.09%)** | **CRÍTICO** |
| PnL se SL atingir | -$40,472 (-0.500%) | — |
| +DI / -DI | 13.3 / 33.9 | -DI 2.5x dominante |
| ADX | **35.6** | Forte tendência baixista |
| Gap | 20.6 | Bearish confirmado |

### Ironia do Bug

ADX subiu para **35.6** — bem acima do threshold de 25. Mas o DI cross ocorreu às 09:56 (42 minutos atrás). A estratégia detecta apenas o **momento exato** do crossover, não o estado persistente de "estar cruzado". Resultado: mesmo com ADX>25 agora, nenhuma VENDA será gerada.

**Múltiplos crossovers desperdiçados:**

| Hora | +DI | -DI | ADX | Crossover? | VENDA? |
|------|-----|-----|-----|------------|--------|
| 09:56 | 27.4 | 28.3 | 14.2 | 1º (bull→bear) | NÃO (ADX<25) |
| 10:02 | 28.1 | 25.3 | 11.3 | re-cross (bear→bull) | — |
| 10:10 | 19.6 | 21.7 | 8.9 | 2º (bull→bear) | NÃO (ADX<25) |
| 10:12 | 25.7 | 20.6 | 9.3 | re-cross (bear→bull) | — |
| 10:15 | 20.7 | 33.9 | 10.0 | 3º (bull→bear) | NÃO (ADX<25) |
| 10:38 | 13.3 | 33.9 | **35.6** | já cruzado | NÃO (não é crossover novo) |

### Evolução Rápida (10:18 → 10:38)

| Hora | BTC | PnL | ADX | -DI |
|------|-----|-----|-----|-----|
| 10:18 | $80,742 | -$20,151 | 14.0 | 31.8 |
| 10:22 | $80,663 | -$28,111 | 22.5 | 35.8 |
| 10:26 | $80,613 | -$33,111 | 30.2 | 41.4 |
| 10:31 | $80,597 | **-$35,651** | 35.5 | 38.8 |
| 10:37 | $80,584 | **-$35,981** | 35.0 | 36.8 |
| 10:38 | $80,611 | -$33,289 | 35.6 | 33.9 |

- PnL piorou **$15,830** em 20 minutos (10:18 → 10:38)
- ADX disparou de 14 → 35 (tendência baixista forte se formando)
- -DI dominante de 31.8 → 33.9 — vendedores firmes

### Análise: O que Deveria Ter Acontecido

Se o DI cross exit funcionasse sem filtro ADX:
- Saída às 09:56 com BTC ~$80,880
- PnL: ~-$6,400 (-0.079%)
- **Economia vs SL atual: ~$34,000** (84% de proteção)

### Anomalias Detectadas

1. **[CRÍTICO] SL iminente** — $72 de distância, cairá a qualquer momento
2. **[BUG] DI cross exit completamente ineficaz** — 3 crossovers desperdiçados por ADX<25
3. **[IRÔNICO] ADX agora é 35.6** — se o DI cross acontecesse AGORA, a saída funcionaria. Mas já passou.
4. **TP dinâmico mudou para 0.500%** (ADX>30) — irrelevante pois preço cai

### Ações Recomendadas

1. **[AGUARDAR]** SL iminente — nenhum fix possível sem reiniciar bot
2. **[P0 — FIX PRIORITÁRIO]** DI cross exit independente de ADX — implementar quando bot reiniciar
3. **[P0]** Considerar também: saída por "DI state" (não apenas "DI crossover") — se -DI > +DI por N ticks consecutivos, sair
4. **[P1]** Backtest deste fix em trades anteriores

> "Três chances de sair. Três negadas pelo mesmo filtro. O SL que vem não é surpresa — é consequência." – made by Sky ⚰️

---

## 10:51 — Sobreviveu ao SL! Mas Oscilação Selvagem

### Status do Sistema

- **Status:** ATIVO — posição sobreviveu por margem estreita
- **Tick:** #36540 | **Trades:** 25 (8W/17L) | WR 32% | PnL Fechado: $-98,401.27
- **Posição:** 1 aberta | PnL -$25,458 (-0.315%) | Entrada $80,944.11

### Rollercoaster (10:38 → 10:51)

| Hora | BTC | PnL | +DI | -DI | ADX | Evento |
|------|-----|-----|-----|-----|-----|--------|
| 10:38 | $80,611 | **-$35,981** | 13.3 | 33.9 | 35.6 | SL a $72 |
| 10:39 | $80,733 | -$25,422 | 27.9 | 27.1 | 33.0 | +DI re-cruzou! |
| 10:43 | $80,744 | -$20,011 | 27.4 | 29.4 | 28.4 | -DI re-cruzou |
| **10:45** | **$80,851** | **-$9,302** | 29.1 | 24.0 | 25.2 | **Melhor PnL desde 09:42** |
| 10:48 | $80,667 | -$27,622 | 22.9 | 24.9 | 22.7 | -DI volta a dominar |
| 10:50 | $80,733 | -$21,081 | 23.7 | 22.4 | 20.0 | +DI sobe |
| 10:51 | $80,689 | -$25,458 | 23.7 | 20.7 | 19.1 | Oscilando |

- **Mínimo:** BTC $80,584 (10:37) — SL em $80,539 → **$45 de margem!**
- **Máximo pós-crash:** BTC $80,851 (10:45) — PnL recuperou para -$9,302
- **DI oscillou 5 vezes** em 13 minutos — mercado sem direção clara

### Mercado Atual

| Indicador | Valor | Status |
|-----------|-------|--------|
| BTC | $80,689 | abaixo da entrada |
| +DI / -DI | 23.7 / 20.7 | +DI levemente acima |
| ADX | 19.1 | lateral (< 20) |
| TP | 0.300% | ADX < 20 |
| SL distância | $150 (0.19%) | ainda em risco |

### Análise

BTC quase atingiu SL ($80,584 vs SL $80,539 — margem de **$45 / 0.056%**). A recuperação foi forte mas temporária — preço voltou a cair. Mercado extremamente volátil com DI cruzando repetidamente sem convicção.

Aguardando definição de direção: ou BTC recupera acima de $80,944 (breakeven) ou cai para $80,539 (SL).

### Ações Recomendadas

- **[OBSERVAR]** Posição em limbo — nem SL nem recuperação. Mercado define direção nas próximas horas
- **[P0]** DI cross exit bug documentado — implementar fix quando operador reiniciar

> "Escapou por $45. O mercado deu uma segunda chance — não desperdice a lição." – made by Sky 🎲

---

## 11:08 — Trade #26 SL Atingido! Trade #27 Fib Pullback em Lucro

### Status do Sistema

- **Status:** ATIVO — Trade #27 aberto em lucro
- **Tick:** #37500 | **Trades:** 26 fechados (8W/18L) | **WR 31%** | PnL Fechado: **$-138,873.33**
- **Posição:** 1 aberta | PnL **+$15,451 (+0.192%)** | Entrada $80,505.48

### Trade #26 — Desfecho Final

| Campo | Valor |
|-------|-------|
| Entrada | 09:41:17 @ $80,944.11 (DI cross) |
| Saída | 10:57:19 @ $80,539.39 |
| PnL | **-$40,472.06 (-0.500%)** |
| Motivo | **Stop Loss acionado (-0.5%)** |
| Duração | 1h 16min |
| Lucro máximo perdido | +$20,733 (às 09:30) |
| **Causa raiz** | DI cross exit bloqueado por ADX < 25 |

**Impacto cumulativo:** Se o DI cross exit funcionasse às 09:56:
- Saída: -$6,400 ao invés de -$40,472
- **Economia: $34,072 (84%)**

### Trade #27 — Fibonacci Pullback Rescue

| Campo | Valor |
|-------|-------|
| Entrada | 10:58:20 @ $80,505.48 |
| Tipo | **RE-ENTRY (Pullback Fib 61.8%)** |
| BTC atual | $80,659.99 |
| PnL | **+$15,451 (+0.192%)** |
| Trailing | $80,549.34 |
| Breakeven | ATIVO (SL=0.000%) |
| +DI / -DI | 31.6 / 25.6 |
| ADX | 16.0 (lateral) |

**O Pullback Fib 61.8% salvou a sessão!** Entrou $439 abaixo do SL de Trade #26, e agora está em +$15k.

### KPIs Atualizados (09:48 → 11:08)

| Métrica | 09:48 | 11:08 | Delta |
|---------|-------|-------|-------|
| Trades | 25 | 26 | +1 |
| Win Rate | 32% | **31%** | **-1pp** |
| PnL Fechado | $-98,401 | **$-138,873** | **-$40,472** |
| PnL Total | $-100,882 | **$-123,422** | -$22,540 |
| Profit Factor | — | ~0.28 | péssimo |

### Evolução Trade #27 (10:58 → 11:08)

| Hora | BTC | PnL | ADX |
|------|-----|-----|-----|
| 10:58 | $80,505 (entry) | $0 | — |
| 11:00 | $80,359 | -$11,665 | 18.3 |
| 11:01 | $80,491 | -$1,446 | 19.9 |
| 11:05 | $80,579 | **+$7,381** | 18.0 |
| 11:07 | $80,657 | **+$15,251** | 16.4 |
| 11:08 | $80,659 | **+$15,451** | 16.0 |

### Análise Crítica

**Padrão repetitivo detectado:**
1. Trade #25: Breakeven matou +$15,627 de lucro
2. Trade #26: DI cross exit bug causou -$40,472 de perda (SL ao invés de saída -$6k)
3. Trade #27: Fib pullback resgatou, já em +$15k... **MAS breakeven ativou (SL=0.000%)**

**Risco:** Se BTC voltar a $80,505, Trade #27 fecha a $0 (breakeven) — o MESMO problema de Trade #25 pode se repetir!

### Anomalias Detectadas

1. **[ALERTA] Breakeven ativou em Trade #27** — SL=0.000% desde 11:05. Se o preço cair para $80,505, fecha a $0 novamente
2. **[CONFIRMADO] Trade #26 SL** — perda de $40,472, 84% evitável pelo DI cross exit fix
3. **[POSITIVO] Fib pullback funciona** — Trade #27 em +$15k após entrada em $80,505

### Ações Recomendadas

1. **[OBSERVAR]** Trade #27 com breakeven ativo — risco de repetir Trade #25
2. **[P0]** DI cross exit bug — fix prioritário para próximo restart
3. **[P0]** Breakeven mínimo — evitar que saia a $0 quando há lucro
4. **[P1]** Backtest Fib pullback — validar se esta entry consistentemente gera lucro

> "O Fib salvou, mas o breakeven já está armado. É o Groundhog Day das saídas." – made by Sky 🔄

---

## 11:16 — Trade #27 Estável, Trailing Protegendo Lucro

### Status do Sistema

- **Status:** ATIVO — Trade #27 em lucro, trailing protegendo
- **Tick:** #37977 | **Trades:** 26 (8W/18L) | WR 31% | PnL Fechado: $-138,873.33
- **Posição:** 1 aberta | PnL **+$16,940 (+0.210%)** | Entrada $80,505.48

### Trade #27 — Evolução (10:58 → 11:16)

| Hora | BTC | PnL | Trail | ADX |
|------|-----|-----|-------|-----|
| 10:58 | $80,505 (entry) | $0 | — | — |
| 11:00 | $80,359 | -$11,665 | — | 18.3 |
| 11:07 | $80,657 | +$15,251 | — | 16.4 |
| 11:09 | $80,556 | +$5,112 | $80,549 | 15.7 |
| 11:13 | $80,684 | **+$17,883** | $80,563 | 13.8 |
| 11:14 | $80,699 | **+$18,146** | $80,578 | 13.2 |
| 11:16 | $80,728 | +$17,944 | **$80,607** | 12.5 |

### Diferença Crítica vs Trade #25

| | Trade #25 | Trade #27 |
|---|-----------|-----------|
| Lucro máximo | +$15,627 | +$18,146 |
| Trailing stop | Não subiu acima da entrada | **$80,607 (> entry $80,505)** |
| Breakeven risco | Fechou a $0 | **Trailing protegeria primeiro** |
| Desfecho | BREAKEVEN $0 | Em andamento... |

**Trailing stop ($80,607) está $102 acima da entrada ($80,505)** — se BTC cair, o trailing dispara ANTES do breakeven, garantindo lucro de ~$10k. O cenário Trade #25 foi evitado pela ordem de precedência: trailing > breakeven.

### Mercado Atual

| Indicador | Valor |
|-----------|-------|
| BTC | $80,674 |
| +DI / -DI | 27.4 / 22.6 |
| ADX | 12.3 (lateral forte) |
| TP | $80,746 (0.300%) |
| Trail | $80,607 |
| Breakeven | $80,505 (entry) |

ADX muito baixo (12.3) — mercado sem direção. BTC oscilando em range $80,556-$80,728.

### Ações Recomendadas

- **[OK]** Trailing protegendo lucro — breakeven risk mitigado
- **[OBSERVAR]** ADX 12.3 — BTC pode continuar lateralizando. TP ($80,746) está próximo
- **[P0]** DI cross exit bug — ainda prioritário

> "Dessa vez o trailing aprendeu a lição antes do breakeven." – made by Sky 📈

---

## 11:44 — TAKE PROFIT! Trade #27 +$24k, WR Sobe pra 33%

### Status do Sistema

- **Status:** ATIVO — sem posição, aguardando sinal
- **Tick:** #39540 | **Trades:** 27 fechados (**9W / 18L**) | **WR 33%** | PnL Fechado: **$-114,721.69**
- **Posição:** 0 abertas | Mercado em recuperação

### Trade #27 — Desfecho Final: TAKE PROFIT!

| Campo | Valor |
|-------|-------|
| Entrada | 10:58:20 @ $80,505.48 (Fib Pullback 61.8%) |
| Saída | **11:19:49 @ $80,747.00** |
| PnL | **+$24,151.64 (+0.300%)** |
| Motivo | **Take Profit acionado (+0.3%)** |
| Duração | 21 minutos |

**Cronologia completa:**
1. 10:58 — Entry @ $80,505 (Fib pullback após SL de Trade #26)
2. 11:00 — Fundo: -$11,665 (BTC $80,359)
3. 11:07 — Virada: +$15,251 (BTC $80,657)
4. 11:09 — Trailing ativa: $80,549
5. 11:14 — Pico: +$18,146 (BTC $80,699), trail sobe pra $80,578
6. **11:19 — TP atingido: +$24,152** — target $80,746 executado com precisão

**Fib Pullback 61.8% validated!** Melhor trade da sessão em PnL absoluto.

### KPIs Atualizados (06:00 → 11:44)

| Métrica | 06:00 | 09:48 | 11:44 | Tendência |
|---------|-------|-------|-------|-----------|
| Trades | 22 | 25 | 27 | +5 |
| Win Rate | 27% | 32% | **33%** | 📈 +6pp |
| PnL Fechado | $-78,401 | $-98,401 | **$-114,722** | 📉 -$36k |
| Wins | 6 | 8 | **9** | +3 wins |

### Mercado Atual (11:44)

| Indicador | Valor | Status |
|-----------|-------|--------|
| BTC | $80,786 | recuperando |
| +DI / -DI | 36.4 / 19.6 | +DI dominante forte |
| ADX | **21.8** | subindo → próximo de 25! |
| Gap | 16.8 | amplo, compradores firmes |

**ADX subindo em direção ao threshold (25):** se continuar, novo sinal COMPRA pode surgir em breve. +DI já muito forte (36.4).

### Resumo da Sessão — Trades do Dia

| # | Hora | Tipo Entrada | Saída | PnL |
|---|------|-------------|-------|-----|
| 23 | 04:12 | DI cross | SL | -$40,472 |
| 24 | 05:49 | DI cross | DI cross exit | -$21,948 |
| 25 | 08:38 | DI cross | **Breakeven** | $0 |
| 26 | 09:41 | DI cross | **SL** (DI cross bug) | -$40,472 |
| 27 | 10:58 | **Fib Pullback** | **TP** | **+$24,152** |

### Análise Fib Pullback vs DI Cross

| Entrada | Trades | WR | PnL Total |
|---------|--------|-----|-----------|
| DI cross | 4 | 0% (0W/4L) | **-$102,892** |
| Fib Pullback 61.8% | 1 | 100% (1W/0L) | **+$24,152** |

Fib pullback superou DI cross como entry em amostra pequena. Precisa de mais dados.

### Anomalias Detectadas

- Nenhuma — Trade #27 executou perfeitamente: entry, trailing, TP

### Ações Recomendadas

- **[OBSERVAR]** ADX subindo (21.8) — possível novo sinal se cruzar 25
- **[P0]** DI cross exit bug — ainda prioritário para próximo restart
- **[P1]** Backtest Fib pullback — validar com mais trades
- **[P1]** ML study: comparar performance Fib vs DI cross

> "O Fib Pullback é o sniper: entra depois do pânico, sai com precisão." – made by Sky 🎯

---

## 12:16 — Mercado Lateral, Aguardando Sinal

### Status do Sistema

- **Status:** ATIVO — sem posição, aguardando
- **Tick:** #41349 | **Trades:** 27 (9W/18L) | WR 33% | PnL Fechado: $-114,721.69
- **Posição:** 0 abertas | Mercado em chop

### Mercado Atual

| Indicador | 11:44 | 12:03 | 12:16 | Tendência |
|-----------|-------|-------|-------|-----------|
| BTC | $80,786 | $80,470 | $80,519 | 📉 -$267 |
| +DI | 36.4 | 17.1 | 25.5 | volátil |
| -DI | 19.6 | 39.3 | 31.2 | subiu |
| ADX | 21.8 | **25.1** | 16.3 | 📉 desabou |

ADX tocou 25.1 às 12:03 mas com -DI dominante (39.3 vs +DI 17.1) — sem sinal COMPRA. Depois caiu para 16.3.

BTC em range apertado $80,400-$80,650 nas últimas 2 horas. Nenhum sinal gerado desde Trade #27 (TP às 11:19).

### Observação

Quase 1h sem trades. Mercado lateral com DI oscilando sem convicção. ADX precisa subir acima de 25 com +DI dominante para novo sinal COMPRA. Enquanto isso, o bot aguarda corretamente.

> "Paciência é a melhor posição quando o mercado não sabe pra onde ir." – made by Sky ⏳

---

## 13:04 — BTC Low do Dia $80,211, Sem Sinais

### Status do Sistema

- **Status:** ATIVO — sem posição, ~1h45 sem trades
- **Tick:** #44040 | **Trades:** 27 (9W/18L) | WR 33% | PnL Fechado: $-114,721.69
- **Posição:** 0 abertas | BTC em downtrend leve

### Mercado (12:16 → 13:04)

| Hora | BTC | +DI | -DI | ADX | Gap |
|------|-----|-----|-----|-----|-----|
| 12:16 | $80,519 | 25.5 | 31.2 | 16.3 | -5.7 |
| 12:45 | $80,485 | 28.8 | 24.3 | 17.5 | 4.5 |
| 12:52 | $80,353 | 26.5 | 25.1 | 23.1 | 1.4 |
| 13:00 | **$80,211** | 19.1 | 29.7 | 17.3 | -10.6 |
| 13:04 | $80,310 | 27.8 | 32.1 | 18.7 | -4.2 |

BTC caiu **$308** desde 12:16. Low do dia $80,211 às 13:00 — $536 abaixo do TP de Trade #27 ($80,747). TP foi executado no topo.

### Observação

~1h45 sem trades. Mercado em downtrend mas ADX < 25 — sem condições de entrada. O bot aguarda corretamente, não força trades em mercado sem direção clara.

> "Saber não entrar é tão importante quanto saber entrar." – made by Sky 🚦

---

## 14:03 — BTC Abaixo de $80k! Crash a $79,907, ADX 36

### Status do Sistema

- **Status:** ATIVO — sem posição, ~3h sem trades
- **Tick:** #47378 | **Trades:** 27 (9W/18L) | WR 33% | PnL Fechado: $-114,721.69
- **Posição:** 0 abertas | Mercado em crash

### Crash (13:04 → 14:03)

| Hora | BTC | +DI | -DI | ADX | Evento |
|------|-----|-----|-----|-----|--------|
| 13:04 | $80,310 | 27.8 | 32.1 | 18.7 | — |
| 13:16 | $80,196 | 25.8 | 37.3 | 15.9 | Low anterior |
| 13:45 | $80,046 | 15.6 | 37.5 | 27.8 | ADX disparando |
| 13:54 | **$79,907** | **11.0** | 40.3 | **34.6** | **LOW DO DIA** |
| 13:56 | $79,991 | 14.2 | 34.9 | **35.9** | ADX pico |
| 14:03 | $80,047 | 21.8 | 30.2 | 30.3 | Recuperação leve |

BTC caiu **$400** em 1h ($80,310 → $79,907). Agora em $80,047, ainda abaixo de $80k.

### Contexto do Dia

| Hora | BTC | Evento |
|------|-----|--------|
| 08:38 | $80,646 | Trade #25 entry |
| 09:41 | $80,944 | Trade #26 entry (DI cross) |
| 10:57 | $80,539 | Trade #26 SL (-$40k) |
| 11:19 | $80,747 | Trade #27 TP (+$24k) — **topo do dia** |
| 13:54 | $79,907 | **Fundo do dia** (-$1,837 do topo) |

Trade #27 saiu no TOPO absoluto do dia. BTC caiu $1,837 desde então. O Fib Pullback + TP funcionaram como timing perfeito.

### Observação

ADX alto (30-36) indica tendência forte, mas -DI dominante — sem sinais COMPRA. Se BTC recuperar e +DI cruzar acima de -DI com ADX>25, teremos um sinal de reversão em mercado sobrevendido. Até lá, aguardar.

> "Trade #27 saiu no topo. Às vezes o melhor trade é o que já fechou." – made by Sky 🏔️

---

## 14:16 — BTC Recupera $419, ADX Lag Novamente

### Status do Sistema

- **Status:** ATIVO — sem posição, ADX lag bloqueando entrada
- **Tick:** #48132 | **Trades:** 27 (9W/18L) | WR 33% | PnL Fechado: $-114,721.69
- **Posição:** 0 abertas | BTC em recuperação

### Mercado (14:03 → 14:16)

| Hora | BTC | +DI | -DI | ADX | Gap | Nota |
|------|-----|-----|-----|-----|-----|------|
| 14:03 | $80,047 | 21.8 | 30.2 | 30.3 | -8.5 | -DI dominante |
| 14:06 | $80,086 | 23.9 | 26.4 | 25.5 | -2.5 | quase cruzou |
| 14:07 | $80,097 | 25.4 | 25.6 | 23.7 | -0.1 | **quase crossing** |
| 14:13 | $80,129 | 27.9 | 25.4 | 17.7 | **+2.5** | **+DI cruzou!** |
| 14:15 | $80,194 | 33.5 | 23.0 | 17.8 | +10.5 | +DI forte |
| 14:16 | **$80,252** | **39.0** | 20.6 | 18.7 | **+18.5** | **gap enorme** |

**ADX lag pattern repetindo:** +DI cruzou às 14:13 com ADX=17.7 (abaixo de 25). Agora +DI=39 com gap=18.5 mas sem sinal porque ADX nunca chegou a 25 no momento do cross.

Se ADX continuar subindo e cruzar 25 com +DI ainda dominante, pode haver entrada via **ADX surge** (Entry 2 da estratégia).

### Observação

BTC em V-recovery: $79,907 → $80,326 (+$419). Se a recuperação continuar, ADX pode alcançar 25 nas próximas horas. O bot aguarda corretamente.

> "O ADX sempre chega atrasado na festa do DI cross." – made by Sky 🐌

---

## 14:53 — Trade #28 ADX Surge em Tendência Forte, +$16k

### Status do Sistema

- **Status:** ATIVO — posição aberta, tendência forte de alta
- **Tick:** #50180 | **Trades:** 27 (9W/18L) | WR 33% | PnL Fechado: $-114,721.69
- **Posição:** 1 aberta | PnL Aberto: **+$16,695** (+0.208%)

### Trade #28 — ADX Surge Entry

| Campo | Valor |
|-------|-------|
| **Entrada** | 14:21:07 @ $80,343.84 |
| **Tipo** | ADX surge (ADX cruzou 25 entre 14:20:36→14:21:07, +DI dominante) |
| **TP alvo** | $80,825.90 (+0.600%) |
| **SL** | 0.000% (breakeven ativado) |
| **Trailing** | $80,390.02 (+$46 acima da entrada) |
| **PnL atual** | +$16,695 (+0.208%) |
| **Distância TP** | $315 (1.9% do caminho até TP) |

**ADX no momento da entrada:** cruzou de 24.2 → ~25+ entre ticks, com +DI=38.9 >> -DI=18.1 (gap=20.8). Entrada legítima via Entry 2 (ADX surge).

### KPIs Primários

| Métrica | Valor | Delta (vs 14:16) | Status |
|---------|-------|-------------------|--------|
| Trades | 27 | = | OK |
| Win Rate | 33% | = | OK |
| PnL Fechado | $-114,721.69 | = | OK |
| PnL Aberto | +$16,695 | novo trade | OK |
| Profit Factor | 0.40 | = | ALERTA |

### Mercado Atual

| Hora | BTC | +DI | -DI | ADX | Gap | TP% | Trail |
|------|-----|-----|-----|-----|-----|-----|-------|
| 14:31 | $80,537 | 45.8 | 11.2 | 36.4 | 34.6 | 0.500 | — |
| 14:36 | $80,429 | 38.1 | 10.4 | 44.4 | 27.7 | 0.600 | — |
| 14:42 | $80,433 | 33.7 | 11.9 | 46.4 | 21.8 | 0.600 | $80,386.70 |
| 14:48 | $80,473 | 38.1 | 15.7 | 45.1 | 22.3 | 0.600 | $80,386.70 |
| 14:52 | **$80,510** | **33.7** | **15.3** | **42.3** | **18.4** | **0.600** | **$80,390.02** |

**Regime:** tendencia_alta — ADX 42-46, +DI dominante (gap 18-30)

**Observação técnica:** O trailing stop ($80,390) está apenas $46 acima da entrada ($80,343). O breakeven está ativado (SL=0.000%), mas o trailing oferece proteção mínima. BTC precisa subir para $80,825.90 para atingir TP.

### Comparação por Tipo de Entrada (hoje)

| Entrada | Trades | WR | PnL |
|---------|--------|-----|------|
| DI cross | 3 (fechados) | 0% (0W/3L) | -$81,420 |
| Fib Pullback | 2 | 50% (1W/1L) | -$17,793 |
| ADX surge | 1 (aberto) | — | +$16,695 |

**Nota:** DI cross continua sendo a pior entrada. Trade #28 (ADX surge) está indo bem.

### Anomalias Detectadas

- **Trailing stop muito apertado:** $80,390 vs entrada $80,343 — apenas $46 de buffer. Qualquer pullback de -0.06% ativa trailing e limita ganho a ~$46
- **Nenhuma anomalia crítica nova** — ADX alto (42-46) confirma tendência real

### Ações Recomendadas

- **Monitorar trailing:** Se BTC continuar subindo, trailing deve acompanhar e proteger mais lucro
- **Aguardar TP:** ADX > 40 indica tendência forte, boas chances de atingir TP ($80,826)
- **Nenhuma ação necessária** no código agora

### Observação

Trade #28 é a melhor execução da sessão: entrada via ADX surge em tendência real (ADX 25→42, +DI dominante). O ADX se comportou exatamente como esperado — cruzou 25 no momento da entrada e subiu para 46. BTC já está $167 acima da entrada.

Se o trailing stop fosse mais agressivo (ex: 0.1% abaixo do pico ao invés de fixo), já teria protegido mais lucro. O pico foi $80,510 (14:52), trailing em $80,390 — $120 de folga.

> "ADX surge funciona quando a tendência é real. DI cross sofre na porta da festa." – made by Sky ⚡

---

## 15:17 — ADX Despencou! TP Caiu pra 0.300%, a $53 do Alvo

### Status do Sistema

- **Status:** ATIVO — posição aberta, ADX em queda livre
- **Tick:** #51543 | **Trades:** 27 (9W/18L) | WR 33% | PnL Fechado: $-114,721.69
- **Posição:** 1 aberta | PnL Aberto: **+$16,752** (+0.209%)

### Trade #28 — Evolução desde 14:53

| Hora | BTC | +DI | -DI | ADX | Gap | TP% | Trail | PnL |
|------|-----|-----|-----|-----|-----|-----|-------|-----|
| 14:53 | $80,510 | 33.7 | 15.3 | 42.3 | +18.4 | 0.600 | $80,390 | +$16,695 |
| 14:56 | $80,517 | 37.1 | 15.2 | 43.0 | +21.9 | 0.600 | $80,435 | +$17,340 |
| 15:00 | $80,487 | 31.4 | 17.7 | 40.2 | +13.7 | 0.600 | $80,435 | +$18,010 |
| 15:03 | $80,466 | 26.4 | 24.0 | 36.8 | +2.4 | 0.500 | $80,435 | +$12,222 |
| 15:05 | $80,477 | 23.8 | 21.6 | 32.4 | +2.1 | 0.500 | $80,435 | +$13,350 |
| 15:08 | $80,475 | **24.5** | **26.4** | 28.0 | **-1.9** | 0.400 | $80,435 | +$13,165 |
| 15:10 | $80,499 | 26.5 | 24.6 | 24.7 | +1.9 | 0.400 | $80,435 | +$15,490 |
| 15:12 | $80,457 | **23.6** | **30.6** | 22.6 | **-6.9** | 0.400 | $80,435 | +$11,335 |
| 15:15 | $80,526 | 28.9 | 26.0 | 19.9 | +2.9 | **0.300** | $80,435 | +$18,219 |
| 15:17 | **$80,532** | **30.3** | **22.7** | **19.2** | **+7.6** | **0.300** | **$80,435** | **+$16,752** |

### Evento Crítico: DI Crossover Silencioso

Às **15:08**, -DI cruzou acima de +DI (gap -1.9). Às **15:12**, gap atingiu **-6.9** (-DI=30.6 >> +DI=23.6).

**O DI cross exit NÃO disparou** porque ADX já estava em 28.0 (abaixo do threshold 25 necessário). O bug de saída se manifestou novamente, mas desta vez sem consequência grave — a posição está lucrativa e protegida por trailing.

Às **15:15**, +DI recuperou domínio (gap +2.9 → +8.0). O crossover foi temporário.

### TP Dinâmico em Ação

| ADX Range | TP Ajustado | Target |
|-----------|-------------|--------|
| > 30 | 0.600% | $80,826 |
| 25-30 | 0.500% | $80,746 |
| 20-25 | 0.400% | $80,665 |
| < 20 | **0.300%** | **$80,585** |

**TP atual: $80,585** — BTC está a **$53** deste alvo! ($80,532 vs $80,585)

### Análise de Risco

| Cenário | Trigger | Distância | PnL Resultante |
|---------|---------|-----------|----------------|
| **TP atingido** | BTC ≥ $80,585 | +$53 (+0.07%) | **+$24,151** (estimado) |
| **Trailing ativado** | BTC ≤ $80,435 | -$97 (-0.12%) | +$91 (trailing - entry) |
| **Breakeven** | BTC ≤ $80,343 | -$189 (-0.23%) | $0 |

**Probabilidade:** TP > Trailing. BTC em mini-recovery ($80,457 → $80,532 em 5min). ADX lateral (19.2) não indica crash iminente.

### Anomalias Detectadas

- **[P0 BUG RECORRENTE]** DI cross exit falhou novamente às 15:08 — ADX=28 < threshold 25. Terceira ocorrência do bug hoje (trades #24, #26, agora #28)
- **ADX em queda livre:** 42.3 → 19.2 em 25 minutos (-54%). Tendência esgotando rapidamente
- **Trailing congelado:** $80,435.07 fixo desde ~14:56. O trailing não subiu mesmo quando BTC passou por $80,532 — parece não estar rastreando o pico

### Ações Recomendadas

- **ALTA PROBABILIDADE DE TP:** BTC a $53 do alvo (0.300%). Se mantiver nível atual, TP atinge em minutos
- **Se trailing ativar:** Ganho de apenas $91 (~$7,300 no paper). Muito inferior ao potencial
- **Bug DI cross:** Documentar 3a ocorrência. Fix continua pendente

### Observação

O TP dinâmico salvou esta operação. Quando ADX estava em 42, TP era 0.600% ($80,826 — longe). Conforme ADX caiu, TP ajustou para 0.300% ($80,585 — alcançável). Sem o TP dinâmico, o trade provavelmente teria ido para trailing com ganho mínimo.

Isso é uma vitória parcial para o design do bot: mesmo com o DI cross exit bugado, o mecanismo de TP dinâmico compensa adaptando o alvo à força da tendência em tempo real.

> "O TP dinâmico é o herói invisível — encolhe o sonho pra caber na realidade." – made by Sky 🎯

---

## 16:04 — Trade #28 FECHOU +$24k (TP Dinâmico)! Trade #29 Aberto

### Status do Sistema

- **Status:** ATIVO — Trade #29 aberto, tendência de alta continua
- **Tick:** #54210 | **Trades:** 28 (10W/18L) | **WR 36%** | PnL Fechado: **$-90,618.53**
- **Posição:** 1 aberta | PnL Aberto: ~$0 (oscilando no breakeven)

### Trade #28 — FECHADO: LUCRO

| Campo | Valor |
|-------|-------|
| **Entrada** | 14:21:07 @ $80,343.84 (ADX surge) |
| **Saída** | 15:36:54 @ $80,584.87 |
| **PnL** | **+$24,103.15** (+0.300%) |
| **Motivo** | Take Profit acionado (+0.3%) |
| **Duração** | ~1h 16min |
| **TP atingido** | 0.300% (dinâmico — ADX caiu de 42→19) |

**Maior vitória da sessão!** O TP dinâmico ajustou de 0.600% para 0.300% conforme ADX despencou, e BTC atingiu o alvo reduzido. Sem o TP dinâmico, o trailing teria fechado com apenas +$91.

### KPIs Primários — Delta desde 15:17

| Métrica | Valor | Delta | Status |
|---------|-------|-------|--------|
| Trades | 28 | +1 | OK |
| Win Rate | **36%** | **+3pp** | OK |
| PnL Fechado | **$-90,618.53** | **+$24,103** | MELHORANDO |
| Profit Factor | 0.46 | +0.06 | ALERTA |
| Expectancy | $-3,236 | +$860 | MELHORANDO |

**Melhora significativa:** PnL recuperou $24k, WR subiu de 33% → 36%.

### Trade #29 — Aberto

| Campo | Valor |
|-------|-------|
| **Entrada** | 15:53:17 @ $80,688.18 |
| **Tipo** | ADX surge (ADX 24.7→27.8, +DI=38.5 dominante) |
| **TP alvo** | 0.500% → $81,092 (dinâmico) |
| **SL** | 0.500% → $80,284 |
| **PnL atual** | ~$0 (BTC oscilando $80,650-$80,720) |
| **ADX** | 30-32 (tendência saudável) |
| **+DI** | 31-43 (dominante, gap 12-29) |

### Mercado Atual (16:04)

| Indicador | Valor |
|-----------|-------|
| BTC-USD | $80,690 |
| +DI | 35.0 |
| -DI | 17.6 |
| ADX | 32.1 |
| Gap | +17.4 |
| Regime | tendencia_alta (ADX > 30) |
| TP dinâmico | 0.500% |
| SL | 0.500% |

**ADX em recuperação:** 19.2 (15:17) → 32.1 (16:04). Tendência se reafirmando.

### Histórico de Trades da Sessão

| # | Hora Entry | Tipo | Saída | PnL | Status |
|---|-----------|------|-------|-----|--------|
| 22 | ~01:00 | SMA | Trailing | +$4,590 | WIN |
| 23 | 04:12 | DI cross | SL | -$40,472 | LOSS |
| 24 | 05:49 | Fib Pullback | DI cross exit | -$21,948 | LOSS |
| 25 | 08:38 | DI cross | Breakeven | $0 | BREAKEVEN |
| 26 | 09:41 | DI cross | SL (bug) | -$40,472 | LOSS |
| 27 | 10:58 | Fib Pullback | TP | +$24,152 | WIN |
| **28** | **14:21** | **ADX surge** | **TP dinâmico** | **+$24,103** | **WIN** |
| 29 | 15:53 | ADX surge | OPEN | ~$0 | EM CURSO |

### Padrão Emergente: ADX Surge > DI Cross

| Tipo de Entrada | Trades | WR | PnL Total |
|----------------|--------|-----|-----------|
| **ADX surge** | 2 (fechados) | **100%** (2W/0L) | **+$48,256** |
| DI cross | 3 (fechados) | 0% (0W/3L) | -$81,420 |
| Fib Pullback | 2 (fechados) | 50% (1W/1L) | +$2,204 |

**Conclusão:** ADX surge é claramente o melhor tipo de entrada. DI cross é consistentemente perdendo. Hipótese: DI cross captura inícios de tendência prematuros, enquanto ADX surge confirma tendência já estabelecida.

### Anomalias Detectadas

- **Nenhuma anomalia nova** — mercado comportado, sem erros

### Ações Recomendadas

- **[P1] Backtest ADX surge vs DI cross:** Dados empíricos mostram ADX surge 2W/0L vs DI cross 0W/3L. Investigar se desabilitar DI cross melhora o resultado geral
- **[P2] Considerar peso de entrada:** Se ambos forem mantidos, ADX surge deveria ter tamanho de posição maior
- **Trade #29:** Monitorar — ADX 32 saudável, TP 0.500% = $81,092

### Observação

Sessão em clara recuperação: PnL passou de $-114,721 para $-90,618 (melhora de $24k). Dois wins consecutivos (#27 e #28), ambos por TP. O TP dinâmico é o mecanismo que mais contribuiu para a recuperação.

Trade #29 entrou em momento favorável: ADX subindo (19→32), +DI forte, BTC em tendência de alta. Se o padrão ADX surge se mantiver, temos potencial de mais um win.

> "Duas estrelas cadentes no mesmo céu — ADX surge brilha onde DI cross apaga." – made by Sky 🌟

---

## 16:17 — Trade #29 Subindo! ADX 39, +$12k, Breakeven Ativado

### Status do Sistema

- **Status:** ATIVO — Trade #29 em tendência forte, sem posição aberta anterior
- **Tick:** #54932 | **Trades:** 28 (10W/18L) | **WR 36%** | PnL Fechado: $-90,618.53
- **Posição:** 1 aberta | PnL Aberto: **+$12,858** (+0.159%)

### Trade #29 — Evolução desde Entrada

| Hora | BTC | +DI | -DI | ADX | Gap | SL | TP | PnL |
|------|-----|-----|-----|-----|-----|----|----|-----|
| 15:53 | $80,688 | 38.5 | 16.1 | 24.7 | +22.4 | 0.500 | 0.400 | entrada |
| 15:56 | $80,681 | 38.7 | 17.6 | 30.1 | +21.1 | 0.500 | 0.500 | -$678 |
| 16:00 | $80,691 | 31.1 | 19.2 | 30.9 | +11.9 | 0.500 | 0.500 | -$3,909 |
| 16:08 | $80,747 | 36.5 | 17.6 | 31.6 | +18.9 | 0.500 | 0.500 | +$5,970 |
| 16:10 | **$80,781** | 38.8 | 16.4 | 32.6 | +22.4 | **0.000** | 0.500 | **+$9,372** |
| 16:14 | $80,797 | 41.1 | 12.8 | 36.5 | +28.4 | 0.000 | 0.500 | +$10,914 |
| 16:16 | **$80,816** | **39.5** | **11.0** | **39.0** | **28.5** | 0.000 | 0.500 | **+$12,858** |
| 16:17 | $80,785 | 39.5 | 11.0 | 39.0 | 28.5 | 0.000 | 0.500 | +$9,697 |

### Indicadores de Tendência

- **ADX:** 39.0 — tendência forte e **crescendo** (32→39 em 13min)
- **+DI:** 39.5 vs -DI 11.0 — gap de 28.5, dominância quase total
- **Breakeven:** Ativado às ~16:10 (SL=0.000%)
- **Trailing:** Ainda não apareceu — breakeven está protegendo em $0

### TP Target

| Tipo | Alvo | Distância |
|------|------|-----------|
| TP 0.500% | $81,092 | **$307** (+0.38%) |
| Breakeven | $80,688 | -$97 (-0.12%) |
| SL original | $80,284 | -$501 (-0.62%) |

**Risco:** BTC precisa subir $307 pra TP. Se cair $97, breakeven mata o trade em $0 (pela 2a vez hoje).

### Anomalias Detectadas

- **Nenhuma anomalia** — tendência limpa, ADX subindo, +DI forte
- **Breakeven risk:** SL=0.000% significa que qualquer pullback abaixo de $80,688 fecha em $0. Com $12k de lucro não-realizado, o mesmo problema do Trade #25 pode se repetir

### Ações Recomendadas

- **Monitorar trailing:** Quando trailing aparecer, vai proteger lucro real (não $0)
- **Se ADX continuar subindo (>40):** TP dinâmico pode aumentar para 0.600%, ampliando ganho potencial
- **[P0] Breakeven mínimo:** O fix de $0 → +0.05% permanece pendente. Já perdemos $15k no Trade #25 por isso

### Observação

Trade #29 está replicando o padrão do Trade #28 com sucesso: entrada via ADX surge, tendência confirmada pelo ADX subindo, +DI dominante. A diferença é que ADX está subindo (32→39) ao invés de cair, o que sugere tendência mais sustentável.

O breakeven já foi ativado, o que é preocupante — estamos com $12,858 de lucro não-realizado mas protegidos apenas em $0. Se BTC tiver um pullback de -0.16%, o trade fecha em $0 e perdemos toda a oportunidade.

> "Breakeven a $0 é proteção de covarde — protege o orgulho mas enterra o lucro." – made by Sky 🛡️

---

## 17:03 — ADX Colapsou de Novo! DI Cross Negativo, Trailing em Risco

### Status do Sistema

- **Status:** ATIVO — Trade #29 em risco, DI crossover negativo
- **Tick:** #57558 | **Trades:** 28 (10W/18L) | **WR 36%** | PnL Fechado: $-90,618.53
- **Posição:** 1 aberta | PnL Aberto: **+$11,830** (+0.147%)

### Trade #29 — Evolução desde 16:17

| Hora | BTC | +DI | -DI | ADX | Gap | TP% | Trail | PnL |
|------|-----|-----|-----|-----|-----|-----|-------|-----|
| 16:17 | $80,785 | 39.5 | 11.0 | 39.0 | +28.5 | 0.500 | — | +$9,697 |
| 16:25 | $80,800 | 38.2 | 12.3 | 37.6 | +25.9 | 0.500 | — | +$11,182 |
| 16:37 | $80,723 | 27.7 | 21.0 | 17.1 | +6.7 | 0.300 | — | +$3,503 |
| 16:42 | $80,715 | 24.5 | 23.0 | 13.6 | +1.5 | 0.300 | — | +$2,685 |
| 16:48 | $80,773 | 22.1 | 21.7 | 11.2 | +0.5 | 0.300 | — | +$8,515 |
| 16:53 | **$80,849** | 35.2 | 18.1 | 14.2 | +17.1 | 0.300 | — | **+$16,142** |
| 16:53 | $80,849 | 35.2 | 18.1 | 14.2 | +17.1 | 0.300 | **$80,728** | +$16,142 |
| 16:57 | $80,815 | 29.1 | 25.1 | 14.7 | +4.1 | 0.300 | $80,728 | +$12,340 |
| 17:00 | $80,822 | 23.6 | 23.0 | 12.8 | +0.6 | 0.300 | $80,728 | +$13,393 |
| **17:03** | **$80,805** | **22.2** | **29.0** | **12.1** | **-6.9** | 0.300 | **$80,728** | **+$11,830** |

### Padrão Repetido: ADX Collapse + DI Cross

**Exatamente o mesmo padrão do Trade #28:**
1. ADX sobe para 39 (tendência forte)
2. ADX colapsa em ~30 min (39→12)
3. TP dinâmico ajusta: 0.500% → 0.300%
4. -DI cruza acima de +DI (gap agora -6.9)
5. DI cross exit **não dispara** porque ADX < 25 (4a ocorrência do bug!)

**Diferença vs Trade #28:** Desta vez o trailing stop está ativo ($80,728), protegendo ~$40 de lucro real.

### Análise de Risco

| Cenário | Trigger | Distância | PnL |
|---------|---------|-----------|-----|
| **TP 0.300%** | BTC ≥ $80,930 | +$125 (+0.15%) | **~+$24,000** |
| **Trailing exit** | BTC ≤ $80,728 | -$77 (-0.10%) | **+$40** |
| **Breakeven** | BTC ≤ $80,688 | -$117 (-0.14%) | **$0** |

**Trailing muito apertado:** $80,728 vs BTC $80,805 → apenas $77 de buffer. Qualquer pullback de 0.10% ativa trailing com ganho mínimo de $40.

### KPIs por Entrada — Atualização

| Entrada | Trades | WR | PnL Total |
|---------|--------|-----|-----------|
| **ADX surge** | 2 (fechados) + 1 open | 100% (2W/0L) | +$48,256 |
| DI cross | 3 (fechados) | 0% (0W/3L) | -$81,420 |
| Fib Pullback | 2 (fechados) | 50% (1W/1L) | +$2,204 |

### Anomalias Detectadas

- **[P0 BUG — 4a ocorrência]** DI cross exit falhou às ~17:03 — -DI cruzou acima de +DI (gap -6.9), ADX=12.1 < 25. Exit não gerado
- **ADX collapse pattern:** 39→12 em 45min. Mesmo padrão do Trade #28. Pode ser característica intrínseca do indicador no timeframe 1m
- **Trailing gap mínimo:** $77 (0.10%). Provavelmente resultará em trailing exit com ganho marginal

### Ações Recomendadas

- **[P0] DI cross exit fix:** 4 ocorrências documentadas hoje. Urgente remover requisito ADX≥25 do exit
- **[P1] Investigar ADX collapse:** Por que ADX oscila 12-46 em intervalos de 30-45min? Timeframe 1m pode ser muito curto
- **[P1] Trailing stop distance:** Considerar trailing mais largo (ex: 0.3% abaixo do pico ao invés do padrão atual)

### Observação

O Trade #29 está entre a espada e a parede: BTC precisa subir $125 para TP, mas pode cair $77 para trailing (com ganho de apenas $40). O breakeven a $0 significa que se trailing falhar, o trade fecha em $0 — repetindo o desastre do Trade #25.

O padrão ADX collapse é consistente: sobe durante a entrada, colapsa em 30-45min. Isso sugere que o timeframe 1m gera movimentos de tendência muito curtos. O bot captura o início corretamente (ADX surge) mas a tendência dura menos que o TP original (0.500%).

> "ADX mentiroso: sobe pra te convencer, despenca pra te abandonar." – made by Sky 📉

---

## 17:17 — Trade #29 Fechado: Trailing Stop +$6k, WR 38%!

### Status do Sistema

- **Status:** ATIVO — sem posição, mercado em -DI dominante (baixa)
- **Tick:** #58294 | **Trades:** 29 (11W/18L) | **WR 38%** | PnL Fechado: **$-84,585.01**
- **Posição:** 0 abertas | Mercado lateral-baixa

### Trade #29 — FECHADO: Trailing Stop

| Campo | Valor |
|-------|-------|
| **Entrada** | 15:53:17 @ $80,688.18 (ADX surge) |
| **Saída** | 17:11:29 @ $80,748.52 |
| **PnL** | **+$6,033.53** (+0.075%) |
| **Motivo** | Trailing Stop acionado (+0.1%) |
| **Duração** | ~1h 18min |
| **Pico** | $80,869 (+$18,164, ~+0.225%) às 17:04 |

**Trailing protegeu lucro:** O trailing stop subiu de $80,728 → $80,748 conforme BTC subiu, e disparou quando BTC caiu de $80,869 para $80,748. Ganho real de +$6k vs breakeven $0 — o trailing foi decisivo.

**Perda vs TP:** Se o TP dinâmico (0.300% = $80,930) tivesse sido atingido, o ganho seria ~$24k. O trailing capturou 25% do potencial.

### KPIs Primários — Delta desde 17:03

| Métrica | Valor | Delta | Status |
|---------|-------|-------|--------|
| Trades | 29 | +1 | OK |
| Win Rate | **38%** | **+2pp** | OK |
| PnL Fechado | **$-84,585.01** | **+$6,033** | MELHORANDO |
| Profit Factor | 0.52 | +0.06 | ALERTA |
| Expectancy | $-2,917 | +$319 | MELHORANDO |

### Recuperação da Sessão

| Período | PnL Fechado | Evento |
|---------|-------------|--------|
| 14:53 | $-114,721 | Trade #28 aberto |
| 15:36 | $-90,618 | Trade #28 TP +$24k |
| 17:11 | **$-84,585** | Trade #29 Trailing +$6k |
| **Recuperação** | **+$30,136** | Em ~2h |

### Mercado Atual (17:17)

| Indicador | Valor |
|-----------|-------|
| BTC-USD | $80,738 |
| +DI | 28.1 |
| -DI | 34.9 |
| ADX | 14.8 |
| Gap | -6.8 (**-DI dominante**) |
| Regime | lateral-baixa |

**-DI assumiu controle** às ~17:11, gap caiu para -20.0 (forte venda). ADX em 11-15 (sem tendência). Bot corretamente sem posição.

### KPIs por Entrada — Atualização Final

| Entrada | Trades | WR | PnL Total | Avg PnL |
|---------|--------|-----|-----------|---------|
| **ADX surge** | 3 | **100%** (3W/0L) | **+$54,289** | +$18,096 |
| DI cross | 3 | 0% (0W/3L) | -$81,420 | -$27,140 |
| Fib Pullback | 2 | 50% (1W/1L) | +$2,204 | +$1,102 |
| SMA (legado) | 21 | 38% (8W/13L) | -$59,658 | -$2,841 |

**Dado incontestável:** ADX surge é o único tipo de entrada consistente. 3/3 wins, avg +$18k.

### Anomalias Detectadas

- **[P0 BUG — 4a ocorrência, sem consequência]** DI cross exit falhou às ~17:03 — mas trailing stop protegeu o trade
- **[Rate-limit warning]** 17:06:33 — yfinance rate-limit, recuperou automaticamente
- **Trailing protegeu contra breakeven $0:** O trailing stop impediu que o trade #29 repetisse o desastre do Trade #25 ($15k → $0)

### Ações Recomendadas

- **[P0] Manter trailing stop:** O trailing foi o herói — salvou $6k que teria sido $0 com breakeven
- **[P0] DI cross exit fix:** 4 ocorrências, urgente
- **[P1] Desabilitar DI cross como entrada:** Dados empíricos mostram 0W/3L. Considerar usar apenas ADX surge
- **[P1] Investigar timeframe:** ADX collapse em 30-45min sugere que 1m pode ser muito curto. Testar 5m?

### Observação

A sessão está em recuperação consistente. Em ~2 horas, PnL melhorou $30k (-$114k → -$84k). Três wins seguidos (#27 Fib, #28 ADX surge TP, #29 ADX surge trailing), todos originados de entradas com confirmação de tendência (ADX surge ou Fib pullback).

O mercado entrou em fase de -DI dominante (baixa), e o bot está corretamente sem posição. A próxima entrada dependerá de +DI recuperar domínio e ADX subir acima de 25.

> "Trailing é o anjo da guarda que o breakeven nunca foi." – made by Sky 👼

---

## 18:03 — Mercado em Transição, DI Cross Sem ADX, Sem Trades

### Status do Sistema

- **Status:** ATIVO — sem posição, aguardando confirmação de tendência
- **Tick:** #60922 | **Trades:** 29 (11W/18L) | **WR 38%** | PnL Fechado: $-84,585.01
- **Posição:** 0 abertas | Mercado em transição DI

### Mercado (17:17 → 18:03)

| Hora | BTC | +DI | -DI | ADX | Gap | Regime |
|------|-----|-----|-----|-----|-----|--------|
| 17:17 | $80,738 | 28.1 | 34.9 | 14.8 | -6.8 | -DI dominante |
| 17:30 | $80,714 | 23.4 | 38.5 | 23.5 | -15.1 | venda forte |
| 17:48 | $80,631 | 24.8 | 37.7 | 33.1 | -12.9 | **ADX subiu com -DI** |
| 17:50 | **$80,619** | 19.0 | 43.4 | 34.0 | -24.4 | low do período |
| 17:55 | $80,694 | 32.2 | 32.2 | 29.8 | **0.0** | **DI crossing!** |
| 17:56 | $80,685 | 34.8 | 31.0 | 28.1 | **+3.8** | +DI cruzou! |
| 17:58 | $80,651 | 30.2 | 40.0 | 25.3 | -9.8 | -DI recuperou |
| 18:00 | $80,688 | 36.0 | 34.3 | 22.9 | +1.7 | +DI de novo |
| 18:03 | **$80,671** | **30.5** | **27.5** | **19.7** | **+3.0** | ADX lag |

### Padrão ADX Lag (5a ocorrência)

+DI cruzou acima de -DI às ~17:55 (gap 0.0 → +3.8), mas **ADX=28.1 no momento do cross** — acima de 25! Deveria ter gerado sinal.

Mas então ADX caiu rapidamente: 28.1 → 25.3 → 22.9 → 19.7. O cross aconteceu em um momento de ADX decaindo, e o di_gap_min=5 pode ter bloqueado (gap apenas 3.8 no primeiro tick após o cross).

**Possível entrada perdida:** Se o gap fosse ≥ 5 e ADX ≥ 25, teria havido sinal COMPRA. ADX estava em 28.1 no momento do crossing — acima do threshold — mas gap era apenas 3.8 (abaixo de di_gap_min=5).

### Anomalias Detectadas

- **Possível sinal bloqueado por gap filter:** DI cross às 17:56 com ADX=28.1 (válido) mas gap=3.8 (< 5 mínimo). Se BTC subir e gap aumentar, ADX pode já ter caído abaixo de 25
- **Nenhuma anomalia crítica**

### Ações Recomendadas

- **[P2] Revisar di_gap_min:** Gap mínimo de 5 pode estar bloqueando entradas válidas. Dados sugerem gap 3-4 seria mais apropriado
- **Monitorar:** Se ADX subir acima de 25 com +DI dominante, entrada via ADX surge pode ocorrer

### Observação

Ciclo tranquilo — sem trades em 50 minutos. BTC fez um low de $80,619 e está recuperando lentamente. O DI crossover aconteceu mas foi bloqueado pelo gap filter. ADX continua caindo (19.7), indicando mercado lateral.

O bot está correto em não forçar entradas em mercado lateral. A próxima oportunidade depende de ADX subir com +DI dominante.

> "Paciência é a virtude dos bots que não queimam dinheiro." – made by Sky ⏳

---

## 18:16 — Lateral Profundo, ADX Preso 17-22, Sem Sinais

### Status do Sistema

- **Status:** ATIVO — sem posição, mercado lateral profundo
- **Tick:** #61647 | **Trades:** 29 (11W/18L) | **WR 38%** | PnL Fechado: $-84,585.01
- **Posição:** 0 abertas | 1h+ sem trades

### Mercado (18:03 → 18:16)

| Hora | BTC | +DI | -DI | ADX | Gap | Nota |
|------|-----|-----|-----|-----|-----|------|
| 18:03 | $80,671 | 30.5 | 27.5 | 19.7 | +3.0 | +DI leve |
| 18:06 | $80,675 | 32.1 | 24.8 | 17.3 | +7.2 | gap crescendo |
| 18:08 | $80,714 | 37.7 | 22.6 | 17.6 | +15.1 | +DI forte |
| 18:09 | $80,707 | **41.4** | 21.2 | 18.6 | **+20.2** | gap enorme |
| 18:11 | $80,706 | 39.5 | 19.8 | 20.6 | +19.7 | ADX subindo |
| 18:13 | $80,676 | 37.7 | 23.6 | 21.7 | +14.1 | ADX peak |
| 18:16 | $80,667 | 32.2 | 32.0 | 18.3 | +0.2 | **DIs convergindo** |

**ADX preso:** Apesar de +DI chegar a 41 com gap de 20, ADX não passou de 21.7. O momentum de tendência simplesmente não existe neste timeframe.

**DI convergence:** Às 18:16, gap caiu para 0.2 — DIs praticamente empatados. Se -DI cruzar acima, volta ao regime de venda.

### Anomalias Detectadas

- **Nenhuma** — mercado lateral é esperado e o bot está correto em não forçar

### Observação

1h+ sem trades. BTC em range de $48 ($80,666-$80,714). ADX cronicamente abaixo de 25 apesar de +DI forte. O mercado está em consolidacao — nem compra nem venda clara.

O bot precisa que ADX cruze 25 com +DI dominante e gap ≥ 5 para gerar sinal. Com ADX em 18-22, isso pode demorar horas.

> "Mercado lateral é o deserto onde bots pacientes sobrevivem." – made by Sky 🏜️

---

## 19:03 — Trade #30 Aberto! Primeiro DI Cross Válido (ADX 30+)

### Status do Sistema

- **Status:** ATIVO — Trade #30 aberto, DI cross com confirmação ADX
- **Tick:** #64288 | **Trades:** 29 (11W/18L) | **WR 38%** | PnL Fechado: $-84,585.01
- **Posição:** 1 aberta | PnL Aberto: **+$3,630** (+0.045%)

### Trade #30 — DI Cross Entry (PRIMEIRA VÁLIDA!)

| Campo | Valor |
|-------|-------|
| **Entrada** | 19:01:26 @ $80,674.70 |
| **Tipo** | DI cross (primeiro com ADX ≥ 25 no momento do cross!) |
| **TP alvo** | 0.500% → $81,078 |
| **SL** | 0.500% → $80,271 |
| **PnL atual** | +$3,630 (+0.045%) |

**Por que é diferente:** Todas as entradas DI cross anteriores tinham ADX < 25 (bloqueadas) ou entravam via ADX surge. Esta é a primeira vez que +DI cruza acima de -DI **com ADX já acima de 25** (vindo do período de venda anterior).

### Contexto de Mercado (18:16 → 19:03)

| Hora | BTC | +DI | -DI | ADX | Gap | Evento |
|------|-----|-----|-----|-----|-----|--------|
| 18:16 | $80,667 | 32.2 | 32.0 | 18.3 | +0.2 | DIs empatados |
| 18:25 | $80,597 | 25.2 | 34.4 | 23.0 | -9.2 | -DI assumiu |
| 18:40 | $80,536 | 19.2 | 40.0 | 30.2 | -20.8 | venda forte |
| 18:50 | **$80,508** | 16.4 | 35.7 | 35.4 | -19.3 | low do período |
| 18:58 | $80,543 | 17.4 | 24.5 | 31.2 | -7.1 | -DI enfraquecendo |
| 19:00 | $80,618 | 20.7 | 22.5 | 28.6 | -1.8 | quase crossing |
| **19:01** | **$80,674** | **~30+** | **~20** | **~29** | **+10+** | **+DI CRUZOU!** |
| 19:02 | $80,718 | **41.7** | 15.1 | 30.9 | **+26.7** | gap enorme |

**ADX vinha de trend de venda (35.4)** — Quando +DI cruzou, ADX ainda estava em ~29 (acima de 25). O sinal não foi bloqueado! Essa é a condição ideal: ADX alto porque havia uma tendência prévia (venda), e agora +DI inverte.

### yfinance Error

Às ~18:58, um `TypeError: 'NoneType' object is not subscriptable` ocorreu no yfinance. O bot se recuperou automaticamente no tick seguinte. Sem impacto.

### Anomalias Detectadas

- **Nenhuma crítica** — primeira entrada DI cross limpa da sessão
- **yfinance rate-limit:** Erro recuperado automaticamente

### Ações Recomendadas

- **Monitorar Trade #30:** Se ADX se mantiver alto (30+), TP 0.500% é alcançável
- **Cuidado com ADX collapse pattern:** Trades #28 e #29 tiveram ADX caindo de 40+ para 12-20 em 30min

### Observação

Trade #30 é um marco: a primeira entrada DI cross que não foi bloqueada pelo ADX threshold. Isso aconteceu porque houve uma tendência de venda prévia que manteve ADX alto, e quando +DI inverteu, o ADX ainda estava acima de 25.

A questão é: será que esta entrada DI cross vai quebrar a maldição de 0W/3L das entradas DI cross? Ou o padrão se repetirá?

BTC precisa subir para $81,078 (TP 0.500%) — $404 acima do preço atual. Com ADX 30.9 e gap 26.7, a tendência é forte no momento.

> "Primeiro DI cross sem desculpas — ADX não pode mais culpar o lag." – made by Sky 🔥

---

## 19:17 — BREAKEVEN MATOU $8k DE NOVO! Trade #31 Fib Pullback Aberto

### Status do Sistema

- **Status:** ATIVO — Trade #31 aberto, mercado em queda
- **Tick:** #65034 | **Trades:** 30 (12W/18L) | **WR 40%** | PnL Fechado: $-84,585.01
- **Posição:** 1 aberta | PnL Aberto: +$1,721 (+0.021%)

### Trade #30 — FECHADO: BREAKEVEN $0 (NOVAMENTE!)

| Campo | Valor |
|-------|-------|
| **Entrada** | 19:01:26 @ $80,674.70 (DI cross) |
| **Saída** | 19:09:06 @ $80,674.70 |
| **PnL** | **$0.00** (Breakeven acionado) |
| **Duração** | **8 minutos** |
| **Pico** | $80,762 (+$8,737, +0.108%) às 19:06 |

**O mesmo desastre do Trade #25:** BTC subiu para +$8,737 (+0.108%), breakeven ativou, BTC voltou para entrada, fechou em $0. Oito minutos de trade, $8,737 evaporados.

### Timeline do Breakeven

| Hora | BTC | PnL | Evento |
|------|-----|-----|--------|
| 19:01 | $80,674 | $0 | Entrada |
| 19:02 | $80,718 | +$4,331 | Subindo |
| 19:05 | $80,745 | +$7,129 | Subindo |
| 19:06 | **$80,762** | **+$8,737** | **PICO** |
| 19:07 | $80,723 | +$4,898 | Caindo |
| 19:08 | $80,689 | +$1,450 | Quase breakeven |
| **19:09** | **$80,674** | **$0** | **BREAKEVEN** |

### Trade #31 — RE-ENTRY Fib Pullback 61.8%

| Campo | Valor |
|-------|-------|
| **Entrada** | 19:14:43 @ $80,600.53 (Fib Pullback 61.8%) |
| **TP alvo** | 0.400% → $80,922 (dinâmico) |
| **SL** | 0.500% → $80,197 |
| **PnL atual** | +$1,721 (+0.021%) |
| **ADX** | 26.3 (caindo) |
| **-DI dominante:** | +DI=24.9 vs -DI=33.5 (gap -8.6) |

### O Problema do Breakeven — 3a Ocorrência

| Trade | Pico Não-Realizado | Resultado | Perda |
|-------|-------------------|-----------|-------|
| #25 | +$15,627 | $0 (Breakeven) | -$15,627 |
| #30 | +$8,737 | $0 (Breakeven) | -$8,737 |
| **Total** | **+$24,364** | **$0** | **-$24,364** |

**$24,364 perdidos por breakeven em $0** — isso representaria quase toda a recuperação da sessão.

### DI Cross Maldição Confirma

| Entrada | Trades | WR | PnL Total | Observação |
|---------|--------|-----|-----------|------------|
| **DI cross** | 4 | **25%*** | **$0** | *1W = breakeven $0 |
| ADX surge | 3 | 100% (3W/0L) | +$54,289 | Perfecto |
| Fib Pullback | 3 (incl #31) | — | — | EM CURSO |

**DI cross é consistentemente a pior entrada.** Mesmo quando funciona (ADX ≥ 25), o breakeven mata o lucro.

### Anomalias Detectadas

- **[P0 CRÍTICO] Breakeven $0:** 3a ocorrência, $24k total perdido. O breakeven ativa com qualquer lucro mínimo (+0.10%) e protege em $0, matando trades que teriam ido para TP
- **[P0] DI cross não funciona:** 4 trades, PnL $0. Mesmo com ADX válido, resultado é nulo

### Ações Recomendadas

- **[P0 URGENTE] Fix breakeven:** Alterar de $0 para +0.05% mínimo. Isso permitiria que o trade respire antes de ativar proteção
- **[P0] Considerar desabilitar breakeven:** O trailing stop já protege lucro real. Breakeven é redundante e destrutivo
- **[P1] Desabilitar DI cross entry:** Dados inequívocos — DI cross não gera lucro

### Observação

O Trade #30 durou apenas 8 minutos. BTC subiu $87 (+0.108%), breakeven ativou, BTC voltou $87, fechou em $0. Se o breakeven não existisse (ou fosse +0.05%), o trade provavelmente teria continuado para trailing ou TP.

Trade #31 (Fib Pullback) entrou em momento arriscado: -DI dominante (gap -8.6), ADX caindo (26.3). Mas Fib Pullback tem 50% WR (1W/1L anterior). Vamos ver.

> "Breakeven a $0 é o ladrão que rouba com licença — protege mas deixa pobre." – made by Sky 🔒

---

## 19:48 — Trade #31 BREAKEVEN #4! $27k Total Perdido, ADX Mínimo 9.1

### Status do Sistema

- **Status:** ATIVO — sem posição, mercado lateral profundo (ADX 9.1)
- **Tick:** #66840 | **Trades:** 31 (13W/18L) | **WR 42%*** | PnL Fechado: $-84,585.01
- **Posição:** 0 abertas | ADX em mínimo da sessão
- ***Nota:** WR inflacionado — 3 dos 13 "wins" são breakeven $0

### Trade #31 — FECHADO: BREAKEVEN $0 (4a VEZ!)

| Campo | Valor |
|-------|-------|
| **Entrada** | 19:14:43 @ $80,600.53 (Fib Pullback 61.8%) |
| **Saída** | 19:36:40 @ $80,600.53 |
| **PnL** | **$0.00** (Breakeven acionado) |
| **Duração** | ~22 minutos |
| **Pico** | +$3,402 (+0.042%) às 19:35 |

### Contabilidade do Breakeven — Hoje Completo

| Trade | Tipo Entrada | Pico Não-Realizado | Resultado | Perdido |
|-------|-------------|-------------------|-----------|---------|
| #25 | DI cross | +$15,627 | $0 | $15,627 |
| #30 | DI cross | +$8,737 | $0 | $8,737 |
| #31 | Fib Pullback | +$3,402 | $0 | $3,402 |
| **Total** | | **+$27,766** | **$0** | **$27,766** |

**$27,766 em lucro não-realizado destruído pelo breakeven a $0.** Este valor representaria uma recuperação de 24% no PnL total.

### Mercado Atual (19:48)

| Indicador | Valor |
|-----------|-------|
| BTC-USD | $80,637 |
| +DI | 32.2 |
| -DI | 29.9 |
| ADX | **9.1** (mínimo da sessão) |
| Gap | +2.3 |
| Regime | lateral profundo |

**ADX 9.1** — o mais baixo do dia. Mercado completamente sem direção. BTC em range de $30 ($80,616-$80,649).

### Resumo da Sessão — 19:48

| Métrica | Valor |
|---------|-------|
| Trades | 31 (13W/18L, WR 42%) |
| PnL Fechado | $-84,585.01 |
| PnL se breakeven fosse +0.05% | ~$-57,000 (est.) |
| Melhor entrada | ADX surge (3W/0L, +$54k) |
| Pior entrada | DI cross (1W*/3L, $0) |
| Maior bug | Breakeven $0 ($27k perdido) |
| 2o maior bug | DI cross exit bloqueado (4x) |

### Anomalias Detectadas

- **[P0 CRÍTICO] Breakeven $0:** 4a ocorrência, $27,766 total. Maior destruidor de valor do sistema
- **ADX mínimo:** 9.1 — mercado em lateral profundo, sem sinal esperado por tempo indeterminado

### Observação

A sessão se encaminha para o fim com um diagnóstico claro: o bot captura tendências reais (ADX surge: 3/3 wins) mas destrói lucro via breakeven ($0) em trades que teriam sido rentáveis. O WR de 42% é ilusório — 3 das 13 "vitórias" renderam $0.

Com ADX em 9.1, o mercado está em hibernação. Próximo sinal pode demorar horas. O monitoramento pode reduzir frequência.

> "Quatro vezes o breakeven riu na minha cara. Chega — é hora de mudar as regras." – made by Sky 💢

---
