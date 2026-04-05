# Proposta de Arquitetura - Paper Trading

## Visão Geral

Sistema de paper trading (simulação de negociação) seguindo arquitetura DDD (Domain-Driven Design) com separação clara de responsabilidades.

### Princípios Arquiteturais

1. **Domain-Driven Design (DDD)**: O domínio de negócio é o centro da arquitetura
2. **Dependency Inversion**: O domínio define interfaces (Ports), adaptadores implementam
3. **CQRS**: Separação entre Commands (escrita) e Queries (leitura)
4. **Facade Pattern**: APIs simplificadas para clientes externos (REST e MCP)

## Camadas

### Domain (Domínio)
- **entities/**: Entidades com identidade única (Portfolio, Ordem, Posicao)
- **value_objects/**: Objetos imutáveis sem identidade (Preco, Ticker, Quantidade)
- **events/**: Eventos de domínio (OrdemCriada, StopLossAcionado)
- **services/**: Serviços de domínio com regras de negócio puras

### Application (Aplicação)
- **commands/**: Intenções de mudança de estado (CriarOrdemCommand)
- **queries/**: Consultas de dados (ConsultarPortfolioQuery)
- **handlers/**: Orquestração de commands e queries

### Ports (Portas)
- Interfaces que definem contratos para infraestrutura externa
- `broker_port.py`: Interface para brokers
- `data_feed_port.py`: Interface para feeds de dados
- `repository_port.py`: Interface para persistência

### Adapters (Adaptadores)
- Implementações concretas dos ports
- `brokers/`: Paper broker, Binance adapter, etc.
- `data_feeds/`: Yahoo Finance, Alpha Vantage, etc.
- `persistence/`: SQLite, PostgreSQL, etc.

### Facade (Agrupamento)
- **api/**: Interface REST/HTTP para integração externa
  - Routes: ordens, portfolio, risco
  - Schemas: Pydantic models para validação
- **mcp/**: Interface Model Context Protocol para LLMs
  - Tools: paper_criar_ordem, paper_consultar_portfolio
  - Resources: paper://portfolio

## Fluxo de Dados

```
Cliente → API/MCP → Application → Domain → Ports → Adapters
```

### Exemplo: Criar Ordem

```
1. Cliente chama API: POST /api/v1/paper/ordens
2. API valida input via Pydantic schema
3. API cria CriarOrdemCommand
4. Handler valida regras de negócio
5. Domain service executa lógica
6. Repository persiste mudanças
7. Evento OrdemCriada é publicado
```

## Estrutura de Diretórios

```
src/core/paper/
│
├── README.md
│
├── doc/                         # Documentação
│   ├── arquitetura.md
│   └── proposta.md
│
├── domain/                      # Entidades e regras
│   ├── __init__.py
│   ├── entities/
│   │   └── __init__.py
│   ├── value_objects/
│   │   └── __init__.py
│   ├── events/
│   │   └── __init__.py
│   └── services/
│       └── __init__.py
│
├── application/                 # Casos de uso
│   ├── __init__.py
│   ├── commands/
│   │   └── __init__.py
│   ├── queries/
│   │   └── __init__.py
│   └── handlers/
│       └── __init__.py
│
├── ports/                       # Interfaces
│   ├── __init__.py
│   ├── broker_port.py
│   ├── data_feed_port.py
│   └── repository_port.py
│
├── adapters/                    # Implementações
│   ├── __init__.py
│   ├── brokers/
│   │   └── __init__.py
│   ├── data_feeds/
│   │   └── __init__.py
│   └── persistence/
│       └── __init__.py
│
└── facade/                      # 🆕 Facades agrupadas
    ├── __init__.py
    ├── api/                     # Facade API (REST)
    │   ├── __init__.py
    │   ├── facade.py
    │   ├── routes/
    │   │   ├── __init__.py
    │   │   ├── ordens.py
    │   │   ├── portfolio.py
    │   │   └── risco.py
    │   ├── schemas/
    │   │   ├── __init__.py
    │   │   ├── ordem_schema.py
    │   │   └── portfolio_schema.py
    │   └── dependencies.py
    └── mcp/                     # Facade MCP (LLM Tools)
        ├── __init__.py
        ├── facade.py
        ├── tools/
        │   ├── __init__.py
        │   ├── criar_ordem.py
        │   ├── consultar_portfolio.py
        │   └── avaliar_risco.py
        └── resources/
            ├── __init__.py
            └── portfolio_resource.py
```

## Exemplos de Uso

### Via API REST

```python
from src.core.paper.facade.api.facade import PaperTradingAPI

api = PaperTradingAPI()

# Criar ordem
ordem = await api.criar_ordem(
    ticker="PETR4",
    lado="COMPRA",
    quantidade=100,
    preco_limite=Decimal("28.50")
)

# Consultar portfolio
portfolio = await api.consultar_portfolio("default")
print(f"Saldo: {portfolio['saldo_disponivel']}")
```

### Via MCP (LLM)

```python
from src.core.paper.facade.mcp.facade import PaperTradingMCP

mcp = PaperTradingMCP()

# Tool: Criar ordem
resultado = await mcp.criar_ordem(
    ticker="VALE3",
    lado="COMPRA",
    quantidade=50
)

# Resource: Portfolio
portfolio = await mcp.get_portfolio_resource()
```

### Via Facade Principal (Agregada)

```python
from src.core.paper.facade import PaperTradingAPI, PaperTradingMCP

# Importação simplificada
api = PaperTradingAPI()
mcp = PaperTradingMCP()
```

## Próximos Passos

1. **Implementar entidades do domínio** (Portfolio, Ordem)
2. **Criar value objects** (Preco, Ticker, Quantidade)
3. **Definir ports** (interfaces) - ✅ Estrutura base criada
4. **Implementar adapters** (paper broker, SQLite)
5. **Criar handlers** de commands/queries
6. **Implementar facades** API e MCP

## Roadmap de Implementação

### Fase 1: Core Domain
- [ ] Implementar entidade Portfolio
- [ ] Implementar entidade Ordem
- [ ] Implementar value objects básicos
- [ ] Criar eventos de domínio

### Fase 2: Infrastructure
- [ ] Implementar PaperBroker (adapter)
- [ ] Implementar SQLiteRepository (adapter)
- [ ] Implementar YahooFinanceFeed (adapter)

### Fase 3: Application
- [ ] Implementar CriarOrdemCommand
- [ ] Implementar ConsultarPortfolioQuery
- [ ] Implementar handlers

### Fase 4: Facades
- [ ] Implementar API facade completa
- [ ] Implementar MCP facade completa
- [ ] Testes de integração

## Referências

- ADR002: Estrutura do Repositório Skybridge
- ADR003: Glossário, Arquiteturas e Padrões Oficiais
- [Domain-Driven Design](https://martinfowler.com/bliki/DomainDrivenDesign.html)
- [CQRS Pattern](https://martinfowler.com/bliki/CQRS.html)
