# Plano: Guardião Conservador (SKY-35)

## Contexto

O módulo `core/paper` tem domain, ports, adapters e application 100% implementados. O que falta para o **primeiro trade automático** é:

1. Uma **estratégia de trading** real (atualmente o StrategyWorker é stub que só faz log)
2. **Conectar** o StrategyWorker ao ExecutorDeOrdem → BrokerPort → EventBus
3. **Wiring** no orchestrator para injetar dependências reais

O Guardião Conservador é uma estratégia SMA crossover conservadora:
- SMA 5 cruza acima da SMA 15 → COMPRA
- SMA 5 cruza abaixo da SMA 15 → VENDA
- Posição única por ticker (não acumula)

---

## Arquitetura: Estratégias como Domain Objects

```
src/core/paper/domain/strategies/
├── __init__.py
├── protocol.py          # StrategyProtocol (interface)
├── signal.py            # SinalEstrategia, DadosMercado, TipoSinal
├── position_tracker.py  # PositionTracker (SL/TP por ticker)
└── guardiao_conservador.py  # GuardiaoConservador (SMA 5/15)
```

**Por que no domain?** Estratégias são regras de negócio puras — não dependem de infraestrutura. Recebem dados de mercado (VO) e retornam sinais (VO). Testáveis sem mocks pesados.

---

## Arquivos Novos (4)

### 1. `domain/strategies/signal.py` — Value Objects de sinal

```python
class TipoSinal(str, Enum):
    COMPRA = "compra"
    VENDA = "venda"
    NEUTRO = "neutro"

@dataclass(frozen=True)
class DadosMercado:
    ticker: str
    preco_atual: Decimal
    historico_precos: tuple[Decimal, ...]  # últimos N períodos

@dataclass(frozen=True)
class SinalEstrategia:
    ticker: str
    tipo: TipoSinal
    preco: Decimal
    razao: str  # "SMA5 cruzou acima de SMA15"
    timestamp: datetime
```

### 2. `domain/strategies/protocol.py` — Interface

```python
class StrategyProtocol(Protocol):
    name: str
    def evaluate(self, dados: DadosMercado) -> SinalEstrategia | None: ...
```

### 3. `domain/strategies/position_tracker.py` — Rastreamento de posição

- Mantém posição aberta por ticker
- Stop Loss / Take Profit configuráveis
- `check_price(preco_atual) → SinalEstrategia | None` — dispara saída se preço atingir SL/TP

### 4. `domain/strategies/guardiao_conservador.py` — A estratégia

- SMA(5) vs SMA(15) crossover
- `_calculate_sma(prices, period) → Decimal`
- `_detect_crossover(short_sma, long_sma, prev_short, prev_long) → TipoSinal`
- `evaluate(DadosMercado) → SinalEstrategia | None`

---

## Arquivos Modificados

### 5. `facade/sandbox/workers/strategy_worker.py` — Stub → real + observabilidade

**Modos:** Real (com strategy/datafeed/executor/tracker) e Legacy (backward-compat)

**Observabilidade embutida:**
- `[DIAG]` — diagnóstico no primeiro tick: range dos dados, qtd de velas, intervalo
- `[TICK #N]` — log por tick: preço, velas recebidas, resultado da estratégia
- `[HEARTBEAT]` — resumo a cada 10 ticks: contadores de sinais e erros
- Contadores: `_tick_count`, `_signal_count`, `_error_count`

```python
class StrategyWorker(BaseWorker):
    def __init__(
        self,
        strategy: StrategyProtocol,
        datafeed: DataFeedPort,
        executor: ExecutorDeOrdem,
        position_tracker: PositionTracker,
        tickers: list[str],
        periodo_historico: int = 5,
        intervalo_historico: str = "1m",  # ← velas de 1 minuto!
        quantity: int = 100,
    ): ...
```

### 6. `ports/data_feed_port.py` — Parâmetro `intervalo`

O `obter_historico` agora aceita `intervalo: str = "1d"` (backward-compat). Valores comuns:
- `"1d"` — fechamento diário (default, legado)
- `"1h"` — velas de 1 hora
- `"1m"` — velas de 1 minuto (usado pelo Guardião)

### 7. `adapters/data_feeds/yahoo_finance_feed.py` — Propaga intervalo

O `_buscar_historico` agora recebe o intervalo e passa ao `yf.Ticker.history()`.

**Limitação Yahoo Finance:** intervalo `"1m"` suporta no máximo 8 dias de histórico.

### 8. `domain/__init__.py` — Exportar strategies

---

## Wiring: `run_orchestrator.py`

```python
# Criar dependências
datafeed = YahooFinanceFeed()
broker = PaperBroker(feed=datafeed)
event_bus = get_event_bus()

class SimpleValidator:
    async def validar_e_criar_ordem(self, ticker, lado, quantidade, preco_limit=None):
        return OrdemCriada(...)

executor = ExecutorDeOrdem(broker=broker, datafeed=datafeed, event_bus=event_bus, validator=SimpleValidator())

# Estratégia com SL/TP para ticks de 1 minuto
strategy = GuardiaoConservador()
tracker = PositionTracker(stop_loss_pct=Decimal("0.0025"), take_profit_pct=Decimal("0.005"))

strategy_worker = StrategyWorker(
    strategy=strategy,
    datafeed=datafeed,
    executor=executor,
    position_tracker=tracker,
    tickers=["BTC-USD"],
    periodo_historico=5,       # 5 dias
    intervalo_historico="1m",  # velas de 1 minuto (~6000 pontos)
)
```

---

## Lições Aprendidas — Overnight Bug

### Problema
O bot rodou 7.5h sem executar nenhum trade, mesmo com cruzamentos SMA visíveis no gráfico.

### Causa Raiz
O `obter_historico` retornava **dados diários** (`interval="1d"`) enquanto a estratégia analisava como se fossem **dados de 1 minuto**. A estratégia "funcionava" — só analisava o universo errado. E era **completamente invisível** porque nenhum tick produzia log.

### Correções
1. Parâmetro `intervalo` no port + adapter (backward-compat)
2. StrategyWorker com `intervalo_historico="1m"`
3. Observabilidade: `[DIAG]`, `[TICK]`, `[HEARTBEAT]` — nunca mais tick silencioso
4. Diagnóstico no primeiro tick valida range e quantidade de dados

---

## Sequência TDD (8 passos)

| # | Arquivo | Teste | Status |
|---|---------|-------|--------|
| 1 | `signal.py` | `test_signal_creation_and_types` | ✅ |
| 2 | `protocol.py` | `test_strategy_protocol_duck_typing` | ✅ |
| 3 | `position_tracker.py` | `test_tracker_sl_tp_trigger` | ✅ |
| 4 | `guardiao_conservador.py` | `test_sma_crossover_buy_sell` | ✅ |
| 5 | `strategy_worker.py` | `test_worker_tick_calls_strategy` | ✅ |
| 6 | GREEN — implementar todos | ✅ |
| 7 | REFACTOR — limpar, renomear | ✅ |
| 8 | Wiring no `run_orchestrator.py` | teste de integração manual | 🔲 |

---

## Gatilho de Sucesso

```
COMPRA BTC-USD @ $XX,XXX.XX (SMA5 cruzou acima de SMA15)
```

Esse log no console = Missão A completa.

---

## Verificação

1. `python -m pytest tests/unit/paper/domain/strategies/ -v` — todos verdes
2. `python -m pytest tests/ -k "guardiao or strategy" -v` — específicos
3. Rodar `run_orchestrator.py` e verificar:
   - `[DIAG]` mostra velas de 1m com range correto
   - `[TICK #N]` aparece a cada 60s com preço e status
   - `[HEARTBEAT]` a cada 10 ticks

> "O guardião não dorme enquanto o mercado está aberto" – made by Sky 🛡️
