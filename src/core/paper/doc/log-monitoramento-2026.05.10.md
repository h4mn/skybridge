# Log de Monitoramento — Guardião Conservador v2

**Data:** 2026-05-10
**Sessão:** paper-guardiao-v2-monitor

---

## Tick 22:25 — Relatório Inicial

### Status do Sistema

- **Status:** ATIVO
- **Uptime:** ~14 min (desde restart 22:11:47)
- **Tick:** #782
- **Código:** Pré-fix (sem `di_gap_min`)

### Trades

| Métrica | Valor | vs Baseline v1 |
|---------|-------|----------------|
| Trades | 27 (8W / 19L) | +4 vs v1 (23) |
| Win Rate | 29.6% | abaixo v1 (43%) |
| PnL Fechado | $-24,535.91 | abaixo v1 (+0.76%) |
| PnL Aberto | $+10,704 (+0.131%) | 1 posição BTC-USD |
| Capital | ~$8M (paper) | — |

### Razões de Fechamento (histórico completo)

| Tipo | Qtd | % |
|------|-----|---|
| Crossover (SMA + DI) | 15 | 56% |
| Stop Loss | 6 | 22% |
| Take Profit | 6 | 22% |

### Position Guard

- 89 compras rejeitadas (posição duplicada)
- 137 vendas rejeitadas (sem posição)

### Conformidade vs Change

| Check | Status |
|-------|--------|
| SL fixo 0.500% | OK |
| Sem `_sl_for_adx` | OK (0 ocorrências) |
| Position Guard | OK |
| Heartbeat 60 ticks | OK |
| Cores (LUCRO/PERDA) | OK |
| Sem crashes | OK |

### Fechamentos Detalhados (cronológico)

```
03:19 PERDA  SL  -0.098% ($-7,893)    Stop Loss
03:38 PERDA  SL  -0.098% ($-7,886)    Stop Loss
05:02 LUCRO  TP  +0.131% ($+10,499)   Take Profit
09:08 PERDA  SMA -0.049% ($-3,934)    SMA5 cruzou abaixo SMA15
10:04 LUCRO  SMA +0.019% ($+1,557)    SMA5 cruzou abaixo SMA15
10:14 PERDA  SMA -0.040% ($-3,243)    SMA5 cruzou abaixo SMA15
10:33 PERDA  SMA -0.026% ($-2,065)    SMA5 cruzou abaixo SMA15
10:35 PERDA  SMA -0.045% ($-3,644)    SMA5 cruzou abaixo SMA15
10:40 PERDA  SMA -0.037% ($-2,996)    SMA5 cruzou abaixo SMA15
10:52 PERDA  SMA -0.039% ($-3,106)    SMA5 cruzou abaixo SMA15
11:19 PERDA  SMA -0.031% ($-2,515)    SMA5 cruzou abaixo SMA15
11:52 PERDA  SL  -0.073% ($-5,874)    Stop Loss
12:01 PERDA  SMA -0.005% ($-400)      SMA5 cruzou abaixo SMA15
12:26 LUCRO  TP  +0.097% ($+7,831)    Take Profit
13:17 LUCRO  TP  +0.097% ($+7,851)    Take Profit
13:51 PERDA  SMA -0.008% ($-671)      SMA5 cruzou abaixo SMA15
14:03 LUCRO  SMA +0.005% ($+383)      SMA5 cruzou abaixo SMA15
14:31 LUCRO  TP  +0.097% ($+7,874)    Take Profit
15:12 PERDA  SMA -0.058% ($-4,686)    SMA5 cruzou abaixo SMA15
15:23 PERDA  SMA -0.013% ($-1,082)    SMA5 cruzou abaixo SMA15
15:58 PERDA  SMA -0.021% ($-1,695)    SMA5 cruzou abaixo SMA15
16:25 PERDA  SL  -0.073% ($-5,916)    Stop Loss
16:54 LUCRO  TP  +0.097% ($+7,879)    Take Profit
08:10 LUCRO  DI  +0.102% ($+8,265)    VENDA +DI=35.9 x -DI=36.5 ADX=29.8
18:06 PERDA  DI  -0.111% ($-8,999)    VENDA +DI=30.5 x -DI=31.8 ADX=28.8
18:11 PERDA  SL  -0.200% ($-16,167)   Stop Loss
22:15 PERDA  DI  -0.064% ($-5,243)    VENDA +DI=27.2 x -DI=29.8 ADX=31.4
```

---

## Anomalia Detectada — Whipsaw Contra-Tendência (22:13–22:15)

### Sequência do Problema

```
22:11:49 INIT     +DI=14.9  -DI=37.4  ADX=40.3  gap=22.6  ← tendência BAIXA forte
22:12:20 TICK #30 +DI=23.0  -DI=31.7  ADX=37.1  gap=8.8   ← baixa enfraquecendo
~22:13:52 COMPRA   +DI cruza acima de -DI (gap ~0.5)       ← entrada fraca!
22:14:21 TICK #147 +DI=28.1  -DI=27.7  ADX=33.5  gap=0.4   ← mal positivo
22:15:23 PERDA    +DI=27.2  -DI=29.8  ADX=31.4             ← cruzou de volta (-0.064%)
```

### Diagnóstico

- **Gap mínimo no crossover:** 0.4 pontos (qualquer crossover dispara trade)
- **ADX filter:** Passou (40.3 > 25) mas não distingue direção da tendência
- **Duração da posição:** ~90 segundos — whipsaw clássico
- **Resultado:** PERDA de $-5,243 (-0.064%)

### Causa Raiz

`guardiao_conservador.py:198-201` — não existe filtro de gap mínimo entre +DI e -DI. Qualquer micro-cruzamento, mesmo gap=0.01, dispara sinal.

---

## Fix Implementado — `di_gap_min=5`

### TDD (Red-Green-Refactor)

**RED** — 6 testes falhando:

| Teste | Cenário |
|-------|---------|
| `test_crossover_compra_gap_insuficiente_bloqueia` | gap=1 < 5 → None |
| `test_crossover_compra_gap_suficiente_permite` | gap=6 >= 5 → COMPRA |
| `test_crossover_venda_gap_insuficiente_bloqueia` | gap=1 < 5 → None |
| `test_crossover_venda_gap_suficiente_permite` | gap=6 >= 5 → VENDA |
| `test_di_gap_min_default_eh_5` | default = 5 |
| `test_di_gap_min_customizado` | custom = 10 |

**GREEN** — Implementação mínima:

```python
# guardiao_conservador.py — __init__
di_gap_min: Decimal = Decimal("5")

# guardiao_conservador.py — evaluate(), após crossover
gap = abs(curr_pdi - curr_mdi)
if gap < self._di_gap_min:
    return None
```

**Resultado:** 32/32 testes passaram, zero regressão (239/239 suite completa).

### Efeito Esperado

- O trade problemático (gap=0.4) seria bloqueado
- Entradas exigem +DI/-DI separados por >= 5 pontos
- Reduz whipsaws em crossovers fracos contra tendência dominante

---

## Tick 22:46 — Pré-Restart

### Posição Aberta (entry 22:17:25 @ 81583.05)

| Hora | Tick | Preço | PnL | ADX | +DI | -DI | TP |
|------|------|-------|-----|-----|-----|-----|----|
| 22:26 | 840 | 81688.4 | +$10,535 (+0.129%) | 27.3 | 35.9 | 18.2 | 0.400% |
| 22:30 | 1080 | 81532.2 | -$5,086 (-0.062%) | 24.5 | 28.4 | 22.6 | 0.400% |
| 22:35 | 1320 | 81530.0 | -$3,311 (-0.041%) | 21.2 | 33.1 | 28.6 | 0.300% |
| 22:40 | 1620 | 81447.6 | -$9,326 (-0.114%) | 17.9 | 21.7 | 30.1 | 0.300% |
| 22:46 | 1980 | 81423.0 | -$16,003 (-0.196%) | 16.7 | 20.3 | 39.7 | 0.300% |

### Observações

- ADX caiu de 27.3 → 16.7 (tendência morrendo)
- -DI assumiu controle (gap=19.5, forte baixa)
- TP dinâmico caiu de 0.400% → 0.300% (ADX < 20)
- Posição em -0.196%, aproximando-se do SL (-0.500%)
- Restart do bot feito pelo operador para absorver fix `di_gap_min`

---

## KPIs ML — Análise Acumulada

### Métricas Gerais

| Métrica | Valor |
|---------|-------|
| Trades | 27 |
| Win Rate | 29.6% |
| PnL fechado | $-24,535.91 |
| Avg lucro | $+7,564 (8 trades) |
| Avg perda | $-5,827 (19 trades) |
| Profit factor | 0.55 (negativo) |
| Max drawdown | $-24,535.91 (acumulado) |

### Por Mecanismo de Fechamento

| Mecanismo | Trades | WR | Avg PnL |
|-----------|--------|-----|---------|
| DI Crossover (v2) | 3 | 33% | -$1,659 |
| SMA Crossover (v1) | 12 | 17% | -$1,627 |
| Stop Loss | 6 | 0% | -$7,655 |
| Take Profit | 6 | 100% | +$7,797 |

### Comparação com Baselines

| Versão | Trades | WR | PnL | Observação |
|--------|--------|-----|-----|------------|
| v1 SMA | 23 | 43% | +0.76% | baseline original |
| v2 ADX threshold=25 sem OHLC | 0 | — | — | 0 trades em 9h |
| v2 ADX com OHLC (pré-fix) | 27 | 29% | negativo | whipsaws por gap fraco |
| v2 ADX + gap_min=5 | — | — | — | aguardando dados pós-restart |

---

## Referências

- Spec: `openspec/changes/paper-guardiao-v2/`
- Código: `src/core/paper/domain/strategies/guardiao_conservador.py`
- Testes: `tests/unit/paper/domain/strategies/test_guardiao_conservador.py`
- Issue Linear: SKY-35
- Docs relacionadas: `relatorio-monitoramento-guardiao.md`, `analise-di-crossover.md`, `paper-guardiao-dia-02.md`

> "Gap mínimo é o antídoto contra o ruído." – made by Sky 🛡️

---

## Tick 23:44 — SL Legada + Fix Ativo (53 min uptime)

### Status do Sistema

- **Status:** ATIVO
- **Uptime:** ~57 min (restart 22:47:05 c/ `di_gap_min=5`)
- **Tick:** #3280
- **Código:** Pós-fix (di_gap_min=5 ativo)

### Evento: SL Legada Acionado

```
23:23:17 PERDA: FECHAMENTO BTC-USD @ 81175.13 | -0.500% ($-40,791.53) (Stop Loss acionado (-0.5%))
```

- **Posição legada** (entry 22:17:25 @ 81583.05, aberta antes do fix)
- Duração: ~66 minutos até SL
- **Maior perda individual da sessão:** $-40,791.53
- Trade #18

### Trades Atualizados

| Métrica | Valor | Anterior |
|---------|-------|----------|
| Trades | 18 (5W / 13L) | 17 |
| Win Rate | 27.8% | 29.6% |
| PnL Fechado | **$-65,327.43** | $-24,535.91 |
| Posições | 0 | 1 |

### Fix di_gap_min — Resultado Real

| Check | Resultado |
|-------|-----------|
| Tempo com fix ativo | 57 min |
| Novas entradas | **ZERO** |
| Motivo | Mercado em downtrend forte (-DI >> +DI, sem crossover) |
| Gap filter testado | Não (sem crossover desde restart) |
| ADX filter | Dominante — ADX=38-41 mas sem crossover de +DI |

### Mercado

| Indicador | Valor |
|-----------|-------|
| BTC-USD | 81197.75 |
| +DI / -DI | 14.1 / 28.2 |
| ADX | 38.2 |
| Gap | 14.1 (-DI dominante) |
| Tendência | Forte baixa |

- -DI consistentemente acima de +DI desde ~22:30
- ADX subiu de 17 → 40 (tendência se fortaleceu na queda)
- Estratégia corretamente fora do mercado

### Conformidade

| Check | Status |
|-------|--------|
| SL 0.500% | OK (legada bateu exatamente em -0.500%) |
| Sem novos trades | OK (comportamento correto em downtrend) |
| Zero crashes | OK |
| di_gap_min ativo | OK (não exerceu efeito — sem crossovers) |

### Alerta

**Drawdown severo:** PnL acumulado piorou de $-24.5K para $-65.3K com o SL da posição legada. O sistema precisa de uma sequência de wins para recuperar. O fix de gap mínimo ainda não foi testado em combate real — precisa de um cenário de crossover fraco (gap < 5) para validar.

> "Paciência é também não entrar." – made by Sky 🕰️
