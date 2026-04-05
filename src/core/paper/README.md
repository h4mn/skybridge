# Paper Trading Module

Sistema de paper trading (simulação de negociação) seguindo arquitetura DDD.

## Estrutura

```
paper/
├── domain/          # Entidades e regras de negócio
├── application/     # Casos de uso (commands/queries + handlers)
├── ports/           # Interfaces/contratos
├── adapters/        # Implementações concretas
│   ├── brokers/     # JsonFilePaperBroker
│   ├── data_feeds/  # YahooFinanceFeed
│   └── persistence/ # JsonFilePaperState, JsonFileRepository
└── facade/          # Facades agrupadas
    ├── api/         # Facade REST/HTTP
    ├── mcp/         # Facade MCP (LLM Tools)
    └── sandbox/      # Área de experimentos
```

## Iniciar API

```bash
# Paper Trading API (standalone)
uvicorn src.core.paper.facade.api.app:app --port 8001

# Acessar documentação
open http://localhost:8001/docs
```

## Endpoints Disponíveis

| Método | Rota | Descrição |
|--------|------|-----------|
| GET | `/api/v1/paper/mercado/cotacao/{ticker}` | Cotação atual |
| GET | `/api/v1/paper/mercado/historico/{ticker}` | Histórico OHLCV |
| POST | `/api/v1/paper/ordens` | Criar ordem |
| GET | `/api/v1/paper/ordens` | Listar ordens |
| GET | `/api/v1/paper/portfolio` | Consultar portfolio |
| GET | `/api/v1/paper/posicoes` | Listar posições |
| POST | `/api/v1/paper/deposito` | Depositar fundos |
| POST | `/api/v1/paper/reset` | Resetar portfolio |

## Exemplos de Uso

### Consultar cotação

```bash
curl http://localhost:8001/api/v1/paper/mercado/cotacao/BTC-USD
```

### Criar ordem

```bash
curl -X POST http://localhost:8001/api/v1/paper/ordens \
  -H "Content-Type: application/json" \
  -d '{"ticker": "PETR4.SA", "lado": "COMPRA", "quantidade": 100}'
```

### Consultar portfolio

```bash
curl http://localhost:8001/api/v1/paper/portfolio
```

## Tickers Suportados

- **B3**: `PETR4.SA`, `VALE3.SA`, `ITUB4.SA`
- **Cripto**: `BTC-USD`, `ETH-USD`, `SOL-USD`
- **EUA**: `AAPL`, `MSFT`, `TSLA`

## Arquitetura

O módulo segue Clean Architecture com CQRS:

```
Facade (API/MCP)
    ↓
Handlers (Commands/Queries)
    ↓
Ports (Interfaces)
    ↓
Adapters (Implementações)
    ↓
PaperState (Persistência unificada)
```

### PaperStatePort

Fonte única de verdade para `paper_state.json`. Resolve conflito entre
`JsonFilePaperBroker` e `JsonFilePortfolioRepository`.

- Migração automática v1 → v2
- Write atômico (tmp + rename)
- Sem cache em memória (evita stale reads)

## Documentação

- [`doc/arquitetura.md`](doc/arquitetura.md) - Estrutura DDD aprovada
- [`doc/proposta.md`](doc/proposta.md) - Visão geral e próximos passos
- [`docs/adr/ADR028-paper-state-dono-unico-json.md`](../../../docs/adr/ADR028-paper-state-dono-unico-json.md) - Decisão arquitetural

## Referências

- ADR002: Estrutura do Repositório Skybridge
- ADR003: Glossário, Arquiteturas e Padrões Oficiais
