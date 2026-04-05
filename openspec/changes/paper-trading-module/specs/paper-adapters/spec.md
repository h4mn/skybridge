# Spec: paper-adapters

Implementações concretas dos ports (PaperBroker, YahooFinanceFeed, repositórios).

## ADDED Requirements

### Requirement: Adapter PaperBroker
O sistema SHALL fornecer PaperBroker que simula execução de ordens com preços reais.

#### Scenario: Executar ordem de compra
- **WHEN** `enviar_ordem("PETR4.SA", "COMPRA", 100)` é chamado com saldo suficiente
- **THEN** o sistema SHALL debitar saldo, criar posição, retornar ID da ordem

#### Scenario: Executar ordem de venda
- **WHEN** `enviar_ordem("PETR4.SA", "VENDA", 100)` é chamado com posição suficiente
- **THEN** o sistema SHALL creditar saldo, reduzir posição, retornar ID da ordem

#### Scenario: Compra com saldo insuficiente
- **WHEN** ordem de compra excede saldo disponível
- **THEN** o sistema SHALL lançar SaldoInsuficienteError

#### Scenario: Venda sem posição
- **WHEN** ordem de venda é feita sem posição no ativo
- **THEN** o sistema SHALL lançar ValueError

#### Scenario: Listar posições marcadas a mercado
- **WHEN** `listar_posicoes_marcadas()` é chamado
- **THEN** o sistema SHALL retornar posições com preco_atual, pnl, pnl_percentual

### Requirement: Adapter YahooFinanceFeed
O sistema SHALL fornecer YahooFinanceFeed que obtém dados reais do Yahoo Finance.

#### Scenario: Obter cotação B3
- **WHEN** `obter_cotacao("PETR4.SA")` é chamado
- **THEN** o sistema SHALL retornar Cotacao com preço atual do Yahoo Finance

#### Scenario: Obter cotação cripto
- **WHEN** `obter_cotacao("BTC-USD")` é chamado
- **THEN** o sistema SHALL retornar Cotacao com preço atual do Bitcoin

#### Scenario: Ticker inválido
- **WHEN** `obter_cotacao("INVALIDO")` é chamado
- **THEN** o sistema SHALL lançar ValueError com mensagem apropriada

#### Scenario: Obter histórico
- **WHEN** `obter_historico("PETR4.SA", 30)` é chamado
- **THEN** o sistema SHALL retornar lista de 30 cotações diárias

### Requirement: Adapter InMemoryPortfolioRepository
O sistema SHALL fornecer repositório em memória para desenvolvimento e testes.

#### Scenario: Criar portfolio padrão automaticamente
- **WHEN** o repositório é instanciado
- **THEN** o sistema SHALL criar um portfolio padrão automaticamente

#### Scenario: Salvar e recuperar
- **WHEN** um portfolio é salvo e depois buscado por ID
- **THEN** o sistema SHALL retornar o mesmo portfolio

### Requirement: Adapter JsonFilePortfolioRepository
O sistema SHALL fornecer repositório com persistência em arquivo JSON.

#### Scenario: Persistir entre sessões
- **WHEN** um portfolio é salvo e o sistema reiniciado
- **THEN** o sistema SHALL recuperar o estado salvo do arquivo

### Requirement: Adapter JsonFilePaperBroker
O sistema SHALL fornecer PaperBroker com persistência em arquivo JSON.

#### Scenario: Persistir estado do broker
- **WHEN** ordens são executadas e o sistema reiniciado
- **THEN** o sistema SHALL recuperar saldo, posições e histórico de ordens
