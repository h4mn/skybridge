# PRD018 - Roadmap para Autonomia Completa do Skybridge

**Data:** 2026-01-21
**Status:** 📋 Proposta
**Versão:** 2.0
**Autores:** Baseado em RELATORIO_CONSOLIDADO_SKYBRIDGE_20260121.md + roadmap-pos-adr21.md
**Mudança:** Reorganização de prioridades - Domain Events primeiro

---

## 🔄 Resumo Executivo

Este PRD consolida duas análises independentes do Skybridge para definir um roadmap claro, priorizado e **verificável** para atingir autonomia completa.

### 🎯 Nova Estratégia de Prioridades

**Mudança Fundamental:** Arquitetura limpa (Domain Events) é pré-requisito para autonomia sustentável. Sem desacoplamento, cada nova funcionalidade aumenta complexidade exponencialmente.

```
ORDEM ANTERIOR (Autonomia Primeiro):
1. Commit/Push/PR → valor visível imediato
2. Domain Events → refatoração futura

NOVA ORDEM (Arquitetura Primeiro):
1. Domain Events → fundação limpa
2. Documentação → consistência
3. Redis/DragonflyDB → persistência escalável
4. Demais críticos → autonomia em base sólida
```

### Status Atual Consolidado

| Dimensão | Status | Gap Principal |
|----------|--------|---------------|
| **Arquitetura** | ❌ 0% | **SEM Domain Events (acoplado)** |
| **Documentação** | ⚠️ 70% | Inconsistências de status |
| **Infraestrutura** | ✅ 90% | Fila em memória (não persiste crash) |
| **Webhook → Agente** | ✅ 85% | Apenas GitHub implementado |
| **Geração de Código** | ⚠️ 30% | SEM COMMIT/PUSH/PR automático |
| **Autonomia Atual** | **35-40%** | Fluxo quebra após "código escrito" |

---

## 1. Objetivos

### 1.1 Objetivo Principal

Construir uma **base arquitetural limpa e escalável** que suporte autonomia crescente sem criar débito técnico.

### 1.2 Nova Estrutura de Fases

| Fase | Foco | Objetivo | Timeline | Autonomia |
|------|------|----------|----------|-----------|
| **Fase 0** | **Arquitetura** | Domain Events + Docs | 1 semana | Fundação limpa |
| **Fase 1** | **Infraestrutura** | Redis/DragonflyDB | 1 semana | Escalabilidade |
| **Fase 2** | **Autonomia** | Commit/Push/PR | 1-2 semanas | 60% |
| **Fase 3** | **Workflow** | Multi-Agent | 1-2 meses | 80% |
| **Fase 4** | **Produção** | CI/CD + Dashboard | 3-6 meses | 95% |

---

## 2. Matriz de Prioridades Reorganizada

### 2.1 Nova Ordem de Gaps

| Prioridade | Gap | Criticidade | Esforço | Justificativa |
|------------|-----|-------------|---------|---------------|
| **🥇 #1** | **Domain Events** | 🔴 FUNDACIONAL | 17-25h | Pré-requisito para escalabilidade |
| **🥈 #2** | **Inconsistências Docs** | 🔴 CRÍTICO | 2-3h | Documentação reflete realidade |
| **🥉 #3** | **Redis/DragonflyDB** | 🔴 CRÍTICO | 2 dias | Persistência production-ready |
| 4 | Commit/Push Automation | 🔴 CRÍTICO | 2-4h | Autonomia básica |
| 5 | PR Auto-Creation | 🔴 CRÍTICO | 4-6h | Autonomia básica |
| 6 | Multi-Agent Orchestrator | 🟡 IMPORTANTE | 12-16h | Workflow avançado |
| 7 | Test Runner Agent | 🟡 IMPORTANTE | 6-8h | Qualidade |
| 8 | Sistema de Retry | 🟡 IMPORTANTE | 1-2 dias | Robustez |
| 9 | Cleanup Worktree | 🟡 IMPORTANTE | 0.5 dia | Manutenibilidade |
| 10 | Dashboard | 🟢 DESEJÁVEL | 3-4 dias | Operabilidade |
| 11 | Notificações | 🟢 DESEJÁVEL | 2-3 dias | UX |
| 12 | Rate Limiting | 🟡 IMPORTANTE | 1 dia | Produção |
| 13 | Auth/Permissions | 🟢 DESEJÁVEL | 1-2 dias | Segurança |
| 14 | CI/CD Integration | 🟢 DESEJÁVEL | 8-12h | Deploy |
| 15 | Failure Learning | 🟢 DESEJÁVEL | 12-16h | Melhoria contínua |

### 2.2 Justificativa da Mudança

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    POR QUÊ DOMAIN EVENTS PRIMEIRO?                          │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  SEM DOMAIN EVENTS:                                                         │
│  ├── WebhookProcessor conhece Trello diretamente                           │
│  ├── JobOrchestrator conhece Trello diretamente                            │
│  ├── Adicionar Discord = modificar 2 arquivos                              │
│  ├── Adicionar Slack = modificar 3 arquivos                                │
│  └── Complexidade: O(n²)                                                   │
│                                                                             │
│  COM DOMAIN EVENTS:                                                         │
│  ├── WebhookProcessor emite IssueReceivedEvent                            │
│  ├── JobOrchestrator emite JobCompletedEvent                              │
│  ├── TrelloEventListener escuta eventos                                    │
│  ├── Adicionar Discord = criar DiscordEventListener                       │
│  ├── Adicionar Slack = criar SlackEventListener                           │
│  └── Complexidade: O(n)                                                    │
│                                                                             │
│  DECISÃO: Investir 17-25h agora para economizar 100+ horas depois          │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 3. FASE 0: Arquitetura Limpa (Domain Events) - 17-25h

**Objetivo:** Desacoplar completamente WebhookProcessor e JobOrchestrator via Domain Events.

### Sprint 0.1: Fundação de Domain Events (6-8h)

- [ ] **ARCH-01:** Criar `DomainEvent` base class
  - [ ] Arquivo: `src/core/domain_events/domain_event.py`
  - [ ] Atributos: `event_id`, `timestamp`, `aggregate_id`, `event_type`
  - [ ] Método: `to_dict()`, `from_dict()`
  - [ ] Responsável: @dev-arch
  - [ ] Aceite: Testes unitários passando

- [ ] **ARCH-02:** Criar `EventBus` interface
  - [ ] Arquivo: `src/core/domain_events/event_bus.py`
  - [ ] Métodos: `publish()`, `subscribe()`, `unsubscribe()`
  - [ ] Type hints fortes
  - [ ] Responsável: @dev-arch
  - [ ] Aceite: Interface definida

- [ ] **ARCH-03:** Implementar `InMemoryEventBus`
  - [ ] Arquivo: `src/infra/domain_events/in_memory_event_bus.py`
  - [ ] Pub/sub síncrono (para começar)
  - [ ] Thread-safe com `asyncio.Lock()`
  - [ ] Responsável: @dev-arch
  - [ ] Aceite: Eventos publicados/consumidos

### Sprint 0.2: Eventos Específicos (4-6h)

- [ ] **ARCH-04:** Criar eventos de Job
  - [ ] `JobCreatedEvent`
  - [ ] `JobStartedEvent`
  - [ ] `JobCompletedEvent`
  - [ ] `JobFailedEvent`
  - [ ] Responsável: @dev-arch
  - [ ] Aceite: Eventos definidos com testes

- [ ] **ARCH-05:** Criar eventos de Issue
  - [ ] `IssueReceivedEvent`
  - [ ] `IssueAssignedEvent`
  - [ ] `IssueLabelledEvent`
  - [ ] Responsável: @dev-arch
  - [ ] Aceite: Eventos definidos com testes

- [ ] **ARCH-06:** Criar eventos de Trello
  - [ ] `TrelloCardCreatedEvent`
  - [ ] `TrelloCardUpdatedEvent`
  - [ ] `TrelloCardMovedEvent`
  - [ ] Responsável: @dev-arch
  - [ ] Aceite: Eventos definidos com testes

### Sprint 0.3: Migrar WebhookProcessor (3-4h)

- [ ] **ARCH-07:** Migrar `WebhookProcessor` para eventos
  - [ ] Arquivo: `src/core/webhooks/application/webhook_processor.py`
  - [ ] Remover chamada direta a `trello_service.create_card_from_github_issue()`
  - [ ] Emitir `IssueReceivedEvent` ao invés
  - [ ] Injetar `EventBus` via construtor
  - [ ] Responsável: @dev-core
  - [ ] Aceite: WebhookProcessor desacoplado, testes passando

### Sprint 0.4: Criar TrelloEventListener (2-3h)

- [ ] **ARCH-08:** Criar `TrelloEventListener`
  - [ ] Arquivo: `src/core/webhooks/infrastructure/listeners/trello_event_listener.py`
  - [ ] Subscribe `IssueReceivedEvent`
  - [ ] Chamar `trello_service.create_card()` ao receber evento
  - [ ] Responsável: @dev-core
  - [ ] Aceite: Trello funciona via eventos

### Sprint 0.5: Migrar JobOrchestrator (2-3h)

- [ ] **ARCH-09:** Migrar `JobOrchestrator` para eventos
  - [ ] Arquivo: `src/core/webhooks/application/job_orchestrator.py`
  - [ ] Emitir `JobStartedEvent` no início
  - [ ] Emitir `JobCompletedEvent` ao completar
  - [ ] Emitir `JobFailedEvent` ao falhar
  - [ ] Remover chamadas diretas a `trello_service`
  - [ ] Responsável: @dev-core
  - [ ] Aceite: Orchestrator desacoplado, testes passando

### Sprint 0.6: NotificationEventListener (3-4h)

- [ ] **ARCH-10:** Criar `NotificationEventListener`
  - [ ] Arquivo: `src/core/webhooks/infrastructure/listeners/notification_event_listener.py`
  - [ ] Subscribe `JobCompletedEvent`, `JobFailedEvent`
  - [ ] Enviar notificações (Discord, Slack, Email)
  - [ ] Responsável: @dev-infra
  - [ ] Aceite: Notificações via eventos

### Sprint 0.7: MetricsEventListener (3-4h)

- [ ] **ARCH-11:** Criar `MetricsEventListener`
  - [ ] Arquivo: `src/core/webhooks/infrastructure/listeners/metrics_event_listener.py`
  - [ ] Subscribe todos os eventos
  - [ ] Registrar métricas (jobs/hora, latência, sucesso/falha)
  - [ ] Responsável: @dev-observability
  - [ ] Aceite: Métricas registradas automaticamente

### Deliverable Fase 0

**Arquitetura Final:**
```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    ARQUITETURA PÓS-DOMAIN EVENTS                             │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  WebhookProcessor                                                          │
│      │                                                                      │
│      ├── emit(IssueReceivedEvent) ─────────────────────────┐               │
│      │                                                      │               │
│  EventBus (InMemory)                                        │               │
│      │                                                      │               │
│      ├── subscribe(TrelloEventListener)                     │               │
│      ├── subscribe(NotificationEventListener)               │               │
│      ├── subscribe(MetricsEventListener)                    │               │
│      └── subscribe(FutureEventListener) ← fácil adicionar  │               │
│                                                              ↓               │
│  JobOrchestrator                                              │               │
│      │                                                        │               │
│      ├── emit(JobStartedEvent) ──────────────────────────────┤               │
│      │                                                        │               │
│      └── emit(JobCompletedEvent/JobFailedEvent)              │               │
│                                                                 ↓               │
│  EventBus                                                      │               │
│      │                                                          │               │
│      ├── TrelloEventListener (atualiza card)                   │               │
│      ├── NotificationEventListener (envia alerta)              │               │
│      └── MetricsEventListener (registra métrica)               │               │
│                                                                             │
│  VANTAGENS:                                                                 │
│  ✅ Adicionar nova integração = criar novo listener                         │
│  ✅ WebhookProcessor não conhece Trello                                      │
│  ✅ JobOrchestrator não conhece Trello                                       │
│  ✅ Testes não precisam mockar Trello                                        │
│  ✅ Eventos podem ser persistidos para replay                                │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

**Métricas de Sucesso:**
- [ ] Zero acoplamento direto WebhookProcessor → Trello
- [ ] Zero acoplamento direto JobOrchestrator → Trello
- [ ] Novo listener adicionável sem modificar código existente
- [ ] Testes unitários sem mocks de Trello
- [ ] Autonomia: Fundação limpa (35% → 35%, mas arquitetura escalável)

---

## 4. FASE 1: Consistência de Documentação - 2-3h

**Objetivo:** Documentação reflete realidade do código.

### Sprint 1.1: Atualizar Status de Documentos (2-3h)

- [ ] **DOC-01:** Atualizar PRD017 status
  - [ ] Mudar de "📋 Proposta" para "✅ Implementado"
  - [ ] Adicionar seção "Status de Implementação"
  - [ ] Referenciar `IMPLEMENTACAO_FILEBASEDQUEUE.md`
  - [ ] Responsável: @document-owner
  - [ ] Aceite: PR criado e mergeado

- [ ] **DOC-02:** Atualizar `ANALISE_PROBLEMAS_ATUAIS.md`
  - [ ] Marcar Problema #1 como "✅ RESOLVIDO"
  - [ ] Adicionar referência para `FileBasedJobQueue`
  - [ ] Atualizar data para 2026-01-17
  - [ ] Responsável: @document-owner
  - [ ] Aceite: PR criado e mergeado

- [ ] **DOC-03:** Atualizar PRD016 status
  - [ ] Mudar de "📋 Proposta" para "🔄 Em Implementação"
  - [ ] Adicionar referência para Fase 0 (Domain Events)
  - [ ] Responsável: @document-owner
  - [ ] Aceite: PR criado e mergeado

- [ ] **DOC-04:** Integrar `FLUXO_GITHUB_TRELO_COMPONENTES.md` ao PRD013
  - [ ] Adicionar como seção "Status de Implementação"
  - [ ] Criar referência cruzada
  - [ ] Responsável: @document-owner
  - [ ] Aceite: PR criado e mergeado

### Deliverable Fase 1

**Métricas de Sucesso:**
- [ ] Todos os PRDs com status correto
- [ ] Zero inconsistência entre docs e código
- [ ] Documentação navegável

---

## 5. FASE 2: Redis com DragonflyDB - 2 dias

**Objetivo:** Persistência escalável com DragonflyDB em modo CLI streaming logs.

### Por que DragonflyDB?

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    DRAGONFLYDB VS REDIS                                     │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  REDIS TRADICIONAL:                                                         │
│  ├── Single-threaded                                                       │
│  ├── Memória limitada                                                     │
│  ├── Persistência RDB/AOF                                                 │
│  └── Overhead de gerenciamento                                             │
│                                                                             │
│  DRAGONFLYDB:                                                               │
│  ├── Multi-threaded (3x throughput)                                       │
│  ├── Memória otimizada                                                     │
│  ├── Compatível com protocolo Redis                                        │
│  ├── Modo CLI: `dragonfly --cli --log-level debug`                        │
│  └── Streaming de logs para stdout/stderr                                  │
│                                                                             │
│  VANTAGENS PARA SKYBRIDGE:                                                  │
│  ✅ Cliente redis Python funciona sem mudanças                             │
│  ✅ Modo CLI facilita debug (logs em tempo real)                           │
│  ✅ Sem servidor separado (processo CLI)                                   │
│  ✅ Persistência embutida                                                  │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Sprint 2.1: Setup DragonflyDB CLI (0.5 dia)

- [ ] **INFRA-01:** Instalar DragonflyDB
  - [ ] Download: `curl -L https://dragonflydb.io/get.sh | sh`
  - [ ] Ou Docker: `docker pull docker.dragonflydb.io/dragonflydb/dragonfly`
  - [ ] Responsável: @devops
  - [ ] Aceite: `dragonfly --version` funciona

- [ ] **INFRA-02:** Configurar DragonflyDB modo CLI
  - [ ] Comando: `dragonfly --cli --log-level debug --dir ./data/dragonfly`
  - [ ] Streams logs para stdout/stderr
  - [ ] Porta padrão: 6379
  - [ ] Responsável: @devops
  - [ ] Aceite: DragonflyDB rodando em modo CLI

- [ ] **INFRA-03:** Script de startup com log streaming
  - [ ] Arquivo: `scripts/start_dragonfly.sh`
  - [ ] Background process com `nohup`
  - [ ] Logs redirecionados para `logs/dragonfly.log`
  - [ ] Responsável: @devops
  - [ ] Aceite: `./start_dragonfly.sh` funciona

### Sprint 2.2: Cliente Redis Python (0.5 dia)

- [ ] **INFRA-04:** Instalar cliente redis
  - [ ] `pip install redis`
  - [ ] Adicionar ao `pyproject.toml`
  - [ ] Responsável: @dev-infra
  - [ ] Aceite: `import redis` funciona

- [ ] **INFRA-05:** Testar conexão DragonflyDB
  - [ ] Script: `scripts/test_dragonfly.py`
  - [ ] Conexão: `redis.Redis(host='localhost', port=6379)`
  - [ ] Teste PING/PONG
  - [ ] Responsável: @dev-infra
  - [ ] Aceite: Conexão bem-sucedida

### Sprint 2.3: RedisJobQueue Adapter (1 dia)

- [ ] **INFRA-06:** Criar `RedisJobQueue`
  - [ ] Arquivo: `src/infra/webhooks/adapters/redis_job_queue.py`
  - [ ] Implementar `JobQueuePort` com redis-py
  - [ ] Estrutura no DragonflyDB:
    ```
    skybridge:jobs:queue → List (LPUSH/BRPOP)
    skybridge:jobs:{job_id} → Hash (dados do job)
    skybridge:jobs:processing → Set (jobs em processamento)
    skybridge:jobs:completed → Set (jobs completados)
    skybridge:jobs:failed → Set (jobs falhados)
    ```
  - [ ] Responsável: @dev-infra
  - [ ] Aceite: Testes unitários passando

- [ ] **INFRA-07:** Implementar métodos core
  - [ ] `enqueue()` - LPUSH O(1)
  - [ ] `dequeue()` - BRPOP blocking
  - [ ] `get_job()` - HGETALL
  - [ ] `update_status()` - HSET + SADD/SREM
  - [ ] Responsável: @dev-infra
  - [ ] Aceite: Todos os métodos testados

- [ ] **INFRA-08:** Metrics embutidas
  - [ ] `get_metrics()` - throughput, latência, backlog
  - [ ] Persistência de métricas em DragonflyDB
  - [ ] Responsável: @dev-infra
  - [ ] Aceite: Métricas acessíveis

### Sprint 2.4: Migration e Factory (0.5 dia)

- [ ] **INFRA-09:** Migration FileBased → Redis
  - [ ] Feature flag: `JOB_QUEUE_PROVIDER=redis|dragonfly|file`
  - [ ] Factory pattern em `src/infra/webhooks/adapters/job_queue_factory.py`
  - [ ] Responsável: @dev-infra
  - [ ] Aceite: Feature flag funcional

- [ ] **INFRA-10:** Configurar environment
  - [ ] `.env.example` atualizado com:
    ```bash
    JOB_QUEUE_PROVIDER=dragonfly
    DRAGONFLY_HOST=localhost
    DRAGONFLY_PORT=6379
    DRAGONFLY_DIR=./data/dragonfly
    ```
  - [ ] Documentar em `docs/how-to/dragonfly-setup.md`
  - [ ] Responsável: @devops
  - [ ] Aceite: Documentação completa

### Deliverable Fase 2

**Arquitetura Redis/DragonflyDB:**
```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    DRAGONFLYDB CLI MODE                                     │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  Terminal 1: DragonflyDB Processo                                          │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │ $ ./start_dragonfly.sh                                              │   │
│  │ DragonflyDB version 1.0.0 starting...                               │   │
│  │ [DEBUG] Listening on 127.0.0.1:6379                                │   │
│  │ [DEBUG] Job enqueued: skybridge:jobs:queue → job_123               │   │
│  │ [DEBUG] Job dequeued: job_123                                      │   │
│  │ [DEBUG] Job completed: job_123                                     │   │
│  │ [INFO] Throughput: 45 jobs/hour                                    │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                  ↑                                         │
│                                  │                                         │
│  Terminal 2: Skybridge API Server                                        │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │ $ python -m apps.api.main                                           │   │
│  │ RedisJobQueue connected to DragonflyDB                             │   │
│  │ Job #123 enqueued successfully                                     │   │
│  │ Job #123 processing...                                              │   │
│  │ Job #123 completed                                                  │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  VANTAGENS:                                                                 │
│  ✅ Logs em tempo real via stdout                                         │
│  ✅ Debug sem ferramentas externas                                         │
│  ✅ Processo único (sem docker-compose)                                   │
│  ✅ Persistência automática                                                │
│  ✅ Cliente redis Python sem mudanças                                      │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

**Métricas de Sucesso:**
- [ ] DragonflyDB rodando em modo CLI
- [ ] Logs streaming em tempo real
- [ ] Throughput: >1000 jobs/hora
- [ ] Latência: <5ms/operação
- [ ] Multi-worker: NATIVO
- [ ] Autonomia: Infraestrutura escalável (35% → 40%)

---

## 6. FASE 3: Autonomia Básica (60%) - 8-10h

**Objetivo:** Issues simples são resolvidas end-to-end sem intervenção humana (exceto merge).

### Sprint 3.1: Commit + Push Automation (2-4h)

- [ ] **CODE-01:** Implementar commit automático pós-agente
  - [ ] Arquivo: `src/core/webhooks/application/job_orchestrator.py`
  - [ ] Após agente completar, adicionar:
    ```python
    # Commit changes
    subprocess.run(["git", "add", "."], cwd=worktree_path, check=True)
    commit_msg = f"fix: #{issue_number} - Auto-generated by Skybridge"
    subprocess.run(["git", "commit", "-m", commit_msg], cwd=worktree_path, check=True)
    ```
  - [ ] Emitir `JobCommittedEvent` (Domain Event!)
  - [ ] Responsável: @dev-core
  - [ ] Aceite: Teste unitário passando + integração manual

- [ ] **CODE-02:** Implementar push automático
  - [ ] Arquivo: `src/core/webhooks/application/job_orchestrator.py`
  - [ ] Após commit, adicionar:
    ```python
    # Push to remote
    subprocess.run(["git", "push"], cwd=worktree_path, check=True)
    ```
  - [ ] Emitir `JobPushedEvent` (Domain Event!)
  - [ ] Responsável: @dev-core
  - [ ] Aceite: Branch visível no GitHub após job completar

### Sprint 3.2: PR Auto-Creation (4-6h)

- [ ] **CODE-03:** Criar `src/infra/github/github_api_client.py`
  - [ ] Implementar classe `GitHubAPIClient`
  - [ ] Métodos: `create_pr()`, `comment_on_issue()`, `close_issue()`
  - [ ] Usar httpx para async HTTP
  - [ ] Responsável: @dev-infra
  - [ ] Aceite: Testes unitários passando

- [ ] **CODE-04:** Criar `src/core/webhooks/application/pr_service.py`
  - [ ] Implementar `PRService.create_pr_from_worktree()`
  - [ ] Fluxo: detect changes → commit → push → create PR → comment
  - [ ] Emitir `PRCreatedEvent` ao criar PR (Domain Event!)
  - [ ] Responsável: @dev-core
  - [ ] Aceite: Teste de integração passando

- [ ] **CODE-05:** Integrar PRService ao JobOrchestrator
  - [ ] Arquivo: `src/core/webhooks/application/job_orchestrator.py`
  - [ ] Chamar `pr_service.create_pr_from_worktree()` após push
  - [ ] Atualizar metadata do job com PR URL
  - [ ] Responsável: @dev-core
  - [ ] Aceite: Issue → PR workflow completo funcionando

- [ ] **CODE-06:** Configurar GITHUB_TOKEN
  - [ ] Adicionar ao `.env.example`
  - [ ] Documentar em `docs/how-to/github-setup.md`
  - [ ] Responsável: @devops
  - [ ] Aceite: Documentação atualizada

### Sprint 3.3: Cleanup de Worktree (0.5 dia)

- [ ] **CODE-07:** Ativar cleanup de worktree
  - [ ] Arquivo: `src/core/webhooks/application/job_orchestrator.py`
  - [ ] Chamar `worktree_manager.remove_worktree()` após PR criado
  - [ ] Emitir `WorktreeRemovedEvent` (Domain Event!)
  - [ ] Adicionar logging de cleanup
  - [ ] Responsável: @dev-core
  - [ ] Aceite: `git worktree list` não mostra worktrees órfãos

### Deliverable Fase 3

**Cenário de Aceite:**
```
1. Issue #123 criada no GitHub
2. [DOMAIN EVENTS] WebhookProcessor emite IssueReceivedEvent
3. [DOMAIN EVENTS] TrelloEventListener cria card no Trello
4. Job enfileirado no DragonflyDB
5. [DOMAIN EVENTS] JobOrchestrator emite JobStartedEvent
6. Agente executa e modifica arquivos
7. [DOMAIN EVENTS] JobOrchestrator emite JobCommittedEvent
8. [DOMAIN EVENTS] JobOrchestrator emite JobPushedEvent
9. [DOMAIN EVENTS] PRService cria PR e emite PRCreatedEvent
10. [DOMAIN EVENTS] NotificationEventListener envia notificação
11. [DOMAIN EVENTS] MetricsEventListener registra métricas
12. Worktree removida (emit WorktreeRemovedEvent)
13. [INTERVENÇÃO HUMANA] Merge do PR
```

**Métricas de Sucesso:**
- [ ] Tempo issue→PR: < 5 minutos
- [ ] % de issues com PR criado: > 90%
- [ ] Worktrees órfãos: 0
- [ ] Todos os passos via Domain Events
- [ ] Autonomia medida: 60%

---

## 7. FASE 4: Multi-Agent Workflow (80%) - 40-50h

**Objetivo:** Workflow multi-agente com teste, validação e desafio de qualidade.

### Sprint 4.1: Test Runner Agent (6-8h)

- [ ] **CODE-08:** Criar skill `/test-issue`
  - [ ] Arquivo: `plugins/github-issues/skills/test-issue/SKILL.md`
  - [ ] Implementar `TestRunnerAgent`
  - [ ] Executar `pytest` automaticamente
  - [ ] Emitir `TestsCompletedEvent` ou `TestsFailedEvent`
  - [ ] Responsável: @dev-agents
  - [ ] Aceite: Testes rodam após PR criado

- [ ] **CODE-09:** Criar issue de correção em falha
  - [ ] Se testes falham, criar issue auto-referenciada
  - [ ] Adicionar logs de teste
  - [ ] Responsável: @dev-agents
  - [ ] Aceite: Falha em teste gera issue nova

### Sprint 4.2: Multi-Agent Orchestrator (12-16h)

- [ ] **CODE-10:** Criar `MultiAgentOrchestrator`
  - [ ] Arquivo: `src/core/webhooks/application/multi_agent_orchestrator.py`
  - [ ] Implementar workflow: create → resolve → test → challenge
  - [ ] Handoffs estruturados (context passing)
  - [ ] Emitir `AgentHandoffEvent` a cada transição
  - [ ] Responsável: @dev-core
  - [ ] Aceite: SPEC009 implementado

- [ ] **CODE-11:** Implementar auto-iteração
  - [ ] Agente pode chamar outro agente
  - [ ] Fallback chain (Claude → Roo → Copilot)
  - [ ] Responsável: @dev-agents
  - [ ] Aceite: Agente chama agente

- [ ] **CODE-12:** Quality Challenger Agent
  - [ ] Skill `/challenge-quality`
  - [ ] Testes adversariais (boundary, concurrency, security)
  - [ ] Emitir `QualityChallengeCompletedEvent`
  - [ ] Responsável: @dev-agents
  - [ ] Aceite: Ataques detectam bugs

### Sprint 4.3: Sistema de Retry Avançado (1 dia)

- [ ] **CODE-13:** Implementar `RetryPolicy`
  - [ ] Arquivo: `src/core/webhooks/application/retry_policy.py`
  - [ ] Exponential backoff: [60s, 300s, 900s]
  - [ ] Retry se: timeout, network, 429, 500
  - [ ] Não retry se: 400, 403, 404
  - [ ] Emitir `JobRetriedEvent` a cada retry
  - [ ] Responsável: @dev-core
  - [ ] Aceite: Jobs falhos reprocessam automaticamente

### Sprint 4.4: Notificações Avançadas (2-3 dias)

- [ ] **CODE-14:** Criar `NotificationService`
  - [ ] Já existe `NotificationEventListener` da Fase 0!
  - [ ] Apenas configurar canais: Discord, Slack, Email
  - [ ] Responsável: @dev-infra
  - [ ] Aceite: Notificação enviada em job completo/falha

- [ ] **INFRA-11:** Configurar webhooks de notificação
  - [ ] Adicionar DISCORD_WEBHOOK_URL ao `.env.example`
  - [ ] Documentar em `docs/how-to/notifications.md`
  - [ ] Responsável: @devops
  - [ ] Aceite: Notificações funcionando

### Deliverable Fase 4

**Cenário de Aceite (via Domain Events):**
```
1. Issue #123 criada
2. [EVENT] IssueReceivedEvent emitido
3. Criador Agent analisa e cria plano
   [EVENT] AgentPlanCreatedEvent
4. Resolvedor Agent implementa solução
   [EVENT] AgentResolutionCompletedEvent
5. Test Runner Agent executa pytest
   - Se falha:
     [EVENT] TestsFailedEvent
     Issue #124 criada "Fix tests for #123"
   - Se sucesso:
     [EVENT] TestsPassedEvent
6. Quality Challenger Agent ataca solução
   - Se bug encontrado:
     [EVENT] QualityChallengeFailedEvent
     Issue #125 criada
   - Se sucesso:
     [EVENT] QualityChallengePassedEvent
7. PR criado com todos os artifacts
   [EVENT] PRCreatedEvent
8. [EVENT] NotificationEventListener envia: "✅ PR #456 pronto"
9. Worktree limpa
   [EVENT] WorktreeRemovedEvent
10. [INTERVENÇÃO HUMANA] Aprovação e merge
```

**Métricas de Sucesso:**
- [ ] % de PRs com testes passando: > 80%
- [ ] % de bugs encontrados por challenger: > 30%
- [ ] Tempo issue→PR pronto: < 10 minutos
- [ ] Todos os eventos rastreáveis
- [ ] Autonomia medida: 80%

---

## 8. FASE 5: Produção Escalável (95%) - 60-80h

**Objetivo:** Sistema escalável, monitorável e auto-incidente.

### Sprint 5.1: Rate Limiting (1 dia)

- [ ] **CODE-15:** Implementar `GitHubRateLimiter`
  - [ ] Arquivo: `src/infra/github/rate_limiter.py`
  - [ ] Limites: 5000/hora (auth), 60/hora (não auth)
  - [ ] Semaphore para throttling
  - [ ] Emitir `RateLimitWarningEvent` se próximo do limite
  - [ ] Responsável: @dev-infra
  - [ ] Aceite: Rate limit respeitado

### Sprint 5.2: Auth/Permissions (1-2 dias)

- [ ] **SEC-01:** Implementar `GitHubAuthMiddleware`
  - [ ] Arquivo: `src/core/auth/auth_middleware.py`
  - [ ] IP allowlist (GitHub IPs)
  - [ ] Repository whitelist
  - [ ] Emitir `UnauthorizedWebhookEvent` se rejeitado
  - [ ] Responsável: @dev-security
  - [ ] Aceite: Webhooks não autorizados rejeitados

### Sprint 5.3: CI/CD Integration (8-12h)

- [ ] **DEVOPS-01:** Auto-deploy pós-merge
  - [ ] Workflow: `.github/workflows/auto-deploy.yml`
  - [ ] Trigger: PR merged
  - [ ] Deploy automático para produção
  - [ ] Responsável: @devops
  - [ ] Aceite: Merge → deploy automático

- [ ] **DEVOPS-02:** Rollback automático
  - [ ] Se deploy falhar, rollback automático
  - [ ] Health checks
  - [ ] Emitir `DeployCompletedEvent` ou `DeployFailedEvent`
  - [ ] Responsável: @devops
  - [ ] Aceite: Rollback funciona

### Sprint 5.4: Dashboard (3-4 dias)

- [ ] **UI-01:** Criar dashboard web
  - [ ] Arquivo: `src/presentation/dashboard/app.py`
  - [ ] FastAPI + Jinja2
  - [ ] Rotas: `/`, `/jobs/{job_id}`, `/metrics`
  - [ ] Consumir `MetricsEventListener` data
  - [ ] Responsável: @dev-ui
  - [ ] Aceite: Dashboard acessível

- [ ] **UI-02:** Monitoramento em tempo real
  - [ ] Queue size, active jobs, recent completed/failed
  - [ ] Worktrees list
  - [ ] Metrics (jobs/hour, latência P95)
  - [ ] Event stream via WebSocket (opcional)
  - [ ] Responsável: @dev-ui
  - [ ] Aceite: Dashboard atualiza em tempo real

- [ ] **UI-03:** Debug visual de jobs
  - [ ] Detalhes de job: logs, snapshots, diff
  - [ ] Timeline de execução com eventos
  - [ ] Visualizar todos os Domain Events do job
  - [ ] Responsável: @dev-ui
  - [ ] Aceite: Debug visual funciona

### Sprint 5.5: Failure Learning (12-16h)

- [ ] **ML-01:** Implementar `FailureLearning`
  - [ ] Arquivo: `src/core/webhooks/application/failure_learning.py`
  - [ ] Escutar `JobFailedEvent`
  - [ ] Extrair padrões de falha
  - [ ] Sugerir mitigações
  - [ ] Responsável: @dev-ml
  - [ ] Aceite: Padrões detectados

- [ ] **ML-02:** Auto-iteração em falhas
  - [ ] Falha → nova tentativa automática
  - [ ] Aprendizado de erros passados
  - [ ] Emitir `FailurePatternDetectedEvent`
  - [ ] Responsável: @dev-ml
  - [ ] Aceite: Sistema melhora com tempo

### Deliverable Fase 5

**Cenário de Aceite (Produção):**
```
1. Issue #123 criada
2. [Fase 4 completa]: Workflow multi-agente executa
   - Todos os eventos rastreáveis via Domain Events
3. PR criado e testado
4. [INTERVENÇÃO HUMANA] PR mergeada
5. [EVENT] PRMergedEvent emitido
6. CI/CD detecta merge → deploy automático
   [EVENT] DeployStartedEvent
7. Deploy para produção
   - Se sucesso:
     [EVENT] DeployCompletedEvent
   - Se falha:
     [EVENT] DeployFailedEvent
     Rollback automático
8. Dashboard mostra:
   - Todos os eventos em tempo real
   - Métricas de throughput/latência
   - Timeline de execução visual
9. Se falha detectada:
   [EVENT] FailurePatternDetectedEvent
   Sistema aprende e melhora próxima execução
```

**Métricas de Sucesso:**
- [ ] Throughput: >100 jobs/hora (DragonflyDB)
- [ ] Latência P95: <5 minutos
- [ ] % de deploys bem-sucedidos: > 95%
- [ ] MTTR (Mean Time To Recovery): <15 minutos
- [ ] Todos os eventos rastreáveis
- [ ] Autonomia medida: 95%

---

## 9. Cronograma Consolidado (Nova Ordem)

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    TIMELINE DE IMPLEMENTAÇÃO (VERSÃO 2.0)                   │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  FASE 0: Arquitetura Limpa (Domain Events)                                 │
│  ═══════════════════════════════════════════                                 │
│  Semana 1:                                                                   │
│  ✅ ARCH-01, ARCH-02, ARCH-03 (6-8h) - Fundação                             │
│  ✅ ARCH-04, ARCH-05, ARCH-06 (4-6h) - Eventos                             │
│  ✅ ARCH-07 (3-4h) - Migrar WebhookProcessor                               │
│  ✅ ARCH-08 (2-3h) - TrelloEventListener                                   │
│  ✅ ARCH-09 (2-3h) - Migrar JobOrchestrator                                │
│  ✅ ARCH-10, ARCH-11 (6-8h) - Notification/Metrics Listeners               │
│                                                                             │
│  → Deliverable: Arquitetura desacoplada (fundação limpa)                    │
│                                                                             │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  FASE 1: Documentação Consistente                                            │
│  ════════════════════════════════════                                        │
│  Semana 1 (continuação):                                                     │
│  ✅ DOC-01, DOC-02, DOC-03, DOC-04 (2-3h)                                  │
│                                                                             │
│  → Deliverable: Docs refletem realidade                                     │
│                                                                             │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  FASE 2: Redis/DragonflyDB                                                   │
│  ═════════════════════════════                                              │
│  Semana 2:                                                                   │
│  ✅ INFRA-01, INFRA-02, INFRA-03 (0.5 dia) - Setup DragonflyDB              │
│  ✅ INFRA-04, INFRA-05 (0.5 dia) - Cliente Redis                            │
│  ✅ INFRA-06, INFRA-07, INFRA-08 (1 dia) - RedisJobQueue                   │
│  ✅ INFRA-09, INFRA-10 (0.5 dia) - Migration                                │
│                                                                             │
│  → Deliverable: Persistência escalável com debug via CLI                    │
│                                                                             │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  FASE 3: Autonomia Básica (60%)                                              │
│  ═════════════════════════════════                                           │
│  Semana 2-3:                                                                 │
│  ✅ CODE-01, CODE-02 (2-4h) - Commit/Push                                  │
│  ✅ CODE-03, CODE-04, CODE-05, CODE-06 (4-6h) - PR Automation               │
│  ✅ CODE-07 (0.5 dia) - Cleanup Worktree                                   │
│                                                                             │
│  → Deliverable: Issue → PR automático via Domain Events                     │
│                                                                             │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  FASE 4: Multi-Agent Workflow (80%)                                          │
│  ═══════════════════════════════════                                         │
│  Mês 1-2:                                                                    │
│  ✅ CODE-08, CODE-09 (6-8h) - Test Runner                                   │
│  ✅ CODE-10, CODE-11, CODE-12 (12-16h) - Multi-Agent Orchestrator            │
│  ✅ CODE-13 (1 dia) - Retry Avançado                                        │
│  ✅ CODE-14, INFRA-11 (2-3 dias) - Notificações                            │
│                                                                             │
│  → Deliverable: Workflow multi-agente com eventos                           │
│                                                                             │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  FASE 5: Produção Escalável (95%)                                            │
│  ═══════════════════════════════════════                                      │
│  Mês 3-6:                                                                    │
│  ✅ CODE-15 (1 dia) - Rate Limiting                                         │
│  ✅ SEC-01 (1-2 dias) - Auth/Permissions                                    │
│  ✅ DEVOPS-01, DEVOPS-02 (8-12h) - CI/CD                                    │
│  ✅ UI-01, UI-02, UI-03 (3-4 dias) - Dashboard                              │
│  ✅ ML-01, ML-02 (12-16h) - Failure Learning                                │
│                                                                             │
│  → Deliverable: Produção escalável com 95% autonomia                        │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 10. Matriz de Riscos

### Riscos CRÍTICOS (Mitigação Obrigatória)

| Risco | Probabilidade | Impacto | Mitigação | Status |
|-------|--------------|---------|-----------|--------|
| **Domain Events overhead** | Média | Baixo | InMemoryEventBus é rápido | ✅ Mitigado |
| **DragonflyDB bugs** | Baixa | Alto | Fallback para FileBased | ✅ Mitigado |
| **Agente alucina** | Alta | Alto | Human-in-the-loop para merges | ✅ Mitigado |
| **Worktree suja** | Média | Médio | Validação + cleanup automático | ⚠️ Parcial |

### Riscos MODERADOS (Monitoramento)

| Risco | Probabilidade | Impacto | Mitigação | Status |
|-------|--------------|---------|-----------|--------|
| **GitHub rate limit** | Média | Médio | Rate limiter + eventos | ⚠️ Fase 5 |
| **DragonflyDB crash** | Baixa | Alto | Logs + recovery | ⚠️ Fase 2 |
| **Agente travado** | Baixa | Médio | Timeout + SIGKILL | ✅ Mitigado |

---

## 11. Critérios de Sucesso

### Fase 0 (Arquitetura Limpa)

- [ ] **ACEITE-00:** Zero acoplamento direto
  - [ ] WebhookProcessor não conhece Trello
  - [ ] JobOrchestrator não conhece Trello
  - [ ] Novo listener adicionável sem modificar código existente
  - [ ] Testes sem mocks de Trello

### Fase 1 (Documentação)

- [ ] **ACEITE-01:** Documentação consistente
  - [ ] Todos os PRDs com status correto
  - [ ] Zero inconsistência entre docs e código

### Fase 2 (Redis/DragonflyDB)

- [ ] **ACEITE-02:** Persistência escalável
  - [ ] DragonflyDB rodando em modo CLI
  - [ ] Logs streaming em tempo real
  - [ ] Throughput > 1000 jobs/hora
  - [ ] Latência < 5ms/operação

### Fase 3 (Autonomia 60%)

- [ ] **ACEITE-03:** Issue → PR sem intervenção
  - [ ] Tempo < 5 minutos
  - [ ] Sucesso > 90%
  - [ ] Worktrees limpos
  - [ ] Todos os passos via Domain Events

### Fase 4 (Workflow 80%)

- [ ] **ACEITE-04:** Workflow multi-agente
  - [ ] 4+ agentes executando
  - [ ] Handoffs funcionando
  - [ ] Testes automáticos
  - [ ] Eventos rastreáveis

### Fase 5 (Produção 95%)

- [ ] **ACEITE-05:** Produção escalável
  - [ ] Throughput > 100 jobs/hora
  - [ ] Latência P95 < 5 minutos
  - [ ] Deploy success > 95%
  - [ ] Dashboard funcional

---

## 12. Próximos Passos Imediatos

### Esta Semana

1. **Aprovar PRD018 v2.0** - Revisão nova ordem de prioridades
2. **Criar branch** `feat/phase0-domain-events` - Branch de desenvolvimento
3. **Setup ambiente** - Preparar ambiente para Domain Events

### Sprint 1 (Semana 1)

4. **ARCH-01 a ARCH-03** - Fundação de Domain Events (6-8h)
5. **ARCH-04 a ARCH-06** - Eventos específicos (4-6h)
6. **ARCH-07** - Migrar WebhookProcessor (3-4h)

### Sprint 2 (Semana 1-2)

7. **ARCH-08 a ARCH-11** - Listeners completos (8-11h)
8. **DOC-01 a DOC-04** - Atualizar documentação (2-3h)
9. **Teste manual** - Validar arquitetura desacoplada

---

## 13. Apêndice: Referências

### Documentos Base

- `docs/report/RELATORIO_CONSOLIDADO_SKYBRIDGE_20260121.md`
  - Domain Events 0% implementado
  - Gap crítico de arquitetura

- `docs/report/roadmap-pos-adr21.md` (skybridge-poc-agent-sdk)
  - GitHub API Integration detalhada
  - Redis Job Queue especificação

### PRDs Relacionados

- **PRD016** - Domain Events (agora PRIORIDADE #1)
- **PRD017** - Mensageria Standalone (✅ implementado)
- **PRD013** - Webhook Autonomous Agents (Phase 1 completo)

### Especificação DragonflyDB

- **Site:** https://dragonflydb.io
- **Docs:** https://dragonflydb.io/docs
- **Modo CLI:** `dragonfly --cli --log-level debug`
- **Cliente Python:** `pip install redis` (compatível)

---

## 14. Histórico de Mudanças

| Versão | Data | Autor | Mudanças |
|--------|------|-------|----------|
| 1.0 | 2026-01-21 | Sky | Versão inicial (autonomia primeiro) |
| 2.0 | 2026-01-21 | Sky | **Reorganização**: Domain Events primeiro, depois docs, Redis/DragonflyDB, então demais |

---

> "Arquitetura limpa é fundação, não refinamento" – made by Sky 🏗️
> "Investir na fundação economiza no telhado" – made by Sky 🏠
> "Domain Events primeiro para não pagar juros de acoplamento depois" – made by Sky 💰

---

**Fim do PRD018 v2.0**
