# 📊 Estudo: Skybridge Webhook + Agentes Autônomos

**Data:** 2026-01-07
**Autor:** Sky
**Status:** Planejamento Estratégico

---

## 1. Estado Atual da Skybridge

### Arquitetura
- **Framework**: FastAPI com uvicorn
- **Protocolo**: Sky-RPC v0.3 (tickets + envelopes)
- **Registry**: Auto-discovery de handlers via decorators
- **Segurança**: Bearer tokens, API keys, IP allowlist

### Capacidades Atuais
- ✅ CQRS pattern (Query/Command handlers)
- ✅ Event sourcing para tasks
- ✅ Plugin system (Claude Code)
- ✅ Runtime discovery e reload
- ❌ **Sem webhooks** (genérico para qualquer fonte)
- ❌ **Sem integração com serviços externos** (GitHub, Discord, etc)
- ❌ **Sem background jobs**
- ❌ **Sem scheduler**

---

## 2. Como Developers Fazem (2024/2025)

### Tendências do Mercado

| Abordagem | Descrição | Popularidade |
|-----------|-----------|--------------|
| **Multi-Source Webhooks** | Endpoints para GitHub, Discord, YouTube, Stripe, etc | 🔥 Alta |
| **Event-Driven** | Redis pub/sub, filas async | 🔥 Alta |
| **GitHub Actions** | Workflows que triggeram bots | 🟡 Média |
| **MCP Servers** | Model Context Protocol para agentes | 🆕 Nova |

### Tools Populares

- **[fastgithub](https://pypi.org/project/fastgithub/)**: Pacote Python para FastAPI + GitHub webhooks
- **[fastapi-events](https://github.com/melvinkcx/fastapi-events)**: Sistema de eventos para FastAPI
- **[Neon Webhooks Guide](https://neon.com/guides/fastapi-webhooks)**: Guia completo com PostgreSQL (Mar/2025)
- **[Event-Driven FastAPI + Redis](https://medium.com/@velocitytech/build-an-event-driven-architecture-with-fastapi-and-redis-pub-sub-deploy-it-in-kubernetes-54603ac35335)**: Arquitetura com Redis

### ⚠️ Alerta Importante: Auto-Close Issues

A comunidade **rejeita** bots que fecham issues automaticamente:

- [Kubernetes #103151](https://github.com/kubernetes/kubernetes/issues/103151): "Auto-closing is harmful"
- [VSCode](https://github.com/microsoft/vscode/issues/261976): "Bots should NOT close without human input"
- [Reddit](https://www.reddit.com/r/opensource/comments/14xx8pw/is_it_normal_practice_in_github_for_an_issue_to_be_closed/): Contributors "hate such bots"

**Best Practice 2024/2025**: Warn → Wait → Human Confirm → Close

### 📖 NOTA: Entender Profundamente os Motivos da Comunidade

**Por que a resistência?**

1. **Perda de contexto**: Issues antigas podem ainda ser relevantes mesmo sem atividade recente
2. **Desrespeito ao contribuidor**: Quem abriu a issue pode se sentir invalidado
3. **Falso positivo**: "Stale" ≠ "irrelevante" - problemas podem reaparecer
4. **Barreira de entrada**: Novos contribuidores podem se intimidar
5. **Histórico perdido**: Informações valiosas são ocultadas quando issues são fechadas

**Padrão recomendado pela comunidade:**
```
Day 0: Issue aberta
↓
Day 30: Bot marca como "stale" + comment "Ainda relevante?"
↓
Day 45: Bot marca como "stale-warning" + comment "Fecharemos em 7 dias"
↓
Day 52: Se nenhum response → fecha COM contexto explicativo
         Mas sempre permite reabrir com comentário
```

**Princípio chave**: Bots devem *facilitar* triagem humana, não *substituir* julgamento humano.

---

## 3. Bounded Context: Webhooks (Multi-Source) 🌐

### Conceito Chave

**Bounded Context = Domínio de Negócio, não Tecnologia**

O contexto `webhooks` trata de **"receber e processar eventos externos de forma padronizada"**, suportando múltiplas fontes:

```
┌─────────────────────────────────────────────────────────────────┐
│                    Bounded Context: webhooks                     │
│                                                                  │
│  "Receber e processar eventos externos de forma padronizada"    │
│                                                                  │
│  ┌─────────┐  ┌─────────┐  ┌─────────┐  ┌─────────┐            │
│  │ GitHub  │  │ Discord │  │ YouTube │  │ Stripe  │  ...       │
│  └────┬────┘  └────┬────┘  └────┬────┘  └────┬────┘            │
│       │            │            │            │                   │
│       └────────────┴────────────┴────────────┘                   │
│                            │                                     │
│                    ┌───────▼───────┐                             │
│                    │ Webhook Core   │                             │
│                    │ - Verify       │                             │
│                    │ - Parse        │                             │
│                    │ - Enqueue      │                             │
│                    │ - Route        │                             │
│                    └───────┬───────┘                             │
└────────────────────────────────┼─────────────────────────────────┘
                                 │
                                 ↓
                    Agent Orchestrator
```

### Casos de Uso por Fonte

| Source | Eventos | Use Case | Skill |
|--------|---------|----------|-------|
| **GitHub** | issues, PR, comments | `/resolve-issue` | Resolução automática |
| **Discord** | messages, commands | `/respond-discord` | Chatbot assistente |
| **YouTube** | new video, comments | `/summarize-video` | Sumarização |
| **Stripe** | payment, subscription | `/update-subscription` | Gestão de pagamentos |
| **Slack** | commands, events | `/slack-command` | Comandos de trabalho |
| **Notion** | database updates | `/sync-notion` | Sincronização |

---

## 4. Opções de Evolução para Skybridge

### Opção A: Webhook Handler (Minimal) ⚡
```python
# Adicionar ao registry existente
@webhook(
    source="github",
    events=["issues", "issue_comment", "pull_request"]
)
def github_webhook_handler(payload: dict):
    # Criar worktree → spawn subagente → PR
    pass

@webhook(
    source="discord",
    events=["message", "interaction"]
)
def discord_webhook_handler(payload: dict):
    # Responder mensagem → spawn subagente
    pass
```

**Complexidade**: Baixa | **Tempo**: 1-2 dias | **Mudanças**: Mínimas

### Opção B: Context Webhooks + Background Jobs (Recomendado) 🎯
```python
# Novo bounded context multi-source
src/skybridge/core/contexts/webhooks/
├── domain/
│   ├── WebhookEvent.py          # Entidade genérica
│   ├── WebhookSource.py         # Enum: GITHUB, DISCORD, YOUTUBE, STRIPE
│   └── WebhookSignature.py      # Security abstrata
├── application/
│   ├── handlers/
│   │   ├── github_handler.py    # Issues, PRs, comments
│   │   ├── discord_handler.py   # Messages, commands
│   │   ├── youtube_handler.py   # New video, comments
│   │   └── stripe_handler.py    # Payment events
│   ├── dispatcher.py            # Route para handler correto
│   └── agent_orchestrator.py    # Spawn subagentes
└── infrastructure/
    ├── routes.py                # /webhooks/{source}
    ├── job_queue.py
    └── processors/
        ├── github_processor.py
        ├── discord_processor.py
        └── youtube_processor.py
```

**Complexidade**: Média | **Tempo**: 3-5 dias | **Mudanças**: Arquitetural

### Opção C: Event-Driven Architecture (Robusto) 🚀
```python
# Event-driven com Redis/RabbitMQ
Webhook (any source) → Event → Queue → Workers → Worktree → Agent → Action
```

**Complexidade**: Alta | **Tempo**: 1-2 semanas | **Mudanças**: Grande

---

## 5. Plano Completo de Implementação

### FASE 1: Fundação Multi-Source (Dia 1-2)
```
src/skybridge/core/contexts/webhooks/
├── __init__.py
├── domain/
│   ├── WebhookEvent.py          # Entity genérica
│   ├── WebhookSource.py         # Enum: GITHUB, DISCORD, YOUTUBE, STRIPE
│   └── WebhookSignature.py      # Security abstrata
├── application/
│   ├── handlers/
│   │   ├── github_handler.py    # Use cases GitHub
│   │   └── base_handler.py      # Handler base
│   ├── dispatcher.py            # Route para handler correto
│   └── agent_orchestrator.py    # Spawn subagentes
└── infrastructure/
    └── routes.py                # /webhooks/{source}
```

**Tarefas**:
- [ ] Criar módulo `webhooks` context multi-source
- [ ] Implementar `POST /webhooks/{source}` com signature verification genérica
- [ ] Criar dispatcher baseado em `WebhookSource`
- [ ] Integração com Task tool (spawn subagente)

### FASE 2: Integração Agentes (Dia 3-4)
```
src/skybridge/core/contexts/agents/
├── __init__.py
├── domain/
│   └── AgentWorktree.py     # Gerencia worktrees
├── application/
│   ├── orchestrator.py      # Fluxo genérico: event → worktree → action
│   └── pr_creator.py        # Cria PRs (GitHub-specific)
└── infrastructure/
    └── git_operations.py    # git worktree, branch, push
```

**Tarefas**:
- [ ] Agent orchestrator genérico com Task tool
- [ ] Worktree lifecycle (create → work → cleanup)
- [ ] Worktree validation com GitExtractor (snapshot-based)
- [ ] Action handlers (resolve, respond, summarize, etc)
- [ ] PR creation automation (GitHub-specific)

**Worktree Validation** (usando snapshot existente):
- [ ] `GitExtractor`: Detecta staged/unstaged/untracked files
- [ ] `WorktreeValidator`: Snapshot inicial + validação pré-cleanup
- [ ] `safe_worktree_cleanup()`: Dry-run + confirmação antes de remover

### FASE 3: Background Processing (Dia 5-7)
```
src/skybridge/platform/background/
├── __init__.py
├── job_queue.py             # Queue system
├── workers.py               # Background workers
└── scheduler.py             # Optional: cron jobs
```

**Tarefas**:
- [ ] Implementar fila de jobs (Redis/memory)
- [ ] Workers async para webhook processing
- [ ] Retry mechanisms
- [ ] Dead letter queue

### FASE 4: Integrações Externas (Dia 8-10)
```
src/skybridge/infrastructure/external/
├── __init__.py
├── github/
│   ├── client.py              # GitHub API wrapper
│   └── webhook_manager.py     # Configurar webhooks
├── discord/
│   ├── client.py              # Discord API wrapper
│   └── webhook_manager.py     # Configurar webhooks
├── youtube/
│   ├── client.py              # YouTube API wrapper
│   └── pubsub_handler.py      # PubSubHubbub
└── stripe/
    ├── client.py              # Stripe API wrapper
    └── webhook_handler.py     # Webhook endpoints
```

**Tarefas**:
- [ ] GitHub API client (pygithub ou gh)
- [ ] Discord API client (discord.py)
- [ ] YouTube API client (google-api-python-client)
- [ ] Stripe API client (stripe)
- [ ] Auto-label issues (GitHub)
- [ ] Auto-respond commands (Discord)

### FASE 5: Skills Multi-Source (Dia 11-12)
```
.claude/skills/
├── resolve-issue.md          # GitHub issue → worktree → PR
├── respond-discord.md        # Discord message → response
├── summarize-video.md        # YouTube new video → summary
└── update-subscription.md    # Stripe payment → update
```

**Uso**:
```bash
# GitHub
claude
> /resolve-issue #225

# Discord
> /respond-discord "Summarize this thread"

# YouTube
> /summarize-video https://youtube.com/watch?v=xxx

# Stripe
> /update-subscription sub_123456
```

**Fluxo Genérico**:
1. Recebe evento (source-specific)
2. Cria worktree `skybridge-{source}-{id}`
3. Spawn subagente no worktree
4. Executa ação específica
5. Cleanup worktree
```
.claude/skills/resolve-issue.md
```

**Uso**:
```bash
claude
> /resolve-issue #225
```

**Fluxo**:
1. Lê issue #225
2. Cria worktree `skybridge-fix-225`
3. Spawn subagente no worktree
4. Implementa solução
5. Commit + Push + PR
6. Cleanup worktree

### FASE 6: Monitoramento & Observabilidade (Dia 13-14)
```
src/skybridge/platform/observability/
├── webhook_metrics.py       # Prometheus metrics
├── agent_tracer.py          # OpenTelemetry
└── dashboards.py            # Grafana dashboards
```

**Tarefas**:
- [ ] Métricas de webhook (received, processed, failed)
- [ ] Tracing de agentes (spawn → work → PR)
- [ ] Alerts para failures
- [ ] Dashboard de operações

---

## 6. Roadmap Resumido

| Fase | Dias | Entrega | Complexidade |
|------|------|---------|--------------|
| **1** | 1-2 | Webhook core multi-source | ⚡ Baixa |
| **2** | 3-4 | Agent orchestrator genérico | 🟡 Média |
| **3** | 5-7 | Background jobs + queue | 🟡 Média |
| **4** | 8-10 | Integrações externas (GitHub, Discord, etc) | 🟡 Média |
| **5** | 11-12 | Skills multi-source | ⚡ Baixa |
| **6** | 13-14 | Monitoring + dashboards | 🟡 Média |

**Total**: ~2 semanas para MVP completo multi-source

---

## 7. Arquitetura Multi-Source Proposta

```
┌─────────────────────────────────────────────────────────────────────────────────────┐
│                           Serviços Externos (Multi-Source)                        │
│                                                                                     │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐             │
│  │  GitHub  │  │ Discord  │  │ YouTube  │  │  Stripe  │  │  Slack   │  ...       │
│  └────┬─────┘  └────┬─────┘  └────┬─────┘  └────┬─────┘  └────┬─────┘             │
│       │             │             │             │             │                    │
│       │ Issue #225  │ Message     │ New video   │ Payment     │ Command            │
│       └─────────────┴─────────────┴─────────────┴─────────────┴──────────┐         │
│                                                                   │ POST    │         │
│                                                         /webhooks/{source}  │         │
│                                                                   ↓         │         │
│  ┌────────────────────────────────────────────────────────────────────────┐  │         │
│  │                    Skybridge API (FastAPI)                            │  │         │
│  │                                                                        │  │         │
│  │  POST /webhooks/{source}                                              │◄─┘         │
│  │  ↓                                                                     │            │
│  │  1. Identify source (github, discord, etc)                             │            │
│  │  2. Verify signature (source-specific)                                │            │
│  │  3. Parse event (source-specific parser)                              │            │
│  │  4. Route to handler (dispatcher)                                     │            │
│  │  5. Enqueue job                                                       │            │
│  └────────────────────────────────────────────────────────────────────────┘            │
│                                                                   │                    │
│                                                                   ↓                    │
│  ┌────────────────────────────────────────────────────────────────────────┐            │
│  │                    Background Worker (Async)                         │            │
│  │  ↓                                                                    │            │
│  │  1. Dequeue job                                                       │            │
│  │  2. Determine action type (resolve, respond, summarize, etc)          │            │
│  │  3. Create worktree: skybridge-{source}-{id}                         │            │
│  │  4. Task tool → Subagente                                             │            │
│  └────────────────────────────────────────────────────────────────────────┘            │
│                                                                   │                    │
│                                                                   ↓                    │
│  ┌────────────────────────────────────────────────────────────────────────┐            │
│  │                 Subagente (Worktree Isolado)                         │            │
│  │  ↓                                                                    │            │
│  │  GitHub:     Ler issue → Analisar → Implementar → commit → PR         │            │
│  │  Discord:    Ler message → Contextualizar → Responder                 │            │
│  │  YouTube:    Baixar video → Transcrever → Sumarizar → Post            │            │
│  │  Stripe:    Ver payment → Atualizar subscription → Notificar          │            │
│  │  Slack:      Ler command → Executar → Responder                       │            │
│  │  ↓                                                                    │            │
│  │  Exit (worktree cleanup)                                              │            │
│  └────────────────────────────────────────────────────────────────────────┘            │
│                                                                   │                    │
│                                                                   ↓                    │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐             │
│  │   PR     │  │ Response │  │ Summary  │  │ Update   │  │  Reply   │             │
│  │ criada   │  │ Discord  │  │ postada  │  │ database │  │  Slack   │             │
│  └──────────┘  └──────────┘  └──────────┘  └──────────┘  └──────────┘             │
│                                                                                     │
└─────────────────────────────────────────────────────────────────────────────────────┘
```

---

## 8. Níveis de Automação

| Nível | Descrição | Exemplo | Risco |
|-------|-----------|---------|-------|
| **Manual** | Skill `/resolve-issue` | Você chama, agente executa | ⚡ Baixo |
| **Semi-auto** | Webhook + Aprovação | GitHub triggera, você aprova | 🟡 Médio |
| **Full-auto** | Webhook → Agent → PR | Totalmente autônomo | 🔴 Alto |

### Recomendação: Roadmap de Adoção

1. **Fase 5 primeiro** (Manual) - Validar fluxo
2. **Fase 1-2** depois (Semi-auto) - Webhook + aprovação
3. **Fase 3-6** por último (Full-auto) - Quando confiável

---

## 9. Exemplo de Uso Multi-Source

```bash
# ========== GitHub ==========
# Manual (Fase 5)
claude
> /resolve-issue #225

# Semi-auto (Fase 1-2)
# GitHub issue aberta → Notificação → Você aprova → Agente executa

# Full-auto (Fase 3-6)
# GitHub issue aberta → Agente executa → PR criada → Notificação

# ========== Discord ==========
# Manual
claude
> /respond-discord "Summarize last 50 messages"

# Semi-auto
# Discord message → Notificação → Você aprova → Agente responde

# Full-auto
# Discord command → Agente responde automaticamente

# ========== YouTube ==========
# Manual
claude
> /summarize-video https://youtube.com/watch?v=xxx

# Semi-auto
# Novo video → Notificação → Você aprova → Agente sumariza

# Full-auto
# Novo video → Agente sumariza → Posta comentário

# ========== Stripe ==========
# Manual
claude
> /update-subscription sub_123456

# Semi-auto
# Payment → Notificação → Você aprova → Agente atualiza

# Full-auto
# Payment → Agente atualiza database → Envia email
```

---

## 10. Worktree Validation com Snapshot 🔍

### Recurso Existente: Skybridge Snapshot System

A Skybridge já possui um sistema de snapshots robusto em `src/skybridge/platform/observability/snapshot/`:

```
snapshot/
├── capture.py              # Core capture logic
├── diff.py                 # Comparison between snapshots
├── models.py               # Pydantic models
├── registry.py             # Extractor registry
└── extractors/
    ├── fileops_extractor.py  # File system snapshots (JÁ CAPTURA GIT HASH/BRANCH)
    ├── health_extractor.py   # System health
    ├── tasks_extractor.py    # Task state
    └── git_extractor.py      # ✨ NOVO: Git worktree validation
```

### Como Funciona a Validação

```
┌─────────────────────────────────────────────────────────────────┐
│  Fluxo: Webhook → Worktree → Agent → Validation → Cleanup      │
│                                                                   │
│  1. git worktree add ../skybridge-fix-225                        │
│     ↓                                                             │
│  2. GitExtractor.capture()  ← Snapshot inicial                   │
│     - Captura: branch, hash, staged, unstaged, untracked         │
│     - Salva estado para comparação posterior                     │
│     ↓                                                             │
│  3. [Agente trabalha: código, test, commit, push, PR]            │
│     ↓                                                             │
│  4. GitExtractor.validate_worktree() ← Valida ANTES de remover   │
│     - Verifica: staged files? unstaged? conflicts?               │
│     - Retorna: can_remove + mensagem detalhada                   │
│     ↓                                                             │
│  ┌─────────────────┐                                             │
│  │ Pode remover?   │                                             │
│  └────┬───────┬────┘                                             │
│       SIM       NÃO                                                 │
│       │          │                                                │
│       ↓          ↓                                                │
│  git worktree   Alerta: "Worktree tem X arquivos                  │
│     remove      modificados não commitados"                       │
│                   + mantém worktree para investigação             │
│                                                                   │
└───────────────────────────────────────────────────────────────────┘
```

### Componentes Criados

1. **GitExtractor** (`git_extractor.py`)
   - Captura status completo do git (staged, unstaged, untracked, conflicts)
   - Método `validate_worktree()`: retorna `can_remove + mensagem`
   - Método `can_safely_remove()`: lógica de validação

2. **WorktreeValidator** (`worktree_validator.py`)
   - Snapshot inicial antes do trabalho
   - Validação pré-cleanup com dry-run
   - Modo estrito vs relaxado (untracked OK)

3. **Exemplo de Uso** (`worktree-validation-example.md`)
   - Fluxo completo de validação
   - Integração com agents
   - Exemplos de saída JSON

### Vantagens da Abordagem

| Benefício | Descrição |
|-----------|-----------|
| **Segurança** | Nunca remove worktree sujo acidentalmente |
| **Observabilidade** | Snapshot antes/depois para debugging |
| **Recuperação** | Se falhar, worktree ainda existe para investigação |
| **Flexibilidade** | Modo estrito vs relaxado conforme contexto |
| **Extensibilidade** | Usa pattern extractor já existente |

---

## 11. Riscos e Mitigações

| Risco | Impacto | Mitigação |
|-------|---------|-----------|
| Agente alucina | Alto | Human-in-the-loop (Semi-auto primeiro) |
| Worktree sujo não removido | **Baixo** | **GitExtractor + validação pré-cleanup** |
| Worktree removido acidentalmente | Médio | **Dry-run obrigatório antes de remover** |
| Rate limit (qualquer API) | Baixo | Exponential backoff + cache |
| Segurança webhook | Alto | Signature verification por source |
| Conflito de branches | Médio | Worktree isolado + merge strategy |
| Spam de webhooks | Médio | Rate limiting por source |
| Falha de API externa | Médio | Retry + dead letter queue |

---

## 12. Próximos Passos

---

## Sources

### Tools & Libraries
- [fastgithub - PyPI](https://pypi.org/project/fastgithub/)
- [fastapi-events - GitHub](https://github.com/melvinkcx/fastapi-events)
- [Neon Webhooks Guide](https://neon.com/guides/fastapi-webhooks)
- [Event-Driven FastAPI + Redis](https://medium.com/@velocitytech/build-an-event-driven-architecture-with-fastapi-and-redis-pub-sub-deploy-it-in-kubernetes-54603ac35335)
- [FastAPI Official: OpenAPI Webhooks](https://fastapi.tiangolo.com/advanced/openapi-webhooks/)
- [Handling GitHub Webhooks - LSST](https://safir.lsst.io/user-guide/github-apps/handling-webhooks.html)

### Best Practices
- [GitHub Webhooks Best Practices](https://docs.github.com/en/webhooks/using-webhooks/best-practices-for-using-webhooks)
- [Kubernetes on Auto-Closing Issues](https://github.com/kubernetes/kubernetes/issues/103151)
- [VSCode: Bot should not close issues](https://github.com/microsoft/vscode/issues/261976)
- [Auto-closing issues discussion - Reddit](https://www.reddit.com/r/opensource/comments/14xx8pw/is_it_normal_practice_in_github_for_an_issue_to_be_closed/)

### Community Projects
- [AI-Agent-Platforms-Automation-Tools](https://github.com/rembertdesigns/AI-Agent-Platforms-Automation-Tools)
- [DreamOps: AI Agent for Oncall](https://github.com/SkySingh04/DreamOps)
- [webhook_receive - GitHub](https://github.com/falkben/webhook_receive)

---

## 12. Próximos Passos

1. **✅ Estudo completo** (este documento)
2. **🔲 PRD** - Validar ideia com stakeholders
3. **🔲 Proof of Concept** - Fase 5 (Skill `/resolve-issue`)
4. **🔲 Testes reais** - Validar fluxo com issues reais
5. **🔲 ADR** - Documentar decisões arquiteturais após validação
6. **🔲 Implementação** - Fases 1-6 baseado em aprendizados

---

> "Primeiro valide, depois documente decisões, por último implemente" – made by Sky 🔄

---

> "A melhor arquitetura é aquela que evolui com necessidades reais, não com hipóteses" – made by Sky 🏗️

---

**Documento versão:** 2.0
**Última atualização:** 2026-01-07
**Mudanças:** Adicionada visão multi-source para bounded context webhooks