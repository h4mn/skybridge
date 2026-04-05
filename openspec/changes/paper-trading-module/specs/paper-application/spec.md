# Spec: paper-application

Casos de uso CQRS (commands e queries).

## ADDED Requirements

### Requirement: Query ConsultarPortfolio
O sistema SHALL fornecer query para consultar dados do portfolio.

#### Scenario: Consultar portfolio por ID
- **WHEN** `ConsultarPortfolioQuery(portfolio_id="abc123")` é executada
- **THEN** o sistema SHALL retornar PortfolioResult com dados do portfolio específico

#### Scenario: Consultar portfolio padrão
- **WHEN** `ConsultarPortfolioQuery()` é executada sem portfolio_id
- **THEN** o sistema SHALL retornar PortfolioResult do portfolio padrão

### Requirement: Handler PortfolioQueryHandler
O sistema SHALL fornecer handler para processar queries do portfolio.

#### Scenario: Processar consulta
- **WHEN** `handle_consultar(query)` é chamado com query válida
- **THEN** o sistema SHALL retornar PortfolioResult com id, nome, saldos, pnl

#### Scenario: Portfolio não encontrado
- **WHEN** query referencia portfolio inexistente
- **THEN** o sistema SHALL propagar erro do repositório

### Requirement: Result PortfolioResult
O sistema SHALL fornecer objeto de resultado para consultas de portfolio.

#### Scenario: Estrutura do resultado
- **WHEN** um PortfolioResult é retornado
- **THEN** o sistema SHALL incluir campos: id, nome, saldo_inicial, saldo_atual, pnl, pnl_percentual
