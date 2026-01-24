# Análise de Problemas Atuais - Skybridge

**Data:** 2026-01-17
**Última atualização:** 2026-01-21
**Branch:** `refactor/events`
**Autor:** Sky

---

## 📋 Resumo Executivo

Esta análise identifica os **problemas críticos** que o Skybridge enfrenta hoje, suas **causas raiz** e **impactos** no sistema. Os problemas estão categorizados por severidade e prioridade de resolução.

---

## 🔴 CRÍTICOS (Bloqueiam Produção)

### 1. Filas Separadas - Jobs Nunca São Processados

**Descrição:**
Webhook Server e Webhook Worker rodam em **processos separados**, cada um criando sua **própria instância** de `InMemoryJobQueue`. Jobs enfileirados pelo servidor **nunca são vistos** pelo worker.

**Evidência:**
```python
# github_webhook_server.py (linha 126)
job_queue = InMemoryJobQueue()  # Instância #1

# webhook_worker.py (linha 146)
job_queue = InMemoryJobQueue()  # Instância #2 - SEPARADA!
```

**Impacto:**
- ✅ Webhooks são recebidos e cards criados no Trello
- ❌ Jobs ficam na fila para sempre
- ❌ Agentes nunca são executados
- ❌ Cards mostram "Aguardando processamento..." eternamente

**Causa Raiz:**
Arquitetura atual assume fila compartilhada, mas `InMemoryJobQueue` não compartilha estado entre processos.

**Solução:**
**Opção A (Quick Fix):** Unificar servidor + worker no mesmo processo
**Opção B (Produção):** Implementar `RedisJobQueue` para fila compartilhada
**Opção C (Simplificado):** Processar jobs diretamente no endpoint com `asyncio.create_task()`

**Prioridade:** 🔴 URGENTE - Sistema não funciona sem isso

---

### 2. Issue #32 - Implementada Mas Não Fechada

**Descrição:**
A issue #32 (deduplicação multi-camadas) foi **completamente implementada e commitada** (commit `3ca81ee`), mas a issue continua **ABERTA** no GitHub.

**Evidência:**
```bash
$ gh issue view 32
State: OPEN
Status: "Implementação completa em worktree skybridge-github-32-a3a2d70e"

# Commit existe:
$ git log --oneline -1
3ca81ee feat(webhooks): implementar deduplicação multi-camadas
```

**Impacto:**
- Confusão sobre status da feature
- Testes (9 testes) passando mas issue não reflete isso
- Branch isolada não integrada ao main

**Solução:**
1. Merge da worktree `skybridge-github-32-a3a2d70e` → main
2. Fechar issue #32 com comentário "Resolvido em commit 3ca81ee"
3. Atualizar milestones

**Prioridade:** 🔴 ALTA - Completação de trabalho feito

---

## 🟡 IMPORTANTES (Degradam Performance)

### 3. Erro "Event loop is closed" no Trello

**Descrição:**
Ocorre erro ao adicionar comentários em cards do Trello, mas cards **são criados mesmo assim**.

**Evidência:**
```log
Erro ao criar card: Event loop is closed
Card criado no Trello: 696bxxxx para issue #42
```

**Causa Raiz:**
`TrelloAdapter` usa `httpx.AsyncClient` que requer event loop ativo. O erro ocorre quando:
- Múltiplas operações concorrentes no mesmo cliente HTTP
- Client fechado prematuramente (método `_close()` existe mas não é chamado)
- Timeout em operações assíncronas

**Impacto:**
- ❌ Logs poluídos com erros falsos
- ✅ Funcionalidade preservada (cards são criados)
- ⚠️ Pode piorar com concorrência

**Solução:**
```python
# Garantir que AsyncClient seja compartilhado e fechado corretamente
class TrelloAdapter:
    def __init__(self):
        self._client = httpx.AsyncClient(...)

    async def __aenter__(self):
        return self

    async def __aexit__(self, *args):
        await self._client.aclose()
```

**Prioridade:** 🟡 MÉDIA - Funciona mas não é ideal

---

### 4. Issues Duplicadas #30, #31

**Descrição:**
Três issues abertas sobre o **mesmo bug** (webhooks duplicados).

**Evidência:**
```bash
$ gh issue list --state open
#30  [Bug] Webhooks being processed multiple times
#31  [Bug] Webhooks being processed multiple times
```

**Impacto:**
- Confusão sobre quais issues estão válidas
- Esforço duplicado em triagem
- Histórico fragmentado

**Solução:**
- Fechar #30 e #31 como **duplicatas de #32**
- #32 já resolve o problema com deduplicação multi-camadas

**Prioridade:** 🟡 BAIXA - Limpeza de backlog

---

## 🟢 MELHORIAS (Não Bloqueiam)

### 5. Falta de Métricas e Observabilidade

**Descrição:**
Sistema **não coleta métricas** agregadas. Impossível responder perguntas como:
- Quantos jobs por hora estamos processando?
- Qual é o tempo médio de execução?
- Qual taxa de erro?
- Quando precisamos escalar?

**Impacto:**
- ❌ Decisões baseadas em "achismo"
- ❌ Impossível detectar regressões
- ❌ Difícil justificar investimentos

**Solução:**
Implementar sistema de métricas (ver **PRD015**)

**Prioridade:** 🟢 RECOMENDADO - Base para crescimento

---

### 6. Workflow de Domain Events Não Implementado

**Descrição:**
Sistema usa chamadas diretas entre componentes em vez de **Domain Events** para comunicação assíncrona.

**Exemplo Atual:**
```python
# WebhookProcessor chama TrelloIntegrationService diretamente
trello_card_id = await self.trello_service.create_card_from_github_issue(...)
```

**Impacto:**
- 🔗 Acoplamento alto entre componentes
- ❌ Difícil adicionar novos listeners (ex: notificação Discord)
- ❌ Impossível replay de eventos
- ❌ Difícil testar isoladamente

**Solução:**
✅ **RESOLVIDO** - Implementar Domain Events (ver **PRD016**)

**Status de Implementação (2026-01-21):**
- ✅ Fase 0 do PRD018 completa
- ✅ DomainEvent base class criado
- ✅ EventBus interface definido
- ✅ InMemoryEventBus implementado
- ✅ 17 eventos de domínio definidos (Job, Issue, Trello)
- ✅ WebhookProcessor migrado (emite IssueReceivedEvent)
- ✅ JobOrchestrator migrado (emite JobStarted/Completed/Failed)
- ✅ TrelloEventListener criado
- ✅ NotificationEventListener criado
- ✅ MetricsEventListener criado

**Arquitetura Pós-Implementação:**
```
WebhookProcessor → emit(IssueReceivedEvent) → EventBus
                                                        ↓
JobOrchestrator → emit(JobStartedEvent) ─────────→ [TrelloEventListener]
                                                        ↓
                                              [NotificationEventListener]
                                                        ↓
                                               [MetricsEventListener]
```

**Prioridade:** 🟢 RECOMENDADO - Melhora arquitetura **✅ RESOLVIDO**

---

## 📊 Matriz de Priorização

| Problema | Severidade | Impacto | Esforço | Prioridade | ROI | Status |
|----------|------------|---------|---------|------------|-----|--------|
| 1. Filas separadas | 🔴 CRÍTICA | Sistema não funciona | 2-4h | P0 | 🔥🔥🔥 | ⚠️ Pendente |
| 2. Issue #32 aberta | 🟡 ALTA | Compleção bureaucratic | 0.5h | P1 | 🔥🔥 | ⚠️ Pendente |
| 3. Event loop closed | 🟡 MÉDIA | Logs poluídos | 2h | P2 | 🔥 | ⚠️ Pendente |
| 4. Issues duplicadas | 🟢 BAIXA | Limpeza | 0.5h | P3 | | ⚠️ Pendente |
| 5. Sem métricas | 🟢 MÉDIA | Decisões cegas | 2-3d | P1 | 🔥🔥 | ⚠️ Pendente |
| 6. Sem domain events | 🟢 BAIXA | Acoplamento | 5-7d | P2 | 🔥 | ✅ **RESOLVIDO** |

---

## 🎯 Plano de Ação Recomendado

### Fase 1: Estabilizar (Semanal)
```
Dia 1-2: Fix problema #1 (filas separadas)
  → Implementar Opção A (unificar processos)
  → Testar E2E com webhook real

Dia 3: Fix problema #2 (issue #32)
  → Merge worktree → main
  → Fechar issues #30, #31 como duplicatas

Dia 4-5: Fix problema #3 (event loop)
  → Implementar async context manager
  → Adicionar testes de concorrência
```

### Fase 2: Observar (Quinzenal)
```
Semana 2-3: Implementar métricas (PRD015)
  → InMemoryMetricsStore
  → Endpoint /metrics
  → Dashboard CLI

Semana 4: Analisar dados
  → Coletar baseline de performance
  → Identificar gargalos
  → Decidir próximo passo
```

### Fase 3: Evoluir (Mensal) ✅ **Domain Events COMPLETO**
```
✅ Mês 2: Domain Events (PRD016) - COMPLETADO 2026-01-21
  ✅ Event bus em memória (InMemoryEventBus)
  ✅ Migrar WebhookProcessor (emite IssueReceivedEvent)
  ✅ Migrar JobOrchestrator (emite JobStarted/Completed/Failed)
  ✅ Adicionar listeners (Trello, Notification, Metrics)
  → Ver PRD018 Fase 0 para detalhes

Mês 3+: Escalar
  → Redis como fila (PRD018 Fase 2)
  → Múltiplos workers
  → Prometheus + Grafana
```

---

## 📝 Notas

- **Problema #1 é o mais crítico** - sem isso, sistema não funciona
- **Métricas vêm antes de Domain Events** - precisa medir antes de otimizar
- **Domain Events facilitam teste** - mas não bloqueiam funcionamento
- **✅ Problema #6 RESOLVIDO** - Domain Events implementados em 2026-01-21 (PRD018 Fase 0)

---

> "Identificar problemas é o primeiro passo para resolvê-los" – made by Sky 🔍
