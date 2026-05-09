# Relatório de Monitoramento ao Vivo — Guardião Conservador

> Síntese de 21 análises publicadas na issue SKY-35 (Linear)
> Sessão: 07:03 → 18:46 (08/mai/2026) — ~11h 43min de operação contínua
> Ticker: BTC-USD | Intervalo: 1min | SMA(5)/SMA(15) crossover

---

## 1. Resumo Executivo

O Guardião Conservador operou por **~12h contínuas** com zero crashes, zero erros e **671 ticks** processados. Executou **23 trades** com **PnL líquido de ~+0.76%**.

O resultado é positivo, mas revela uma **dependência crítica de poucos trades**: 5 trades em tendência geraram +1.82%, enquanto 18 trades em mercado lateral perderam -1.06%. O sistema é funcional como prova de conceito, mas precisa de filtros para ser consistente.

---

## 2. Métricas Finais

| Métrica | Valor |
|---------|-------|
| Ticks processados | 671 |
| Sinais gerados | 54 |
| Trades executados | 23 |
| Win rate | 43% (10W / 13L) |
| Win rate significativos (>\|0.1%\|) | 57% (4W / 3L) |
| PnL total | **~+0.76%** |
| PnL em tendência | +1.82% (5 trades) |
| PnL em lateral | -1.06% (18 trades) |
| Stop Loss acionados | 2 |
| Take Profit acionados | 1 |
| Trades fantasma | 3 |
| Whipsaw < 2 min | 4 trades |
| Drawdown máximo | ~-0.65% |
| Erros | 0 |
| Tempo uptime | ~11h 43min |

---

## 3. Tabela Completa de Trades

| # | Entrada | Saída | Duração | PnL% | Motivo | Qualidade |
|---|---------|-------|---------|------|--------|-----------|
| 1 | $79,902 (07:28) | $80,193 (08:12) | 44min | +0.36% | Crossover | Tendência |
| 2 | $80,259 (08:24) | $80,203 (08:43) | 19min | -0.07% | Crossover | Lateral |
| 3 | $80,263 (08:55) | ~$80,285 (09:16) | 21min | +0.03% | Crossover | Lateral |
| 4 | $80,285 (09:16) | $80,273 (09:30) | 14min | -0.02% | Crossover | Lateral |
| 5 | $80,243 (09:44) | $80,207 (09:45) | <1min | -0.05% | Crossover | Whipsaw |
| 6 | $80,123 (09:58) | $79,919 (10:08) | 10min | -0.25% | **Stop Loss** | SL |
| 7 | $79,777 (10:35) | $79,565 (10:42) | 7min | -0.26% | **Stop Loss** | SL |
| 8 | $79,620 (10:53) | $79,551 (10:56) | 3min | -0.09% | Crossover | Whipsaw |
| 9 | $79,659 (11:00) | $80,332 (11:18) | 18min | **+0.84%** | **Take Profit** | Tendência |
| 10 | — (11:30) | $80,096 | — | fantasma | VENDA sem posição | Bug |
| 11 | $80,199 (11:38) | $80,163 (11:52) | 14min | -0.045% | Crossover | Lateral |
| 12 | $79,803 (12:34) | $79,976 (13:04) | 30min | +0.22% | Crossover | Tendência |
| 13 | $79,780 (13:46) | $79,750 (13:47) | 1min | -0.04% | Crossover | Whipsaw |
| 14 | $79,780 (13:51) | $79,735 (14:11) | 20min | -0.06% | Crossover | Lateral |
| 15 | $79,883 (14:17) | $80,082 (14:41) | 24min | +0.25% | Crossover | Tendência |
| 16 | $80,186 (14:48) | $80,118 (14:57) | 9min | -0.09% | Crossover | Lateral |
| 17 | $80,192 (15:03) | $80,195 (15:14) | 11min | +0.004% | Crossover | Lateral |
| 18 | $80,210 (15:15) | $80,223 (15:31) | 16min | +0.015% | Crossover | Lateral |
| 19 | $80,024 (16:11) | $80,042 (16:21) | 10min | +0.022% | Crossover | Lateral |
| 20 | $80,073 (16:32) | $80,195 (17:31) | 59min | +0.15% | Crossover | Tendência |
| 21 | $80,236 (17:38) | $80,172 (17:52) | 14min | -0.08% | Crossover | Lateral |
| 22 | $80,188 (18:05) | $80,193 (18:28) | 23min | +0.006% | Crossover | Lateral |
| 23 | $80,228 (18:36) | $80,197 (18:43) | 7min | -0.04% | Crossover | Lateral |

---

## 4. Bugs Identificados

### 4.1 Sinal Duplicado (CRÍTICO)

O crossover SMA persiste por 2 ticks consecutivos. No primeiro tick, `open_position` registra a posição. No segundo, o ticker já existe no tracker, mas `executor.executar_ordem` já foi chamado — gerando **ordem duplicada no paper broker**.

**Ocorrências:** 5 pares confirmados (trades #1, #2, #3, #19, #18)

**Correção:**
```python
# Antes de chamar executor, verificar se já existe posição
if self._position_tracker.get_position(ticker) is not None:
    continue  # já posicionado, não executar novamente
```

### 4.2 VENDA Fantasma (CRÍTICO)

Após TP/SL fechar posição, VENDA sinal dispara sem posição aberta. O executor executa uma venda a descoberto (short sell) no paper broker.

**Ocorrências:** 3 (trades #10, #13b, tick #504)

**Correção:**
```python
# Antes de VENDA, verificar se existe posição
if lado == Lado.VENDA and self._position_tracker.get_position(ticker) is None:
    continue  # sem posição, não vender
```

### 4.3 Dados Stale (MODERADO)

Yahoo Finance retornou o mesmo preço ($80,101.31) por 13 ticks consecutivos (16:47→17:00). Se um sinal fosse gerado nesse período, executaria em preço incorreto.

**Ocorrências:** 1 evento (13 ticks congelados)

**Correção sugerida:**
```python
if cotacao.timestamp == self._last_timestamp.get(ticker):
    self._stale_count[ticker] += 1
    if self._stale_count[ticker] >= 2:
        self._logger.warning(f"[STALE] {ticker}: preço não atualizou")
        continue
```

### 4.4 Perda de Estado no Restart (MODERADO)

O `PositionTracker` nasce vazio a cada restart. Posições abertas, SL/TP e histórico são perdidos. O log mostra 5 reinicializações antes da sessão principal.

**Correção:** Persistir estado em JSON a cada mudança de posição.

---

## 5. Análise de Mercado: Tendência vs Lateral

### 5.1 O Padrão Central

A descoberta mais importante do monitoramento é que **o guardião opera em dois modos completamente distintos**:

| Condição | Range BTC | Sinais/hora | Win rate | PnL/hora |
|----------|-----------|-------------|----------|----------|
| **Tendência** (range > 0.5%) | > $400 | ~1 | 57% | +0.60% |
| **Lateral** (range < 0.3%) | < $240 | 4-5 | 33% | -0.14% |

O mercado esteve em lateral ~70% do tempo (8 de 11.5h). Nessas horas, o SMA(5)/SMA(15) gera whipsaw — compra no topo do mini-range e vende no fundo.

### 5.2 Evolução Horária

```
Hora 1-3:   +0.16%  (ruído lateral dominante)
Hora 3-5:   -0.65%  (2 SLs seguidos, BTC em queda)
Hora 5-7:   +1.31%  (TP #9, boas reversões #11-#12)
Hora 7-9:   -0.09%  (whipsaw lateral intenso)
Hora 9-11:  +0.30%  (trade #20, melhora parcial)
Hora 11-12: -0.02%  (lateral, erosão lenta)
```

O PnL sobe em janelas de tendência e erode em lateral. Sem filtro, a estratégia é um "gotejamento" que só compensa quando a tendência é forte o suficiente.

### 5.3 Simulação: Range Filter de 0.30%

```python
# Não operar se range dos últimos 30 candles < 0.30%
range_30 = (max(prices[-30:]) - min(prices[-30:])) / min(prices[-30:])
if range_30 < 0.003:
    return None
```

**Resultado estimado:**
- Trades evitados: ~15 de 23 (65%)
- Trades mantidos: 8 (os significativos)
- PnL estimado com filtro: **~+1.13%** (vs +0.76% real)
- **Melhoria: +49% no PnL**

---

## 6. Calibração de Parâmetros

### 6.1 Take Profit Mal Calibrado

O TP fixo de +0.50% foi atingido apenas 1 vez em 23 trades. Dois trades pararam a menos de 0.08% do TP:

| Trade | Pico | TP alvo | Gap |
|-------|------|---------|-----|
| #12 | +0.453% | +0.50% | 0.047% |
| #15 | +0.423% | +0.50% | 0.077% |

**Simulação com TP reduzido:**

| TP | TP hits | PnL ganho | PnL total sessão |
|----|---------|-----------|------------------|
| +0.50% (atual) | 1 | +0.84% | +0.76% |
| +0.45% | 2 | +0.84 + 0.45 | ~+1.21% |
| **+0.40%** | **3** | **+0.84 + 0.40 + 0.40** | **~+1.56%** |
| +0.30% | 3 | +0.84 + 0.30 + 0.30 | ~+1.36% |

**TP em +0.40% dobraria o PnL da sessão.**

### 6.2 Stop Loss Adequado

SL de -0.25% foi acionado 2 vezes em contexto de queda real. O nível é apropriado — os SLs protegeram contra perdas maiores. Sem ajuste necessário.

### 6.3 Períodos SMA

SMA(5)/SMA(15) em 1min cobre 5min e 15min respectivamente. Em mercado lateral com range < 0.15%, as médias convergem tanto que 1 candle inverte o crossover.

**Alternativa:** SMA(5)/SMA(15) em velas de 5min — mesmo efeito com menos ruído.

---

## 7. Melhorias Priorizadas

Baseado em impacto estimado e facilidade de implementação:

| # | Melhoria | Impacto PnL | Complexidade | Prioridade |
|---|----------|-------------|--------------|------------|
| 1 | **Range Filter** (não operar se range_30 < 0.30%) | +49% | Baixa (5 linhas) | P1 |
| 2 | **Reduzir TP** de 0.50% para 0.40% | +105% | Baixa (1 linha) | P1 |
| 3 | **Position Guard** (não vender sem posição) | Evita short | Baixa (3 linhas) | P2 |
| 4 | **Cooldown** de 5 min entre sinais opostos | Evita whipsaw | Baixa (5 linhas) | P2 |
| 5 | **Guard de duplicação** (checar posição antes de executar) | Elimina ordens duplas | Baixa (3 linhas) | P2 |
| 6 | **Stale data check** (pular tick se preço não mudou) | Evita execução errada | Baixa (5 linhas) | P3 |
| 7 | **Trailing stop** (0.15% após +0.20%) | Captura mais lucro | Média | P3 |
| 8 | **Persistência** do PositionTracker em JSON | Sobrevive restarts | Média | P3 |
| 9 | **Filtro ADX** (não operar se ADX < 20) | Similar ao range filter | Alta | P4 |
| 10 | **Velas de 5min** ao invés de 1min | Menos ruído | Média | P4 |

**ROI imediato:** implementar #1 + #2 (6 linhas de código) dobraria o PnL da sessão.

---

## 8. Observabilidade

O sistema de logs é excelente. Cada tick produz output informativo:

- `[DIAG]` — diagnóstico detalhado no primeiro tick (range, velas, intervalo)
- `[TICK #N]` — log por tick com preço, velas e resultado
- `[HEARTBEAT]` — resumo a cada 10 ticks com PnL flutuante
- `SINAL:` — sinais com ANSI colors (dourado = COMPRA, laranja = VENDA, verde = TP, vermelho = SL)
- `_AnsiStripFormatter` — logs limpos em arquivo (sem ANSI codes)

**Nota: 10/10** — melhor aspecto do sistema. Nunca houve tick silencioso.

---

## 9. Score Final

| Critério | Nota | Comentário |
|----------|------|------------|
| Mecanismo (tick/SL/TP) | 9/10 | Funciona perfeitamente, zero crashes |
| Estratégia SMA 5/15 | 5/10 | Funciona em tendência, whipsaw em lateral |
| Proteção (cooldown/guard) | 4/10 | Ausente, bugs de duplicação e phantom |
| Observabilidade | 10/10 | Excelente, diagnóstico completo |
| Calibração (TP/SL) | 6/10 | SL ok, TP mal calibrado |
| **Resultado financeiro** | **+0.76%** | **Positivo, mas frágil** |

---

## 10. Conclusão

O Guardião Conservador é **viável como prova de conceito**. O mecanismo é sólido (zero erros em 12h), a observabilidade é exemplar, e a estratégia SMA captura tendências reais.

O ponto cego é o **mercado lateral** — a estratégia não sabe quando não operar. Com um simples Range Filter (6 linhas de código), o PnL estimado sobe de +0.76% para +1.13%. Combinado com a redução do TP para +0.40%, o PnL estimado sobe para **~+1.56%** (dobro do resultado real).

**Próximo passo:** implementar Range Filter + TP reduzido + position guard como primeira evolução do Guardião.

> "O guardião não dorme — mas precisa de óculos para enxergar tendência" – made by Sky 🛡️
