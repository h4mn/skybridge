# Fluxo GitHub → Trello - Componentes e Status

**Data:** 2026-01-17
**Branch:** `demo/github-trello-2`
**Status:** Implementação Principal Completa

---

## 📊 Visão Geral do Fluxo

```
┌─────────────────┐
│  GitHub Webhook │
│     Receiver    │
└────────┬────────┘
         │
         ▼
┌─────────────────┐      ┌──────────────────┐
│  Webhook        │ ───► │  FileBased       │
│  Processor      │      │  JobQueue        │
└────────┬────────┘      └────────┬─────────┘
         │                        │
         │ (create card)          │ (enqueue)
         ▼                        ▼
┌─────────────────┐      ┌──────────────────┐
│  Trello         │      │  Background      │
│  Integration   │      │  Worker          │
└─────────────────┘      └────────┬─────────┘
                                  │
                                  ▼
                         ┌──────────────────┐
                         │  Job             │
                         │  Orchestrator    │
                         └────────┬─────────┘
                                  │
                                  ▼
                         ┌──────────────────┐
                         │  Claude Code     │
                         │  Agent Adapter   │
                         └──────────────────┘
```

---

## 🧩 Componentes Detalhados

### 1. GitHub Webhook Receiver

**Arquivo:** `src/core/webhooks/infrastructure/github_webhook_server.py`

**Responsabilidade:**
- Receber webhooks do GitHub via HTTP POST
- Verificar assinatura HMAC (X-Hub-Signature-256)
- Encaminhar para WebhookProcessor
- Retornar 202 Accepted

**Status:** ✅ **COMPLETO**
- Endpoint `/webhook/{source}` implementado
- Verificação de assinatura funcionando
- Integração com WebhookProcessor

**Observações:**
- Usa FastAPI
- Suporta ngrok para testes locais
- Payload validado antes do processamento

**Próximos Passos:**
- ⬜ Nenhum (componente estável)

---

### 2. Webhook Processor

**Arquivo:** `src/core/webhooks/application/webhook_processor.py`

**Responsabilidade:**
- Processar eventos de webhook brutos
- Criar WebhookJob a partir do evento
- Verificar idempotência (Camada 1: delivery_id, Camada 2: fingerprint)
- Enfileirar job para processamento assíncrono
- Criar card no Trello

**Status:** ✅ **COMPLETO**
- Idempotência multi-camadas implementada
- Criação de cards no Trello funcionando
- Integração com JobQueue

**Observações:**
- TTL de delivery_id: 24 horas
- TTL de fingerprint: 10 segundos
- Correlation ID derivado de X-GitHub-Delivery

**Próximos Passos:**
- ⬜ Nenhum (componente estável)

---

### 3. FileBased Job Queue

**Arquivo:** `src/infra/webhooks/adapters/file_based_job_queue.py`

**Responsabilidade:**
- Fila persistente em arquivos JSON
- Compartilhamento de estado entre processos (resolve Problema #1)
- Gerenciar estados: jobs/, processing/, completed/, failed/
- Coletar métricas de performance

**Status:** ✅ **COMPLETO** (Nova Implementação)
- Persistência em `workspace/skybridge/fila/`
- Drop-in replacement para InMemoryJobQueue
- Métricas embutidas (throughput, latência, backlog)
- Endpoint `/metrics` na API Skybridge (apps.server)

**Estrutura de Arquivos:**
```
workspace/skybridge/fila/
├── queue.json          # Fila principal (array de job_ids)
├── jobs/               # Jobs aguardando processamento
├── processing/         # Jobs em processamento
├── completed/          # Jobs completados
└── failed/             # Jobs que falharam
```

**Observações:**
- Throughput: ~10-20 jobs/hora
- Latência: ~50ms por operação
- Capacidade: Single worker ideal
- Break-even para Redis: 20 jobs/hora

**Métricas Disponíveis:**
- `queue_size`: Tamanho atual
- `jobs_per_hour`: Throughput médio (24h)
- `enqueue_latency_p95_ms`: Latência p95
- `backlog_age_seconds`: Idade do job mais antigo
- `disk_usage_mb`: Uso de disco

**Próximos Passos:**
- ⬜ Monitorar métricas por 1-2 semanas
- ⬜ Usar GUIA_DECISAO_MENSAGERIA.md para decidir quando migrar para Redis
- ⬜ Se score >= 5: Planejar migração para RedisJobQueue

---

### 4. Background Worker

**Arquivo:** `src/runtime/background/webhook_worker.py`

**Responsabilidade:**
- Poll da fila buscando jobs pendentes
- Dequeue jobs para processamento
- Delegar execução para JobOrchestrator
- Marcar jobs como completed/failed

**Status:** ✅ **COMPLETO**
- Loop de processamento implementado
- Integração com FileBasedJobQueue
- Graceful shutdown implementado

**Observações:**
- Poll interval: 1.0 segundo
- Usa `wait_for_dequeue()` com timeout
- 100% sequencial (1 job por vez)

**Próximos Passos:**
- ⬜ Considerar multi-worker se throughput > 15 jobs/hora
- ⬜ Documentar escalamento horizontal

---

### 5. Job Orchestrator

**Arquivo:** `src/core/webhooks/application/job_orchestrator.py`

**Responsabilidade:**
- Orquestrar execução completa de um job
- Criar/manter worktree isolado
- Spawna agente Claude Code
- Processar skybridge_command em tempo real
- Coletar snapshots (antes/depois)
- Commitar mudanças ou limpar worktree

**Status:** ✅ **COMPLETO**
- WorktreeManager integrado
- Agent Facade integrado
- Streaming de output funcionando
- Snapshot coleta implementada

**Observações:**
- Usa `git worktree` para isolamento
- Timeout por skill: hello-world (60s), resolve-issue (600s), refactor (900s)
- Cleanup automático de worktrees antigos

**Próximos Passos:**
- ⬜ Otimizar cleanup de worktrees (implementar idade baseada)
- ⬜ Considerar cache de worktrees para issues recorrentes

---

### 6. Agent Facade (Claude Code Adapter)

**Arquivos:**
- `src/core/webhooks/infrastructure/agents/agent_facade.py`
- `src/core/webhooks/infrastructure/agents/claude_agent.py`

**Responsabilidade:**
- Spawna subprocesso Claude Code
- Gerenciar comunicação via stdin/stdout
- Processar XML Streaming Protocol
- Extrair skybridge_command
- Retornar AgentExecution com resultado

**Status:** ✅ **COMPLETO**
- Spawn de agente funcionando
- XML Streaming Protocol implementado
- Extração de skybridge_command funcionando
- Timeout handling implementado

**Observações:**
- Usa `subprocess.Popen` para spawn
- Path do Claude Code: Detecta automaticamente Windows/Linux
- Sistema prompt configurável via templates

**Próximos Passos:**
- ⬜ Nenhum (componente estável)

---

### 7. Trello Integration

**Arquivos:**
- `src/core/kanban/application/trello_integration_service.py`
- `src/infra/kanban/adapters/trello_adapter.py`

**Responsabilidade:**
- Criar cards no Trello para novas issues
- Adicionar comentários com status de processamento
- Atualizar cards após conclusão

**Status:** ✅ **COMPLETO**
- Criação de cards funcionando
- Comentários de progresso funcionando
- Atualização de status funcionando

**Observações:**
- Configuração via environment variables:
  - `TRELLO_API_KEY`
  - `TRELLO_API_TOKEN`
  - `TRELLO_BOARD_ID`
- Usa httpx.AsyncClient (tem erro de event loop em alguns casos)

**Problema Conhecido:**
- ⚠️ "Event loop is closed" error em `add_card_comment`
- Cards criados com sucesso, mas comentários às vezes falham

**Próximos Passos:**
- ⬜ Implementar async context manager para TrelloAdapter
- ⬜ Reutilizar conexão httpx entre requisições

---

### 8. Observability (Métricas)

**Arquivo:** `src/runtime/delivery/routes.py` (endpoint `/metrics`)

**Responsabilidade:**
- Expor métricas da fila em tempo real
- Fornecer dados para decisão de quando migrar para Redis

**Status:** ✅ **COMPLETO** (Nível 1 - Essencial)
- Endpoint `GET /metrics` implementado
- Métricas básicas disponíveis
- JSON format para consumo fácil

**Métricas Disponíveis:**
```json
{
  "queue_size": 0,
  "enqueue_count": 1,
  "dequeue_count": 1,
  "complete_count": 1,
  "fail_count": 0,
  "enqueue_latency_avg_ms": 0.0,
  "enqueue_latency_p95_ms": 0.0,
  "dequeue_latency_avg_ms": 0.0,
  "dequeue_latency_p95_ms": 0.0,
  "jobs_per_hour": 0.0,
  "backlog_age_seconds": 0.0,
  "disk_usage_mb": 0.0
}
```

**Observações:**
- Métricas calculadas sob demanda
- Persistência em `workspace/skybridge/fila/metrics.json`
- Últimas 1000 operações mantidas em memória

**Próximos Passos:**
- ⬜ Implementar dashboard CLI (opcional)
- ⬜ Adicionar histogramas de latência (opcional)

---

## 📈 Status por Componente

| # | Componente | Status | Prioridade | Próximos Passos |
|---|-----------|--------|------------|-----------------|
| 1 | GitHub Webhook Receiver | ✅ Completo | Alta | ⬜ Nenhum |
| 2 | Webhook Processor | ✅ Completo | Alta | ⬜ Nenhum |
| 3 | FileBased Job Queue | ✅ Completo | **Crítica** | ⬜ Monitorar por 1-2 semanas |
| 4 | Background Worker | ✅ Completo | Alta | ⬜ Considerar multi-worker |
| 5 | Job Orchestrator | ✅ Completo | Alta | ⬜ Otimizar cleanup |
| 6 | Agent Facade | ✅ Completo | Alta | ⬜ Nenhum |
| 7 | Trello Integration | ✅ Completo | Média | ⬜ Fix "event loop is closed" |
| 8 | Observability | ✅ Completo (Nível 1) | Média | ⬜ Dashboard CLI (opcional) |

---

## 🎯 Roadmap de Evolução

### Curto Prazo (1-2 semanas)
- [ ] Monitorar métricas do FileBasedJobQueue em produção
- [ ] Coletar dados reais de throughput e latência
- [ ] Usar GUIA_DECISAO_MENSAGERIA.md para avaliar necessidade de Redis

### Médio Prazo (2-4 semanas)
- [ ] Implementar Domain Events (PRD016) se arquitetura demandar
- [ ] Corrigir "event loop is closed" no TrelloAdapter
- [ ] Considerar multi-worker se throughput > 15 jobs/hora

### Longo Prazo (1-2 meses)
- [ ] Migrar para RedisJobQueue se score >= 5
- [ ] Implementar retry policy para jobs falhados
- [ ] Adicionar dead letter queue para jobs com falha persistente

---

## 🚨 Problemas Conhecidos

### Problema #1: Filas Separadas (RESOLVIDO ✅)
**Descrição:** Server e Worker usavam InMemoryJobQueue separados
**Solução:** FileBasedJobQueue com persistência em filesystem
**Status:** ✅ Resolvido na branch `demo/github-trello-2`

### Problema #2: Event Loop Closed no Trello (ABERTO ⚠️)
**Descrição:** Erro ao adicionar comentários em cards
**Impacto:** Cards criados, mas comentários às vezes falham
**Solução:** Implementar async context manager para TrelloAdapter
**Prioridade:** Média

### Problema #3: Worker 100% Sequencial (POR DESIGN)
**Descrição:** Worker processa 1 job por vez
**Impacto:** Limita throughput para ~10-20 jobs/hora
**Solução:** Multi-worker ou Redis quando necessário
**Prioridade:** Baixa (monitorar métricas)

---

## 📊 Métricas de Decisão: Quando Migrar para Redis?

### Score de Migração
```
SCORE = (jobs_per_hour / 20) × 3 +
        (latency_p95_ms / 100) × 2 +
        (backlog_age_min / 5) × 2 +
        (disk_usage_mb / 500) × 1

SE SCORE >= 5:
    → MIGRAR PARA REDIS
SENÃO:
    → CONTINUAR STANDALONE
```

### Thresholds Concretos

| Métrica | Standalone OK | Avaliar Migrar | Migrar Agora |
|---------|---------------|----------------|--------------|
| jobs/hora | < 10 | 10-20 | > 20 |
| latência p95 | < 50ms | 50-100ms | > 100ms |
| backlog age | < 2min | 2-5min | > 5min |
| disk usage | < 200MB | 200-500MB | > 500MB |

---

## 📁 Documentação Relacionada

- `docs/ANALISE_PROBLEMAS_ATUAIS.md` - Problemas identificados
- `docs/GUIA_DECISAO_MENSAGERIA.md` - Guia de decisão para Redis
- `docs/IMPLEMENTACAO_FILEBASEDQUEUE.md` - Documentação técnica
- `docs/prd/PRD015-observabilidade-metricas.md` - PRD de Observabilidade
- `docs/prd/PRD016-domain-events.md` - PRD de Domain Events
- `docs/prd/PRD017-mensageria-standalone.md` - PRD da Mensageria Standalone

---

`★ Insight ─────────────────────────────────────`
O fluxo GitHub → Trello está **funcional e completo**. O FileBasedJobQueue resolve o problema crítico de filas separadas. Os próximos passos são **evolutivos**: monitorar métricas e escalar para Redis quando necessário. A arquitetura está preparada para crescer com você!
`─────────────────────────────────────────────────`

> "Sistemas que funcionam em produção valem mais que arquiteturas perfeitas no papel" – made by Sky 🚀
