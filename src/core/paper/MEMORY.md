# MEMORY - Domínio Paper Trading

## [2026-03-27T02:05:00Z] - Sky usando Roo Code via GLM-5

**Tarefa:** Criar fachada helloworld/ com implementação mínima funcional da arquitetura DDD.

**Arquivos Criados:**
- `src/core/paper/domain/entities/portfolio.py` - Entidade Portfolio com métodos depositar, retirar, pnl, pnl_percentual
- `src/core/paper/domain/value_objects/ticker.py` - Value Object Ticker imutável
- `src/core/paper/application/queries/consultar_portfolio.py` - Query e Result para consulta de portfolio
- `src/core/paper/application/handlers/portfolio_handler.py` - Handler para processar queries do portfolio
- `src/core/paper/adapters/persistence/in_memory_repository.py` - Repositório em memória para desenvolvimento/testes
- `src/core/paper/facade/helloworld/__init__.py` - Exportação do módulo helloworld
- `src/core/paper/facade/helloworld/facade.py` - Facade FastAPI com endpoints /, /health, /portfolio
- `src/core/paper/facade/helloworld/README.md` - Documentação de como executar

**Arquivos Atualizados:**
- `src/core/paper/ports/repository_port.py` - Adicionada classe PortfolioRepositoryPort
- `src/core/paper/domain/entities/__init__.py` - Exporta Portfolio
- `src/core/paper/domain/value_objects/__init__.py` - Exporta Ticker
- `src/core/paper/application/queries/__init__.py` - Exporta ConsultarPortfolioQuery, PortfolioResult
- `src/core/paper/application/handlers/__init__.py` - Exporta PortfolioQueryHandler
- `src/core/paper/ports/__init__.py` - Exporta PortfolioRepositoryPort
- `src/core/paper/adapters/persistence/__init__.py` - Exporta InMemoryPortfolioRepository

**Resumo das Alterações:**
Implementação mínima funcional demonstrando o fluxo completo DDD:
```
Facade → Application (Query/Handler) → Port (RepositoryPort) → Adapter (InMemoryRepository) → Domain (Portfolio)
```

A fachada HelloWorldFacade expõe 3 endpoints:
- `GET /` - Hello World
- `GET /health` - Health check
- `GET /portfolio` - Consulta portfolio padrão (demonstra fluxo DDD completo)

**Como Executar:**
```bash
uvicorn src.core.paper.facade.helloworld.facade:app --reload --port 8000
```

**Exemplo de Uso:**
```bash
curl http://localhost:8000/portfolio
```

**Próximos Passos:**
1. Executar o servidor e testar os endpoints
2. Implementar mais casos de uso (criar ordem, cancelar ordem)
3. Adicionar testes unitários

---

## [2026-03-27T01:45:00Z] - Sky usando Roo Code via GLM-5

**Tarefa:** Reorganizar estrutura - criar facade/ e mover api/ e mcp/ para agrupar facades.

**Arquivos Movidos:**
- `src/core/paper/api/` → `src/core/paper/facade/api/` (toda a pasta)
- `src/core/paper/mcp/` → `src/core/paper/facade/mcp/` (toda a pasta)

**Arquivos Criados:**
- `src/core/paper/facade/__init__.py` - Módulo agregador das facades

**Arquivos Atualizados:**
- `src/core/paper/facade/api/__init__.py` - Atualizado exemplo de uso
- `src/core/paper/facade/mcp/__init__.py` - Atualizado exemplo de uso
- `src/core/paper/doc/arquitetura.md` - Nova estrutura com facade/
- `src/core/paper/doc/proposta.md` - Atualizados caminhos e exemplos
- `src/core/paper/README.md` - Atualizado com novos caminhos

**Resumo das Alterações:**
Reorganização arquitetural para agrupar as facades em uma pasta dedicada (`facade/`). A mudança melhora a organização do código separando claramente as interfaces de entrada (API REST e MCP) das demais camadas DDD.

Nova estrutura:
```
src/core/paper/
├── domain/          # Entidades e regras
├── application/     # Casos de uso
├── ports/           # Interfaces
├── adapters/        # Implementações
└── facade/          # 🆕 Facades agrupadas
    ├── api/         # REST/HTTP
    └── mcp/         # LLM Tools
```

**Impacto nos Imports:**
- Antigo: `from src.core.paper.api.facade import PaperTradingAPI`
- Novo: `from src.core.paper.facade.api.facade import PaperTradingAPI`
- Ou simplificado: `from src.core.paper.facade import PaperTradingAPI`

**Próximos Passos:**
1. Verificar se há imports externos que referenciam os caminhos antigos
2. Atualizar testes se existirem

---

## [2026-03-27T01:27:00Z] - Sky usando Roo Code via GLM-5

**Tarefa:** Criar estrutura de pastas DDD para Paper Trading conforme arquitetura aprovada.

**Arquivos Criados:**
- `src/core/paper/README.md` - Documentação principal do módulo
- `src/core/paper/domain/__init__.py` - Camada de domínio
- `src/core/paper/domain/entities/__init__.py` - Entidades (Portfolio, Ordem, Posicao)
- `src/core/paper/domain/value_objects/__init__.py` - Value objects (Preco, Ticker, Quantidade)
- `src/core/paper/domain/events/__init__.py` - Eventos de domínio (OrdemCriada, StopLossAcionado)
- `src/core/paper/domain/services/__init__.py` - Serviços de domínio
- `src/core/paper/application/__init__.py` - Camada de aplicação
- `src/core/paper/application/commands/__init__.py` - Commands CQRS
- `src/core/paper/application/queries/__init__.py` - Queries CQRS
- `src/core/paper/application/handlers/__init__.py` - Handlers de commands/queries
- `src/core/paper/ports/__init__.py` - Interfaces/contratos
- `src/core/paper/ports/broker_port.py` - Interface para brokers
- `src/core/paper/ports/data_feed_port.py` - Interface para feeds de dados
- `src/core/paper/ports/repository_port.py` - Interface para persistência
- `src/core/paper/adapters/__init__.py` - Implementações concretas
- `src/core/paper/adapters/brokers/__init__.py` - Adapters de broker
- `src/core/paper/adapters/data_feeds/__init__.py` - Adapters de data feed
- `src/core/paper/adapters/persistence/__init__.py` - Adapters de persistência
- `src/core/paper/api/__init__.py` - Facade REST/HTTP
- `src/core/paper/api/facade.py` - Facade principal da API
- `src/core/paper/api/routes/__init__.py` - Rotas FastAPI
- `src/core/paper/api/routes/ordens.py` - Rotas de ordens
- `src/core/paper/api/routes/portfolio.py` - Rotas de portfolio
- `src/core/paper/api/routes/risco.py` - Rotas de risco
- `src/core/paper/api/schemas/__init__.py` - Schemas Pydantic
- `src/core/paper/api/schemas/ordem_schema.py` - Schema de ordens
- `src/core/paper/api/schemas/portfolio_schema.py` - Schema de portfolio
- `src/core/paper/api/dependencies.py` - Injeção de dependências
- `src/core/paper/mcp/__init__.py` - Facade MCP (LLM Tools)
- `src/core/paper/mcp/facade.py` - Facade principal MCP
- `src/core/paper/mcp/tools/__init__.py` - Tools MCP
- `src/core/paper/mcp/tools/criar_ordem.py` - Tool criar ordem
- `src/core/paper/mcp/tools/consultar_portfolio.py` - Tool consultar portfolio
- `src/core/paper/mcp/tools/avaliar_risco.py` - Tool avaliar risco
- `src/core/paper/mcp/resources/__init__.py` - Resources MCP
- `src/core/paper/mcp/resources/portfolio_resource.py` - Resource portfolio
- `src/core/paper/doc/proposta.md` - Documentação da proposta arquitetural

**Resumo das Alterações:**
Estrutura completa DDD criada seguindo os padrões definidos em ADR002 e ADR003. A arquitetura implementa:
- **Domain Layer**: Entidades, value objects, eventos e serviços de domínio
- **Application Layer**: Commands, queries e handlers (CQRS)
- **Ports Layer**: Interfaces para broker, data feed e repository
- **Adapters Layer**: Implementações concretas (paper broker, SQLite, Yahoo Finance)
- **API Facade**: Interface REST com FastAPI, rotas organizadas por domínio
- **MCP Facade**: Interface para LLMs com tools e resources

Todos os arquivos possuem docstrings detalhadas com exemplos de uso e próximos passos de implementação.

**Próximos Passos:**
1. Implementar entidades do domínio (Portfolio, Ordem, Posicao)
2. Criar value objects (Preco, Ticker, Quantidade)
3. Implementar adapters (PaperBroker, SQLiteRepository, YahooFinanceFeed)
4. Criar handlers de commands/queries
5. Implementar lógica completa nas facades

---

## [2026-03-27T00:18:00Z] - Sky usando Roo Code via GLM-5

**Tarefa:** Análise crítica da arquitetura proposta para o sistema de negociação (paper trading).

**Arquivos Analisados:**
- `src/core/paper/doc/arquitetura.md` - Proposta de estrutura engine/
- `src/core/paper/doc/mvp-arquitetura-sistema-negociacao.md` - MVP realista
- `src/core/paper/doc/checklist-sistema-negociacao.md` - Checklist de componentes
- `docs/adr/ADR002-Estrutura do Repositório Skybridge.md` - Padrões de estrutura
- `docs/adr/ADR003-Glossário, Arquiteturas e Padrões Oficiais.md` - Padrões DDD

**Resumo das Análises:**

### Pontos Fortes da Proposta
- Separação por responsabilidade bem definida (data, risk, execution, backtesting)
- Nomenclatura intuitiva (circuit_breakers.py, position_sizing.py)
- Orchestrator centralizado para coordenação
- Cobertura funcional essencial para trading

### Pontos Críticos Identificados
1. **Desalinhamento com DDD** - Estrutura não segue padrões domain/application/ports/adapters
2. **Sem Ports/Adapters** - Acoplamento direto com brokers e data sources
3. **Ausência de Eventos de Domínio** - Comunicação síncrona acoplada
4. **Segurança** - Sem correlation ID, idempotência ou auditoria

### Estrutura Recomendada
```
src/core/paper/
├── domain/           # Entidades (portfolio, ordem, posicao)
├── application/      # Commands/Queries (CQRS)
├── ports/            # Interfaces (broker_port, data_feed_port)
└── adapters/         # Implementações (paper_broker, yahoo_feed)
```

### Próximos Passos Sugeridos
1. Refatorar estrutura para seguir DDD
2. Criar README.md do contexto paper (obrigatório por ADR002)
3. Definir ports para broker e data feed antes de implementar
4. Implementar eventos de domínio para ordens
5. Adicionar correlation ID e idempotência desde o início

---
