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
    historico_precos: list[Decimal]  # últimos N períodos

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

## Arquivos Modificados (2)

### 5. `facade/sandbox/workers/strategy_worker.py` — Refatorar stub → real

**Antes:** `_do_tick()` só faz log
**Depois:**
```python
class StrategyWorker(BaseWorker):
    def __init__(
        self,
        strategy: StrategyProtocol,
        datafeed: DataFeedPort,
        executor: ExecutorDeOrdem,
        position_tracker: PositionTracker,
        tickers: list[str],
        periodo_historico: int = 30,
    ): ...

    async def _do_tick(self) -> None:
        for ticker in self._tickers:
            # 1. Busca dados de mercado
            historico = await self._datafeed.obter_historico(ticker, self._periodo_historico)
            cotacao = await self._datafeed.obter_cotacao(ticker)

            # 2. Monta DadosMercado
            dados = DadosMercado(ticker, cotacao.preco, [c.preco for c in historico])

            # 3. Avalia estratégia
            sinal = self._strategy.evaluate(dados)
            if sinal and sinal.tipo != TipoSinal.NEUTRO:
                await self._executor.executar_ordem(
                    ticker=sinal.ticker,
                    lado=Lado.COMPRA if sinal.tipo == TipoSinal.COMPRA else Lado.VENDA,
                    quantidade=100,  # fixo por enquanto
                )

            # 4. Verifica SL/TP
            sl_tp_sinal = self._position_tracker.check_price(ticker, cotacao.preco)
            if sl_tp_sinal:
                await self._executor.executar_ordem(...)
```

### 6. `domain/__init__.py` — Exportar strategies

Adicionar `from . import strategies` e `"strategies"` ao `__all__`.

---

## Wiring: `run_orchestrator.py`

```python
# Criar dependências
datafeed = YahooFinanceFeed()  # adapter existente
broker = PaperBroker(feed=datafeed)
event_bus = get_event_bus()
validator = ValidadorDeOrdem(broker)
executor = ExecutorDeOrdem(broker=broker, datafeed=datafeed, event_bus=event_bus, validator=validator)

# Criar estratégia
strategy = GuardiaoConservador()
tracker = PositionTracker(stop_loss_pct=Decimal("0.05"), take_profit_pct=Decimal("0.10"))

# Criar worker com dependências reais
strategy_worker = StrategyWorker(
    strategy=strategy,
    datafeed=datafeed,
    executor=executor,
    position_tracker=tracker,
    tickers=["BTC-USD"],
    periodo_historico=30,
)
```

---

## Sequência TDD (8 passos)

| # | Arquivo | Teste | Status |
|---|---------|-------|--------|
| 1 | `signal.py` | `test_signal_creation_and_types` | RED |
| 2 | `protocol.py` | `test_strategy_protocol_duck_typing` | RED |
| 3 | `position_tracker.py` | `test_tracker_sl_tp_trigger` | RED |
| 4 | `guardiao_conservador.py` | `test_sma_crossover_buy_sell` | RED |
| 5 | `strategy_worker.py` | `test_worker_tick_calls_strategy` | RED |
| 6 | GREEN — implementar todos | GREEN |
| 7 | REFACTOR — limpar, renomear | REFACTOR |
| 8 | Wiring no `run_orchestrator.py` | teste de integração manual | VERIFY |

---

## Gatilho de Sucesso

```
COMPRA BTC-USD @ $XX,XXX.XX (SMA5 cruzou acima de SMA15)
```

Esse log no console = Missão A completa.

---

## Arquivos Críticos (já existentes, somente leitura)

- `src/core/paper/domain/services/executor_ordem.py` — ExecutorDeOrdem + ValidatorProtocol
- `src/core/paper/ports/data_feed_port.py` — Cotacao, DataFeedPort
- `src/core/paper/adapters/brokers/paper_broker.py` — PaperBroker
- `src/core/paper/domain/events/event_bus.py` — EventBus singleton
- `src/core/paper/facade/sandbox/workers/base.py` — BaseWorker
- `src/core/paper/domain/events/ordem_events.py` — Lado enum

---

## Verificação

1. `python -m pytest tests/unit/paper/domain/strategies/ -v` — todos verdes
2. `python -m pytest tests/ -k "guardiao or strategy" -v` — específicos
3. Rodar `run_orchestrator.py` e verificar log "COMPRA BTC-USD" após ~2 ciclos

> "O guardião não dorme enquanto o mercado está aberto" – made by Sky 🛡️
