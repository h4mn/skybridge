# Relatório: Bounded Context para Agentes AI

**Data:** 2026-01-10
**Autor:** Sky
**Status:** Análise Concluída

---

## 1. Pergunta Fundamental

**Agentes AI precisam de um novo bounded context ou se encaixam no contexto "webhooks"?**

## 2. Resposta Executiva

**Agentes devem permanecer no contexto `webhooks/`.**

Separar seria uma violação dos princípios do DDD, criando fronteiras artificiais e acoplamento desnecessário.

## 3. Análise DDD

### 3.1) Linguagem Ubíqua Compartilhada

O contexto webhooks e agentes compartilham a mesma linguagem:

```
WebhookEvent → WebhookJob → Agent execution → Worktree validation
```

| Termo | Uso em Webhooks | Uso em Agentes |
|-------|-----------------|-----------------|
| `job_id` | Identifica evento webhook | Identifica execução do agente |
| `worktree_path` | Onde webhook cria worktree | Onde agente opera |
| `branch_name` | Branch do worktree criado | Branch onde agente commita |
| `issue_number` | Issue que triggerou webhook | Issue que agente resolve |

### 3.2) Coesão: Alta

**Agentes e webhooks são dois lados da mesma moeda:**

- **Webhooks são o gatilho**: Eventos externos que iniciam o processo
- **Agentes são a execução**: Lógica que processa esses eventos

**Separar seria como separar "receber pedidos" de "preparar pizza" na pizzaria.**

### 3.3) Acoplamento: Baixo

Não existe dependência externa que justifique separação:

- Agentes não são usados fora do contexto de webhooks
- Webhooks não têm propósito sem agentes executarem tarefas
- Não há outros "consumidores" de agentes no sistema

### 3.4) Autonomia: Preservada

O contexto webhooks é **totalmente autônomo**:
- Recebe eventos (GitHub, Discord, etc)
- Cria worktrees isolados
- Spawn agentes
- Valida worktrees
- Limpa recursos

### 3.5) Fronteiras Naturais

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    Bounded Context: webhooks                              │
│                                                                              │
│  "Receber eventos externos e executar tarefas autônomas em worktrees"     │
│                                                                              │
│  ┌────────────────┐  ┌────────────────┐  ┌────────────────┐              │
│  │  Webhook       │  │  Job           │  │  Agent         │              │
│  │  Receiver      │→ │  Orchestrator   │→ │  Spawner       │              │
│  │                │  │                │  │                │              │
│  │  - Verify      │  │  - Queue       │  │  - Spawn CLI   │              │
│  │  - Parse       │  │  - Worktree    │  │  - Context     │              │
│  │  - Route       │  │  - Lifecycle   │  │  - Monitor     │              │
│  └────────────────┘  └────────────────┘  └────────────────┘              │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

## 4. Quando Separaria? (Sinais para Evolução Futura)

Separar para um bounded context `agents/` seria justificado se:

| Sinal | Descrição | Status Atual |
|-------|-----------|--------------|
| Múltiplos gatilhos | Agentes usados por API, CLI, scheduler | ❌ Não |
| Complexidade | Lógica de agentes se torna muito complexa | ❌ Não |
| Reutilização | Outros contextos usam agentes | ❌ Não |
| Tipos diversos | Múltiplos tipos de agentes com comportamentos distintos | ❌ Não |

## 5. Estrutura Recomendada

```python
src/skybridge/core/contexts/webhooks/
├── domain/
│   ├── webhook_event.py          # WebhookEvent, WebhookJob, JobStatus
│   └── agent_execution.py        # AgentExecution (entidade futura)
├── application/
│   ├── handlers.py               # Sky-RPC: webhooks.github.receive
│   ├── webhook_processor.py      # Processa webhook → cria job
│   ├── job_orchestrator.py       # Orquestra execução → spawn agent
│   ├── worktree_manager.py       # Gerencia worktrees git
│   ├── agent_spawner.py          # Spawna subagentes (RF004)
│   └── agent_executor.py         # Executa e monitora agentes
├── ports/
│   ├── job_queue_port.py         # Interface JobQueuePort
│   ├── webhook_signature_port.py # Interface WebhookSignaturePort
│   └── agent_execution_port.py   # Interface AgentExecutionPort
└── adapters/
    ├── in_memory_queue.py        # Fila em memória (MVP)
    ├── github_signature_verifier.py
    └── claude_code_adapter.py    # Adaptação Claude Code CLI
```

## 6. Conclusão

**Manter agentes no contexto `webhooks/` é a decisão arquitetural correta** para o estágio atual do projeto.

Benefícios:
- ✅ Simplicidade preservada
- ✅ Coesão natural mantida
- ✅ Comunicação eficiente (mesma linguagem)
- ✅ Menos coordenação entre times

> "A divisão correta não é entre tecnologias, mas entre responsabilidades de negócio." – made by Sky 🏗️

---

## Fontes

- [Análise de código do projeto](../core/contexts/webhooks/)
- [Domain-Driven Design](https://martinfowler.com/bliki/BoundedContext.html)
- [SPEC008 — AI Agent Interface](../spec/SPEC008-AI-Agent-Interface.md)
