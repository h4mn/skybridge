# Tasks: Paper Backlog 2026.03.27

## 1. Fase 1 — Quantity + Money (Domain)

### 1.1 Currency Enum
- [x] 1.1.1 Criar `src/core/paper/domain/currency.py` com enum `Currency`
- [x] 1.1.2 Adicionar moedas: BRL, USD, EUR, GBP, BTC, ETH
- [x] 1.1.3 Adicionar propriedades `is_fiat` e `is_crypto`
- [x] 1.1.4 Criar teste unitário para Currency

### 1.2 Money Value Object
- [x] 1.2.1 Criar `src/core/paper/domain/money.py` com dataclass `Money`
- [x] 1.2.2 Implementar operações: `__add__`, `__sub__`, `__mul__`
- [x] 1.2.3 Implementar `convert_to(rate: Decimal) -> Money`
- [x] 1.2.4 Implementar `format()` com símbolos de moeda
- [x] 1.2.5 Criar `CurrencyMismatchError` para operações inválidas
- [x] 1.2.6 Criar testes unitários para Money

### 1.3 Quantity Value Object
- [x] 1.3.1 Criar `src/core/paper/domain/quantity.py` com `AssetType` enum
- [x] 1.3.2 Criar dataclass `Quantity` com `value`, `precision`, `min_tick`
- [x] 1.3.3 Implementar validação no `__post_init__`
- [x] 1.3.4 Implementar `adjust_to_tick()` para arredondamento
- [x] 1.3.5 Implementar `is_valid_for(ticker: str) -> bool`
- [x] 1.3.6 Criar testes unitários para Quantity

### 1.4 QuantityRules Service
- [x] 1.4.1 Criar `src/core/paper/services/quantity_rules.py`
- [x] 1.4.2 Criar `QuantitySpec` dataclass (min, max, precision, lot_size)
- [x] 1.4.3 Implementar `for_ticker(ticker, exchange) -> QuantitySpec`
- [x] 1.4.4 Mapear tickers B3 (lote padrão e fracionário)
- [x] 1.4.5 Mapear cripto principal (BTC, ETH)
- [x] 1.4.6 Criar testes unitários para QuantityRules

---

## 2. Fase 2 — Currency Converter

### 2.1 CurrencyConverterPort
- [x] 2.1.1 Criar `src/core/paper/ports/currency_converter_port.py`
- [x] 2.1.2 Definir protocol com `get_rate(from, to) -> Decimal`
- [x] 2.1.3 Definir protocol com `convert(money, to) -> Money`

### 2.2 YahooCurrencyAdapter
- [x] 2.2.1 Criar `src/core/paper/adapters/currency/yahoo_currency_adapter.py`
- [x] 2.2.2 Mapear pares de moeda para tickers Yahoo (BRL=X, EURBRL=X)
- [x] 2.2.3 Implementar `get_rate()` usando `yfinance`
- [x] 2.2.4 Implementar cache em memória com TTL 5min
- [x] 2.2.5 Criar testes unitários para YahooCurrencyAdapter

### 2.3 Integrar no DI
- [x] 2.3.1 Adicionar `get_currency_converter()` em `dependencies.py`
- [x] 2.3.2 Injetar converter nos handlers que precisam (disponível para Fase 3)

---

## 3. Fase 3 — Portfolio Multi-Moeda

### 3.1 PositionView e PortfolioView
- [x] 3.1.1 Criar `src/core/paper/domain/portfolio_view.py`
- [x] 3.1.2 Criar `PositionView` com ticker, quantity, market_price (Money)
- [x] 3.1.3 Criar `PortfolioView` com positions e base_currency
- [x] 3.1.4 Implementar `total_by_currency() -> dict[Currency, Money]`
- [x] 3.1.5 Implementar `total_converted(converter, target) -> Money`

### 3.2 Atualizar Handlers
- [x] 3.2.1 Atualizar `ConsultarPortfolioHandler` para usar Money
- [x] 3.2.2 Adicionar parâmetro `base_currency` opcional
- [x] 3.2.3 Calcular PnL com conversão quando necessário

### 3.3 Atualizar API
- [x] 3.3.1 Adicionar query param `base_currency` em `/portfolio`
- [x] 3.3.2 Atualizar response schema com campo `currency`
- [x] 3.3.3 Smoke test: BTC-USD + PETR4-BRL consolidados em BRL

---

## 4. Fase 4 — Orchestrator + Workers (Sandbox)

### 4.1 Worker Base
- [x] 4.1.1 Criar `src/core/paper/facade/sandbox/workers/base.py`
- [x] 4.1.2 Definir protocol `Worker` com name, start, stop, tick
- [x] 4.1.3 Criar `BaseWorker` com implementação comum

### 4.2 PaperOrchestrator
- [x] 4.2.1 Criar `src/core/paper/facade/sandbox/orchestrator.py`
- [x] 4.2.2 Implementar `register(worker)`
- [x] 4.2.3 Implementar `run()` com loop asyncio
- [x] 4.2.4 Implementar `shutdown()` graceful
- [x] 4.2.5 Implementar tratamento de erro por worker

### 4.3 PositionWorker
- [x] 4.3.1 Criar `src/core/paper/facade/sandbox/workers/position_worker.py`
- [x] 4.3.2 Implementar tick que atualiza cotações
- [x] 4.3.3 Implementar verificação de ordens limite
- [x] 4.3.4 Implementar callback para mudanças de PnL

### 4.4 StrategyWorker (Stub)
- [x] 4.4.1 Criar `src/core/paper/facade/sandbox/workers/strategy_worker.py`
- [x] 4.4.2 Definir interface para estratégias plugáveis
- [x] 4.4.3 Implementar stub que apenas loga

### 4.5 BacktestWorker (Stub)
- [x] 4.5.1 Criar `src/core/paper/facade/sandbox/workers/backtest_worker.py`
- [x] 4.5.2 Definir interface para backtest
- [x] 4.5.3 Implementar stub que apenas loga

### 4.6 Experimento no Sandbox
- [x] 4.6.1 Criar script `run_orchestrator.py` no sandbox
- [x] 4.6.2 Configurar PositionWorker com intervalo 10s
- [x] 4.6.3 Testar shutdown graceful (Ctrl+C)
- [x] 4.6.4 Documentar uso no README do sandbox

---

## 5. Validação Final

### 5.1 Testes
- [x] 5.1.1 Todos os testes unitários passando
- [x] 5.1.2 Smoke test de câmbio com Yahoo real
- [x] 5.1.3 Smoke test de portfolio multi-moeda
- [x] 5.1.4 Smoke test de orchestrator

### 5.2 Documentação
- [x] 5.2.1 Atualizar troubleshooting.md com novos cenários
- [x] 5.2.2 Atualizar operations_reference.md com novos endpoints
- [x] 5.2.3 Criar README do sandbox com exemplos de orchestrator
