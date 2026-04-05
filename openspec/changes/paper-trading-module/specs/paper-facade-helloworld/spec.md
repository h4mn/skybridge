# Spec: paper-facade-helloworld

Playground completo de paper trading com dados reais.

## ADDED Requirements

### Requirement: Facade HelloWorldFacade
O sistema SHALL fornecer facade que expõe playground completo de paper trading.

#### Scenario: Inicialização
- **WHEN** HelloWorldFacade é instanciado
- **THEN** o sistema SHALL configurar YahooFinanceFeed, JsonFilePaperBroker, FastAPI app

### Requirement: Endpoint GET /
O sistema SHALL fornecer endpoint de health check.

#### Scenario: Health check
- **WHEN** GET / é chamado
- **THEN** o sistema SHALL retornar status "ok" com mensagem de boas-vindas

### Requirement: Endpoint GET /health
O sistema SHALL fornecer endpoint de verificação de saúde.

#### Scenario: Health verify
- **WHEN** GET /health é chamado
- **THEN** o sistema SHALL retornar status "healthy"

### Requirement: Documentação OpenAPI
O sistema SHALL gerar documentação automática da API.

#### Scenario: Acessar Swagger UI
- **WHEN** GET /docs é chamado
- **THEN** o sistema SHALL retornar interface Swagger com todos os endpoints

#### Scenario: Acessar OpenAPI JSON
- **WHEN** GET /openapi.json é chamado
- **THEN** o sistema SHALL retornar especificação OpenAPI completa

### Requirement: Startup/Shutdown lifecycle
O sistema SHALL gerenciar ciclo de vida da conexão com data feed.

#### Scenario: Conectar ao iniciar
- **WHEN** a aplicação inicia
- **THEN** o sistema SHALL conectar ao YahooFinanceFeed

#### Scenario: Desconectar ao parar
- **WHEN** a aplicação para
- **THEN** o sistema SHALL desconectar do YahooFinanceFeed
