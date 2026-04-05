# Spec: paper-ports

Interfaces/contratos para brokers, data feeds e repositórios.

## ADDED Requirements

### Requirement: Interface BrokerPort
O sistema SHALL definir uma interface BrokerPort para execução de ordens.

#### Scenario: Conectar ao broker
- **WHEN** o método `conectar()` é chamado
- **THEN** o sistema SHALL estabelecer conexão com o broker

#### Scenario: Enviar ordem
- **WHEN** o método `enviar_ordem(ticker, lado, quantidade, preco_limite)` é chamado
- **THEN** o sistema SHALL retornar ID único da ordem criada

#### Scenario: Cancelar ordem
- **WHEN** o método `cancelar_ordem(ordem_id)` é chamado com ID válido
- **THEN** o sistema SHALL cancelar a ordem e retornar True

#### Scenario: Consultar ordem
- **WHEN** o método `consultar_ordem(ordem_id)` é chamado
- **THEN** o sistema SHALL retornar dicionário com status, quantidade, preço

#### Scenario: Obter saldo
- **WHEN** o método `obter_saldo()` é chamado
- **THEN** o sistema SHALL retornar o saldo disponível

### Requirement: Interface DataFeedPort
O sistema SHALL definir uma interface DataFeedPort para obtenção de dados de mercado.

#### Scenario: Obter cotação
- **WHEN** o método `obter_cotacao(ticker)` é chamado com ticker válido
- **THEN** o sistema SHALL retornar Cotacao com preco, volume, timestamp

#### Scenario: Obter histórico
- **WHEN** o método `obter_historico(ticker, periodo_dias)` é chamado
- **THEN** o sistema SHALL retornar lista de cotações históricas

#### Scenario: Validar ticker
- **WHEN** o método `validar_ticker(ticker)` é chamado
- **THEN** o sistema SHALL retornar True se ticker existe, False caso contrário

### Requirement: Interface RepositoryPort
O sistema SHALL definir uma interface RepositoryPort para persistência.

#### Scenario: Salvar portfolio
- **WHEN** o método `salvar_portfolio(portfolio_id, saldo, usuario_id)` é chamado
- **THEN** o sistema SHALL persistir os dados do portfolio

#### Scenario: Carregar portfolio
- **WHEN** o método `carregar_portfolio(portfolio_id)` é chamado com ID válido
- **THEN** o sistema SHALL retornar dicionário com dados do portfolio

#### Scenario: Salvar ordem
- **WHEN** o método `salvar_ordem(ordem)` é chamado
- **THEN** o sistema SHALL persistir a ordem e retornar seu ID

### Requirement: Interface PortfolioRepositoryPort
O sistema SHALL definir uma interface simplificada PortfolioRepositoryPort para repositório de Portfolio.

#### Scenario: Buscar por ID
- **WHEN** o método `find_by_id(portfolio_id)` é chamado
- **THEN** o sistema SHALL retornar entidade Portfolio

#### Scenario: Buscar padrão
- **WHEN** o método `find_default()` é chamado
- **THEN** o sistema SHALL retornar o portfolio padrão

#### Scenario: Salvar
- **WHEN** o método `save(portfolio)` é chamado
- **THEN** o sistema SHALL persistir o portfolio
