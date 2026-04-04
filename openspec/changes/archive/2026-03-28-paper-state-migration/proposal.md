# Proposal: Paper State Migration

## Why

O helloworld cumpriu seu papel de validar dados reais de mercado, execução de ordens,
persistência e PnL marcado a mercado — tudo funcionando em produção no mesmo dia.
Porém, dois problemas bloqueiam a evolução do sistema:

1. **Conflito de JSON** — `JsonFilePaperBroker` e `JsonFilePortfolioRepository` escrevem
   schemas incompatíveis no mesmo arquivo `paper_state.json`. O último a salvar
   sobrescreve silenciosamente o estado do outro.

2. **Lógica concentrada no helloworld** — commands e queries que deveriam estar na
   camada de application vivem diretamente no facade, impedindo que `facade/api` e
   `facade/mcp` reutilizem o mesmo código.

A migração é necessária agora porque as facades oficiais (API REST e MCP) precisam
ser implementadas com DI real, e isso requer que a lógica esteja na camada correta.

## What Changes

### Fase 1 — PaperState (pré-requisito)
- Criar `PaperStatePort` (interface) em `ports/paper_state_port.py`
- Criar `JsonFilePaperState` (implementação) em `adapters/persistence/`
- Refatorar `JsonFilePaperBroker` para delegar persistência ao PaperState
- Refatorar `JsonFilePortfolioRepository` para delegar persistência ao PaperState
- Schema canônico versionado do `paper_state.json`

### Fase 2 — Commands e Queries
- Extrair `CriarOrdemCommand` + `CriarOrdemHandler` do helloworld
- Extrair `ConsultarMercadoQuery` + `ConsultarMercadoHandler` (cotação e histórico)
- Expandir `ConsultarPortfolioQuery` com PnL real marcado a mercado
- Criar `ConsultarOrdensQuery` para listar ordens

### Fase 3 — facade/api
- Implementar `dependencies.py` com DI real (get_broker, get_feed, get_state)
- Criar `routes/mercado.py` com endpoints de cotação e histórico
- Implementar `routes/ordens.py` via `CriarOrdemHandler`
- Implementar `routes/portfolio.py` via handlers de query

### Fase 4 — facade/mcp
- Implementar `CriarOrdemTool.execute()` via `CriarOrdemHandler`
- Implementar `ConsultarPortfolioTool.execute()` via handler
- Criar `paper_cotacao_ticker` como nova tool MCP

## Capabilities

### New Capabilities
- `paper-state`: Port e adapter para gestão unificada do paper_state.json
- `paper-commands`: Commands CQRS para operações de escrita (criar ordem, depositar, resetar)
- `paper-market-queries`: Queries para consulta de mercado (cotação, histórico)
- `paper-portfolio-queries`: Queries expandidas para portfolio com PnL real

### Modified Capabilities
- `paper-facade-api`: Scaffold → Implementação completa com DI real
- `paper-facade-mcp`: Scaffold → Tools funcionais conectadas aos handlers

## Impact

### Arquivos Afetados
```
src/core/paper/
├── ports/paper_state_port.py          # NOVO
├── adapters/
│   ├── persistence/
│   │   ├── json_file_paper_state.py   # NOVO
│   │   ├── json_file_repository.py    # REFACTORED (delegar)
│   │   └── json_file_broker.py        # REFACTORED (delegar)
│   └── brokers/
│       └── paper_broker.py            # REFACTORED (herda delegação)
├── application/
│   ├── commands/
│   │   ├── criar_ordem.py             # NOVO
│   │   └── handlers/
│   │       └── criar_ordem_handler.py # NOVO
│   └── queries/
│       ├── consultar_mercado.py       # NOVO
│       ├── consultar_portfolio.py     # EXPANDIDO
│       └── handlers/
│           ├── consultar_mercado_handler.py  # NOVO
│           └── consultar_portfolio_handler.py # EXPANDIDO
├── facade/
│   ├── helloworld/facade.py           # REFACTORED (importa handlers)
│   ├── api/
│   │   ├── dependencies.py            # IMPLEMENTADO
│   │   └── routes/
│   │       ├── mercado.py             # NOVO
│   │       ├── ordens.py              # IMPLEMENTADO
│   │       └── portfolio.py           # IMPLEMENTADO
│   └── mcp/
│       └── tools/
│           ├── criar_ordem_tool.py    # IMPLEMENTADO
│           ├── consultar_portfolio_tool.py # IMPLEMENTADO
│           └── cotacao_ticker_tool.py # NOVO
```

### Dependências
- Nenhuma dependência externa nova
- Reutiliza adapters existentes (YahooFinanceFeed, PaperBroker)

### Sistemas Afetados
- **paper_state.json**: Schema muda de v1 para v2 (unificado)
- **Discord MCP**: Tools passam a retornar dados reais
- **API REST**: Endpoints funcionais (não mais NotImplementedError)

### Breaking Changes
- **BREAKING**: Schema do `paper_state.json` muda para versão 2
  - Migração automática de v1 → v2 no primeiro carregamento
  - Backup automático do arquivo v1 antes de migrar
