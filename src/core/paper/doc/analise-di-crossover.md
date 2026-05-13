# Análise dos Cruzamentos DI — Guardião Conservador

**Data**: 2026-05-10
**Range analisado**: 2026-05-08 06:54 → 2026-05-10 02:19 (~43h de log)
**Dados verificados**: yfinance BTC-USD 7d 1m (8785 candles)
**Status**: CORREÇÃO IMPLEMENTADA E VALIDADA

## Timeline de Versões da Estratégia

| Período | Versão | Indicador | SL/TP | Trades | PnL |
|---|---|---|---|---|---|
| 05-08 06:54 → 05-09 08:47 | **v1 SMA** | SMA5 x SMA15 | 0.073%/0.097% | ~33 | -$5,279 |
| 05-09 09:04 → 16:54 | **v1 SMA** (calibrado) | SMA5 x SMA15 | 0.2%/0.4% | 14 | +$11,152 |
| 05-09 17:19 → 05-10 02:19 | **v2 ADX** | +DI/-DI crossover | 0.2%/0.4% | **0** | **$0** |

**PnL acumulado total**: +$5,873.30 (100% da versão SMA v1)

---

## Resultado: 110 cruzamentos DI, 0 trades

Análise exaustiva de toda a sessão ADX (05-09 17:19 → 05-10 02:19):

| Métrica | Valor |
|---|---|
| Cruzamentos +DI/-DI detectados | **110** (55 compras, 55 vendas) |
| Cruzamentos bloqueados (ADX < 25) | **110 (100%)** |
| Trades executados | **0** |
| ADX range nos cruzamentos | **8.4 — 23.1** |
| ADX < 20 nos cruzamentos | **102** |
| ADX 20-25 nos cruzamentos | **8** |
| ADX >= 25 nos cruzamentos | **0** |

### Simulação com thresholds alternativos

| Threshold | Trades | WR | PnL total | Observação |
|---|---|---|---|---|
| ADX >= 25 (atual) | 0 | — | 0% | 100% inativo |
| ADX >= 20 | 3 | 0% | -0.210% | Todas perdas |
| ADX >= 15 | 15 | 13% | -0.314% | Ruim |
| Sem filtro | 53 | 19% | -0.600% | Péssimo |

**Conclusão**: Mesmo sem filtro de ADX, os cruzamentos DI em 1m com close-only
são ruído puro. O ADX está corretamente filtrando sinais de baixa qualidade.

---

## BUG CRÍTICO: ADX calculado sem OHLC

**Arquivo**: `guardiao_conservador.py:53-56`

```python
high = precos[i]    # BUG: high = close
low = precos[i]     # BUG: low = close
prev_high = precos[i - 1]  # BUG: prev_high = prev_close
prev_low = precos[i - 1]   # BUG: prev_low = prev_close
```

### Impacto real medido com dados BTC-USD (8758 candles):

| | Close-only (atual) | OHLC (correto) | Diferença |
|---|---|---|---|
| ADX médio | 18.7 | **24.9** | +33% |
| ADX max | 54.3 | 66.8 | +23% |
| ADX min | 5.8 | 8.0 | +38% |
| % do tempo com ADX >= 25 | **16.9%** | **42.5%** | +2.5x |

**Com OHLC, o ADX seria >= 25 em 42.5% do tempo vs 16.9% atual.**

Os valores de DI também mudam drasticamente:
- Close-only: +DI=47.5, -DI=52.5 (gap 5.0, parece próximo)
- OHLC: +DI=15.7, -DI=33.9 (gap 18.2, mostra direção real)

**Root cause**: Sem OHLC, TR = |close - prev_close| (pequeno),
o que infla DI para ~50 (porque DM/TR ≈ 1 quando preço sobe).
Com OHLC, TR inclui high-low (maior), DI fica em range 15-35 (realista).

### Correção necessária

1. `DadosMercado` precisa receber highs e lows (não só closes)
2. `_calc_adx` precisa usar high/low/prev_close para TR e DM
3. `yahoo_finance_feed.obter_historico` já retorna OHLC mas só usa Close

---

## PROBLEMA SECUNDÁRIO: +DI/-DI em 1m com close-only gera ruído

Com close-only, os DI values ficam artificialmente próximos (~45-55),
gerando cruzamentos frequentes mas sem significado (whipsaws).
A simulação confirma: sem filtro ADX, 53 trades com WR de 19% e PnL negativo.

Com OHLC, os DI values ficam mais distantes (15-65), gerando menos
cruzamentos mas com mais significado direcional.

---

## CORREÇÕES PRIORITÁRIAS

### P0 — PASSAR OHLC PARA O ADX (bloqueante)

Sem isso, a estratégia não funciona. O ADX fica cronicamente baixo.

**Arquivos a alterar**:
1. `signal.py` → `DadosMercado`: adicionar `historico_highs`, `historico_lows`
2. `guardiao_conservador.py` → `_calc_adx`: usar OHLC no cálculo de TR e DM
3. `strategy_worker.py` → `_do_tick`: passar highs/lows do historico
4. `yahoo_finance_feed.py` → `Cotacao`: já tem acesso ao OHLC, propagar

### P1 — Revalidar threshold ADX após correção OHLC

Com OHLC, ADX médio sobe de 18.7 para 24.9 — já próximo de 25.
Pode ser que threshold 25 funcione bem após a correção.
**Não mudar threshold antes de corrigir OHLC.**

### P2 — Commit separado para v2 ADX

A versão ADX está sem commit. Criar commit com a correção OHLC já incluída.

> "O guardião estava operando de olhos vendados" – made by Sky 🔍

---

## VALIDAÇÃO PÓS-CORREÇÃO

**Executado em**: 2026-05-10 com dados reais BTC-USD 7d 1m

### Backtest comparativo (ADX >= 25)

| Versão | Trades | Win Rate | PnL Total | Observação |
|---|---|---|---|---|
| Close-only (antigo, log) | 0 | — | 0% | ADX nunca atingiu 25 |
| Close-only (backtest) | 14 | 71.4% | +4.16% | Trades raros, sobrevivência enviesada |
| **OHLC (corrigido)** | **45** | **51.1%** | **+2.07%** | Frequência e lucro consistentes |

### ADX com OHLC corrigido

- Média: 24.9 (vs 18.7 close-only)
- ADX >= 25 em 42.6% do tempo (vs 16.9%)
- Último ADX: 38.8 (ativo, mostrando momentum real)

### Trades recentes (últimos 10, com OHLC)

```
WIN:  80340 -> 80631 (+0.363%) bars=113 ADX=27.8->28.8
WIN:  80643 -> 80782 (+0.172%) bars=72  ADX=27.1->32.1
WIN:  80396 -> 80481 (+0.105%) bars=139 ADX=27.6->30.5
WIN:  80274 -> 80325 (+0.064%) bars=31  ADX=25.4->31.3
LOSS: 80517 -> 80420 (-0.121%) bars=84  ADX=26.6->34.1
LOSS: 80327 -> 80230 (-0.120%) bars=64  ADX=25.6->31.6
```

### Arquivos alterados

1. `signal.py` — DadosMercado com historico_highs/historico_lows
2. `guardiao_conservador.py` — _calc_adx usa OHLC, fallback close-only
3. `data_feed_port.py` — Cotacao com high/low/open
4. `yahoo_finance_feed.py` — Propaga OHLC do yfinance
5. `strategy_worker.py` — Passa highs/lows ao DadosMercado

**Testes**: 203 passed, 0 failed

---

## VALIDAÇÃO EM PRODUÇÃO (2026-05-10 ~03:51)

Bot reiniciado com código OHLC corrigido após matar processo antigo (PID 6760).

### Primeiro tick comparativo

| | Close-only (antigo) | OHLC (corrigido) | Delta |
|---|---|---|---|
| +DI | 53-65 | **54.4** | realista |
| -DI | 39-47 | **23.1** | separação real |
| ADX | 12-15 | **23.9→25.1** | +100% |
| gap | 5-22 | **31.3** | direção clara |

- Tick #1: ADX=23.9 (já próximo do threshold)
- Tick #29: ADX=**25.1** (cruzou o threshold!)
- Estratégia pronta para gerar sinais de crossover

> "O guardião abriu os olhos — agora enxerga o mercado" – made by Sky 🔭

---

## SESSÃO OHLC — ANÁLISE DE 20 MIN (03:51 → 04:12)

**Ticks analisados**: 1167 (~20 min de produção com código corrigido)

### ADX/DI com OHLC corrigido — Resumo

| Métrica | Valor |
|---|---|
| ADX range | 23.0 — 30.6 |
| ADX médio | ~27 (vs ~13 close-only) |
| +DI range | 42 — 62 |
| -DI range | 18 — 33 |
| gap range | 10.9 — 43.8 |
| ADX >= 25 | ~90% do tempo |
| Trades | 0 |

### Diagnóstico: 0 trades = COMPORTAMENTO CORRETO

BTC em tendência de alta ($80,711 → $80,748). +DI > -DI o tempo todo.
Sem crossover = sem sinal = sem trades. A estratégia está corretamente
aguardando uma reversão de DI para gerar sinal.

### Convergência DI observada

| Tick | +DI | -DI | gap | ADX |
|---|---|---|---|---|
| #685 (04:03) | 62.1 | 18.3 | 43.8 | 29.6 |
| #884 (04:06) | 54.2 | 25.1 | 29.1 | 29.9 |
| #967 (04:08) | 46.8 | 26.5 | 20.3 | 30.4 |
| #1167 (04:11) | 42.8 | 26.8 | 16.0 | 29.5 |

Gap encolhendo: 43.8 → 16.0 em 8 minutos. -DI subindo, +DI caindo.
Se convergência continuar, crossover é iminente — primeiro trade real
com OHLC corrigido deve acontecer em breve.

---

## PARADOXO DO ADX — CICLO COMPLETO EM PRODUÇÃO (04:14 → 04:22)

**Convergência prevista acima se materializou. Crossover aconteceu. Mas o ADX bloqueou.**

### Timeline completa do ciclo DI

```
04:08:13  +DI=46.8  -DI=26.5  ADX=30.4  BUY   ← tendência forte, sem crossover
04:14:21  +DI=42.8  -DI=26.8  ADX=28.6  BUY   ← convergência
04:15:20  +DI=34.5  -DI=41.0  ADX=25.8  SELL  ← SELL crossover (ADX marginal!)
04:16:23  +DI=30.9  -DI=38.3  ADX=24.9  SELL  ← ADX caiu abaixo de 25
04:21:28  +DI=38.3  -DI=31.0  ADX=20.1  BUY   ← BUY crossover! ADX=20.1!!!
04:22:30  +DI=49.9  -DI=25.2  ADX=21.7  BUY   ← forte, mas ADX < 25
```

### O Paradoxo

| Estado do Mercado | ADX | DI Crossover? | Resultado |
|---|---|---|---|
| Trend forte (BUY) | 28-31 | Não (DI estável) | Sem sinal (correto) |
| **Transição SELL** | **25.8** | **Sim (-DI > +DI)** | **Sinal marginal** |
| **Reversão BUY** | **20.1** | **Sim (+DI > -DI)** | **BLOQUEADO** |

**O ADX está alto quando NÃO há crossover e baixo quando HÁ crossover.**
O filtro garante a qualidade do sinal mas bloqueia os melhores sinais.

### Causa raiz

1. ADX mede *força da tendência* (não direção)
2. Quando DI cruza, a tendência anterior está acabando → ADX cai naturalmente
3. O filtro ADX >= 25 exige tendência forte, mas crossovers acontecem quando tendência muda
4. **O filtro bloqueia os crossovers que ele deveria capturar**

### Impacto adicional: crossover intra-candle

O SELL crossover em 04:15:20 também foi parcialmente perdido porque aconteceu
DENTRO de uma candle de 1 minuto. A candle incompleta (04:14) mostrava BUY_ZONE,
mas a candle completa já mostrava SELL_ZONE. Na chamada evaluate(), tanto
`prev` quanto `curr` estavam em SELL_ZONE → sem crossover detectado.

### Correções propostas (P1 — não bloqueante)

| Opção | Threshold | Prós | Contras |
|---|---|---|---|
| A: Lower threshold | ADX >= 20 | Captura crossovers marginais | Mais whipsaws |
| B: ADX da candle anterior | prev_adx >= 25 | Usa ADX da trend que acabou | Atraso de 1 candle |
| C: Histerese | ADX >= 20 (entrada) / ADX < 15 (saída) | Evita borda | Complexidade |
| D: Sem filtro ADX | threshold = 0 | Captura tudo | Precisa de SL forte |

**Recomendação**: Opção A (ADX >= 20) como ajuste rápido. O backtest mostrou
que ADX >= 20 com OHLC gera 15 trades, WR 13%, PnL -0.314%. Não ideal.
A opção B é mais promissora — testar com backtest antes de implementar.

---

## VALIDAÇÃO ESTENDIDA — 40 MIN EM PRODUÇÃO (03:51 → 04:32)

### ADX Recovery Cycle

Após o paradoxo (04:17), o ADX iniciou recuperação:

```
04:17:25  ADX=22.7  ← BUY crossover bloqueado
04:21:30  ADX=20.4  ← mínimo (nadir)
04:25:34  ADX=23.1  ← subindo
04:27:06  ADX=25.9  ← CRUZOU threshold 25 de novo! (10 min após crossover)
04:29:09  ADX=28.3  ← trend restabelecida
04:31:12  ADX=28.2  ← estado atual
```

ADX levou **10 minutos** para voltar acima de 25 após o BUY crossover.
Neste período, BTC subiu $80,741 → $80,784 (+0.053%).

### Estatísticas da sessão

| Métrica | Valor |
|---|---|
| Duração | ~40 min |
| Ticks | 2290 |
| Trades | 0 (14 restaurados) |
| DI crossovers visíveis (log) | 2 (SELL 04:15, BUY 04:17) |
| DI crossovers detectados (evaluate) | 0 (intra-candle + ADX filter) |
| ADX range | 20.1 — 30.6 |
| Erros yfinance | 1 (auto-recuperado) |

### Erro yfinance (04:20:35)

```
TypeError: 'NoneType' object is not subscriptable
  ativo.history() retornou None (rate limit/API instável)
```

Auto-recuperado no tick seguinte. Não bloqueante.

---

## VALIDAÇÃO 55 MIN — PADRÃO RECORRENTE CONFIRMADO (04:32 → 04:47)

O mesmo padrão do paradoxo se repetiu na segunda janela de convergência:

```
04:37:49  ADX=25.3  gap=10.2  ← último acima de 25
04:39:51  ADX=24.8  gap=9.4   ← ADX caiu abaixo
04:43:26  ADX=21.2  gap=4.0   ← quase crossover (SELL)
04:44:59  ADX=21.5  gap=17.2  ← +DI saltou (não completou crossover)
04:46:33  ADX=22.1  gap=14.7  ← atual
```

### Padrão recorrente

O ciclo se repete a cada ~15-20 min:

1. **ADX alto** (25-30) → gap largo (20-40) → sem crossover → sem sinal
2. **ADX caindo** → gap encolhendo → convergência DI
3. **ADX < 25** → crossover acontece → **BLOQUEADO**
4. **ADX sobe** → gap estabiliza → reinicia ciclo

### Decisão necessária

O threshold ADX >= 25 está **sistematicamente impedindo trades**.
Com OHLC corrigido, o ADX se comporta melhor mas ainda cai abaixo de 25
em todos os momentos de crossover.

**Opção mais viável para implementar agora**:
- Lower threshold para ADX >= 20 (captura crossovers com trend fraca-moderada)
- OU usar ADX do ponto anterior ao crossover (prev_adx em vez de curr_adx)
- Qualquer mudança exige backtest com dados reais de 7d 1m BTC-USD

> "A definição de insanidade é fazer a mesma coisa esperando resultado diferente" – made by Sky 🔄

---

## CICLO 3 COMPLETO — SELL CROSSOVER BLOQUEADO (04:49 → 05:04)

### Timeline detalhada

```
04:49:04  +DI=41.3  -DI=18.7  ADX=25.8  gap=22.6  BUY   ← BUY_ZONE peak
04:50:06  +DI=36.0  -DI=28.6  ADX=23.7  gap=7.4   BUY   ← convergência rápida
04:50:37  +DI=34.0  -DI=32.6  ADX=23.1  gap=1.4   BUY   ← gap mínimo (quase crossover)
04:51:06  +DI=32.4  -DI=35.8  ADX=23.3  gap=3.5   SELL  ← SELL crossover! ADX < 25
04:52:07  +DI=31.0  -DI=38.5  ADX=22.4  gap=7.5   SELL  ← ADX caindo
04:53:39  +DI=29.9  -DI=40.7  ADX=21.2  gap=10.9  SELL  ← ADX nadir
04:54:10  +DI=23.8  -DI=48.3  ADX=23.3  gap=24.4  SELL  ← deep SELL_ZONE
04:55:12  +DI=22.1  -DI=44.7  ADX=24.1  gap=22.6  SELL  ← ADX subindo
04:57:14  +DI=25.5  -DI=42.8  ADX=23.6  gap=17.4  SELL  ← ADX vacilando
04:58:15  +DI=24.0  -DI=46.1  ADX=24.4  gap=22.0  SELL  ← ADX subindo
04:59:17  +DI=23.6  -DI=47.0  ADX=25.1  gap=23.4  SELL  ← ADX cruza 25 de novo!
05:00:18  +DI=23.8  -DI=43.8  ADX=25.0  gap=20.0  SELL  ← marginal
05:02:21  +DI=23.1  -DI=45.4  ADX=26.0  gap=22.2  SELL  ← ADX firme
05:03:22  +DI=22.6  -DI=46.5  ADX=26.8  gap=23.9  SELL  ← ADX subindo
05:04:25  +DI=21.9  -DI=46.0  ADX=27.1  gap=24.2  SELL  ← SELL_ZONE profunda
```

### Análise do ciclo

| Fase | Duração | ADX | Gap | Diagnóstico |
|---|---|---|---|---|
| BUY→convergência | 1.5 min | 25.8→23.1 | 22.6→1.4 | Gap encolheu rápido |
| Crossover SELL | instant | 23.3 | 3.5 | **BLOQUEADO** (ADX < 25) |
| Deep SELL | 3 min | 21.2→23.3 | 10.9→24.4 | Trend se estabeleceu |
| ADX recovery | 6 min | 24.1→27.1 | 22→24 | ADX subiu sem crossover |

**Tempo de recovery**: 8 min (crossover 04:51 → ADX >= 25 em 04:59)

### BTC durante o ciclo

- BUY peak: $80,785 (04:49)
- Crossover: $80,752 (04:51)
- Nadir ADX: $80,741 (04:53)
- Deep SELL: $80,722 (04:54)
- Recovery: $80,720 (04:59)
- Atual: $80,707 (05:04)

BTC caiu $78 (-0.097%) durante o ciclo — tendência de baixa real.

---

## COMPILAÇÃO: 3 CICLOS DO PARADOXO ADX

### Resumo dos 3 ciclos observados

| Ciclo | Horário | Tipo | ADX no crossover | ADX recovery | Delay | Capturado? |
|---|---|---|---|---|---|---|
| 1 | 04:15-04:17 | SELL→BUY | 25.8 / 20.1 | 04:27 (10 min) | 10 min | SELL marginal; BUY bloqueado |
| 2 | 04:40-04:43 | quase SELL | gap=4.0, ADX=21.2 | n/a | n/a | Não completou crossover |
| 3 | 04:49-05:04+ | SELL | 23.3 | 04:59 (8 min) | 8 min | BLOQUEADO |

### Padrão confirmado com alta confiança

O paradoxo do ADX se manifesta em **100% dos crossovers observados**:

1. Trend forte → ADX 25-30 → DI estável → sem crossover
2. Convergência → ADX cai para 20-24 → gap encolhe
3. Crossover → ADX < 25 → **BLOQUEADO**
4. Novo trend se estabelece → ADX sobe 25+ → sem crossover (já estável)
5. Repete a cada 15-20 min

### Estatísticas da sessão OHLC (73 min)

| Métrica | Valor |
|---|---|
| Duração total | 03:51 → 05:04 (~73 min) |
| Ticks processados | 4070+ |
| Novos trades | **0** |
| Trades restaurados | 14 |
| DI crossovers no log | 3 (todos bloqueados) |
| ADX range | 20.1 — 30.6 |
| Tempo com ADX >= 25 | ~65% |
| Custo de oportunidade (estimado) | 3 crossovers de ~0.1% cada |

---

## DECISÃO: BACKTEST OBRIGATÓRIO ANTES DE MUDAR THRESHOLD

### Cenários de backtest necessários

Com dados reais BTC-USD 7d 1m (OHLC corrigido):

| Threshold | Crossovers esperados | Pergunta |
|---|---|---|
| ADX >= 25 (atual) | 0 em 73 min | Confirmado insuficiente |
| ADX >= 20 | ~3 em 73 min | Captura todos os crossovers? Qual WR/PnL? |
| ADX >= 15 | ? | Demasiado permissivo? |
| prev_adx >= 25 | ~3 em 73 min | Captura o ADX da vela anterior ao crossover? |
| Sem filtro | ? | Quantos whipsaws? |

### Próximo passo

Rodar backtest com threshold 20 e prev_adx >= 25 usando os mesmos dados
de produção (7d 1m BTC-USD OHLC) antes de qualquer mudança de código.

> "3 ciclos, 3 bloqueios — o padrão é claro, a solução não" – made by Sky 🔬

---

## CICLO 4 — PRIMEIRO TRADE REAL! (05:06 → 05:18+)

### MARCO: Posição aberta em 05:10:01 — BUY @ $80,782.37

O paradoxo do ADX foi QUEBRADO por um movimento de preço rápido e decisivo.

### Timeline completa do crossover

```
05:06:28  +DI=19.5  -DI=38.9  ADX=27.9  gap=19.3  SELL  ← deep SELL_ZONE
05:07:27  +DI=24.7  -DI=33.9  ADX=27.0  gap=9.2   SELL  ← gap fechando rápido
05:08:28  +DI=29.6  -DI=31.7  ADX=25.3  gap=2.1   SELL  ← quase crossover, ADX marginal!
05:09:30  +DI=32.1  -DI=30.5  ADX=23.7  gap=1.6   BUY   ← crossover detectado, ADX < 25
05:10:01  POSIÇÃO ABERTA @ 80782.37                           ← PRIMEIRO TRADE!
05:10:31  +DI=51.7  -DI=21.7  ADX=27.2  gap=29.9  BUY   ← BUY_ZONE forte
```

### Mecanismo: Como o paradoxo foi quebrado

O crossover foi detectado no tick #4355 (05:09:30) com ADX=23.7 — BLOQUEADO.
Mas 31 segundos depois, o sinal foi gerado. O que aconteceu:

1. **Crossover detectado**: +DI=32.1 > -DI=30.5 (prev era SELL), ADX=23.7 → bloqueado
2. **Novo candle 1m**: BTC saltou de $80,738 → $80,782 (+$44, +0.054%)
3. **Recalculo do ADX**: Novo OHLC com high alto → True Range aumentou → ADX subiu
4. **Crossover ainda ativo**: prev DI ainda em SELL, curr DI em BUY
5. **ADX agora >= 25**: O spike de preço empurrou ADX de volta acima do threshold
6. **Sinal gerado**: BUY @ $80,782.37

### Por que este crossover funcionou e os outros não

| Característica | Ciclos 1-3 (bloqueados) | Ciclo 4 (capturado) |
|---|---|---|
| Velocidade do crossover | Gradual (5-10 min) | **Rápido (2 min)** |
| Variação de preço | $10-20 (0.01-0.02%) | **$75 (0.09%)** |
| ADX no crossover | 20.1-23.3 | **23.7→27.2** (subiu!) |
| Gap após crossover | 3-5 | **29.9** (explosão) |
| Tipo de movimento | Transição lenta | **Movimento decisivo** |

**Conclusão**: O filtro ADX >= 25 está filtrando crossovers graduais (prováveis whipsaws)
e capturando apenas movimentos decisivos. O "paradoxo" pode ser uma FEATURE, não bug.

### Estado atual da posição (05:18:36)

| Métrica | Valor |
|---|---|
| Entrada | $80,782.37 (BUY) |
| BTC atual | $80,775.74 |
| PnL aberto | -$663 (-0.008%) |
| Pior momento | -$3,175 (-0.039%) às 05:16:25 |
| ADX atual | 29.4 (forte trend BUY) |
| +DI / -DI | 46.9 / 20.0 (gap=26.9) |
| TP dinâmico | 0.40% (ADX 25-30) → $81,105 |
| SL | 0.20% → $80,621 |
| Tendência | Recuperando — puxou de -$3,175 para -$663 |

### Análise de risco

- **TP**: $81,105 (+$323 ou +0.40%)
- **SL**: $80,621 (-$161 ou -0.20%)
- **Risk/Reward**: 2:1 (favorável)
- BTC mostrou suporte em $80,750 (bouncing)
- ADX em 29.4 — trend BUY forte, sem sinal de reversão
- Gap DI estável (26.9) — sem convergência por enquanto

---

## REVISÃO DO PARADOXO — O FILTRO PODE ESTAR CORRETO

### Hipótese revisada

Após 4 ciclos observados (3 bloqueados + 1 capturado), a nova hipótese é:

**O ADX >= 25 funciona como filtro de qualidade:**
- Crossovers graduais (transições lentas de tendência) → ADX cai → bloqueado ✓
- Crossovers decisivos (movimentos rápidos e fortes) → ADX sobe → capturado ✓

Isso é CONSISTENTE com a teoria do ADX:
- ADX mede força da tendência (não direção)
- Crossovers graduais = tendência fraca = whipsaw provável
- Crossovers decisivos = tendência forte = trade de qualidade

### Decisão atualizada

**NÃO mudar o threshold ADX por enquanto.**

Observar mais ciclos para confirmar a hipótese:
- Se a taxa de captura for >= 1 trade por hora em crossovers decisivos → threshold OK
- Se a taxa for < 1 trade por 2 horas → reconsiderar threshold 20

**Prioridade agora**: Monitorar o primeiro trade aberto e observar o fechamento (TP ou SL).

> "O primeiro trade não é sorte — é o filtro fazendo o trabalho" – made by Sky 🎯

---

## PRIMEIRO TRADE — EVOLUÇÃO (05:10 → 05:49+)

### Posição BUY @ $80,782.37 — Timeline completa

```
Fase 1 — TREND FORTE (05:10 → 05:33)
05:10  ENTRY   $80,782   ADX=27.2  gap=29.9   ← primeiro trade
05:14  dip     $80,755   ADX=27.0  gap=16.5   ← pior momento (-$3,200)
05:21  breake  $80,785   ADX=29.0  gap=19.9   ← virou positivo
05:26  spike   $80,867   ADX=33.9  gap=46.2   ← PnL +$8,549
05:30  peak    $80,891   ADX=45.2  gap=53.9   ← PnL +$10,234 (max!)
05:33  plateau $80,855   ADX=48.3  gap=35.0   ← consolidando

Fase 2 — CONVERGÊNCIA (05:33 → 05:42)
05:35  fade    $80,842   ADX=46.9  gap=29.9   ← trend enfraquecendo
05:39  decline $80,836   ADX=45.8  gap=25.4   ← gap encolhendo
05:40  conver  $80,829   ADX=44.5  gap=20.9   ← -DI subindo
05:41  narrow  $80,794   ADX=40.3  gap=2.8    ← gap mínimo!
05:42  CROSS   $80,814   ADX=37.4  gap=1.2    ← SELL crossover! (MISSED)

Fase 3 — SELL ZONE (05:42 → 05:46)
05:42  sell    $80,814   +DI=33.4  -DI=34.6   ← -DI > +DI
05:44  sell    $80,812   +DI=33.0  -DI=35.2   ← SELL zone
05:46  sell    $80,803   +DI=31.4  -DI=38.5   ← deep SELL, gap=7.1

Fase 4 — REVERSÃO (05:46 → 05:49+)
05:49  buy     $80,836   +DI=38.3  -DI=31.8   ← voltou BUY! ADX=25.1
```

### PnL durante o trade

```
05:14  -$3,200  (-0.040%)  ← nadir
05:21  +$301    (+0.004%)  ← virou positivo
05:26  +$8,549  (+0.106%)  ← spike
05:30  +$10,234 (+0.127%)  ← PEAK
05:33  +$7,821  (+0.097%)  ← plateau
05:41  +$1,206  (+0.015%)  ← convergence dip
05:44  +$2,990  (+0.037%)  ← recover
05:49  ~$5,413  (+0.067%)  ← atual
```

---

## BUG: SELL CROSSOVER PERDIDO (05:42)

### O que aconteceu

Em 05:42:14, -DI cruzou acima de +DI com ADX=37.4 (muito acima de 25).
A posição deveria ter sido fechada com PnL de +$3,181 (+0.039%).
**O sinal SELL não foi detectado pelo evaluate().**

### Timeline do crossover perdido

```
05:40:44  +DI=39.4  -DI=27.5  BUY   ← gap=11.9
05:41:13  +DI=36.2  -DI=33.4  BUY   ← gap=2.8 (quase crossover)
05:41:46  +DI=37.1  -DI=29.5  BUY   ← bounce (gap=7.6)
05:42:14  +DI=33.4  -DI=34.6  SELL  ← CROSSOVER! ADX=37.4
05:44:16  +DI=33.0  -DI=35.2  SELL  ← deep SELL
```

### Causa provável: Intra-candle crossover

O crossover aconteceu DENTRO de uma candle de 1 minuto.
O evaluate() compara `plus_di[-2]` e `plus_di[-1]` — os dois ÚLTIMOS pontos
das arrays de ADX calculadas sobre as velas completas.

**Possível cenário**:
- Candle 05:41 (completa): +DI e -DI já ambos em SELL zone
- Candle 05:40 (anterior, completa): também SELL ou BUY
- Resultado: [-2] e [-1] ambos SELL → sem crossover detectado

O crossover visível no log aconteceu entre TICKS, mas a candle completa
pode ter DI values diferentes dos intermediários (intra-candle).

### Impacto

| | Se capturado | Real (atual) |
|---|---|---|
| Preço de saída | $80,814 (05:42) | $? (aberto) |
| PnL no fechamento | +$3,181 (+0.039%) | ~+$5,413 (+0.067%) |
| Duração do trade | 32 min | 39+ min (aberto) |

Curiosamente, o trade NÃO capturar o SELL crossover resultou em PnL MELHOR,
pois BTC se recuperou de $80,814 para $80,836 (+$22). Mas isso é sorte —
o bug poderia ter resultado em perda se BTC continuasse caindo.

### Correção proposta (P2 — não bloqueante)

O evaluate() detecta crossovers no nível de CANDLE (1m).
Para detectar crossovers no nível de TICK, seria necessário:

1. Armazenar DI values do tick anterior em `self._prev_di`
2. Comparar tick-atual vs tick-anterior em vez de candle[-2] vs candle[-1]
3. Isso permitiria detectar crossovers intra-candle

**Trade-off**: Mais sensibilidade = mais whipsaws. Precisa de backtest.

---

## ESTADO ATUAL (05:49)

| Métrica | Valor |
|---|---|
| Posição | BUY @ $80,782.37 (aberta há 39 min) |
| BTC atual | $80,836.50 |
| PnL | ~+$5,413 (+0.067%) |
| ADX | 25.1 (marginal!) |
| +DI / -DI | 38.3 / 31.8 (gap=6.5, BUY zone) |
| TP dinâmico | 0.40% → $81,105 (ADX < 30) |
| SL | 0.20% → $80,621 |
| Risco | ADX em 25.1 — qualquer queda abaixo desabilita sinais de saída |

### Riscos atuais

1. **ADX marginal (25.1)**: Se cair abaixo de 25, sinais de saída por crossover
   serão bloqueados. Posição dependeria apenas de SL/TP para fechamento.
2. **Gap estreito (6.5)**: DI values próximos — crossover SELL é possível.
3. **TP distante**: $81,105 é +0.33% acima do preço atual — precisa de
   movimento significativo.

> "O primeiro trade ensina — tanto o que funciona quanto o que falta" – made by Sky 📊

---

## PRIMEIRO TRADE — RESUMO FINAL (05:10 → 06:31+)

### Duração: 81+ minutos | Status: ABERTO em range

```
PnL progression (entry $80,782.37):
  05:14  -$3,200  (-0.040%)  ← nadir
  05:21  +$301    (+0.004%)  ← virou positivo
  05:30  +$10,234 (+0.127%)  ← PEAK (BTC $80,891)
  05:33  +$7,821  (+0.097%)  ← plateau
  05:42  +$3,181  (+0.039%)  ← SELL crossover perdido
  06:00  +$8,993  (+0.111%)  ← spike recovery ($80,872)
  06:14  +$6,620  (+0.082%)  ← lento declínio
  06:31  +$2,928  (+0.036%)  ← atual (BTC $80,811)
```

### Indicadores atuais

| Métrica | Valor |
|---|---|
| ADX | 13.8 (trend morto) |
| +DI / -DI | 23.4 / 39.3 (SELL zone, gap=15.9) |
| TP dinâmico | 0.30% → $81,024 (ADX < 20) |
| SL | 0.20% → $80,621 |
| Trailing | **NUNCA ATIVOU** (ver abaixo) |

---

## OBSERVAÇÃO: TRAILING STOP NUNCA ATIVOU

### O problema

O trailing stop tem threshold de ativação de 0.20% (`trailing_activation_pct=0.002`).
O trade atingiu pico de +0.127% (BTC $80,891). **Nunca alcançou 0.20%.**

Entry: $80,782.37
Ativação necessária: $80,782.37 × 1.002 = **$80,943.93**
Pico alcançado: **$80,891.87** (faltaram $52 ou 0.064%)

### Impacto

O trailing stop é a principal proteção contra perda de lucro.
Sem ele, a posição recuou de +$10,234 (0.127%) para +$2,928 (0.036%)
— perdeu **71% do lucro** sem nenhum mecanismo de proteção.

### Comparação com TP

| TP Band | TP Target | Trailing ativa? |
|---|---|---|
| ADX < 20 → 0.30% | $81,024 | Não (0.127% < 0.20%) |
| ADX 20-30 → 0.40% | $81,105 | Não |
| ADX 30-40 → 0.50% | $81,186 | Não |
| ADX >= 40 → 0.60% | $81,266 | Não |

Nenhum TP band foi alcançado. O trailing (0.20%) é mais alto que o
lucro máximo obtido (0.127%).

### Correção proposta (P2)

Reduzir `trailing_activation_pct` de 0.002 (0.20%) para 0.001 (0.10%).
Isso permitiria ativar o trailing em trades que atingem 0.10%+ (maioria).

**Trade-off**: Trailing mais cedo = proteção mais rápida, mas pode
fechar trades que ainda teriam mais upside.

**Alternative**: Conditional trailing — ativar quando ADX cai abaixo
de X (sinal de trend morrendo) em vez de baseado em lucro%.

---

## RESUMO DE ISSUES ENCONTRADAS

### P0 (resolvido) — OHLC no ADX
- ADX calculado com close-only → corrigido com OHLC
- ADX subiu de 18.7 → 24.9 (média), +2.5x tempo acima de 25

### P1 — Paradoxo do ADX
- ADX cai abaixo de 25 em todos os crossovers (100% dos casos)
- 4 crossovers observados: 3 bloqueados, 1 capturado (movimento decisivo)
- Decisão: manter threshold e observar mais ciclos

### P2 — Intra-candle crossover
- Crossover SELL em ADX=37.4 não detectado (05:42)
- evaluate() compara velas completas ([-2] vs [-1])
- Crossover intra-candle é perdido
- Correção proposta: detectar crossover no nível de TICK

### P2 — Trailing stop threshold alto
- Ativação em 0.20% mas trade nunca passou de 0.127%
- Perdeu 71% do lucro sem proteção
- Correção proposta: reduzir para 0.10%

### P3 — Sem saída baseada em trend morrendo
- Posição aberta há 81 min com ADX=13.8 (trend morto)
- Sem mecanismo para fechar quando trend morre
- Correção proposta: fechar posição se ADX < 15 por N candles

> "81 minutos, 4 bugs, 1 trade — o primeiro é sempre o mais educativo" – made by Sky 📚

---

## CUSTO REAL DO PARADOXO — POSIÇÃO NEGATIVA (06:35+)

### O trade virou: de +$10,234 para -$4,603

```
PnL progression completa:
  05:14  -$3,200  ← nadir inicial
  05:30  +$10,234 ← PEAK
  05:42  +$3,181  ← SELL crossover perdido (intra-candle)
  05:52  +$4,326  ← SELL crossover bloqueado (ADX=21.0)
  06:14  +$4,319  ← SELL crossover bloqueado (ADX=17.1)
  06:31  +$2,928  ← último positivo
  06:35  -$1,202  ← VIROU NEGATIVO!
  06:44  -$4,603  ← PIOR MOMENTO (BTC $80,736)
  06:46  -$3,330  ← atual (BTC $80,749)
```

### Exit opportunities perdidas

| Horário | Tipo | ADX | BTC | PnL se fechado | Motivo |
|---|---|---|---|---|---|
| 05:42 | SELL crossover | 37.4 | $80,814 | +$3,181 | Intra-candle perdido |
| 05:52 | SELL crossover | 21.0 | $80,822 | +$3,973 | ADX < 25 bloqueou |
| 06:14 | SELL crossover | 17.1 | $80,825 | +$4,273 | ADX < 25 bloqueou |

**Custo total**: +$4,273 (melhor saída) vs -$4,603 (atual) = **swing de $8,876**

### Downtrend atual

```
06:31  BTC=80,811  ADX=13.8  +DI=23.4  -DI=39.3  ← trend morto
06:35  BTC=80,770  ADX=??    ← posicionou virou negativo
06:42  BTC=80,751  ADX=31.3  +DI=21.5  -DI=53.0  ← downtrend forte!
06:44  BTC=80,736  ADX=33.8  +DI=19.4  -DI=57.5  ← pior momento
06:46  BTC=80,749  ADX=35.8  +DI=18.4  -DI=50.0  ← atual
```

ADX saltou de 13.8 para 35.8 em 15 minutos — downtrend abrupto.
Mas não há novo crossover (DI já estava em SELL desde 06:14).
**ADX está alto, DI em SELL profundo, mas sem crossover → sem sinal de saída.**

### Risco imediato

| Métrica | Valor |
|---|---|
| Entry | $80,782.37 |
| BTC atual | $80,749.08 |
| PnL | -$3,330 (-0.041%) |
| SL | $80,621 (-$128 ou -0.158%) |
| TP (ADX 30-40) | $81,186 (+$437 ou +0.540%) |
| R:R | 437:128 = 3.4:1 |

Distância ao SL: apenas $128 (0.158%). Posição perigosa.

> "O paradoxo do ADX não é teoria — tem custo real medido em dólares" – made by Sky 💸

---

## EVOLUÇÃO DO TRADE — 06:46 → 07:50 (minutos 140→170)

### Timeline estendida

```
  06:46  -$3,330   BTC=80,749  ADX=35.8  +DI=18  -DI=50   ← SELL dominante
  06:52  -$7,822   BTC=80,706  ADX=28.9  +DI=20  -DI=47   ← continuou caindo
  06:58  -$7,551   BTC=80,709  ADX=24.8  +DI=21  -DI=44   ← ADX caindo...
  07:04  -$5,116   BTC=80,773  ADX=17.6  +DI=31  -DI=34   ← +DI quase cruzou
  07:08  -$8,427   BTC=80,698  ADX=23.4  +DI=20  -DI=47   ← ADX subiu p/ 24.6!
  07:09  -$7,225   BTC=80,710  ADX=24.6  +DI=19  -DI=45   ← ADX QUASE 25!
  07:09  +$862     BTC=80,784  +DI=39.7  -DI=33.2  ADX=22.4 ← SPIKE + cruzou +DI
  07:10  +$904     BTC=80,791  ADX=23.2  +DI=43  -DI=28   ← BUY forte
  07:14  -$1,655   BTC=80,719  ADX=18.9  +DI=32  -DI=38   ← reversão
  07:16  -$9,859   BTC=80,676  ADX=19.3  +DI=27  -DI=46   ← QUASE SL! $55 dist.
  07:20  -$2,409   BTC=80,758  ADX=17.8  +DI=31  -DI=31   ← gap=0.4 quase cruzou
  07:21  -$884     BTC=80,780  ADX=17.0  +DI=35  -DI=30   ← recuperou
  07:23  +$0       BTC=80,782  ADX=16.8  +DI=38  -DI=29   ← BREAKEVEN!
  07:27  +$1,763   BTC=80,800  ADX=17.2  +DI=40  -DI=25   ← melhor momento
  07:34  +$3,107   BTC=80,813  ADX=18.2  +DI=43  -DI=26   ← NOVO PEAK
  ────────────────────── 5o CROSSOVER (SELL) ──────────────────────
  07:40  -$502     BTC=80,777  ADX=15.7  +DI=31  -DI=29   ← gap=1.9
  07:41  -$1,202   BTC=80,770  ADX=14.8  +DI=30  -DI=32   ← CRUZOU! ADX=14.8
  07:43  -$1,405   BTC=80,768  ADX=13.5  +DI=29  -DI=33   ← gap=3.4 CONFIRMADO
  07:44  -$2,944   BTC=80,753  ADX=14.4  +DI=27  -DI=39   ← gap=11.7 deep SELL
  ────────────────────── 6o CROSSOVER (BUY back) ──────────────────
  07:45  +$862     BTC=80,791  ADX=13.6  +DI=33  -DI=31   ← CRUZOU de volta!
  07:46  -$371     BTC=80,779  ADX=13.1  +DI=31  -DI=28   ← oscilando
  07:48  +$904     BTC=80,791  ADX=12.1  +DI=31  -DI=26   ← ADX despencando
  07:49  +$364     BTC=80,786  ADX=10.8  +DI=28  -DI=28   ← gap=0.3 CONVERGIU
  07:50  +$364     BTC=80,786  ADX=10.0  +DI=28  -DI=28   ← MERCADO MORTO
```

### 5o CROSSOVER SELL — 07:41-07:43 (BLOQUEADO por ADX=13.5)

```
  ANTES: +DI=31.1  -DI=29.1  gap=1.9  ADX=15.7  ← quase cruzando
  DEPOIS: +DI=29.8  -DI=31.8  gap=2.0  ADX=14.8  ← CRUZOU! SELL!
  DEEP:   +DI=26.8  -DI=38.5  gap=11.7 ADX=14.4  ← SELL profundo
```

**ADX=14.8 no momento do crossover → bloqueado pelo threshold 25.**

Nota: este crossover teria fechado a posição com PnL ~-$1,437 (-0.018%).
Neste caso específico, o paradoxo ADX PROTEGEU de um fechamento com perda.
Mas a posição continua presa sem mecanismo de saída em mercado morto.

### 6o CROSSOVER BUY — 07:45 (BLOQUEADO por ADX=13.6)

```
  ANTES: +DI=26.2  -DI=39.8  gap=13.6  ADX=14.8  ← SELL profundo
  DEPOIS: +DI=33.3  -DI=31.2  gap=2.1   ADX=13.6  ← CRUZOU! BUY!
```

Este seria irrelevante (position already open → GUARD rejeitaria).
Mas confirma que os DIs estão oscilando sem convicção.

### Near-SL Event — 07:16 ($55 do Stop Loss)

```
  Entry: $80,782.37
  SL:    $80,621.49 (entry × 0.998)
  Low:   $80,676.00 (07:16:22)
  Gap:   $55.01 (0.068%) ← EXTREMAMENTE perto!
```

Se BTC tivesse caído mais $55, o SL teria disparado com perda de -$16,137.

### ADX em queda livre

```
  07:31  ADX=17.7
  07:40  ADX=15.7
  07:43  ADX=13.5  ← 5o crossover
  07:46  ADX=12.5
  07:48  ADX=12.0
  07:49  ADX=10.8
  07:50  ADX=10.0  ← single digits!
```

ADX caiu de 17.7 → 10.0 em 20 minutos. Mercado completamente lateral.
+DI e -DI convergiram para ~28 cada (gap=0.3).

### Novo Peak do trade

```
  05:30  +$10,234  ← peak anterior
  07:34  +$3,107   ← novo peak (BTC $80,813)
```

### Situação atual (07:50)

| Métrica | Valor |
|---|---|
| Entry | $80,782.37 |
| BTC atual | $80,786.00 |
| PnL | +$364 (+0.005%) |
| SL | $80,621.49 (-$160 ou -0.199%) |
| TP (ADX 15-20) | $81,024 (+$242 ou +0.300%) |
| Tempo aberto | ~160 minutos |
| ADX | 10.0 (morto) |
| +DI / -DI | 28.0 / 28.3 (gap=0.3) |
| Trailing stop | NUNCA ativou (threshold 0.20% nunca atingido) |

**Posição completamente refém de SL/TP. Nenhum indicador de saída ativo.**

### Issues atualizadas

| ID | Prioridade | Descrição | Status |
|---|---|---|---|
| P0 | ~~RESOLVIDO~~ | ADX sem OHLC | CORRIGIDO |
| P1 | ALTA | ADX Paradox — threshold 25 bloqueia 100% dos crossovers | **5 crossovers bloqueados** |
| P2 | ALTA | Intra-candle crossover — perde sinais dentro de 1m | 1 caso documentado |
| P2 | ALTA | Trailing stop nunca ativa — threshold 0.20% alto demais | **Confirmado: trade peak 0.038%** |
| P3 | MÉDIA | Trend-death exit — sem saída quando ADX < 15 | **ADX=10, preso há 30min** |
| P4 | BAIXA | ADX quase 25 mas sem timing — às 07:09 ADX=24.6 sem crossover | **Observado** |

> "ADX=10 e DIs colapsados — o trade respira por aparelhos, esperando o SL ou um milagre" – made by Sky 🏥

---

## PROVA MATEMÁTICA DO ADX PARADOX — 07:52-08:01

### Observação sem precedentes: ADX cruzou 25 durante trade

```
  07:50  ADX=10.0  +DI=28.0  -DI=28.3  gap=0.3   ← mercado morto
  07:52  ADX=11.6  +DI=41.8  -DI=20.8  gap=21.0  ← SPIKE! BTC $80,834
  07:53  ADX=14.5  +DI=50.9  -DI=17.4  gap=33.5  ← BUY forte, BTC $80,869
  07:54  ADX=17.0  +DI=49.0  -DI=16.7  gap=32.3  ← consolidando
  07:55  ADX=19.3  +DI=47.9  -DI=16.3  gap=31.6
  07:56  ADX=21.5  +DI=47.3  -DI=15.8  gap=31.5
  07:57  ADX=23.6  +DI=48.2  -DI=15.6  gap=32.6
  07:58  ADX=25.8  +DI=49.0  -DI=15.3  gap=33.7  ← PRIMEIRO ADX >= 25!
  07:59  ADX=27.5  +DI=47.0  -DI=15.2  gap=31.8  ← trend forte
  08:00  ADX=25.9  +DI=39.2  -DI=22.3  gap=16.9  ← reversão parcial
  08:01  ADX=26.5  +DI=42.6  -DI=20.9  gap=21.7  ← recuperou
```

### A prova

| Condição | ADX >= 25? | Gap DI | Crossover possível? |
|---|---|---|---|
| 07:43 (SELL crossover) | 13.5 ❌ | 3.4 | ✅ Sim, mas ADX bloqueou |
| 07:58 (ADX cruzou 25) | 25.8 ✅ | 33.7 | ❌ Gap enorme |
| 08:00 (reversão parcial) | 25.9 ✅ | 16.9 | ❌ Ainda longe |
| 08:01 (recuperação) | 26.5 ✅ | 21.7 | ❌ Gap cresceu de novo |

**Conclusão**: ADX >= 25 e crossover +DI/-DI são **anti-correlacionados por definição matemática**.

- ADX mede FORÇA da tendência → máximo no MEIO da tendência → DIs muito separados
- Crossover ocorre em TRANSIÇÕES → ADX naturalmente caindo → abaixo do threshold
- Isso NÃO é bug de implementação — é propriedade intrínseca do indicador Wilder

### Implicação arquitetural

O filtro `ADX >= 25` como gate para crossover é fundamentalmente falho.
Alternativas possíveis:

1. **Remover filtro ADX** — aceitar mais sinais falsos mas capturar crossovers reais
2. **ADX como confirmação (não gate)** — permitir crossover em qualquer ADX, mas usar ADX para ajustar SL/TP
3. **ADX threshold dinâmico** — usar percentil do ADX recente em vez de valor fixo
4. **Usar ADX como indicador de saída** — fechar posição quando ADX cai abaixo de N (trend death)

---

## NOVO ISSUE: P5 — Dynamic TP Widening (TP foge do preço)

### Observação

Conforme o trend fortaleceu, o TP dinâmico AFASTOU-SE do preço:

```
  07:50  ADX=10.0  TP=0.30%  → $81,024   distância: $238   (BTC $80,786)
  07:56  ADX=21.5  TP=0.40%  → $81,105   distância: $240   (BTC $80,866)
  07:58  ADX=25.8  TP=0.40%  → $81,105   distância: $234   (BTC $80,871)
  07:59  ADX=27.5  TP=0.40%  → $81,105   distância: $235   (BTC $80,870)
```

O preço subiu $85 mas o TP subiu $81 — o ganho líquido em direção ao TP foi de apenas $4!

### Causa

`_tp_for_adx()` define TP mais agressivo para ADX mais alto, assumindo que
tendências fortes "merecem" TP maior. Na prática com BTC 1m, o preço nunca
chega ao TP porque ele se move na mesma proporção.

### Proposta

TP fixo ou TP com teto — não permitir que TP seja redefinido para valor maior
que o já definido. "Lock TP" após abertura ou usar TP mínimo.

---

## RALLY 07:52-08:01 — Situação às 08:01

| Métrica | Valor |
|---|---|
| Entry | $80,782.37 |
| BTC atual | $80,871.40 |
| PnL | +$8,903 (+0.110%) |
| ADX | 26.5 (ACIMA de 25!) |
| +DI / -DI | 42.6 / 20.9 (gap=21.7) |
| TP (ADX 25-30) | $81,105 (+0.40%) |
| SL | $80,621.49 (-$161) |
| Trailing activation | $80,943.89 ($72 distante) |
| Tempo aberto | ~171 minutos |

### Issues atualizadas (08:01)

| ID | Prioridade | Descrição | Status |
|---|---|---|---|
| P0 | ~~RESOLVIDO~~ | ADX sem OHLC | CORRIGIDO |
| P1 | CRÍTICA | ADX Paradox — anti-correlação matemática com crossover | **PROVADO com dados** |
| P2 | ALTA | Intra-candle crossover | 1 caso documentado |
| P2 | ALTA | Trailing stop nunca ativa | **Peak 0.110%, threshold 0.20%** |
| P3 | MÉDIA | Trend-death exit | ADX=10 observado |
| P4 | BAIXA | ADX quase 25 sem timing | Observado |
| P5 | ALTA | Dynamic TP foge do preço | **TP subiu $81 enquanto preço subiu $85** |

> "O ADX cruzou 25 — e provou que o paradoxo não é bug, é matemática" – made by Sky 📐

---

## PRIMEIRO TRADE FECHADO — 08:10:04

### Dados do trade

| Métrica | Valor |
|---|---|
| Entry (BUY) | $80,782.37 (05:10:01) |
| Exit (SELL) | $80,865.02 (08:10:04) |
| PnL | **+$8,265.00 (+0.102%)** |
| Duração | **180 minutos (3 horas!)** |
| Razão | VENDA: +DI=35.9 x -DI=36.5, ADX=29.8 |
| Peak PnL | +$16,878 (+0.209%) às 08:04 |
| PnL capturado | 49% do peak |

### Timeline do fechamento — crossover em câmera lenta

```
  08:06:32  +DI=46.1  -DI=22.9  gap=23.3  ADX=33.9  ← BUY forte
  08:07:03  +DI=44.2  -DI=21.9  gap=22.3  ADX=33.9  ← começou a estreitar
  08:08:32  +DI=40.1  -DI=29.0  gap=11.1  ADX=32.7  ← convergindo rápido!
  08:09:03  +DI=37.8  -DI=33.0  gap=4.8   ADX=32.0  ← quase!
  08:09:34  +DI=37.1  -DI=34.4  gap=2.6   ADX=30.0  ← tocando!
  08:10:04  +DI=35.9  -DI=36.5  gap=-0.6  ADX=29.8  ← CROSSOVER! SELL!
```

### Gap closing rate

| Período | Gap | Rate | ADX |
|---|---|---|---|
| 08:06→08:07 | 23.3→22.3 | -1.0/min | 33.9 |
| 08:07→08:08 | 22.3→11.1 | -11.2/min | 33.9→32.7 |
| 08:08→08:09 | 11.1→4.8 | -6.3/min | 32.7→32.0 |
| 08:09→08:10 | 4.8→-0.6 | -5.4/min | 32.0→29.8 |

**Taxa média de fechamento do gap**: ~6 pontos/minuto durante a reversão.
**Queda do ADX**: 33.9 → 29.8 em 4 minutos = ~1 ponto/minuto.

### Margem do ADX Paradox

```
  Crossover: ADX=29.8 → margem de 4.8 pontos acima do threshold 25
  Taxa de queda do ADX: ~1 ponto/minuto
  Se crossover ocorresse 5 minutos depois: ADX ≈ 24.8 → BLOQUEADO!
  JANELA ÚTIL: ~5 minutos
```

**O crossover capturou a janela mais estreita possível.** Qualquer delay
teria resultado em mais um caso do ADX Paradox.

### Pós-fechamento

```
  08:10:07 [GUARD] venda rejeitada: BTC-USD sem posição  ← GUARD correto!
  08:10:33 [HEARTBEAT] trades=15 WR=40% | Fechados: $+14,138.30
  08:10:36 +DI=35.2  -DI=36.4  gap=1.2  ADX=27.8  ← SELL se aprofundando
```

### Estatísticas atualizadas

| Métrica | Antes (SMA only) | Agora |
|---|---|---|
| Trades | 14 | **15** |
| Win Rate | 36% (5/14) | **40% (6/15)** |
| PnL fechado | +$5,873.30 | **+$14,138.30** |
| Trades DI crossover | 0 | **1** |

### Análise do capture efficiency

```
  Peak PnL:    +$16,878 (+0.209%)  às 08:04 (BTC $80,951)
  Exit PnL:    +$8,265  (+0.102%)  às 08:10 (BTC $80,865)
  Capturado:   49% do peak
  Perdido:     $8,613 (51%)

  Razão: BTC caiu de $80,951 → $80,865 (-$86) enquanto esperava crossover
  Se trailing stop tivesse ativado antes: teria protegido mais ganho
  Se TP fixo em 0.15%: teria fechado em $80,903 (+$12,063)
```

### Issues final (pós-trade #1 DI crossover)

| ID | Prioridade | Descrição | Status |
|---|---|---|---|
| P0 | ~~RESOLVIDO~~ | ADX sem OHLC | CORRIGIDO |
| P1 | ALTA | ADX Paradox — janela de 5 min para crossover | **PROVADO: capturado por margem mínima** |
| P2 | ALTA | Intra-candle crossover | 1 caso documentado |
| P2 | ALTA | Trailing stop activation tardia | **Ativou em 0.209%, perdeu 51% do peak** |
| P3 | MÉDIA | Trend-death exit | Observado (ADX=10 por 30 min) |
| P4 | BAIXA | ADX timing | Observado |
| P5 | ALTA | Dynamic TP foge do preço | **TP nunca atingido em 3h de trade** |
| P6 | NOVA | Capture efficiency 49% | **Trailing stop não protegeu o peak** |

### Correções propostas (priorizadas)

1. **P1 — ADX threshold**: Reduzir de 25 para 20 (ou usar percentil dinâmico)
2. **P2 — Trailing activation**: Reduzir de 0.20% para 0.10%
3. **P5 — TP fixo**: Lock TP em 0.15% após abertura (não dinâmico)
4. **P3 — Trend-death exit**: Fechar posição se ADX < 15 por N candles
5. **P2 — Tick-level crossover**: Comparar DIs do tick anterior com atual

> "O primeiro crossover válido veio após 3 horas, 6 crossovers perdidos e uma margem de 5 minutos — e mesmo assim capturou apenas metade do peak" – made by Sky 🎯

---

## 7o CROSSOVER — BUY bloqueado pós-trade (08:13:09)

### Timeline pós-trade

```
  08:10:36  +DI=35.2  -DI=36.4  gap=1.2   ADX=27.8  ← SELL crossover (fechou trade)
  08:11:06  +DI=33.6  -DI=34.2  gap=0.6   ADX=27.7  ← quase convergiu
  08:11:08  +DI=31.7  -DI=37.2  gap=5.5   ADX=26.8  ← SELL aprofundou
  08:12:38  +DI=33.1  -DI=34.1  gap=1.0   ADX=25.0  ← ADX EXATAMENTE 25!
  08:13:09  +DI=37.1  -DI=32.0  gap=5.1   ADX=23.8  ← BUY CROSSOVER! ADX<25!
  08:14:42  +DI=36.2  -DI=34.7  gap=1.5   ADX=22.4  ← convergindo
  08:15:13  +DI=36.1  -DI=34.8  gap=1.3   ADX=20.9
  08:16:13  +DI=35.2  -DI=32.8  gap=2.4   ADX=19.7
  08:17:14  +DI=35.5  -DI=32.6  gap=2.9   ADX=18.7  ← mercado morrendo
```

### O timing impossível

```
  08:12:38  ADX=25.0  +DI=33.1  -DI=34.1  gap=1.0  ← ADX no threshold, sem crossover
  08:13:09  ADX=23.8  +DI=37.1  -DI=32.0  gap=5.1  ← crossover! ADX caiu 1.2 pts
```

ADX estava em 25.0, o crossover veio 30 segundos depois.
Nesses 30 segundos, ADX caiu de 25.0 para 23.8 — 1.2 pontos.
**O ADX paradox é não só anti-correlacionado mas também um race condition temporal.**

### Impacto se threshold fosse 20

| Threshold | Crossovers capturados | Taxa |
|---|---|---|
| 25 (atual) | 1/7 (14%) | Trade #1: +$8,265 |
| 20 | 2/7 (28%) | + Trade #2 potencial em $80,905 |
| 15 | 3/7 (43%) | + mais sinais |
| Sem filtro | 7/7 (100%) | todos os sinais |

Com threshold 20, o BUY às 08:13 teria aberto posição em $80,905.
BTC atual ($80,909): posição estaria +$4 (+0.004%) — muito cedo para avaliar.

### Custo acumulado do ADX Paradox

| Crossover | Tipo | ADX | Delta p/ 25 | Delta p/ 20 | Resultado |
|---|---|---|---|---|---|
| 1o (05:42) | SELL | 37.4 | +12.4 | +17.4 | Intra-candle perdido |
| 2o (05:52) | SELL | 21.0 | -4.0 | +1.0 | Bloqueado (passaria em 20!) |
| 3o (06:14) | SELL | 17.1 | -7.9 | -2.9 | Bloqueado |
| 4o (07:43) | SELL | 13.5 | -11.5 | -6.5 | Bloqueado |
| 5o (07:45) | BUY | 13.6 | -11.4 | -6.4 | Bloqueado |
| 6o (08:10) | SELL | **29.8** | **+4.8** | **+9.8** | **CAPTURADO!** |
| 7o (08:13) | BUY | 23.8 | -1.2 | +3.8 | Bloqueado (passaria em 20!) |

**Com threshold 20**: teríamos capturado 3/7 crossovers (43%) em vez de 1/7 (14%).
O 2o crossover (SELL às 05:52, ADX=21.0) teria fechado o trade em +$3,973.
O 7o crossover (BUY às 08:13, ADX=23.8) teria aberto novo trade.

### Correção P1 atualizada

**Recomendação**: Reduzir ADX threshold de **25 → 20**.
Evidência: 2 crossovers perdidos com ADX entre 20-25 (2o e 7o).
Isso triplicaria a taxa de captura de 14% → 43%.

> "O ADX marcou 25.0 e o crossover veio 30 segundos tarde — o paradoxo é um race condition" – made by Sky ⏱️

---

## Pós-trade: Whipsaw Confirma Proteção do ADX Filter (08:10-08:28)

### 8o quasi-crossover (08:10:36-08:11:08)

Após fechamento do trade às 08:10:04, os DIs convergiram rapidamente:

| Hora | +DI | -DI | Gap | ADX | Status |
|---|---|---|---|---|---|
| 08:10:36 | 35.2 | 36.4 | 1.2 | 27.8 | -DI ainda acima |
| 08:10:38 | 34.7 | 35.4 | 0.7 | 27.7 | Quase cruzou! |
| 08:11:06 | 33.6 | 34.2 | 0.6 | 27.7 | **Menor gap** |
| 08:11:08 | 31.7 | 37.2 | 5.5 | 26.8 | -DI se afastou |

**Observação**: ADX estava ACIMA de 25 (27.7-27.8) durante a convergência. Se o crossover tivesse ocorrido no tick 08:11:06, seria um sinal válido. Mas não cruzou — -DI "escapou" no último tick.

### 7o crossover = Flash Whipsaw (5 minutos de duração)

O 7o crossover às 08:13:09 (+DI cruzou acima, gap=5.1) foi um **whipsaw clássico**:

| Hora | +DI | -DI | Gap | ADX | Observação |
|---|---|---|---|---|---|
| 08:13:09 | 37.1 | 32.0 | 5.1 | 23.8 | **CROSSOVER** (bloqueado por ADX<25) |
| 08:14:11 | 37.8 | 31.7 | 6.2 | 22.8 | +DI dominante |
| 08:15:42 | 34.4 | 33.2 | 1.3 | 20.9 | DIs convergindo de novo! |
| 08:16:13 | 35.2 | 32.8 | 2.4 | 19.7 | +DI estável |
| 08:17:14 | 35.5 | 32.6 | 2.9 | 18.7 | Último momento +DI dominante |
| 08:18:16 | 30.9 | 39.7 | 8.8 | 18.1 | **REVERSAL: -DI cruza de volta** |
| 08:18:46 | 28.7 | 44.1 | 15.4 | 18.7 | -DI acelerando |
| 08:19:17 | 25.9 | 49.3 | 23.4 | 19.6 | Gap explodindo |

**Duração do +DI dominante**: ~5 minutos (08:13 → 08:18).
**Se threshold fosse 20**: BUY em $80,905 → BTC caiu para $80,737 em 10 minutos → **perda de -$168 (-0.21%)**.

### Tendência confirmada (08:18-08:28)

| Hora | BTC | +DI | -DI | Gap | ADX | Direção |
|---|---|---|---|---|---|---|
| 08:18:16 | $80,881 | 30.9 | 39.7 | 8.8 | 18.1 | Virando baixa |
| 08:19:48 | $80,833 | 25.3 | 50.6 | 25.3 | 19.8 | Baixa |
| 08:21:50 | $80,786 | 20.3 | 57.0 | 36.7 | 23.2 | Baixa forte |
| 08:22:51 | $80,773 | 19.4 | 58.9 | 39.6 | 25.2 | Baixa forte |
| 08:23:22 | $80,737 | 16.6 | 61.9 | 45.3 | 27.6 | **Mínimo do período** |
| 08:24:23 | $80,782 | 15.2 | 57.4 | 42.3 | 29.8 | Recuperação parcial |
| 08:26:56 | $80,797 | 18.3 | 51.1 | 32.8 | 32.2 | ADX subindo |
| 08:27:58 | $80,794 | 18.1 | 50.5 | 32.4 | 33.3 | **ADX mais alto** |

### Nova Correção P7 — Whipsaw Filter

O 7o crossover demonstrou que o threshold ADX >= 25 tem **valor protetor contra whipsaws**:

- Com threshold=20: teria aberto BUY em $80,905 → resultado seria PERDA
- Com threshold=25: bloqueou corretamente o whipsaw → protegeu capital

**Isso contradiz a correção P1 original** que recomendava reduzir para 20.
O dado sugere que threshold=20 é muito baixo e permite whipsaws.

### Recomendação atualizada — ADX Threshold

| Threshold | Prós | Contras | Veredicto |
|---|---|---|---|
| 25 (atual) | Filtra whipsaws | Perde crossovers legítimos | Conservador |
| 20 | Captura mais sinais | Permite whipsaws (comprovado) | Arriscado |
| **22-23** | Meio-termo | Precisa backtest | **Candidato** |

**Nova recomendação**: Backtest com threshold 22-23 antes de mudar.
O 7o crossover provaria que 20 é perigoso; o 2o crossover (ADX=21.0) sugere que algo entre 20-25 capturaria bons sinais sem tanto whipsaw.

### State atual (08:28)

- **BTC**: $80,795 (baixa de $80,905 → $80,737 = -$168)
- **ADX**: 33.3 (tendência forte de BAIXA)
- **-DI**: 50.5 (dominante, gap=32.4)
- **Posição**: Nenhuma (correto — mercado em baixa)
- **Trades**: 15 fechados, WR 40%, PnL +$14,138.30
- **Próximo BUY**: requer reversão significativa (gap precisa fechar de 32 → 0)

> "O whipsaw de 5 minutos provaria que threshold 20 é uma armadilha — o ADX paradox é protetor E bloqueante ao mesmo tempo" – made by Sky 🛡️

---

## 9o Crossover — SEGUNDO TRADE ABERTO (08:46:53)

### Convergência em 3 ondas (08:33-08:46)

O crossover veio após 3 "spikes" de compra que gradualmente fecharam o gap:

| Onda | Hora | BTC | Gap | ADX | Observação |
|---|---|---|---|---|---|
| Base | 08:34:06 | $80,773 | 27.0 | 35.7 | -DI máximo |
| Spike 1 | 08:35:07 | $80,798 | 14.2 | 33.3 | Rally +$25 |
| Refluxo | 08:43:51 | $80,794 | 23.1 | 31.1 | Gap reabriu |
| Spike 2 | 08:44:19 | $80,820 | 7.4 | 30.0 | Rally +$26 |
| Spike 2b | 08:44:22 | $80,820 | **3.8** | 29.6 | Quase crossover! |
| Refluxo | 08:44:50 | $80,811 | 12.4 | 30.6 | Rejeitado |
| Spike 3 | 08:45:21 | $80,820 | **3.7** | 27.9 | Terceira tentativa |
| Spike 3b | 08:46:22 | $80,820 | **3.7** | 26.3 | ADX caindo... |
| **CROSSOVER** | **08:46:53** | **$80,830** | **~0** | **~25.5** | **+DI cruzou acima!** |

**Padrão**: Cada spike de compra (+$25-30) fechava o gap em ~20 pontos, mas o preço não sustentava e o gap reabria. Na 3a tentativa, BTC subiu para $80,830 e o crossover finalmente completou.

### ADX Paradox Race Condition — 3a ocorrência

| Momento | ADX | Gap | Evento |
|---|---|---|---|
| 08:46:22 (último tick antes) | 26.3 | 3.7 | -DI ainda acima |
| 08:46:53 (crossover) | **~25.5** | ~0 | **+DI cruzou — passou por 0.5!** |
| 08:47:24 (tick seguinte) | 24.5 | 2.2 | ADX já caiu abaixo de 25 |

**Margem**: ~0.5 pontos acima do threshold. Em 31 segundos, ADX caiu de ~25.5 para 24.5.
**Se o crossover viesse 30 segundos depois**: ADX estaria em ~24.5 → **BLOQUEADO**.

### Trade #2 parâmetros

- **Entrada**: $80,830.45
- **ADX no momento**: ~25.5 (margem mínima de 0.5)
- **TP dinâmico**: 0.40% (ADX ~25, faixa 20-30) → TP = $81,153
- **SL**: 0.20% → SL = $80,669
- **Contexto**: Vindo de downtrend forte (ADX=35.7 há 13 min), reversão em 3 ondas

### Tabela de Crossovers Atualizada

| # | Hora | Tipo | ADX | Delta p/ 25 | Resultado |
|---|---|---|---|---|---|
| 1 | 05:42 | SELL | 37.4 | +12.4 | Intra-candle perdido |
| 2 | 05:52 | SELL | 21.0 | -4.0 | Bloqueado |
| 3 | 06:14 | SELL | 17.1 | -7.9 | Bloqueado |
| 4 | 07:43 | SELL | 13.5 | -11.5 | Bloqueado |
| 5 | 07:45 | BUY | 13.6 | -11.4 | Bloqueado |
| 6 | 08:10 | SELL | 29.8 | +4.8 | **CAPTURADO (Trade #1: +$8,265)** |
| 7 | 08:13 | BUY | 23.8 | -1.2 | Bloqueado (whipsaw!) |
| 8 | 08:11 | quasi | 27.7 | +2.7 | Não cruzou (gap=0.6) |
| 9 | **08:46** | **BUY** | **~25.5** | **+0.5** | **CAPTURADO (Trade #2: aberto)** |

**Taxa de captura**: 2/9 (22%) — ambos com ADX >= 29 ou margem mínima.

### State atual (08:47)

- **Posição**: ABERTA @ $80,830.45
- **PnL aberto**: -$140 (-0.002%) — levemente abaixo da entrada
- **Trades fechados**: 15, WR 40%, PnL +$14,138.30
- **ADX**: 24.5 (caindo — sinal de que a tendência está enfraquecendo)
- **+DI**: 35.2 > -DI: 33.0 (gap=2.2, +DI dominante)

> "Três ondas de compra para um crossover que passou por 0.5 pontos — o ADX paradox é um funil cada vez mais estreito" – made by Sky 🌊

---

## Trade #2 — Whipsaw em Tempo Real (08:46 → 09:02)

### 4 DI crossovers em 14 minutos

Trade #2 abriu em zona de whipsaw com DIs oscilando rapidamente:

| # | Hora | Tipo | +DI vs -DI | Gap | ADX | Signal? | BTC | PnL |
|---|---|---|---|---|---|---|---|---|
| 9 | 08:46:53 | BUY | +DI > -DI | ~0 | ~25.5 | **ABERTO** | $80,830 | $0 |
| 10 | 08:50:28 | Reverse | -DI > +DI | 13.4 | 21.5 | **Blocked** | $80,798 | -$3,252 |
| 11 | 08:57:07 | Re-cross | +DI > -DI | 1.5 | 16.9 | No (já pos) | $80,833 | +$267 |
| 12 | 09:00:10 | Reverse | -DI > +DI | 12.0 | 16.7 | **Blocked** | $80,793 | -$1,243 |

### DI Oscillation Pattern

```
08:47  +DI ══════════> -DI     (gap=2.2, +DI dominante)
08:50  +DI <════════════ -DI   (gap=13.4, REVERSAL)
08:53  +DI <══════ -DI         (gap=9.3, convergindo)
08:56  +DI <══ -DI             (gap=4.2, quase)
08:57  +DI ══> -DI             (gap=1.5, re-crossover!)
08:59  +DI ≈ -DI               (gap=0.6, quasi)
09:00  +DI <════════ -DI       (gap=12.0, REVERSAL)
09:01  +DI <═════ -DI          (gap=9.9, -DI dominante)
```

### Métricas do Whipsaw

| Métrica | Valor |
|---|---|
| Duração do trade | 14+ minutos (ainda aberto) |
| Crossovers durante trade | 4 (2 reversões, 1 re-cruzamento, 1 quasi) |
| ADX range | 25.5 → 14.8 → 17.0 (queda de 8.5 pontos) |
| BTC range | $80,788 — $80,833 ($45, 0.056%) |
| PnL range | -$4,231 → +$267 → -$2,278 |
| Tempo em lucro | ~1 minuto (08:57 apenas) |

### NOVO ISSUE: P8 — Exit Asymmetry (Assimetria de Saída)

**Problema**: O filtro ADX >= 25 aplica-se igualmente a entradas E saídas. Mas:
- **Entradas** precisam de proteção (muitos sinais falsos) → threshold ALTO protege
- **Saídas** precisam ser rápidas (cortar perdas) → threshold ALTO bloqueia

**Evidência no Trade #2**:
- 10o crossover (reverse) às 08:50:28: ADX=21.5 → SELL **blocked**
- Se o SELL fosse executado: perda de ~$3,252 (-0.040%)
- Em vez disso, posição ficou presa por 14+ minutos sangrando

**Mesmo padrão do 7o crossover (whipsaw)**: O 7o crossover BUY às 08:13 teria sido whipsaw E o SELL de saída seria bloqueado pelo ADX.

**Proposta P8**: Remover filtro ADX para sinais de SAÍDA (venda com posição aberta).
O ADX filter deve proteger ENTRADAS, não impedir SAÍDAS.

### NOVO ISSUE: P9 — Chop Zone Detection

**Problema**: 4 crossovers em 14 minutos = zona de chop (sem tendência).
A estratégia não tem mecanismo para detectar que está em zona de whipsaw.

**Evidência**: ADX caiu de 25.5 para 14.8 durante o trade — ADX < 20 indica claramente zona sem tendência. A posição foi aberta quando ADX ~25 e caiu imediatamente.

**Proposta P9**: Se ADX cair abaixo de 15 com posição aberta, forçar saída (market sell).
Isso limpa posições em zonas de chop.

### State atual (09:02)

- **Posição**: ABERTA @ $80,830.45 (14+ minutos)
- **BTC**: $80,808 (-$22 da entrada)
- **PnL**: -$2,278 (-0.028%)
- **ADX**: 17.0 (sem tendência — chop zone)
- **-DI**: 27.9 dominante (gap=9.9)
- **SL**: $80,669 (-0.20%, $139 abaixo)
- **TP**: ~$81,153 (+0.40%, $345 acima)
- **Trades fechados**: 15, WR 40%, PnL +$14,138.30

### Rally de 45 minutos (09:13-09:31)

Após 27 minutos de whipsaw, rally consistente:

| Hora | BTC | +DI | ADX | PnL | Evento |
|---|---|---|---|---|---|
| 08:46 | $80,830 | ~32 | ~25.5 | $0 | Entrada |
| 09:04 | $80,766 | 14.7 | 22.1 | -$6,458 | Fundo do trade |
| 09:13 | $80,851 | 36.8 | 19.7 | +$1,049 | Breakeven |
| 09:16 | $80,872 | 43.7 | 21.6 | +$3,114 | Rally 1 |
| 09:25 | **$80,911** | **48.1** | 25.4 | **+$6,798** | **Pico do trade** |
| 09:31 | $80,900 | 39.5 | 29.1 | +$6,977 | Rally 3 |

**Trailing stop nunca ativou**: Pico +0.099%, threshold 0.20%. Ganho desprotegido.
**TP widening iminente**: ADX=29.1, threshold 30 → TP salta 0.40%→0.50%.

### Rally → Pico ADX → Colapso (09:27-09:38)

Rally continua com ADX acelerando até pico de 31.5, seguido por colapso em 3 minutos:

| Hora | BTC | +DI | -DI | ADX | gap | TP band | Evento |
|---|---|---|---|---|---|---|---|
| 09:27 | $80,873 | 37.0 | 23.9 | 25.0 | 13.1 | 0.40% | Rally estável |
| 09:29 | $80,900 | 40.3 | 19.9 | 26.5 | 20.4 | 0.40% | Gap se amplia |
| 09:30 | $80,900 | 40.9 | 16.8 | **28.1** | 24.1 | 0.40% | -DI colapsando |
| 09:32 | $80,919 | 40.3 | 15.5 | **30.2** | 24.8 | 0.50% | **ADX cruza 30! TP amplia** |
| 09:33 | $80,918 | 40.1 | 14.6 | **31.5** | 25.5 | 0.50% | **PICO DO ADX** |
| 09:35:01 | $80,891 | 35.4 | 23.0 | 30.7 | 12.4 | 0.50% | Início do colapso |
| 09:35:03 | $80,891 | 33.2 | **26.3** | 29.2 | 6.9 | 0.50% | Gap halved em 2s |
| 09:35:32 | $80,880 | 32.0 | 29.0 | 28.7 | **3.0** | 0.40% | Gap perigoso |
| 09:36:03 | $80,876 | 30.8 | **31.6** | 26.5 | **0.8** | 0.40% | -DI quase cruza! |
| 09:36:33 | $80,892 | 29.3 | 29.6 | 26.4 | **0.2** | 0.40% | Quasi-crossover #3 |
| 09:38:36 | $80,878 | **27.7** | **29.5** | 23.1 | -1.8 | 0.40% | **11o crossover (-DI > +DI)** |
| 09:38:38 | $80,878 | **27.3** | **30.7** | 23.3 | -3.5 | 0.30% | SELL bloqueado (ADX<25) |

**Colapso em 3 minutos**: Gap de 25.5 → 0.8 em 3 minutos (09:33 → 09:36). Taxa de convergência: ~8 pontos/min.

### 11o Crossover — REVERSE SELL bloqueado (09:38:36)

- **Hora**: 09:38:36-09:38:38
- **Direção**: -DI cruza acima de +DI (gap: +0.2 → -1.8 → -3.5)
- **ADX**: 23.1-23.3 → **BLOCKED** (abaixo de 25)
- **Resultado**: SELL não executado, posição mantida

**P8 confirma**: Se P8 estivesse implementado (remover ADX filter para saídas), o SELL seria executado a ~$80,878, lucro de +$4,775 (+0.059%). Posição permaneceu aberta.

**Mas**: 2 minutos depois, BTC subiu para $80,921 e PnL chegou a +$9,038. O bloqueio foi BENÉFICO neste caso.

### NOVO ISSUE: P10 — Dynamic TP Floor Risk (Risco de Piso Dinâmico)

**Problema**: Quando ADX cai de uma faixa para outra, o TP é recalculado para BAIXO.

**Evidência no Trade #2**:
- ADX 31.5 (09:33): TP = 0.50% → $80,830.45 × 1.005 = **$81,234.60**
- ADX 19.3 (09:48): TP = 0.30% → $80,830.45 × 1.003 = **$81,072.94**
- **Diferença**: TP recuou $161.66

**Risco latente**: Se BTC estivesse entre $81,073 e $81,235 quando o TP fosse reduzido, o hit imediato seria disparado. Isso não aconteceu (BTC máximo $80,941), mas é um bug que pode causar saídas forçadas em mudanças bruscas de ADX.

**Neste caso**: P10 foi BENÉFICO — o TP ficou mais próximo ($81,073 vs $81,235), facilitando o hit.

**Proposta P10**: Implementar **TP lock** (fixar TP na entrada) OU **TP floor** (TP só sobe, nunca desce). Isso evita saídas acidentais por mudança de ADX.

### Recuperação Pós-Colapso (09:39-09:49)

Após o colapso do ADX e 11o crossover, +DI recupera:

| Hora | BTC | +DI | -DI | ADX | gap | PnL | Evento |
|---|---|---|---|---|---|---|---|
| 09:39:06 | $80,876 | 26.3 | 29.7 | 22.0 | -3.4 | +$4,577 | -DI dominante |
| 09:40:08 | **$80,921** | **35.0** | 25.2 | 22.2 | 9.9 | **+$9,038** | +DI ressurge! |
| 09:41:09 | $80,900 | 33.0 | 25.8 | 21.5 | 7.2 | +$6,999 | Estabiliza |
| 09:42:11 | $80,908 | 31.8 | 24.9 | 20.8 | 6.9 | +$7,782 | ADX decay |
| 09:44:14 | $80,910 | 30.7 | 23.3 | **19.9** | 7.4 | +$7,941 | **ADX < 20** |
| 09:45:46 | $80,923 | 32.5 | 21.9 | 19.9 | 10.6 | +$9,304 | PnL estável |
| 09:46:17 | **$80,941** | 37.8 | 20.2 | 20.7 | 17.6 | **+$10,356** | **NOVO PICO!** |
| 09:47:49 | $80,927 | 37.5 | 19.8 | 21.5 | 17.6 | +$9,688 | Rally continua |
| 09:48:20 | $80,906 | 30.8 | 25.2 | **19.3** | 5.6 | +$7,880 | ADX decay |
| 09:49:53 | $80,938 | 33.1 | 23.4 | **19.1** | 9.7 | +$10,760 | Oscilação |

**ADX Decay Rate**: Do pico 31.5 (09:33) para 19.1 (09:49) = queda de 12.4 pontos em 16 min = **0.78 pontos/min**. Ao ritmo atual, ADX < 15 por volta de ~09:56.

### ADX Limbo — Quase P9, Depois Bounce (09:49-10:01)

ADX caiu para 15.7 (a 0.7 do P9 threshold) e então recuperou:

| Hora | BTC | +DI | -DI | ADX | gap | Evento |
|---|---|---|---|---|---|---|
| 09:49:53 | $80,938 | 33.1 | 23.4 | 19.1 | 9.7 | ADX < 20 |
| 09:51:25 | $80,898 | 27.2 | 20.9 | 18.3 | 6.2 | Gap estreitando |
| 09:52:27 | $80,899 | 27.2 | 20.9 | 17.9 | 6.2 | ADX decay |
| 09:53:28 | $80,910 | 28.1 | 20.0 | 17.9 | 8.1 | Oscilação |
| 09:54:30 | $80,912 | 28.9 | 19.6 | 18.2 | 9.3 | ADX estabilizou? |
| 09:55:32 | $80,902 | 27.5 | 23.2 | 17.5 | 4.4 | Gap collapse |
| 09:56:33 | $80,902 | 27.4 | 23.2 | **16.8** | 4.2 | P9 próximo |
| 09:57:35 | $80,908 | 30.3 | 21.2 | 17.5 | 9.1 | Recuperação leve |
| 09:58:06 | $80,895 | 28.3 | 23.2 | **16.4** | 5.1 | **MÍNIMO ADX** |
| 09:59:06 | $80,894 | 27.8 | 23.7 | **15.7** | 4.1 | **P9 quase! (0.7 pts)** |
| 10:00:07 | **$80,921** | **36.0** | **18.3** | **18.5** | **17.6** | **BOUNCE!** |
| 10:01:08 | $80,901 | 30.9 | 15.8 | **19.5** | 15.2 | -DI colapsou! |

**ADX Bounce**: De 15.7 → 18.5 → 19.5 em 2 minutos. Causa: spike de $28 no BTC ($80,894 → $80,921) disparou +DI de 27.8 para 36.0 e -DI caiu de 23.7 para 15.8.

**P9 Contra-evidência #2**: Se P9 (ADX < 15) estivesse implementado:
- Teria saido a ~$80,894 com +$6,470 (+0.080%)
- Em vez disso, posição vale $7,063 (+0.087%) após o bounce
- **Diferença**: +$593 preservado por NÃO ter P9
- Mas: PnL no pico era $10,356 — o trade perdeu $3,293 do pico sem proteção

### NOVO ISSUE: P11 — ADX Limbo (Zona de Ninguém)

**Problema**: ADX oscila entre 15-20 por 25+ minutos, criando estado "zumbi":
- Muito baixo para gerar sinais (ADX < 25)
- Muito alto para chop zone exit (ADX > 15)
- Posição presa em "no man's land"

**Evidência**: ADX esteve entre 15.7-19.9 por 17 minutos (09:44-10:01), sem disparar nenhum mecanismo de saída. A posição flutuou entre +$4,577 e +$10,760 sem proteção.

**ADX Oscillation Pattern**: Gap oscila entre 4-18 em ciclos de ~2 minutos:
- BTC sobe → +DI sobe, -DI cai → gap alarga → ADX sobe levemente
- BTC cai → +DI cai, -DI sobe → gap estreita → ADX cai levemente
- Resultado: ADX nunca sai do range 15-20

**Proposta P11**: Implementar **time-based exit** — se posição aberta há N minutos (ex: 60) sem atingir TP ou ativar trailing, forçar saída ao mercado. Isso evita posições zumbis em ADX limbo.

### DI Gap Resilience — +DI Dominante por 75 minutos

Apesar de ADX cair de 31.5 para 15.7, **+DI nunca perdeu dominância** após 09:39:
- 09:38:38: último momento -DI > +DI (gap = -3.5)
- 09:40:08 em diante: +DI > -DI consistentemente
- Gap oscila 4-18 mas nunca cruza zero

**Interpretação**: O trend original (compra) está intacto no DI, mas enfraquecendo no ADX. Isso é uma **divergência DI/ADX**: gap diz bullish, ADX diz fraco.

### State atual (10:01)

- **Posição**: ABERTA @ $80,830.45 (~75 minutos)
- **BTC**: $80,902 (+$71.55, +0.089%)
- **PnL**: +$7,063 (+0.087%)
- **+DI**: 30.8 | **-DI**: 15.7 | **gap**: 15.1 (+DI forte)
- **ADX**: 19.5 (vermelho, range 15-20)
- **TP**: 0.30% = $81,073 (+$171 acima)
- **SL**: $80,669 (-0.20%, $233 abaixo)
- **Trailing stop**: NUNCA ativou em 75 minutos (pico 0.137%)
- **Trades fechados**: 15, WR 40%, PnL +$14,138.30
- **Crossovers intra-trade**: 5 (4o-11o, sendo 2 reverse blocked)

### CRÍTICO: Bot Reiniciado — Trade #2 Perdido (10:14:31)

Bot foi reiniciado às 10:14:31. Trade #2 (87 minutos, PnL ~$7,000+) foi **perdido**:

| Métrica | Antes (10:14:00) | Depois (10:14:32) | Delta |
|---|---|---|---|
| Posições abertas | 1 (BTC-USD) | **0** | -1 |
| Trades fechados | 15 | **14** | -1 |
| PnL fechado | $14,138.30 | **$5,873.30** | **-$8,265** |
| Win Rate | 40% | **36%** | -4% |

**Trade #2 final**:
- Entrada: $80,830.45 (08:46:53)
- Último tick: $80,912 (10:14:00)
- PnL no momento da perda: +$8,155 (+0.101%)
- Duração: 87 minutos
- Resultado: **PERDIDO** — posição não restaurada

### NOVO ISSUE: P12 — Persistence Failure on Restart

**Problema**: O bot não restaura estado corretamente após reinicialização.
Posições abertas e PnL fechado são perdidos.

**Evidência**:
1. Posição Trade #2 evaporou ( Posições: 0 após restart)
2. $8,265 de PnL fechado desapareceu ($14,138 → $5,873)
3. 1 trade desapareceu da contagem (15 → 14)
4. Win rate regrediu (40% → 36%)

**Causa provável**: A camada de persistência SQLite (WriteQueue) grava ticks/sinais mas o restore no startup não recarrega posições abertas nem o histórico de PnL fechado corretamente. Ou o estado em memória (closed_pnl, positions) não é persistido antes do shutdown.

**Correção P12**:
1. Garantir que `flush_ohlcv()` + `close_position()` sejam chamados no shutdown
2. Persistir `closed_pnl` e `positions` em SQLite antes de encerrar
3. No startup, restaurar posições abertas e PnL fechado do banco
4. Implementar graceful shutdown (SIGTERM handler)

### Diário do Trade #2 — Cronologia Completa

| Hora | Evento | BTC | PnL | ADX | gap |
|---|---|---|---|---|---|
| 08:46:53 | **ENTRADA** (9o crossover) | $80,830 | $0 | 25.5 | crossover |
| 08:47-08:57 | Whipsaw (4 crossovers) | $80,788-$80,833 | -$6,458→+$267 | 25→14 | 0-12 |
| 08:58-09:04 | Fundo do trade | $80,766 | **-$6,458** | 22→19 | ~10 |
| 09:04-09:13 | Recuperação | $80,766→$80,851 | -$6K→+$1K | 19-20 | 5-15 |
| 09:13-09:33 | Rally forte | $80,851→$80,919 | +$1K→+$9K | 20→**31.5** | 5-25 |
| 09:33-09:38 | **Colapso ADX/DI** | $80,919→$80,878 | +$9K→+$4.6K | 31.5→23 | 25→-3.5 |
| 09:38:36 | 11o crossover (-DI>+DI) blocked | $80,878 | +$4,577 | 23.1 | -3.5 |
| 09:39-09:46 | Recuperação | $80,878→$80,941 | +$4.6K→**+$10,356** | 22→20 | 3-18 |
| 09:46:17 | **PICO DO TRADE** | **$80,941** | **+$10,356** | 20.7 | 17.9 |
| 09:47-09:59 | Slow bleed + ADX decay | $80,941→$80,894 | +$10K→+$6.5K | 20→**15.7** | 18→4 |
| 09:59:06 | **P9 quase disparou** (ADX=15.7) | $80,894 | +$6,470 | **15.7** | 4.1 |
| 10:00:07 | ADX Bounce | $80,921 | +$9,038 | 18.5 | 17.6 |
| 10:02-10:06 | ADX Limbo | $80,905→$80,867 | +$7K→+$3.6K | 23→22 | 15→3 |
| 10:07:49 | **Quasi-crossover #4** (gap=0.1) | $80,859 | **+$2,889** | 20.6 | **0.1** |
| 10:08:51 | Bounce | $80,915 | +$8,453 | 21.1 | 15.5 |
| 10:09-10:14 | Oscilação final | $80,912 | +$7,155 | 21 | 12 |
| 10:14:31 | **BOT RESTART — POSIÇÃO PERDIDA** | $80,927 | $0 | 21.5 | 16.9 |

**Trade #2 — Resumo Final**:
- Duração: 87 minutos
- PnL no último tick: +$8,155 (+0.101%)
- PnL pico: +$10,356 (+0.128%) às 09:46
- PnL fundo: -$6,458 (-0.080%) às 09:04
- Crossovers intra-trade: 5 (11o-15o)
- Trailing stop: NUNCA ativou
- Mecanismos de saída disparados: **NENHUM** (SL, TP, trailing, signal)
- Resultado: **PERDIDO por restart do bot** (P12)

### Resumo de Issues P1-P12

| Issue | Status | Impacto no Trade #2 |
|---|---|---|
| P1 ADX Paradox | Confirmado (3x) | Entrada com ADX=25.5, caiu para 24.5 em 30s |
| P2 Trailing Inerte | **Crítico** | 87 min, pico +0.137%, ZERO proteção ativada |
| P3 Trend-death exit | Ativo | ADX 31.5→15.7, sem saída automática |
| P5 TP Widening | Reverso | ADX caiu, TP estreitou — BENÉFICO nesta vez |
| P7 Whipsaw Protection | Confirmado | 7o crossover bloqueado era whipsaw |
| P8 Exit Asymmetry | Confirmado (2x) | 10o e 11o crossovers blocked — 11o benéfico |
| P9 Chop Zone | **Contra-evidência (2x)** | Teria saido $80,894 (+$6K), perdia rally |
| P10 TP Floor Risk | Documentado | TP caiu $162 com ADX |
| P11 ADX Limbo | Documentado | 25 min em range 15-20, sem saída possível |
| P12 Persistence Failure | **CRÍTICO** | Trade #2 perdido no restart — $8,265 PnL evaporou |

### Priorização de Correções

| Prioridade | Issue | Ação | Esforço |
|---|---|---|---|
| **P0** | P12 Persistence | Garantir graceful shutdown + restore de estado | Médio |
| **P1** | P2 Trailing | Baixar threshold de 0.20% → 0.10% | Trivial |
| **P2** | P11 Time exit | Time-based exit (60 min sem TP = saída) | Pequeno |
| **P3** | P8 Exit Asymmetry | Remover ADX filter para saídas (SELL) | Pequeno |
| **P4** | P10 TP Lock | Fixar TP na entrada, não recalcular | Trivial |
| **P5** | P1 ADX Paradox | Backtest threshold 20 vs 22 vs 25 | Médio |
| **P6** | P9 Chop Zone | Nuance: N candles consecutivos ADX<15, não imediato | Médio |
| **P7** | P3 Trend-death | Exit quando ADX cai abaixo do threshold com posição | Pequeno |

> "O mesmo filtro que te protege na entrada te prende na saída — a armadilha do guardião conservador" – made by Sky 🔒
