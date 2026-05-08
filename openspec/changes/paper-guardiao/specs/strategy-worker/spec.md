## MODIFIED Requirements

### Requirement: StrategyWorker com injeção de dependências
O StrategyWorker SHALL aceitar via construtor: `strategy` (StrategyProtocol), `datafeed` (DataFeedPort), `executor` (ExecutorDeOrdem), `position_tracker` (PositionTracker), `tickers` (list[str]), e `periodo_historico` (int, default 30).

#### Scenario: Criar worker com dependências
- **WHEN** criar `StrategyWorker(strategy, datafeed, executor, tracker, tickers=["BTC-USD"])`
- **THEN** o worker SHALL ser inicializado com todas as dependências e `name="strategy-guardiao-conservador"`

#### Scenario: Worker sem tickers
- **WHEN** criar `StrategyWorker` com `tickers=[]`
- **THEN** `_do_tick()` SHALL ser no-op (nada a processar)

### Requirement: Ciclo de tick busca dados e avalia estratégia
O `_do_tick()` SHALL iterar sobre os tickers configurados, buscar dados de mercado via DataFeedPort, avaliar a estratégia e executar ordens via ExecutorDeOrdem quando há sinal.

#### Scenario: Tick com sinal de compra
- **WHEN** `_do_tick()` executa e a estratégia retorna `TipoSinal.COMPRA`
- **THEN** SHALL chamar `executor.executar_ordem(ticker, Lado.COMPRA, quantidade=100)` e registrar posição no `position_tracker`

#### Scenario: Tick com sinal de venda
- **WHEN** `_do_tick()` executa e a estratégia retorna `TipoSinal.VENDA`
- **THEN** SHALL chamar `executor.executar_ordem(ticker, Lado.VENDA, quantidade=100)` e fechar posição no `position_tracker`

#### Scenario: Tick sem sinal
- **WHEN** `_do_tick()` executa e a estratégia retorna `None`
- **THEN** SHALL não chamar `executor.executar_ordem()` (apenas verificar SL/TP)

#### Scenario: Tick com erro no datafeed
- **WHEN** `_do_tick()` executa e `datafeed.obter_cotacao()` lança exceção
- **THEN** o erro SHALL ser capturado e logado sem crashar o worker (BaseWorker garante isso)

### Requirement: Verificação de Stop Loss e Take Profit
O `_do_tick()` SHALL verificar Stop Loss e Take Profit para cada ticker com posição aberta antes de avaliar a estratégia.

#### Scenario: Stop Loss acionado durante tick
- **WHEN** `_do_tick()` executa e `position_tracker.check_price()` retorna sinal de venda por SL
- **THEN** SHALL executar ordem de venda e fechar posição, sem avaliar estratégia para esse ticker

#### Scenario: Take Profit acionado durante tick
- **WHEN** `_do_tick()` executa e `position_tracker.check_price()` retorna sinal de venda por TP
- **THEN** SHALL executar ordem de venda e fechar posição, sem avaliar estratégia para esse ticker

### Requirement: Construtor backward-compatible
O StrategyWorker SHALL manter compatibilidade com o construtor antigo (strategy_name, on_suggestion) para não quebrar testes existentes.

#### Scenario: Construtor antigo ainda funciona
- **WHEN** criar `StrategyWorker(strategy_name="test", on_suggestion=callback)`
- **THEN** SHALL funcionar como antes (stub behavior)

> "O worker é a ponte entre a estratégia e o mercado" – made by Sky 🔗
