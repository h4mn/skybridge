# Tasks: Paper State Migration

## 1. Fase 1 — PaperState (pré-requisito)

### 1.1 Criar PaperStatePort
- [x] 1.1.1 Criar arquivo `src/core/paper/ports/paper_state_port.py`
- [x] 1.1.2 Definir interface `PaperStatePort` com métodos: `carregar()`, `salvar()`, `resetar()`
- [x] 1.1.3 Definir dataclass `PaperStateData` com schema v2

### 1.2 Implementar JsonFilePaperState
- [x] 1.2.1 Criar `src/core/paper/adapters/persistence/json_file_paper_state.py`
- [x] 1.2.2 Implementar migração automática v1 → v2
- [x] 1.2.3 Implementar backup de arquivo v1 antes de migrar
- [x] 1.2.4 Implementar `carregar()` com deserialização correta
- [x] 1.2.5 Implementar `salvar()` com serialização e updated_at

### 1.3 Refatorar JsonFilePaperBroker
- [x] 1.3.1 Injetar `PaperStatePort` no construtor
- [x] 1.3.2 Delegar leitura de saldo/posições para `paper_state.carregar()`
- [x] 1.3.3 Delegar escrita para `paper_state.salvar()`
- [x] 1.3.4 Remover I/O direto de arquivo

### 1.4 Refatorar JsonFilePortfolioRepository
- [x] 1.4.1 Injetar `PaperStatePort` no construtor
- [x] 1.4.2 Delegar leitura para `paper_state.carregar().portfolios`
- [x] 1.4.3 Delegar escrita para `paper_state.salvar()` preservando outros dados

### 1.5 Testes Fase 1
- [x] 1.5.1 Criar `tests/unit/core/paper/test_paper_state_port.py`
- [x] 1.5.2 Teste: carregar estado vazio cria schema v2
- [x] 1.5.3 Teste: migrar v1 → v2 preserva dados
- [x] 1.5.4 Teste: broker e repository não conflitam
- [x] 1.5.5 Implementar write atômico (tmp + rename) no `salvar()`
- [x] 1.5.6 Teste: arquivo original preservado se escrita falhar

---

## 2. Fase 2 — Commands e Queries

### 2.1 Criar Commands
- [x] 2.1.1 Criar `src/core/paper/application/commands/criar_ordem.py` com `CriarOrdemCommand`
- [x] 2.1.2 Criar `src/core/paper/application/commands/depositar.py` com `DepositarCommand`
- [x] 2.1.3 Criar `src/core/paper/application/commands/resetar.py` com `ResetarCommand`

### 2.2 Criar Command Handlers
- [x] 2.2.1 Criar `src/core/paper/application/handlers/criar_ordem_handler.py` com lógica de validação e execução
- [x] 2.2.2 Criar `src/core/paper/application/handlers/depositar_handler.py`
- [x] 2.2.3 Criar `src/core/paper/application/handlers/resetar_handler.py`

### 2.3 Criar Queries
- [x] 2.3.1 Criar `src/core/paper/application/queries/consultar_cotacao.py` com `ConsultarCotacaoQuery` e `CotacaoResult`
- [x] 2.3.2 Criar `src/core/paper/application/queries/consultar_historico.py` com `ConsultarHistoricoQuery` e `CandleData`
- [x] 2.3.3 Criar `src/core/paper/application/queries/consultar_portfolio.py` expandido com PnL
- [x] 2.3.4 Criar `src/core/paper/application/queries/consultar_ordens.py` com filtros

### 2.4 Criar Query Handlers
- [x] 2.4.1 Criar `src/core/paper/application/handlers/consultar_cotacao_handler.py` delegando para DataFeedPort
- [x] 2.4.2 Criar `src/core/paper/application/handlers/consultar_historico_handler.py`
- [x] 2.4.3 Criar `src/core/paper/application/handlers/consultar_portfolio_handler.py` com marcação a mercado
- [x] 2.4.4 Criar `src/core/paper/application/handlers/consultar_ordens_handler.py`

### 2.5 Refatorar helloworld para usar handlers
- [x] 2.5.1 Injetar handlers no `HelloWorldFacade`
- [x] 2.5.2 Substituir chamadas diretas ao broker por `CriarOrdemHandler`
- [x] 2.5.3 Substituir chamadas ao feed por `ConsultarCotacaoHandler` e `ConsultarHistoricoHandler`
- [x] 2.5.4 Atualizar endpoint `/ordem` para usar command
- [x] 2.5.5 Atualizar endpoints `/cotacao` e `/historico` para usar queries

### 2.6 Testes Fase 2
- [x] 2.6.1 Criar `tests/unit/core/paper/application/test_criar_ordem_handler.py`
- [x] 2.6.2 Teste: ordem de compra executada
- [x] 2.6.3 Teste: saldo insuficiente rejeita
- [x] 2.6.4 Teste: consulta de cotação retorna dados
- [x] 2.6.5 Teste: portfolio com PnL calculado

---

## 3. Fase 3 — facade/api

### 3.1 Implementar Dependencies
- [x] 3.1.1 Criar `src/core/paper/facade/api/dependencies.py`
- [x] 3.1.2 Implementar `get_paper_state()` retornando `JsonFilePaperState`
- [x] 3.1.3 Implementar `get_broker()` com injeção de PaperState
- [x] 3.1.4 Implementar `get_feed()` retornando `YahooFinanceFeed`
- [x] 3.1.5 Implementar `get_handlers()` retornando handlers configurados

### 3.2 Criar Rotas de Mercado
- [x] 3.2.1 Criar `src/core/paper/facade/api/routes/mercado.py`
- [x] 3.2.2 Implementar `GET /api/v1/paper/mercado/cotacao/{ticker}`
- [x] 3.2.3 Implementar `GET /api/v1/paper/mercado/historico/{ticker}`

### 3.3 Implementar Rotas de Ordens
- [x] 3.3.1 Atualizar `src/core/paper/facade/api/routes/ordens.py`
- [x] 3.3.2 Implementar `POST /api/v1/paper/ordens` via `CriarOrdemHandler`
- [x] 3.3.3 Implementar `GET /api/v1/paper/ordens` via `ConsultarOrdensHandler`

### 3.4 Implementar Rotas de Portfolio
- [x] 3.4.1 Atualizar `src/core/paper/facade/api/routes/portfolio.py`
- [x] 3.4.2 Implementar `GET /api/v1/paper/portfolio` com PnL
- [x] 3.4.3 Implementar `GET /api/v1/paper/posicoes`
- [x] 3.4.4 Implementar `POST /api/v1/paper/deposito` via `DepositarHandler`
- [x] 3.4.5 Implementar `POST /api/v1/paper/reset` via `ResetarHandler`

### 3.5 Atualizar Main da API
- [x] 3.5.1 Registrar rotas no router principal
- [x] 3.5.2 Configurar OpenAPI/Swagger
- [x] 3.5.3 Testar subida sem NotImplementedError

### 3.6 Testes Fase 3
- [x] 3.6.1 Teste manual: API sobe e responde em `/docs`
- [x] 3.6.2 Teste: GET /cotacao/{ticker} retorna JSON
- [x] 3.6.3 Teste: POST /ordens executa via handler
- [x] 3.6.4 Teste: GET /portfolio retorna PnL

---

## 4. Fase 4 — facade/mcp

### 4.1 Implementar Tools MCP
- [x] 4.1.1 Atualizar `src/core/paper/facade/mcp/tools/criar_ordem.py`
- [x] 4.1.2 Implementar `execute()` chamando `CriarOrdemHandler`
- [x] 4.1.3 Atualizar `src/core/paper/facade/mcp/tools/consultar_portfolio.py`
- [x] 4.1.4 Implementar `execute()` chamando handler

### 4.2 Criar Nova Tool de Cotação
- [x] 4.2.1 Criar `src/core/paper/facade/mcp/tools/cotacao_ticker.py`
- [x] 4.2.2 Definir schema MCP com parâmetro ticker
- [x] 4.2.3 Implementar `execute()` chamando `ConsultarCotacaoHandler`

### 4.3 Atualizar Server MCP
- [x] 4.3.1 Registrar novas tools no server
- [x] 4.3.2 Injetar handlers via construtor ou factory

### 4.4 Testes Fase 4
- [x] 4.4.1 Teste: tool `paper_criar_ordem` executa via MCP
- [x] 4.4.2 Teste: tool `paper_consultar_portfolio` retorna PnL
- [x] 4.4.3 Teste: tool `paper_cotacao_ticker` retorna preço

---

## 5. Validação Final

### 5.1 Integração
- [x] 5.1.1 Smoke test: helloworld funciona identicamente
- [x] 5.1.2 Smoke test: API REST responde em todos os endpoints
- [x] 5.1.3 Smoke test: MCP tools retornam dados reais

### 5.2 Documentação
- [x] 5.2.1 Atualizar README do paper-trading com novos endpoints
- [x] 5.2.2 Documentar migração de schema no ADR028

### 5.3 Cleanup
- [x] 5.3.1 Remover código morto (I/O direto no broker/repository antigo)
- [x] 5.3.2 Verificar imports não utilizados
