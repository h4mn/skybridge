# Plano: Guardião Conservador v2 — Bug Fixes + Observabilidade + Calibração

## Contexto

O Guardião Conservador completou seu primeiro dia completo de operação (08/05/2026):
- 16h de uptime, 875 ticks, 31 trades, PnL +0.948%
- **14 bugs de execução**: 6 compras duplicadas + 8 vendas fantasma
- TP fechou em +0.84% ao invés de +0.50% (slippage entre ticks)
- Heartbeat não mostra portfolio/fechados/PnL aberto
- Log não diferencia saída positiva de negativa com cores

As decisões do usuário estão em `.sky/temp-prompt.md` (15 itens). Este plano implementa as melhorias priorizadas.

---

## Decisões do Usuário — Mapeamento

| # | Decisão | Status neste plano |
|---|---------|-------------------|
| 1 | Yahoo API rate limiting | **Confirmado** 1 req/s via yfinance + TTL cache + backoff exponencial. Tick do orchestrator: **1 segundo** |
| 2 | TP/SL executar no preço configurado | **Implementar** (P1) |
| 3 | Sinal duplicado: checar 2 ticks + posição | **Implementar** (P1) |
| 4 | Separar sinal de execução (position guard) | **Implementar** (P1) |
| 5 | Stale data | **Implementar** — não operar enquanto stale, apenas logar |
| 6 | Persistência no restart | **Implementar** — integrar PositionTracker ao JsonFilePaperState existente |
| 7 | Calibrador dinâmico de parâmetros | **Implementar** (P2) — velas **15m** (default) |
| 8 | CSV diário com melhorias + comportamento | **Implementar** (P2) |
| 9 | Velas 5min | **Pular** (futuro: módulo multi-timeframe) |
| 10 | Cooldown | **Pular** (filtros + position guard bastam) |
| 11 | Trailing stop simples + estudo estatístico | **Implementar** (P3: placeholder + SKY-136) |
| 12 | Comparação de estratégias | **Pular** (futuro) |
| 13 | Log verde/vermelho ao fechar posição | **Implementar** (P1) |
| 14 | Heartbeat: portfolio + fechados + PnL aberto | **Implementar** (P1) |

---

## Fase P1 — Bug Fixes + Observabilidade (implementar primeiro)

### 1.1 Position Guard: Eliminar Duplicadas + Fantasmas

**Problema:** O `_do_tick()` não verifica estado de posição antes de executar.
**Solução:** Guard centralizado no `_do_tick()`:

```python
# strategy_worker.py::_do_tick()

# Para COMPRA: só executar se NÃO posicionado
if sinal.tipo == TipoSinal.COMPRA:
    if self._position_tracker.get_position(ticker) is not None:
        continue  # já posicionado
    await self._executor.executar_ordem(...)
    self._position_tracker.open_position(ticker, cotacao.preco)

# Para VENDA: só executar se posicionado
if sinal.tipo == TipoSinal.VENDA:
    if self._position_tracker.get_position(ticker) is None:
        continue  # sem posição, não vender
    await self._executor.executar_ordem(...)
    self._position_tracker.close_position(ticker)
```

**Arquivo:** `src/core/paper/facade/sandbox/workers/strategy_worker.py:206-223`
**Teste:** `test_position_guard_rejeita_compra_duplicada`, `test_position_guard_rejeita_venda_fantasma`

### 1.2 TP/SL com Preço de Threshold (não mercado)

**Problema:** TP de +0.50% fechou em +0.84% porque o preço passou do target entre ticks. O `check_price()` só detecta no tick seguinte, e a ordem executa ao preço atual.
**Solução:** `check_price()` retorna o preço do threshold, não o preço atual:

```python
# position_tracker.py::check_price()
if variacao <= -self._stop_loss_pct:
    preco_saida = entrada * (1 - self._stop_loss_pct)  # preço exato do SL
    return SinalEstrategia(ticker=ticker, tipo=TipoSinal.VENDA, preco=preco_saida, ...)

if variacao >= self._take_profit_pct:
    preco_saida = entrada * (1 + self._take_profit_pct)  # preço exato do TP
    return SinalEstrategia(ticker=ticker, tipo=TipoSinal.VENDA, preco=preco_saida, ...)
```

O executor usa `sinal.preco` como `preco_limite` na ordem. O PaperBroker executa nesse preço ao invés do mercado.

**Arquivos:**
- `src/core/paper/domain/strategies/position_tracker.py:33-58` — retornar preço do threshold
- `src/core/paper/facade/sandbox/workers/strategy_worker.py:163-167` — passar `preco_limite` ao executor
- `src/core/paper/adapters/brokers/paper_broker.py` — usar `preco_limite` quando fornecido

**Teste:** `test_tp_executes_at_threshold_price`, `test_sl_executes_at_threshold_price`

### 1.3 Log Verde/Vermelho ao Fechar Posição

**Problema:** O log mostra "SINAL: VENDA" sem indicar se a posição fechou em lucro ou prejuízo.
**Solução:** Ao fechar posição (VENDA por sinal, SL ou TP), calcular e logar o resultado:

```python
# strategy_worker.py — ao executar VENDA
pos = self._position_tracker.get_position(ticker)
if pos:
    pnl_pct = float((cotacao.preco - pos["preco_entrada"]) / pos["preco_entrada"] * 100)
    pnl_val = float(cotacao.preco - pos["preco_entrada"]) * self._quantity
    cor = _GREEN if pnl_pct >= 0 else _RED
    tag = "LUCRO" if pnl_pct >= 0 else "PERDA"
    self._logger.info(
        f"{cor}{_B}[{tag}] FECHAMENTO {ticker} @ {cotacao.preco} "
        f"| PnL {pnl_pct:+.3f}% (${pnl_val:+,.2f}){_R}"
    )
```

**Arquivo:** `src/core/paper/facade/sandbox/workers/strategy_worker.py` (seção de VENDA)
**Teste:** verificar output do log no teste de integração

### 1.4 Heartbeat Enriquecido

**Problema:** Heartbeat mostra PnL flutuante mas não mostra resultado fechado nem resumo do portfolio.
**Solução:** Adicionar ao `_log_heartbeat()` — heartbeat a cada **60 ticks** (1/min):

```
[HEARTBEAT] ticks=930 | sinais=77 | erros=1
  Portfolio: $8,000,000.00 | Fechados: +$75,498.00 (+0.948%) | Aberto: BTC-USD +$2,300.00 (+0.029%)
```

```python
# strategy_worker.py::_log_heartbeat()
# Adicionar tracking de PnL fechado
self._closed_pnl: Decimal = Decimal("0")  # novo campo no __init__

# Ao fechar posição:
self._closed_pnl += pnl_val

# No heartbeat:
positions = self._position_tracker.list_positions()
open_pnl = ...  # calcular PnL das posições abertas
self._logger.info(
    f"[HEARTBEAT] ticks={self._tick_count} | sinais={self._signal_count} | erros={self._error_count}\n"
    f"  Fechados: ${self._closed_pnl:+,.2f} | Aberto: ${open_pnl:+,.2f} | Posições: {len(positions)}"
)
```

**Arquivo:** `src/core/paper/facade/sandbox/workers/strategy_worker.py`
**Teste:** verificar output no teste de integração

---

## Fase P2 — Calibração Dinâmica + CSV Enriquecido

### 2.1 Calibrador Dinâmico

**Conceito:** Um componente que analisa o histórico recente de preços e sugere/ajusta automaticamente os parâmetros de SL/TP/Range Filter.

**Abordagem inicial (MVP):**
- Calcular ATR(14) em velas de **15m** (default)
- SL = entrada - k1 * ATR (k1 = 1.5)
- TP = entrada + k2 * ATR (k2 = 2.0)
- Range Filter = não operar se ATR normalizado < threshold
- Resultado do teste (09/05): BTC -0.18/+0.24%, PETR4 -0.43/+0.58%

**Arquivo novo:** `src/core/paper/domain/strategies/calibrador_dinamico.py`
- `calibrar(historico_precos) -> ParametrosCalibrados` (dataclass com sl, tp, range_min)
- Puro domain object, sem infraestrutura
- Testável com dados sintéticos

**Integração:** O StrategyWorker chama `calibrador.calibrar(historico)` no início de cada sessão (ou a cada N ticks) e atualiza o PositionTracker com os novos SL/TP.

**Teste:** `test_calibrador_atr_baixa_volatilidade`, `test_calibrador_atr_alta_volatilidade`

### 2.2 CSV Diário Enriquecido

**Arquivo:** `src/core/paper/data/guardiao-desempenho.csv`
**Colunas adicionais:**

```
melhorias_impl    | texto  | quais melhorias estavam ativas no dia (ex: "v2: position_guard+tp_threshold")
range_filter_on   | bool   | range filter estava ativo?
tp_pct_config     | float  | TP configurado no dia
sl_pct_config     | float  | SL configurado no dia
calibrador_on     | bool   | calibrador dinâmico ativo?
avg_holding_min   | float  | tempo médio de posição
trades_tendencia  | int    | trades em tendência (range > 0.5%)
trades_lateral    | int    | trades em lateral (range < 0.3%)
```

---

## Fase P3 — Trailing Stop Simples + Coleta de Dados

### 3.1 Trailing Stop Placeholder

**Regra simples:** Após posição atingir +0.20%, ativar trailing stop a 0.15% do pico.
- Se preço sobe para +0.30%, trailing sobe para +0.15% (do pico)
- Se preço cai 0.15% do pico, executar VENDA
- Nunca abaixo do breakeven (entrada)

**Implementação no PositionTracker:**
```python
def check_price(self, ticker, preco_atual):
    pos = self._positions.get(ticker)
    # ... SL/TP check ...
    
    # Trailing stop (se ativado)
    if pos.get("trailing_active"):
        if preco_atual <= pos["trailing_stop_price"]:
            return SinalEstrategia(tipo=TipoSinal.VENDA, razao="Trailing Stop")
    
    # Ativar trailing após atingir threshold
    pnl_pct = (preco_atual - pos["preco_entrada"]) / pos["preco_entrada"]
    if pnl_pct >= self._trailing_activation_pct:
        pos["trailing_active"] = True
        pos["trailing_stop_price"] = preco_atual * (1 - self._trailing_distance_pct)
    
    # Atualizar trailing stop (sobe junto com o preço)
    if pos.get("trailing_active") and preco_atual > pos.get("peak_price", preco_atual):
        pos["peak_price"] = preco_atual
        pos["trailing_stop_price"] = preco_atual * (1 - self._trailing_distance_pct)
```

**Arquivo:** `src/core/paper/domain/strategies/position_tracker.py`
**Teste:** `test_trailing_stop_apos_020`, `test_trailing_stop_sobe_com_preco`, `test_trailing_stop_nunca_abaixo_breakeven`

### 3.2 Coletor de Dados Pós-Entrada (SKY-136)

**Objetivo:** Alimentar estudo estatístico para calibrar trailing stop real.

**Arquivo novo:** `src/core/paper/facade/sandbox/workers/reversal_collector.py`
- Observa preços pós-entrada por N ticks
- Registra: entrada, pico, tempo_ate_pico, drawdown_max, reversao_pct
- Salva em `src/core/paper/data/estudo-reversao.csv`
- Issue Linear: **SKY-136**

---

## Fase P4 — Rate Limiting + Stale Guard

### 4.1 Rate Limiting: TTL Cache + Backoff Exponencial

**Resultado do teste (09/05/2026):** yfinance 20/20 OK a 1 req/s. Requests diretos sem auth = 429.
**Estratégia:** Limite de 1 req/s ao Yahoo via yfinance, com TTL cache + backoff exponencial como segurança:

```python
# strategy_worker.py
class RateLimiter:
    def __init__(self, min_interval=1.0, max_retries=3):
        self._min_interval = min_interval
        self._max_retries = max_retries

    async def fetch_with_backoff(self, ticker):
        for attempt in range(self._max_retries):
            try:
                data = await self._feed.get_cotacao(ticker)
                return data
            except Exception as e:
                wait = (2 ** attempt) * self._min_interval
                self._logger.warning(f"Rate limit hit, retrying in {wait}s...")
                await asyncio.sleep(wait)
        raise RuntimeError(f"Yahoo API failed after {self._max_retries} retries")
```

**TTL Cache:** Cachear cotações por 30s por ticker. Se mesmo ticker for consultado 2x em 30s, usar cache.

### 4.2 Stale Guard: Não Operar, Apenas Logar

**Regra:** Quando dados stale forem detectados (preço não muda há N ticks), o sistema:
- NÃO executa nenhuma operação de compra/venda
- NÃO pula silenciosamente
- LOGa claramente: `[STALE] Dados defasados detectados para {ticker} — operações suspensas`
- Retoma automaticamente quando dados frescos retornam

```python
# strategy_worker.py::_do_tick()
if self._is_stale(cotacao):
    self._logger.warning(
        f"{_YELLOW}[STALE] {cotacao.ticker} — preço não muda há "
        f"{self._stale_ticks} ticks. Operações suspensas.{_R}"
    )
    return  # não faz nada, apenas loga
```

**Arquivo:** `src/core/paper/facade/sandbox/workers/strategy_worker.py`
**Teste:** `test_stale_guard_nao_operar`, `test_stale_guard_retoma_com_dados_frescos`

---

## Arquivos Modificados

| Arquivo | Mudança | Fase |
|---------|---------|------|
| `workers/strategy_worker.py` | Position guard, log verde/vermelho, heartbeat enriquecido, PnL fechado | P1 |
| `domain/strategies/position_tracker.py` | `check_price()` retorna preço do threshold | P1 |
| `adapters/brokers/paper_broker.py` | Usar `preco_limite` quando fornecido | P1 |
| `data/guardiao-desempenho.csv` | Colunas extras de melhorias e configuração | P2 |
| `domain/strategies/calibrador_dinamico.py` | **NOVO** — Calibração baseada em ATR | P2 |
| `domain/strategies/position_tracker.py` | Trailing stop (ativação + tracking de pico) | P3 |
| `facade/sandbox/workers/reversal_collector.py` | **NOVO** — Coleta dados pós-entrada (SKY-136) | P3 |

---

## Ordem de Implementação (TDD)

### P1 — Bug Fixes + Observabilidade
1. Teste: `test_position_guard_rejeita_compra_duplicada` → RED
2. Teste: `test_position_guard_rejeita_venda_fantasma` → RED
3. Implementar position guard no `_do_tick()` → GREEN
4. Teste: `test_tp_executes_at_threshold_price` → RED
5. Implementar preço de threshold no `check_price()` → GREEN
6. Implementar `preco_limite` no PaperBroker → GREEN
7. Implementar log verde/vermelho ao fechar posição
8. Implementar tracking de `_closed_pnl` e heartbeat enriquecido
9. Rodar testes + integração manual

### P2 — Calibração + CSV
10. Teste: `test_calibrador_atr` → RED
11. Implementar `CalibradorDinamico` → GREEN
12. Integrar calibrador no StrategyWorker
13. Atualizar CSV com colunas extras

### P3 — Coleta de Dados
14. Implementar `ReversalCollector` worker
15. Registrar dados pós-entrada em CSV

### P4 — Rate Limiting + Stale Guard
16. Teste: `test_stale_guard_nao_operar` → RED
17. Teste: `test_stale_guard_retoma_com_dados_frescos` → RED
18. Implementar stale guard no `_do_tick()` → GREEN
19. Implementar TTL cache + backoff exponencial no fetch

---

## Verificação

1. `python -m pytest tests/unit/paper/domain/strategies/ -v` — todos verdes
2. Rodar orchestrator 30min e verificar:
   - Zero "DUPLICADA" no log
   - Zero "VENDA FANTASMA" no log
   - TP fecha em +0.50% (não +0.84%)
   - Log mostra `[LUCRO]` verde ou `[PERDA]` vermelho
   - Heartbeat mostra Fechados + Aberto
3. CSV preenchido ao fim do dia

---

## Fora de Escopo (decisões do usuário)

- Cooldown entre sinais (#10) — posição + filtros bastam
- Velas 5min (#9) — futuro: módulo multi-timeframe
- Comparação de estratégias (#12) — futuro: módulo de criação
- Stale data (#5) — P4: não operar enquanto stale, apenas logar

---

## Fase P5 — Persistência de Estado no Restart

### 5.1 Integrar PositionTracker ao JsonFilePaperState

**Problema:** Reiniciar o orchestrador com posição aberta perde todo o estado — PositionTracker e PnL acumulado são in-memory. O guardião abre nova posição ignorando a existente.

**Infraestrutura existente:**
- `PaperStatePort` (porta): `carregar()` / `salvar()`
- `JsonFilePaperState` (adapter): schema v3 com `posicoes`, `ordens`, `cashbook`, `saldo_inicial`
- Migração automática v1 → v2 → v3
- Atomic writes (tmp + rename)

**Integração necessária:**

1. **PositionTracker** — receber `PaperStatePort` no construtor (opcional)
   - `open_position()` → salva no PaperState
   - `close_position()` → salva no PaperState
   - `__init__()` → restaura posições do PaperState (se houver)
   - Sem PaperState → comportamento atual (in-memory puro)

2. **StrategyWorker** — restaurar `_closed_pnl` do PaperState ao iniciar
   - Somar ordens de venda fechadas anteriores

3. **run_orchestrator.py** — instanciar `JsonFilePaperState` e injetar
   - Caminho: `src/core/paper/data/paper-state.json`
   - Passar para PositionTracker e StrategyWorker

**Arquivos:**
- `src/core/paper/domain/strategies/position_tracker.py` — aceitar PaperStatePort
- `src/core/paper/facade/sandbox/workers/strategy_worker.py` — restaurar closed_pnl
- `src/core/paper/facade/sandbox/run_orchestrator.py` — injetar persistência

**Teste:**
- `test_position_tracker_persist_open_position`
- `test_position_tracker_restore_on_init`
- `test_closed_pnl_restored_from_state`

> "O guardião evolui: de provinha de conceito a operação consistente" – made by Sky 🛡️
