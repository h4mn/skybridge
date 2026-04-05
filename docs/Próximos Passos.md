  Próximos Passos Possíveis

  Opção A: Tornar o Sistema "Vivo" de Verdade

  Integrar o PositionWorker com dados reais:
  - Buscar cotações via DataFeedPort
  - Atualizar paper_state.json automaticamente
  - Executar ordens limite quando preço atinge target

  Opção B: Estratégias Automatizadas

  Implementar StrategyWorker:
  - Definir interface de estratégia plugável
  - Criar estratégia exemplo (ex: moving average crossover)
  - Callbacks para sugestões de compra/venda

  Opção C: Backtesting

  Implementar BacktestWorker:
  - Carregar dados históricos
  - Simular execução de estratégia
  - Calcular métricas (Sharpe, drawdown, etc.)

  Opção D: Melhorias de Infraestrutura

  - Migrar de JSON para SQLite
  - Adicionar WebSocket para updates em tempo real
  - Integrar com Discord (vi que você abriu SPEC011)