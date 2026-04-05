# Design - Paper Trading Module

## Context

O módulo `src/core/paper` implementa um sistema de paper trading (simulação de negociação) seguindo arquitetura DDD (Domain-Driven Design). O sistema permite operações de compra/venda simuladas usando preços reais do mercado via Yahoo Finance.

### Estado Atual
- **Domain**: Entidade `Portfolio` com métodos de saldo/PnL, Value Object `Ticker`
- **Ports**: Interfaces para `BrokerPort`, `DataFeedPort`, `RepositoryPort`
- **Adapters**: `PaperBroker`, `YahooFinanceFeed`, `InMemoryPortfolioRepository`, `JsonFilePortfolioRepository`
- **Facade**: API REST (FastAPI), MCP Tools, HelloWorld playground

### Stakeholders
- Desenvolvedores que precisam manter/evoluir o módulo
- Usuários finais que utilizam o playground de paper trading
- LLMs que consomem as MCP Tools

## Goals / Non-Goals

**Goals:**
- Documentar a arquitetura existente
- Estabelecer contrato formal entre camadas via specs
- Facilitar extensão para novos brokers e data feeds
- Permitir persistência configurável (memória, arquivo, banco de dados)

**Non-Goals:**
- Trading com dinheiro real (sempre paper/simulação)
- Backtesting de estratégias (futuro)
- Integração com brokers reais (futuro)
- WebSocket para dados em tempo real (atualmente polling)

## Decisions

### D1: Arquitetura DDD com Ports & Adapters
**Decisão:** Usar Clean Architecture com separação domain/application/ports/adapters.

**Racional:**
- Permite testar regras de negócio isoladamente
- Facilita trocar implementações (ex: Yahoo Finance → Alpha Vantage)
- Segue padrões definidos em ADR002 e ADR003 do projeto

**Alternativas consideradas:**
- Arquitetura monolítica: rejeitada por acoplar demais
- Microserviços: overkill para escopo atual

### D2: Yahoo Finance como Data Feed Padrão
**Decisão:** Usar `yfinance` como fonte de dados por ser gratuita e sem API key.

**Racional:**
- Sem custo para usar
- Suporta B3 (PETR4.SA), cripto (BTC-USD), EUA (AAPL)
- Dados com delay de ~15min para B3 (aceitável para paper trading)

**Limitações:**
- Rate limiting não documentado
- Dados podem ter delay
- Não é tempo real

### D3: Persistência em JSON File
**Decisão:** `JsonFilePaperBroker` persiste estado entre sessões.

**Racional:**
- Simples de implementar e debugar
- Portável entre ambientes
- Útil para desenvolvimento e testes

**Alternativas:**
- SQLite: mais robusto, mas adiciona complexidade
- PostgreSQL: overkill para escopo atual

### D4: FastAPI para API REST
**Decisão:** Usar FastAPI com Pydantic para validação automática.

**Racional:**
- Documentação automática (OpenAPI/Swagger)
- Validação de tipos integrada
- Assíncrono nativo
- Alinhado com stack do projeto

## Risks / Trade-offs

### R1: Rate Limiting do Yahoo Finance
**Risco:** Yahoo pode bloquear requisições em uso intenso.
**Mitigação:** Cache de cotações por 1 minuto, throttling de requisições.

### R2: Precisão dos Dados
**Risco:** Dados com delay podem não refletir mercado real.
**Mitigação:** Documentar claramente que é paper trading com dados defasados.

### R3: Estado em Arquivo JSON
**Risco:** Corrupção de arquivo em crash.
**Mitigação:** Write atômico com arquivo temporário + rename.

### R4: Sem Autenticação
**Risco:** API exposta sem controle de acesso.
**Mitigação:** Documentar que é para uso local/desenvolvimento apenas.

## Open Questions

1. **Multi-portfolio:** Suportar múltiplos portfolios por usuário?
2. **Histórico de operações:** Persistir histórico completo em banco?
3. **Webhooks:** Notificar sistemas externos sobre eventos de trading?

> "Arquitetura é sobre decisões difíceis feitas com clareza" – made by Sky 🚀
