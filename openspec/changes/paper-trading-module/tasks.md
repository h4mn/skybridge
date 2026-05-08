# Tasks - Paper Trading Module Documentation

Este change documenta o módulo `src/core/paper` já implementado.

## 1. Documentação Core

- [x] 1.1 Criar proposal.md com visão geral do módulo
- [x] 1.2 Criar design.md com decisões arquiteturais
- [x] 1.3 Criar specs para paper-domain
- [x] 1.4 Criar specs para paper-ports
- [x] 1.5 Criar specs para paper-adapters
- [x] 1.6 Criar specs para paper-application
- [x] 1.7 Criar specs para paper-facade-api
- [x] 1.8 Criar specs para paper-facade-mcp
- [x] 1.9 Criar specs para paper-facade-helloworld

## 2. Verificação de Alinhamento

- [x] 2.1 Verificar se specs refletem implementação atual do domain/ → **✅ ALINHADO**
- [x] 2.2 Verificar se specs refletem implementação atual dos ports/ → **✅ ALINHADO**
- [x] 2.3 Verificar se specs refletem implementação atual dos adapters/ → **✅ ALINHADO**
- [x] 2.4 Verificar se specs refletem implementação atual da facade/ → **⚠️ PARCIAL**

## 3. Melhorias Futuras (Sincronizado 2026-05-07)

- [x] 3.1 Implementar eventos de domínio (domain/events/) — ✅ DONE: DomainEvent, EventBus, 5 eventos
- [x] 3.2 Implementar serviços de domínio (domain/services/) — ✅ DONE: Validador, Executor, CalculadorRisco, GeradorRelatorio
- [x] 3.3 Implementar commands CQRS (application/commands/) — ✅ DONE: criar_ordem, depositar, resetar + queries + handlers
- [x] 3.4 Adicionar testes unitários para specs — ✅ DONE: 122+ testes unitários
- [ ] 3.5 Adicionar cache de cotações para reduzir rate limiting

## Notas

O módulo já está funcional com:
- Domain: Portfolio, Ticker
- Ports: BrokerPort, DataFeedPort, RepositoryPort
- Adapters: PaperBroker, YahooFinanceFeed, InMemoryRepository, JsonFileRepository
- Facades: API REST, MCP Tools, HelloWorld playground

### Resultado da Validação de Alinhamento

| Spec | Status | Observação |
|------|--------|------------|
| paper-domain | ✅ ALINHADO | Portfolio e Ticker correspondem à implementação |
| paper-ports | ✅ ALINHADO | Todas interfaces implementadas |
| paper-adapters | ✅ ALINHADO | PaperBroker, YahooFinanceFeed, repositórios OK |
| paper-application | ✅ ALINHADO | ConsultarPortfolioQuery e Handler OK |
| paper-facade-api | ⚠️ PARCIAL → ✅ ALINHADO | API REST funcional com rotas mercado/ordens/portfolio/risco (FastAPI) |
| paper-facade-mcp | ⚠️ PARCIAL | MCP facade ainda com NotImplementedError — tools são stubs |
| paper-facade-helloworld | ✅ ALINHADO | Implementação completa e funcional |

**Conclusão:** A implementação funcional real está em `facade/helloworld/`. As facades `api/` e `mcp/` são scaffolds com interfaces definidas mas não implementadas.

Para executar o playground:
```bash
uvicorn src.core.paper.facade.helloworld.facade:app --reload --port 8000
```

> "Tarefas documentadas são promessas cumpridas" – made by Sky 🚀

---

## Sincronização 2026-05-07

Revisão do estado real do módulo vs documentação. Resultado:

| Componente | Antes | Depois |
|------------|-------|--------|
| Domain Events | Pendente | ✅ 5 eventos + EventBus |
| Domain Services | Pendente | ✅ 4 serviços completos |
| Commands CQRS | Pendente | ✅ 3 commands + 4 queries + 8 handlers |
| Testes Unitários | Pendente | ✅ 122+ testes |
| Facade API | Stub | ✅ FastAPI funcional |
| Facade MCP | Stub | ⚠️ Ainda NotImplementedError |
| Guardião Conservador | — | ❌ Não existe |
| HeartbeatWorker | — | ❌ Não existe |

**Linear sincronizado:** SKY-21, SKY-34, SKY-28 → Done. SKY-35, SKY-38 → Backlog (reais).
