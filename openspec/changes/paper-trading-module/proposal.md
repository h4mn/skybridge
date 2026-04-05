# Paper Trading Module - Documentação OpenSpec

## Why

O módulo `src/core/paper` já está implementado com arquitetura DDD completa, mas não possui documentação OpenSpec formal. Este change documenta o que existe para:

1. Estabelecer a especificação formal do sistema de paper trading
2. Facilitar manutenção e evolução futura
3. Alinhar implementação com documentação

## What Changes

### Arquitetura Documentada
- **Domain Layer**: Entidades (Portfolio), Value Objects (Ticker), Ports (interfaces)
- **Application Layer**: Queries (ConsultarPortfolio), Handlers
- **Adapters Layer**: PaperBroker, YahooFinanceFeed, repositórios (InMemory, JsonFile)
- **Facade Layer**: API REST, MCP Tools, HelloWorld playground

### Capacidades Implementadas
- Sistema de paper trading com dados reais do Yahoo Finance
- Execução de ordens de compra/venda simuladas
- Cálculo de PnL em tempo real
- Persistência em memória ou arquivo JSON
- API REST completa com FastAPI
- Interface MCP para integração com LLMs

## Capabilities

### New Capabilities

- `paper-domain`: Entidades e value objects do domínio de paper trading (Portfolio, Ticker)
- `paper-ports`: Interfaces/contratos para brokers, data feeds e repositórios
- `paper-adapters`: Implementações concretas dos ports (PaperBroker, YahooFinanceFeed)
- `paper-application`: Casos de uso CQRS (commands e queries)
- `paper-facade-api`: API REST para paper trading via FastAPI
- `paper-facade-mcp`: Tools e resources MCP para integração com LLMs
- `paper-facade-helloworld`: Playground completo de paper trading

### Modified Capabilities

_Nenhuma - este é um módulo novo_

## Impact

### Código Afetado
- `src/core/paper/` - módulo completo (~60 arquivos)

### Dependências Externas
- `yfinance` - dados de mercado do Yahoo Finance
- `fastapi` - API REST
- `pydantic` - validação de schemas

### APIs Expostas
- REST: `/cotacao/{ticker}`, `/historico/{ticker}`, `/ordem`, `/posicoes`, `/portfolio`, `/ordens`
- MCP Tools: `paper_criar_ordem`, `paper_consultar_portfolio`, `paper_avaliar_risco`
- MCP Resources: `paper://portfolio`

### Sistemas Integrados
- Yahoo Finance API (dados de mercado em tempo real)

> "Documentar é construir pontes entre o que fizemos e o que faremos" – made by Sky 🚀
