## Why

O módulo `core/paper` tem domain, ports, adapters e application 100% implementados, mas o StrategyWorker é um stub que só faz log. Não existe nenhuma estratégia de trading real conectada ao pipeline de execução (ExecutorDeOrdem → BrokerPort → EventBus). O Guardião Conservador é a primeira estratégia funcional — SMA crossover — que viabiliza o primeiro trade automático (Missão A do roadmap).

## What Changes

- Novo pacote `domain/strategies/` com Value Objects de sinal (TipoSinal, DadosMercado, SinalEstrategia) e StrategyProtocol
- Implementação do Guardião Conservador: estratégia SMA(5) vs SMA(15) crossover com detecção de cruzamento
- PositionTracker: rastreamento de posição aberta com Stop Loss (5%) e Take Profit (10%) por ticker
- Refatoração do StrategyWorker de stub para worker real com injeção de dependências (DataFeedPort, ExecutorDeOrdem)
- Wiring no `run_orchestrator.py` para conectar dependências reais (YahooFinanceFeed, PaperBroker, EventBus)

## Capabilities

### New Capabilities
- `trading-strategies`: Protocolo de estratégias pluggable + Value Objects de sinal (TipoSinal, DadosMercado, SinalEstrategia)
- `guardiao-conservador`: Estratégia SMA crossover conservadora (SMA5 vs SMA15) com posição única por ticker
- `position-tracker`: Rastreamento de posição com Stop Loss / Take Profit automatizados

### Modified Capabilities
- `strategy-worker`: Refatoração de stub para worker real com injeção de DataFeedPort, ExecutorDeOrdem e PositionTracker

## Impact

- **Novos arquivos**: 4 em `domain/strategies/` (protocol, signal, position_tracker, guardiao_conservador) + `__init__.py`
- **Arquivos modificados**: `facade/sandbox/workers/strategy_worker.py`, `domain/__init__.py`, `facade/sandbox/run_orchestrator.py`
- **Dependências**: Usa interfaces existentes (DataFeedPort, BrokerPort, EventBus, ExecutorDeOrdem) — sem novas dependências externas
- **Ticker padrão**: BTC-USD (mercado 24/7 para testes)
- **Linear**: SKY-35

> "O guardião não dorme enquanto o mercado está aberto" – made by Sky 🛡️
