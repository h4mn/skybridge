## Context

O Guardião Conservador v1 usa DI crossover como único gatilho de entrada. Após SL, +DI já está dominante — sem novo crossover, não há re-entrada. Em 7 dias de dados reais (BTC-USD 1m), 65% dos BUY signals ocorreram com ADX 25-30 (zona de tendência fraca), causando whipsaws frequentes. O SL fixo -0.20% é insuficiente — o ML validou 0.50% fixo como ponto doce.

O PositionTracker atual suporta 1 posição por ticker. Precisa evoluir para suportar o Dual Entry System e preparar a arquitetura para integração com brokers reais (MT5, Binance).

## Goals / Non-Goals

**Goals:**
- SL fixo 0.50% (validado pelo ML)
- Dual Entry System: pullback Fibonacci (Entry 1) + breakout + confirmação ADX (Entry 2)
- Swing low lookback para calcular níveis Fibonacci
- PositionTrackerPort + SimpleTracker (arquitetura forward-compatible MT5)
- Estado de re-entrada rastreado como Orders pendentes
- Zero regressão: KPIs existentes não podem piorar

**Non-Goals:**
- SL dinâmico por ADX (tiers) — o ML mostrou 0.50% fixo como ponto doce
- HedgeTracker — futura implementação para brokers hedge (Binance FTW)
- Deal (conceito MT5) — não implementar agora, só deixar caminho aberto
- Integração real com MT5 — somente preparação arquitetural
- Novos indicadores (EMA, RSI, Bollinger)
- Interface gráfica / dashboard

## Decisions

### D1: SL fixo 0.50%

**Decisão**: SL fixo em 0.50% para todas as entradas.

**Alternativa**: SL dinâmico por tiers de ADX. Rejeitado — o ML mostrou 0.50% fixo como ponto doce.

**Racional**: Valor fixo é mais fácil de backtestar, debugar e raciocinar. Remove complexidade sem perder performance.

### D1b: Breakeven Standalone (+0.10%)

**Decisão**: Quando o preço atinge +0.10% de lucro, mover SL para o ponto de entrada (0%). O breakeven é independente do trailing stop — ativa primeiro (+0.10% vs +0.20%), e o SL vai exatamente para o preço de entrada (não usa distância).

**Alternativa A**: Breakeven integrado ao trailing stop. Rejeitado — o trailing ativa em +0.20% e usa distância de 0.15%. O breakeven precisa ativar antes (+0.10%) e garantir zero perda, não uma distância.

**Alternativa B**: Sem breakeven. Rejeitado — em 40h de trading real (81k ticks), o bot teve 21 trades com WR=29% e P&L de -$78.993. Trades que atingiram +0.10% mas voltaram para negativo foram a principal fonte de perda.

**Racional**: O breakeven standalone é o primeiro mecanismo de proteção de lucro. Quando atinge +0.10%, o pior cenário passa a ser zero (não perda). Isso reduz o drawdown sem sacrificar trades que vão para TP. Executa no preço de entrada (não no preço de mercado), garantindo saída limpa.

**Camada de proteção (ordem de ativação):**
```
0.00%  → Entrada (SL original: -0.50%)
+0.10% → Breakeven: SL → 0.00% (ponto de entrada)
+0.20% → Trailing Stop ativa (distância 0.15%)
+TP%   → Take Profit (dinâmico por ADX)
```

### D2: PositionTrackerPort + SimpleTracker (forward-compatible MT5)

**Decisão**: Extrair interface `PositionTrackerPort` do PositionTracker atual. Renomear implementação para `SimpleTracker` (netting mode — 1 posição/ticker). Nomenclatura MT5-compatible: `ticket` (int sequencial), `position_type` (BUY/SELL), `volume`.

**Alternativa**: Manter PositionTracker monolítico e adicionar re-entry state. Rejeitado porque não prepara para brokers reais.

**Racional**: MT5 usa 3 conceitos (Order → Deal → Position). Hoje pulamos Deal. Com a port, o StrategyWorker não sabe se usa SimpleTracker ou HedgeTracker. Futuro: adicionar Deal como camada entre Order e Position, e HedgeTracker para brokers hedge.

```
Hoje:    Order → Position (SimpleTracker, netting)
Futuro:  Order → Deal → Position (HedgeTracker, hedging)
```

### D3: Dual Entry via Orders pendentes (não posições diretas)

**Decisão**: Entry 1 e Entry 2 geram Orders pendentes armazenadas no re-entry state. Quando preço atinge o nível, a Order executa e vira Position via `open_position()`.

**Alternativa**: Abrir posição diretamente quando condições são atendidas. Rejeitado porque não modela corretamente o fluxo MT5 (Order → Position).

**Racional**: Orders pendentes são o modelo correto para "Buy Limit" (Entry 1) e "Buy Stop" condicional (Entry 2). Prepara para quando o broker real receber essas ordens.

### D4: Swing low via lookback simples

**Decisão**: Encontrar o mínimo dos últimos 100 períodos em `evaluate()`. Armazenar como `swing_low` no `_last_indicators`.

**Racional**: Simples, determinístico, sem hiperparâmetros.

### D5: Cooldown em ticks

**Decisão**: Cooldown de re-entrada medido em número de ticks após SL.

**Racional**: No paper trading, o intervalo entre ticks é constante (~60s). Medir em ticks é mais simples e testável.

### D6: SimpleTracker — modo atual (netting)

**Decisão**: SimpleTracker mantém comportamento atual: 1 posição por ticker. `open_position()` substitui posição existente. Entry 1 e Entry 2 são **mutuamente exclusivas** no SimpleTracker — só executa se sem posição.

**Futuro (HedgeTracker)**: Ambas podem executar, criando sub-posições independentes com tickets próprios. SL/TP por ticket.

**Racional**: Evita over-engineering agora. O SimpleTracker resolve o caso paper trading. HedgeTracker é adicionado quando integrar com broker real.

### D7: Multi-Entry Strategy — DI cross + ADX surge

**Decisão**: Duas estratégias de entrada independentes no `evaluate()`, cada uma com seus próprios filtros condicionais. Gap mínimo reduzido de 5 para 3 (mais sensível sem perder proteção anti-whipsaw).

**Entrada 1 — DI cross (COMPRA):**
```
+DI cruza acima de -DI
  AND ADX >= threshold (tendência forte)
  AND -DI < ADX (força da tendência domina o contra-tendência)
  AND gap |+DI - -DI| >= 3 (anti-whipsaw)
```

**Entrada 2 — ADX surge (COMPRA):**
```
ADX cruza de abaixo para acima do threshold (prev_adx < threshold <= curr_adx)
  AND +DI > -DI (direção já é compradora)
  AND gap |+DI - -DI| >= 3 (anti-whipsaw)
```

**Alternativa**: Manter apenas DI crossover. Rejeitado — perde a oportunidade de entrar quando a tendência dispara de força sem novo crossover DI.

**Racional**: As duas entradas capturam momentos diferentes do ciclo de tendência:
- **DI cross**: entra na virada — o momento exato em que a direção muda. O filtro `-DI < ADX` garante que a força da tendência já domina o contra-tendência, evitando entradas em crossovers fracos onde o ADX não sustenta.
- **ADX surge**: entra na aceleração — o ADX subindo acima do threshold confirma que a tendência está ganhando força. O filtro `+DI > -DI` garante que a direção já está correta.

**VENDA**: Análoga para os dois casos (DI cruza pra baixo com +DI < ADX; ADX surge com -DI > +DI).

**Trade-off**: Mais sinais = mais trades = mais exposure. Mitigação: gap mínimo e filtros condicionais reduzem whipsaws.

### D8: Dual Entry — Entry 2 simplificado (ADX above, sem cruzamento)

**Decisão**: Na Dual Entry (re-entry system do worker), Entry 2 agora requer apenas `ADX >= threshold` em vez de `ADX cruza acima do threshold`. O preço já precisa estar acima do crossover_price (breakout confirmado).

**Racional**: O Entry 2 acontece após o crossover inicial. Se o preço já rompeu o nível do crossover, basta confirmar que a tendência está forte (ADX acima). Exigir cruzamento do ADX é restritivo demais — a tendência já pode estar forte desde o crossover original.

## Risks / Trade-offs

- **[SL 0.50% largo em lateral]** → Em mercado lateral, perdas maiores. Mitigação: filtro ADX >= 25 bloqueia entradas em lateral.
- **[Entry 1 pode não ser testada]** → Se não retrai ao 61.8%, não executa. Aceitável — Entry 2 como fallback.
- **[SimpTracker limita a 1 posição]** → Não suporta aumento de posição. Mitigação: é o comportamento correto para netting. HedgeTracker resolve quando necessário.
- **[Falso breakout]** → Entry 2 pode entrar em falso rompimento. Mitigação: ADX cruzando threshold filtra whipsaws.

> "Design é a arte de decidir o que NÃO fazer" – made by Sky 🎯
