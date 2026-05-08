## 1. Estrutura e Value Objects (domain/strategies/)

- [x] 1.1 Criar pacote `domain/strategies/__init__.py` com exports
- [x] 1.2 Implementar `TipoSinal` enum (COMPRA, VENDA, NEUTRO) em `signal.py`
- [x] 1.3 Implementar `DadosMercado` VO (frozen dataclass) em `signal.py`
- [x] 1.4 Implementar `SinalEstrategia` VO (frozen dataclass com to_dict) em `signal.py`
- [x] 1.5 Implementar `StrategyProtocol` (typing.Protocol) em `protocol.py`

## 2. Testes RED — Value Objects e Protocol

- [x] 2.1 Testar `TipoSinal` criação e valores (3 cenários)
- [x] 2.2 Testar `DadosMercado` imutabilidade e criação (2 cenários)
- [x] 2.3 Testar `SinalEstrategia` criação, timestamp auto e to_dict (2 cenários)
- [x] 2.4 Testar `StrategyProtocol` duck typing, None return, sinal return (3 cenários)

## 3. PositionTracker

- [x] 3.1 Implementar `PositionTracker` em `position_tracker.py` (open, close, check_price, list_positions)
- [x] 3.2 Testar open_position, posição duplicada, close_position, posição inexistente (4 cenários)
- [x] 3.3 Testar Stop Loss acionado, não acionado, limite exato (3 cenários)
- [x] 3.4 Testar Take Profit acionado, não acionado, limite exato (3 cenários)
- [x] 3.5 Testar check_price sem posição aberta e list_positions (2 cenários)

## 4. Guardião Conservador

- [x] 4.1 Implementar `_calculate_sma(prices, period)` em `guardiao_conservador.py`
- [x] 4.2 Implementar `_detect_crossover` em `guardiao_conservador.py`
- [x] 4.3 Implementar `evaluate(DadosMercado)` em `guardiao_conservador.py`
- [x] 4.4 Testar SMA com dados suficientes, insuficientes, exatos (3 cenários)
- [x] 4.5 Testar crossover compra, venda, sem crossover, dados insuficientes (4 cenários)
- [x] 4.6 Testar propriedade name e parâmetros configuráveis (2 cenários)

## 5. StrategyWorker (refatoração)

- [x] 5.1 Refatorar `StrategyWorker.__init__` para aceitar dependências reais (strategy, datafeed, executor, tracker, tickers)
- [x] 5.2 Implementar `_do_tick()` com fluxo: busca dados → avalia estratégia → verifica SL/TP → executa ordem
- [x] 5.3 Manter backward-compatibilidade com construtor antigo (strategy_name, on_suggestion)
- [x] 5.4 Testar worker com sinal de compra, venda, sem sinal, erro no datafeed (4 cenários)
- [x] 5.5 Testar verificação SL/TP durante tick (2 cenários)
- [x] 5.6 Testar backward-compatibilidade do construtor antigo (1 cenário)

## 6. Wiring e Integração

- [x] 6.1 Atualizar `domain/__init__.py` para exportar `strategies`
- [x] 6.2 Atualizar `run_orchestrator.py` com wiring real (YahooFinanceFeed, PaperBroker, EventBus, ExecutorDeOrdem)
- [ ] 6.3 Teste de integração manual: rodar orchestrator e verificar log "COMPRA BTC-USD"

> "Tarefas documentadas são promessas cumpridas" – made by Sky 📋
