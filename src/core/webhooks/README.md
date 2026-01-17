# Webhooks Context

Contexto de domínio para processamento de webhooks de múltiplas fontes (GitHub, Discord, YouTube, Stripe).

## Arquitetura

Seguindo os princípios de Domain-Driven Design (ADR002):

```
webhooks/
├── domain/          # Entidades de domínio e linguagem ubíqua
│   └── webhook_event.py
├── application/     # Casos de uso e orquestração
│   ├── handlers.py       # Sky-RPC handlers
│   ├── webhook_processor.py
│   ├── job_orchestrator.py
│   └── worktree_manager.py
└── ports/           # Interfaces para infraestrutura
    ├── job_queue_port.py
    └── webhook_signature_port.py
```

## Linguagem Ubíqua

- **WebhookEvent**: Evento recebido de fonte externa (GitHub, Discord)
- **WebhookJob**: Job em background para processar um WebhookEvent
- **JobStatus**: Estado do job (pending, processing, completed, failed)
- **Worktree**: Diretório git isolado para executar o trabalho

## Fluxo Principal

1. **Receber Webhook** → `POST /webhooks/{source}`
2. **Verificar Assinatura** → HMAC SHA-256 (RNF001)
3. **Criar Job** → WebhookJob criado e enfileirado
4. **Processar (Worker)** → JobOrchestrator executa job
5. **Criar Worktree** → Diretório isolado `skybridge-github-{n}`
6. **Capturar Snapshot** → Estado inicial do worktree
7. **Executar Agente** → `/resolve-issue` skill
8. **Validar Cleanup** → safe_worktree_cleanup()
9. **Remover Worktree** → Se validação passar

## Componentes

### Domain Layer

- `WebhookEvent`: Representa evento de webhook
- `WebhookJob`: Job de processamento
- `JobStatus`: Enum de estados
- `WebhookSource`: Enum de fontes (GitHub, Discord, etc)

### Application Layer

- `WebhookProcessor`: Processa webhook → cria job
- `JobOrchestrator`: Orquestra execução do job
- `WorktreeManager`: Gerencia ciclo de vida de worktrees
- `handlers.py`: Sky-RPC handlers registrados

### Ports

- `JobQueuePort`: Interface para fila de jobs
- `WebhookSignaturePort`: Interface para verificação de assinatura

## Infraestrutura

### Adapters

- `InMemoryJobQueue`: Fila em memória (MVP, Phase 1)
- `GitHubSignatureVerifier`: Verificação HMAC SHA-256
- `RedisJobQueue`: Fila persistente em Redis (Phase 3)

### Delivery

- `routes.py`: Endpoint HTTP `/webhooks/{source}`
- `webhook_auth.py`: Middleware de verificação de assinatura

### Background

- `webhook_worker.py`: Worker assíncrono de processamento

## Configuração

Environment variables:

```bash
# Webhook secrets (GitHub)
export WEBHOOK_GITHUB_SECRET="whsec_abc123..."

# Worktree base path
export WEBHOOK_WORKTREE_BASE_PATH="../skybridge-worktrees"

# Enabled sources
export WEBHOOK_ENABLED_SOURCES="github,discord,youtube"
```

## Integração com Componentes Existentes

### GitExtractor

```python
from skybridge.platform.observability.snapshot.extractors.git_extractor import (
    GitExtractor,
)

extractor = GitExtractor()
initial_snapshot = extractor.capture(worktree_path)
can_remove, message, status = extractor.validate_worktree(worktree_path)
```

### WorktreeValidator

```python
from skybridge.core.contexts.agents.worktree_validator import (
    safe_worktree_cleanup,
)

result = safe_worktree_cleanup(worktree_path, dry_run=True)
if result["can_remove"]:
    safe_worktree_cleanup(worktree_path, dry_run=False)
```

## Métricas de Sucesso (Phase 1)

| Métrica | Target |
|---------|--------|
| Issues resolvidas | 10 |
| Cleanup success rate | 90% |
| Signature verification | 100% |
| Average job duration | <5 min |

## Roadmap

### Phase 1 (MVP) - Semana 2-3
- ✅ Domain entities
- ✅ Ports e adapters
- ✅ Application services
- ✅ HMAC verification
- ✅ Webhook route
- ✅ Background worker
- ⏳ Integration tests
- ⏳ 10 real issues

### Phase 2 (Multi-Source) - Semana 4-5
- Discord webhook handler
- YouTube webhook handler
- `/respond-discord` skill
- `/summarize-video` skill

### Phase 3 (Produção) - Semana 6-8
- RedisJobQueue adapter
- Prometheus metrics
- OpenTelemetry tracing
- Grafana dashboard
- Load testing (100 events/hour)

## Referências

- PRD013: `docs/prd/PRD013-webhook-autonomous-agents.md`
- ADR002: Estrutura do Repositório Skybridge (DDD)
- ADR010: Adoção Sky-RPC
- GitExtractor: `src/skybridge/platform/observability/snapshot/extractors/git_extractor.py`
- WorktreeValidator: `src/skybridge/core/contexts/agents/worktree_validator.py`

---

> "A melhor forma de prever o futuro é criá-lo" – made by Sky 🚀
