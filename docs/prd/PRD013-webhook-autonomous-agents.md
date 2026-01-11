# PRD013: Webhook-Driven Autonomous Agents para Skybridge

**Status:** ✅ Implementado (Phase 1 + SPEC008)
**Data:** 2026-01-10
**Autor:** Sky
**Versão:** 1.3

---

## Status de Implementação

### Phase 1: MVP GitHub + SPEC008 (Semana 2-3) - ✅ COMPLETO

- [x] `POST /webhooks/github` com signature verification
- [x] Background worker integrado ao FastAPI (lifespan)
- [x] GitExtractor para validação
- [x] Skill `/resolve-issue` documentado
- [x] Bounded context `webhooks` criado
- [x] Domain entities (WebhookEvent, WebhookJob, JobStatus)
- [x] Ports (JobQueuePort, WebhookSignaturePort)
- [x] Adapters (InMemoryJobQueue, GitHubSignatureVerifier)
- [x] Application services (WebhookProcessor, JobOrchestrator, WorktreeManager)
- [x] Signature verification via verify_webhook_signature() (chamado na rota, não middleware tradicional)
- [x] WebhookConfig no sistema de configuração
- [x] Sky-RPC handler registrado
- [x] Worker iniciado automaticamente com a API
- [x] Testes unitários (50 testes cobrindo domain, adapters, application e integration)

**Componentes Criados:**
```
src/skybridge/
├─ core/contexts/webhooks/
│  ├─ domain/webhook_event.py          # WebhookEvent, WebhookJob, JobStatus
│  ├─ application/
│  │  ├─ handlers.py                   # Sky-RPC: webhooks.github.receive
│  │  ├─ webhook_processor.py          # Processa webhook → cria job
│  │  ├─ job_orchestrator.py           # Executa job → cria agente
│  │  ├─ worktree_manager.py           # Gerencia worktrees git
│  │  └─ agent_spawner.py              # Cria subagentes Claude Code (RF004)
│  └─ ports/
│     ├─ job_queue_port.py             # Interface JobQueuePort
│     └─ webhook_signature_port.py     # Interface WebhookSignaturePort
├─ infra/contexts/webhooks/adapters/
│  ├─ in_memory_queue.py               # Fila em memória (MVP)
│  └─ github_signature_verifier.py     # HMAC SHA-256
├─ platform/delivery/
│  ├─ middleware/__init__.py           # verify_webhook_signature()
│  └─ routes.py                        # POST /webhooks/{source}
├─ platform/background/
│  └─ webhook_worker.py                # Worker assíncrono
├─ platform/config/config.py           # WebhookConfig adicionado
└─ platform/bootstrap/app.py           # lifespan com worker startup

tests/core/contexts/webhooks/          # Testes unitários e integração
├─ test_domain.py                      # 15 testes de domínio
├─ test_adapters.py                    # 14 testes de adapters
├─ test_application.py                 # 10 testes de application
└─ test_integration.py                 # 11 testes de integração

.agents/skills/resolve-issue/SKILL.md  # Skill documentado
```

### Agent Infrastructure (SPEC008)
- [x] Agent Facade Pattern implementado (interface abstrata + adapters)
- [x] Domain entities para agentes (AgentState, AgentExecution, AgentResult, ThinkingStep)
- [x] Claude Code Adapter com stdin/stdout streaming
- [x] XML Streaming Protocol para comunicação bidirecional agente ↔ Skybridge
- [x] Agent state management (CREATED, RUNNING, COMPLETED, TIMED_OUT, FAILED)
- [x] Skill-based timeout configuration
- [x] Testes TDD (38 testes cobrindo toda a infraestrutura de agentes)

**Componentes da SPEC008:**
```
src/skybridge/core/contexts/webhooks/infrastructure/agents/
├── __init__.py                    # Exports públicos (AgentFacade, AgentState, etc)
├── domain.py                      # AgentState, AgentExecution, AgentResult, ThinkingStep
├── agent_facade.py                # Interface abstrata AgentFacade
├── claude_agent.py                # ClaudeCodeAdapter (implementação Claude Code CLI)
└── protocol.py                    # XMLStreamingProtocol, SkybridgeCommand

tests/core/contexts/webhooks/
└── test_agent_infrastructure.py   # 38 testes TDD (todos passando ✅)
```

**Estrutura do AgentResult (conforme SPEC008 seção 9.2):**
```json
{
  "success": true,
  "changes_made": true,
  "files_created": ["hello_world.py"],
  "files_modified": ["__init__.py"],
  "files_deleted": [],
  "commit_hash": "abc123",
  "pr_url": "https://github.com/h4mn/skybridge/pull/123",
  "message": "Issue resolved",
  "issue_title": "Fix version alignment",
  "output_message": "Aligned versions to 0.2.5",
  "thinkings": [
    {"step": 1, "thought": "Analyzing issue...", "timestamp": "...", "duration_ms": 1500},
    {"step": 2, "thought": "Reading __init__.py...", "timestamp": "...", "duration_ms": 300}
  ]
}
```

**Protocolo XML (conforme SPEC008 seção 6):**
```xml
<skybridge_command>
  <command>log</command>
  <parametro name="mensagem">Analisando issue #225...</parametro>
  <parametro name="nivel">info</parametro>
</skybridge_command>
```

**Timeouts por Skill (conforme SPEC008 seção 8.2):**
| Skill | Timeout | Justificativa |
|-------|---------|---------------|
| hello-world | 60s | Simples, deve ser rápido |
| bug-simple | 300s (5min) | Bug fix simples |
| bug-complex | 600s (10min) | Bug fix complexo |
| refactor | 900s (15min) | Refatoração |
| resolve-issue | 600s (10min) | Default para issues |

### Notas de Implementação

#### AgentSpawner
O `agent_spawner.py` implementa RF004 (criar subagentes) com uma abordagem prática:

- **Análise de issue:** Detecta automaticamente o tipo de tarefa (hello world, bug fix, genérico)
- **Execução simulada:** Cria arquivos/diretórios conforme o tipo detectado
- **Estrutura preparada:** Já está pronto para integração com Claude Code CLI

Atualmente, o spawner cria:
- **Hello World:** Script Python funcional `hello_world.py`
- **Bug fix/Genérico:** Simulação (placeholder para futura integração CLI)

#### Signature Verification (não é middleware tradicional)
O PRD original mencionava "HMAC middleware", mas a implementação é mais robusta:

```python
# A verificação é feita DENTRO da rota, não via middleware
@router.post("/webhooks/{source}")
async def receive_webhook(source: str, http_request: Request):
    # 1. Extrai headers PRIMEIRO (antes de consumir body)
    signature = http_request.headers.get("x-hub-signature-256", "")

    # 2. Lê payload body (só pode ser lido uma vez)
    body_bytes = await http_request.body()

    # 3. Verifica assinatura
    error_response = await verify_webhook_signature(body_bytes, signature, source)
    if error_response:
        return error_response
    # ...
```

**Por que não middleware tradicional?**
- FastAPI só permite ler `request.body()` uma vez
- Middleware consumiria o body antes da rota
- Implementação inline evita problemas com streaming

#### Endpoint Genérico Multi-Source
O endpoint `POST /webhooks/{source}` é mais genérico que o documentado:

**Documentado:** `POST /webhooks/github` (específico)
**Implementado:** `POST /webhooks/{source}` (genérico)

Isso facilita adicionar novas fontes (Discord, YouTube, Stripe) sem criar novos endpoints.

### Configuração

```bash
# .env
WEBHOOK_GITHUB_SECRET=seu_segredo_aqui
WEBHOOK_DISCORD_SECRET=seu_segredo_aqui  # Preparado para Phase 2
WEBHOOK_YOUTUBE_SECRET=seu_segredo_aqui  # Preparado para Phase 2
WEBHOOK_STRIPE_SECRET=seu_segredo_aqui   # Preparado para Phase 2
WEBHOOK_ENABLED_SOURCES=github,discord,youtube,stripe
```

**NOTA:** O diretório de worktrees é configurável via `config.py`:

```python
# config.py
from pathlib import Path

# Diretório base para worktrees (configurável por ambiente)
WORKTREES_BASE_PATH = Path("B:/_repositorios/skybridge-worktrees")

# Garante que o diretório existe
WORKTREES_BASE_PATH.mkdir(parents=True, exist_ok=True)
```

### Próximos Passos

1. **Setup webhook no GitHub:**
   - Repository → Settings → Webhooks → Add webhook
   - URL: `https://seu-dominio.com/webhooks/github`
   - Content type: `application/json`
   - Secret: configure e copie para `.env`

2. **Testes unitários** (pendentes)

3. **Phase 2:** Adicionar Discord e YouTube

---

---

## 1. Executivo Resumido

### Problema
Desenvolvedores perdem tempo com tarefas repetitivas de manutenção: triagem de issues, respostas em communities, sumarização de conteúdo, atualização de subscriptions, etc.

### Solução
Sistema de agentes autônomos acionados por webhooks de múltiplas fontes (GitHub, Discord, YouTube, Stripe, etc) que executam workflows em worktrees isolados com validação de estado.

### Proposta de Valor
- **Redução de 80%** em tarefas repetitivas de manutenção
- **Resposta em minutos** ao invés de horas/dias
- **Zero impacto** no repositório principal (worktrees isolados)
- **Segurança máxima** com validação antes de qualquer alteração

### Success Metrics
- **Mês 1:** 50 issues resolvidas automaticamente (GitHub)
- **Mês 1:** 90% de worktrees limpos sem intervenção manual
- **Mês 3:** Expansão para 3 fontes (Discord, YouTube, Stripe)
- **Mês 6:** <5min tempo médio de resposta (issue → PR)

---

## 2. Contexto e Problema

### Dor Atual

```
┌─────────────────────────────────────────────────────────────────┐
│  Fluxo Manual Atual (Lento e Repetitivo)                        │
│                                                                   │
│  1. GitHub issue aberta                                         │
│  2. Desenvolvedor notificado (email/slack)                      │
│  3. Desenvolvedor lê issue (context switch)                     │
│  4. Desenvolvedor cria branch                                   │
│  5. Desenvolvedor implementa solução                            │
│  6. Desenvolvedor testa                                         │
│  7. Desenvolvedor commita e pusha                               │
│  8. Desenvolvedor cria PR                                       │
│  9. Code review manual                                          │
│  10. Merge                                                      │
│                                                                   │
│  Tempo médio: 2-48 horas (dependendo da disponibilidade)        │
└───────────────────────────────────────────────────────────────────┘
```

### Problemas Específicos

| Problema | Frequência | Impacto |
|----------|-----------|---------|
| Issues simples (bugs triviais) | 10/dia | Alta |
| Perguntas repetitivas em Discord | 50/dia | Média |
| Vídeos novos para sumarizar | 5/semana | Baixa |
| Pagamentos para processar | 20/dia | Alta |
| **Total** | **~85 eventos/dia** | **Alta** |

### Persona Principal

**Nome:** DevOps Maintainer
**Meta:** Manter foco em features complexas, não tarefas repetitivas
**Frustrações:**
- "Perco 2h/dia com issues triviais"
- "Semana cheia, acabei não respondendo Discord"
- "Esqueci de processar pagamentos ontem"
- "Tenho medo de auto-merge dar problema"

---

## 3. Solução Proposta

### Visão Arquitetural

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           Serviços Externos (Multi-Source)                │
│                                                                             │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐                 │
│  │  GitHub  │  │ Discord  │  │ YouTube  │  │  Stripe  │  ...            │
│  └────┬─────┘  └────┬─────┘  └────┬─────┘  └────┬─────┘                 │
│       │             │             │             │                        │
│       │ Issue #225  │ Message     │ New video   │ Payment                │
│       └─────────────┴─────────────┴─────────────┴───────┐                 │
│                                                    │ POST                 │
│                                          /webhooks/{source}                 │
│                                                    │                      │
│                                                    ↓                      │
│  ┌──────────────────────────────────────────────────────────────────────┐ │
│  │                    Skybridge API (FastAPI)                          │ │
│  │                                                                     │ │
│  │  1. Identify source → 2. Verify signature → 3. Parse event       │ │
│  │  → 4. Route to handler → 5. Enqueue job                           │ │
│  └──────────────────────────────────────────────────────────────────────┘ │
│                                                    │                      │
│                                                    ↓                      │
│  ┌──────────────────────────────────────────────────────────────────────┐ │
│  │                    Background Worker (Async)                       │ │
│  │  ↓                                                                  │ │
│  │  1. Dequeue job → 2. Create worktree → 3. Task tool → Subagente  │ │
│  └──────────────────────────────────────────────────────────────────────┘ │
│                                                    │                      │
│                                                    ↓                      │
│  ┌──────────────────────────────────────────────────────────────────────┐ │
│  │                 Subagente (Worktree Isolado)                       │ │
│  │  ↓                                                                  │ │
│  │  GitHub: Issue → Analyze → Implement → Commit → PR                │ │
│  │  Discord: Message → Context → Respond                             │ │
│  │  YouTube: Video → Transcribe → Summarize → Post                   │ │
│  │  Stripe: Payment → Update subscription → Notify                   │ │
│  │  ↓                                                                  │ │
│  │  GitExtractor.validate() → can_remove? → Cleanup                  │ │
│  └──────────────────────────────────────────────────────────────────────┘ │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Fluxo Detalhado: GitHub Issue

```python
# 1. Webhook recebido
POST /webhooks/github
{
  "action": "opened",
  "issue": { "number": 225, "title": "Fix version alignment" }
}

# 2. Background worker processa
job = {
  "job_id": "github-issues.opened-abc12345",  # ID único
  "source": "github",
  "event_type": "issues.opened",
  "issue_number": 225,
}

# 3. Worktree criado (nome único com job_id suffix)
# Formato: {WORKTREES_BASE_PATH}/skybridge-{webhook_type}-{event_type}-{issue_id}-{short_id}
worktree_path = "B:\\_repositorios\\skybridge-worktrees\\skybridge-github-issues-225-abc123"
branch_name = "webhook/github/issue/225/abc123"

git worktree add B:\_repositorios\skybridge-worktrees\skybridge-github-issues-225-abc123 -b webhook/github/issue/225/abc123

# 4. GitExtractor captura snapshot inicial
initial_snapshot = git_extractor.capture(worktree_path)
# Salva: branch=webhook/github/issue/225/abc12345, hash=abc123, staged=[], unstaged=[]

# 5. Subagente trabalha
cd B:\_repositorios\skybridge-worktrees\skybridge-github-issues-225-abc123
[agente lê issue, implementa solução, testa]
git add .
git commit -m "fix: resolve issue #225"
git push

# 6. PR criada
gh pr create --title "Fix #225" --body "Resolves issue #225"

# 7. Validação PRÉ-cleanup
can_remove, message, status = git_extractor.validate_worktree(worktree_path)

if can_remove:
    # ✅ Worktree limpo, pode remover
    git worktree remove B:\_repositorios\skybridge-worktrees\skybridge-github-issues-225-abc123
else:
    # ⚠️ Worktree sujo, mantém para investigação
    notify(f"⚠️ {message}")

# 8. Fim
PR criada, worktree limpo, zero resíduo
```

---

## 4. Convenção de Nomes de Artefatos

### Job ID
- **Formato:** `{source}-{event_type}-{suffix}`
- **Exemplo:** `github-issues.opened-cf560ba0`
- **Unicidade:** Cada webhook recebido gera um job_id único

### Worktree (Diretório)
Conforme **SPEC008 seção 8.1.1**, o worktree path é configurável via `config.py`:

- **Formato:** `{WORKTREES_BASE_PATH}/skybridge-{webhook_type}-{event_type}-{issue_id}-{short_id}`
- **Exemplo:** `B:\_repositorios\skybridge-worktrees\skybridge-github-issues-225-abc123`
- **Configuração:** `WORKTREES_BASE_PATH` definido em `config.py` (padrão: `B:/_repositorios/skybridge-worktrees`)
- **Sufixo:** Primeiros 6 caracteres do job_id garantem unicidade

### Branch Git
- **Formato:** `webhook/{source}/issue/{issue_number}/{short_id}`
- **Exemplo:** `webhook/github/issue/225/abc123`
- **Namespace:** Branches de webhook ficam sob `webhook/` para organização

### Propósito do Sufixo Único
O sufixo do job_id nos nomes de worktree e branch garante:

1. **Idempotência:** Webhooks duplicados não sobrescrevem worktrees anteriores
2. **Rastreamento:** Tentativas anteriores ficam preservadas para investigação
3. **Retry:** Retries do worker criam novos worktrees sem conflito
4. **Reabertura:** Issues reabertas geram novos worktrees isolados
5. **Observabilidade:** Worktree nome contém referência direta ao job_id nos logs

### Exemplo de Cenários

```
Issue #225 aberta → job_id=abc123def → worktree=skybridge-github-issues-225-abc123
Issue #225 reaberta → job_id=def456ghi → worktree=skybridge-github-issues-225-def456
Webhook duplicado → job_id=abc123def → branch já existe, não cria novo worktree
Retry do worker → job_id=abc123def → mesmo worktree é reutilizado
```

---

## 5. Requisitos Funcionais

### RF001: Receber Webhooks de Múltiplas Fontes
- **Descrição:** Sistema deve aceitar webhooks de GitHub, Discord, YouTube, Stripe, Slack
- **Entrada:** `POST /webhooks/{source}` com payload específico
- **Saída:** Job enfileirado para processamento
- **Prioridade:** Alta

### RF002: Processar Webhooks de Forma Assíncrona
- **Descrição:** Worker background deve processar webhooks sem bloquear resposta
- **Entrada:** Job da fila
- **Saída:** Worktree criado + subagente criado
- **Prioridade:** Alta

### RF003: Criar Worktrees Isolados por Evento
- **Descrição:** Cada evento deve ter seu próprio worktree isolado
- **Formato:** `skybridge-{source}-{issue_number}-{job_suffix}`
- **Exemplo:** `skybridge-github-225-cf560ba0`
- **Unicidade:** Sufixo do job_id previne conflitos de issues repetidas
- **Prioridade:** Alta

### RF004: Criar Subagentes com Contexto Específico
- **Descrição:** System deve criar subagente Claude Code no worktree com contexto completo do evento
- **Entrada:** Worktree path + issue/event details
- **Saída:** Subagente executando ação específica com autonomia real
- **Prioridade:** Alta
- **Implementação:** Claude Code CLI via subprocess com flags específicas

#### Especificação Técnica (MVP)

**Comando CLI:**
```bash
claude --print \
  --cwd <worktree_path> \
  --system-prompt <rendered_from_json> \
  --output-format json \
  --permission-mode bypass \
  --timeout <skill_timeout> \
  <prompt_principal_via_stdin>
```

**Agent Facade Pattern (Arquitetura Multi-Agente):**

Conforme **SPEC008**, a arquitetura utiliza o padrão **Agent Facade** para abstrair diferentes tipos de agentes:

```
src/skybridge/core/contexts/webhooks/
└── infrastructure/
    └── agents/
        ├── __init__.py
        ├── agent_facade.py          # Facade único para múltiplos agentes
        ├── claude_agent.py          # Implementação Claude Code CLI
        ├── roo_agent.py             # [FUTURO] Implementação Roo Code
        └── copilot_agent.py         # [FUTURO] Implementação GitHub Copilot
```

**Responsabilidades do Facade:**
- Interface única para criar/gerenciar diferentes tipos de agentes
- Compartilhamento de system prompt (JSON como fonte da verdade)
- Tratamento unificado de protocolos de comunicação (XML streaming)
- Normalização de timeouts e estados de lifecycle
- Abstração das diferenças entre agentes Claude, Roo, Copilot

**Vantagens:**
- **Extensibilidade:** Adicionar novos agentes sem modificar código existente
- **Testabilidade:** Facilita mocks e testes unitários
- **Manutenibilidade:** Lógica específica de cada agente isolada

**System Prompt (Fonte da Verdade em JSON):**

Conforme **SPEC008**, o system prompt é gerenciado como **fonte da verdade em JSON**:

```
src/skybridge/platform/config/
├── agent_prompts.py         # Módulo de gerenciamento
└── system_prompt.json      # Fonte da verdade (OBRIGATÓRIO)
```

**Formato do system_prompt.json:**
```json
{
  "version": "1.0.0",
  "template": {
    "role": "You are an autonomous AI agent that executes development tasks through natural language inference.",
    "instructions": [
      "Work in an isolated Git worktree at {worktree_path}",
      "Communicate with Skybridge via XML commands: <skybridge_command>...</skybridge_command>",
      "NEVER use heuristics - always use inference to analyze and solve problems",
      "Maintain internal log at .sky/agent.log",
      "Return structured JSON output upon completion"
    ],
    "rules": [
      "DO NOT modify files outside the worktree",
      "DO NOT execute destructive actions without confirmation",
      "DO NOT use string matching or if/else heuristics for decisions",
      "ALWAYS read and analyze code before making changes"
    ]
  }
}
```

**Renderização do Template:**
```python
from skybridge.platform.config import load_system_prompt_config, render_system_prompt

# Carregar configuração (fonte da verdade)
config = load_system_prompt_config()  # Lê system_prompt.json

# Contexto do job
context = {
    "worktree_path": "B:\\_repositorios\\skybridge-worktrees\\skybridge-github-issues-225-abc123",
    "issue_number": 225,
    "issue_title": "Fix version alignment",
    "repo_name": "h4mn/skybridge",
    "branch_name": "webhook/github/issue/225/abc123",
    "skill": "resolve-issue"
}

# Renderizar template com variáveis injetadas
rendered = render_system_prompt(config, context)

# Resultado passado para o agente via --system-prompt
```

**Contexto passado ao subagente (JSON):**
```json
{
  "worktree_path": "B:\\_repositorios\\skybridge-worktrees\\skybridge-github-issues-225-abc123",
  "issue_number": 225,
  "issue_title": "Fix: alinhar versões da CLI e API",
  "repo_name": "h4mn/skybridge",
  "branch_name": "webhook/github/issue/225/abc123",
  "skill": "resolve-issue"
}
```

**Saída esperada do subagente (JSON final):**
```json
{
  "success": true,
  "changes_made": true,
  "files_created": ["file1.py", "file2.py"],
  "files_modified": ["file3.py"],
  "files_deleted": [],
  "commit_hash": "abc123",
  "pr_url": "https://github.com/h4mn/skybridge/pull/123",
  "message": "Issue resolved: fixed version alignment",
  "thinkings": [
    {"step": 1, "thought": "Analyzing issue #225...", "timestamp": "...", "duration_ms": 1500},
    {"step": 2, "thought": "Reading __init__.py...", "timestamp": "...", "duration_ms": 300}
  ]
}
```

**Protocolo de Comunicação Bidirecional (XML Streaming):**

Conforme **SPEC008**, o agente se comunica com Skybridge através de **stdout streaming** durante a execução:

**Durante execução (comandos XML em tempo real):**
```xml
<skybridge_command>
  <command>log</command>
  <parametro name="mensagem">Analisando issue #225...</parametro>
  <parametro name="nivel">info</parametro>
</skybridge_command>
```

**Ao completar (JSON final):**
O JSON acima é enviado quando o agente finaliza.

**Cuidados no Tratamento de XML:**
- Sanitizar valores de parâmetros (XML injection)
- Usar parser robusto (`lxml` com `recover=True`)
- Limitar tamanho máximo do XML (50.000 caracteres)
- Forçar encoding UTF-8

#### Timeout por Tipo de Tarefa

Conforme **SPEC008 seção 8.2**, o timeout é hierárquico e varia por tipo de tarefa:

**Timeout Global Padrão:** 600 segundos (10 minutos)

| Tarefa | Timeout Recomendado | Timeout Máximo | Justificativa |
|--------|---------------------|----------------|----------------|
| Hello World | 60s | 120s | Simples, deve ser rápido |
| Bug fix simples | 300s (5min) | 600s | Análise + implementação |
| Bug fix complexo | 600s (10min) | 900s (15min) | Pode demandar pesquisa |
| Refatoração | 900s (15min) | 1200s (20min) | Múltiplos arquivos, análise profunda |

**Precedência:**
1. `--timeout` (CLI explícito) > Timeout por skill > Global padrão (600s)
2. Timeout excedido → Estado `TIMED_OUT` (diferente de `FAILED`)
3. Thinkings preservados até o momento do timeout
4. Worktree mantido por 24h para debugging

#### Importante
- **Acesso ao worktree:** Subagentes devem ter acesso de leitura/escrita no worktree isolado
- **Permissões:** Usar `--permission-mode bypass` em worktrees de confiança
- **Non-interactive:** Flag `--print` é obrigatória para uso via subprocess

### RF005: Validar Worktree Antes de Cleanup
- **Descrição:** GitExtractor deve validar se worktree pode ser removido com segurança
- **Validação:** Staged files? Unstaged? Conflicts?
- **Saída:** `can_remove + mensagem detalhada`
- **Prioridade:** Alta

**Ciclo de Vida e Estados do Agente:**

Conforme **SPEC008 seção 12**, o agente passa pelos seguintes estados:

| Estado | Descrição | Transição |
|--------|-----------|-----------|
| `CREATED` | Subprocesso iniciado, stdin enviado, snapshot antes capturado | → RUNNING |
| `RUNNING` | Agente executando inferência, enviando comandos via stdout | → COMPLETED / TIMED_OUT / FAILED |
| `TIMED_OUT` | Tempo limite excedido, processo terminado via SIGKILL | Thinkings parciais preservados |
| `COMPLETED` | Agente finalizou, JSON recebido, snapshot depois capturado | → SUCCESS / FAILED |
| `FAILED` | Erro na execução (crash, permission denied, etc) | Stderr capturado, worktree mantido |

**Preservação de Estado em Falha:**
- Thinkings SEMPRE preservados, mesmo em timeout/falha
- Log interno `.sky/agent.log` com stack trace completo em caso de crash
- Worktree mantido por 24h para debugging
- JSON parcial retornado com `success: false` e campos disponíveis

#### Inferência vs Heurística (CRÍTICO)

Conforme **SPEC008 seção 3**, a distinção entre **inferência** e **heurística** é fundamental para o comportamento correto dos agentes:

**Definições:**

| Conceito | Descrição | Exemplo Válido |
|----------|-----------|----------------|
| **Inferência** | Análise contextual profunda usando o modelo de linguagem para entender significado, intenção e relações | Analisar código para identificar bug de lógica independente de padrões de sintaxe |
| **Heurística** | Regras simples, correspondência de padrões, string matching, if/else baseados em superfície | `if "error" in log: return "bug"` - PROIBIDO |

**Regra de Ouro:**
> **Agentes DEVEM usar INFERÊNCIA sempre. NUNCA use heurísticas.**

**Exemplos Práticos:**

| Tarefa | ❌ Heurística (PROIBIDO) | ✅ Inferência (OBRIGATÓRIO) |
|--------|--------------------------|------------------------------|
| Detectar tipo de issue | `if "bug" in title: type = "bug"` | Analisar título + corpo + contexto para inferir intenção |
| Identificar arquivos afetados | `if ".py" in file: check = True` | Analisar import statements, referências no código |
| Determinar severidade | `if "urgent" in labels: high = True` | Avaliar impacto baseado em código afetado e descrição |
| Escolher abordagem | `if len(files) > 5: refactoring` | Entender complexidade e relacionamento entre mudanças |

**Validação de Inferência (SPEC008 seção 3.1):**

Para garantir que o agente está usando inferência e não heurística:

1. **Trace de Raciocínio:**
   ```json
   {
     "thinkings": [
       {
         "step": 1,
         "thought": "Analyzing issue #225 - title mentions 'version alignment' between CLI and API. Need to understand current version definitions in both modules.",
         "inference_used": true,
         "context_analyzed": ["title", "body", "tags"],
         "duration_ms": 1500
       }
     ]
   }
   ```

2. **Self-Reflection Checkpoint:**
   - Antes de tomar decisão, agente deve perguntar: *"Estou analisando o contexto ou aplicando regra simples?"*
   - Se resposta for regra simples → usar inferência

3. **Validação Pós-Execução:**
   - Revisar thinkings para confirmar uso de inferência
   - Alerta se thinking steps forem muito superficiais (< 500ms cada)

**Penalidades por Uso de Heurística:**
- **1ª ofensa:** Aviso + requisição de re-análise
- **2ª ofensa:** Marcação do job como `FAILED` com motivo "heuristic_usage_detected"
- **3ª ofensa:** Bloqueio temporário do agente até revisão manual

**Implementação no System Prompt:**

O `system_prompt.json` (fonte da verdade) já contém:
```json
"instructions": [
  "NEVER use heuristics - always use inference to analyze and solve problems"
],
"rules": [
  "DO NOT use string matching or if/else heuristics for decisions",
  "ALWAYS read and analyze code before making changes"
]
```

### RF006: Criar Pull Requests Automaticamente
- **Descrição:** Após resolver issue, criar PR automaticamente
- **Entrada:** Branch + issue number
- **Saída:** PR criada com template padronizado
- **Prioridade:** Média

### RF007: Responder Mensagens no Discord
- **Descrição:** Responder comandos/perguntas no Discord automaticamente
- **Entrada:** Message ID + contexto
- **Saída:** Response postada no canal
- **Prioridade:** Média

### RF008: Sumarizar Vídeos do YouTube
- **Descrição:** Sumarizar vídeos novos automaticamente
- **Entrada:** Video URL
- **Saída:** Summary postada nos comentários
- **Prioridade:** Baixa

### RF009: Processar Pagamentos Stripe
- **Descrição:** Atualizar database após pagamento Stripe
- **Entrada:** Payment webhook
- **Saída:** Database atualizado + email enviado
- **Prioridade:** Alta

### RF010: Detectar e Prevenir Remoção Acidental
- **Descrição:** Dry-run obrigatório antes de remover worktree
- **Validação:** `safe_worktree_cleanup(dry_run=True)` primeiro
- **Prioridade:** Alta

---

## 5. Requisitos Não-Funcionais

### RNF001: Segurança de Webhooks
- **Descrição:** Todos os webhooks devem ter signature verification
- **Implementação:** HMAC SHA-256 por source
- **Prioridade:** Crítica

### RNF002: Isolamento Total de Worktrees
- **Descrição:** Worktrees não podem afetar repositório principal
- **Implementação:** Git worktree native isolation
- **Prioridade:** Alta

### RNF003: Observabilidade Completa
- **Descrição:** Todos os passos devem ser observáveis (logging, metrics, tracing)
- **Implementação:** Snapshot antes/depois + OpenTelemetry
- **Prioridade:** Alta

#### Detalhamento de Observabilidade

**1. Logging Estruturado:**

Todos os eventos devem ser logados com formato estruturado (JSON):

```json
{
  "timestamp": "2026-01-10T14:30:00Z",
  "level": "info",
  "job_id": "webhook-github-issue-225-cf560ba0",
  "event_type": "agent.spawned",
  "correlation_id": "gh-webhook-abc123",
  "source": "github",
  "issue_number": 225,
  "worktree_path": "B:\\_repositorios\\skybridge-worktrees\\skybridge-github-issue-225-cf560ba0",
  "agent_type": "claude-code",
  "metadata": {
    "issue_title": "Fix version alignment",
    "skill": "resolve-issue"
  }
}
```

**Níveis de Log:**
- `DEBUG`: Passos internos do agente
- `INFO`: Eventos normais (spawn, completion, success)
- `WARNING`: Recuperações automáticas, retries
- `ERROR`: Falhas que requerem atenção
- `CRITICAL`: Falhas que impedem operação

**2. Métricas (OpenTelemetry Metrics):**

| Métrica | Tipo | Descrição | Labels |
|---------|------|-----------|--------|
| `webhook.received` | Counter | Total de webhooks recebidos | source, event_type |
| `webhook.processed` | Counter | Total de webhooks processados | source, status |
| `agent.spawned` | Counter | Total de agentes spawnados | agent_type, skill |
| `agent.duration` | Histogram | Duração da execução do agente | skill, status |
| `agent.thinking_steps` | Histogram | Número de passos de raciocínio | skill |
| `worktree.created` | Counter | Worktrees criados | source |
| `worktree.cleanup` | Counter | Worktrees removidos | reason |
| `worktree.active` | Gauge | Worktrees ativos no momento | source |
| `agent.timeout` | Counter | Agentes que deram timeout | skill |
| `agent.failure` | Counter | Agentes que falharam | skill, error_type |

**3. Tracing Distribuído (OpenTelemetry Traces):**

Cada job deve ter um trace span principal com spans aninhados:

```
[TRACE] webhook-github-issue-225-cf560ba0 (total: 5m30s)
├── [SPAN] webhook.validation (500ms)
├── [SPAN] worktree.creation (2s)
├── [SPAN] agent.spawn (100ms)
├── [SPAN] agent.execution (5m20s)
│   ├── [SPAN] thinking.step.1 (1.5s) - "Analyzing issue #225"
│   ├── [SPAN] thinking.step.2 (300ms) - "Reading __init__.py"
│   ├── [SPAN] thinking.step.3 (2s) - "Implementing fix"
│   └── [SPAN] thinking.step.4 (1s) - "Running tests"
├── [SPAN] snapshot.after (500ms)
├── [SPAN] commit.creation (200ms)
└── [SPAN] pr.creation (1s)
```

**4. Snapshot Antes/Depois (GitExtractor):**

Conforme **SPEC008**, snapshots capturam estado completo:

```json
{
  "snapshot_id": "snap-abc123",
  "job_id": "webhook-github-issue-225-cf560ba0",
  "timestamp": "2026-01-10T14:30:00Z",
  "type": "before",
  "git": {
    "branch": "main",
    "commit": "a254128",
    "status": "clean"
  },
  "files": [
    {
      "path": "src/skybridge/core/__init__.py",
      "size": 1024,
      "hash": "sha256:abc123...",
      "last_modified": "2026-01-10T10:00:00Z"
    }
  ]
}
```

**5. Comandos XML em Tempo Real:**

Conforme **SPEC008**, agentes enviam comandos via stdout durante execução:

```xml
<!-- Comandos disponíveis -->
<skybridge_command>
  <command>log</command>
  <parametro name="mensagem">Analisando issue #225...</parametro>
  <parametro name="nivel">info</parameto>
</skybridge_command>

<skybridge_command>
  <command>progress</command>
  <parametro name="porcentagem">25</parametro>
  <parametro name="mensagem">Implementando correção...</parametro>
</skybridge_command>

<skybridge_command>
  <command>checkpoint</command>
  <parametro name="mensagem">Checkpoint: código analisado</parametro>
</skybridge_command>

<skybridge_command>
  <command>error</command>
  <parametro name="mensagem">Falha ao executar testes</parametro>
  <parametro name="tipo">test_failure</parametro>
</skybridge_command>
```

**6. Correlation IDs:**

Cada webhook deve propagar correlation ID através de toda a pipeline:

```
GitHub Webhook (X-GitHub-Delivery: abc-123-def)
    ↓
Skybridge API (correlation_id: gh-webhook-abc-123-def)
    ↓
Worktree (.sky/correlation.txt: gh-webhook-abc-123-def)
    ↓
Agent Context (correlation_id: gh-webhook-abc-123-def)
    ↓
All Logs/Metrics/Traces (correlation_id: gh-webhook-abc-123-def)
```

**7. Dashboard Requirements:**

- **Real-time Monitor:** Worktrees ativos, agentes rodando
- **Throughput Chart:** Webhooks recebidos vs processados (últimas 24h)
- **Duration P50/P95/P99:** Duração de execução por skill
- **Error Rate:** Taxa de falhas por source/skill
- **Timeout Rate:** Taxa de timeouts por skill
- **Trace Explorer:** Busca por correlation_id, issue_number, etc.
- **Log Aggregation:** Busca full-text em todos os logs com filtros

**8. Retenção de Dados:**

| Dado | Retenção | Justificativa |
|------|----------|---------------|
| Logs estruturados | 30 dias | Compliance e debugging |
| Métricas | 90 dias | Análise de tendências |
| Traces | 7 dias | Custo/benefício (traces são pesados) |
| Snapshots | 24h | Debugging recente + armazenamento |
| Worktrees | 24h (sucesso) / 7d (falha) | Debugging de erros |

**9. Alertas:**

| Alerta | Condição | Severidade |
|--------|----------|-----------|
| Alta taxa de timeouts | > 10% em 1h | CRITICAL |
| Alta taxa de falhas | > 15% em 1h | HIGH |
| Worktree leak | > 100 worktrees ativos | MEDIUM |
| Agente travado | Sem logs por 5min | MEDIUM |
| Webhook não processado | Fila > 50 itens | HIGH |

### RNF004: Rate Limiting por Source
- **Descrição:** Prevenir spam de webhooks de qualquer fonte
- **Implementação:** Redis + rate limit por IP/source
- **Prioridade:** Média

### RNF005: Retry com Exponential Backoff
- **Descrição:** Webhooks que falham devem ter retry inteligente
- **Implementação:** Dead letter queue + exponential backoff
- **Prioridade:** Média

### RNF006: Human-in-the-Loop
- **Descrição:** Ações críticas devem requerer aprovação humana
- **Implementação:** Modo semi-auto com notificação + aprovação
- **Prioridade:** Alta

### RNF007: Zero Downtime Deploy
- **Descrição:** Sistema deve suportar deploy sem perder webhooks
- **Implementação:** Queue persistence (Redis/RabbitMQ)
- **Prioridade:** Média

### RNF008: Compatibilidade com Skybridge Existente
- **Descrição:** Deve integrar com arquitetura Skybridge atual
- **Implementação:** Usar snapshot system, registry, CQRS
- **Prioridade:** Alta

---

## 6. Casos de Uso

### UC001: Resolução Automática de Issue (Principal)

**Ator:** GitHub Issue
**Pré-condições:** Issue aberta com template claro
**Fluxo Principal:**
1. GitHub envia webhook `issues.opened`
2. Skybridge cria worktree `skybridge-github-225`
3. Subagente analisa issue + código
4. Subagente implementa solução
5. Subagente commita + pusha
6. Skybridge cria PR
7. Validação: worktree limpo?
8. Sim: Remove worktree
9. Notificação: PR criada

**Pós-condições:** PR criada, worktree removido
**Alternativas:**
- 4a: Issue complexa demais → Notifica humano → Encerra
- 7a: Worktree sujo → Mantém worktree → Notifica humano

### UC002: Resposta Automática no Discord

**Ator:** Usuário Discord
**Pré-condições:** Mensagem enviada em canal monitorado
**Fluxo Principal:**
1. Discord envia webhook `message.create`
2. Skybridge detecta comando `/summarize`
3. Subagente lê últimas 50 mensagens
4. Subagente gera resumo
5. Skybridge posta resposta
6. Validação: nenhum cleanup necessário

**Pós-condições:** Resposta postada
**Alternativas:**
- 3a: Contexto insuficiente → Pede mais informações

### UC003: Sumarização de Vídeo YouTube

**Ator:** YouTube API
**Pré-condições:** Novo video uploadado
**Fluxo Principal:**
1. YouTube envia PubSubHubbub event
2. Skybridge cria worktree `skybridge-youtube-xyz`
3. Subagente baixa vídeo
4. Subagente transcreve (whisper)
5. Subagente sumariza
6. Skybridge posta comentário
7. Cleanup: remove worktree + vídeo baixado

**Pós-condições:** Comentário postado, arquivos limpos

---

## 7. Roadmap de Implementação

### Fase 0: Proof of Concept (Semana 1) - ✅ COMPLETO
**Objetivo:** Validar ideia com stakeholders

- [x] Criar PRD (este documento)
- [x] Estudo técnico (`webhook-autonomous-agents-study.md`)
- [x] Apresentar para equipe/stakeholders
- [x] **Decisão: Go/No-Go** ✅ **GO APROVADO**

### Fase 1: MVP GitHub + SPEC008 (Semana 2-3) - ✅ COMPLETO
**Objetivo:** Primeira fonte funcionando end-to-end com Agent Facade Pattern

#### Core Webhook Infrastructure
- [x] `POST /webhooks/github` com signature verification
- [x] Background worker com fila em memória
- [x] GitExtractor para validação
- [x] Skill `/resolve-issue` documentado

#### Agent Infrastructure (SPEC008)
- [x] Agent Facade Pattern implementado
- [x] Domain entities (AgentState, AgentExecution, AgentResult, ThinkingStep)
- [x] Claude Code Adapter com stdin/stdout streaming
- [x] XML Streaming Protocol para comunicação bidirecional
- [x] Agent state management (CREATED, RUNNING, COMPLETED, TIMED_OUT, FAILED)
- [x] Skill-based timeout configuration (hello-world: 60s, bug-simple: 300s, etc)
- [x] system_prompt.json como fonte da verdade
- [x] Testes TDD (38 testes cobrindo toda a infraestrutura)

#### Componentes Criados
```
src/skybridge/core/contexts/webhooks/infrastructure/agents/
├── __init__.py                    # Exports públicos
├── domain.py                      # AgentState, AgentExecution, AgentResult, ThinkingStep
├── agent_facade.py                # Interface abstrata AgentFacade
├── claude_agent.py                # ClaudeCodeAdapter (implementação)
└── protocol.py                    # XMLStreamingProtocol, SkybridgeCommand

tests/core/contexts/webhooks/
└── test_agent_infrastructure.py   # 38 testes TDD
```

### Fase 2: Multi-Source (Semana 4-5) - 🔮 PENDENTE
**Objetivo:** Adicionar 2 fontes (Discord, YouTube)

- [ ] Discord webhook handler
- [ ] YouTube PubSubHubbub handler
- [ ] Skills `/respond-discord`, `/summarize-video`
- [ ] Roo Code Adapter (se disponível)
- [ ] **Teste:** 20 eventos processados

### Fase 3: Produção (Semana 6-8) - 🔮 PENDENTE
**Objetivo:** Hardening + observabilidade

- [ ] Redis para fila persistente
- [ ] Prometheus metrics
- [ ] OpenTelemetry tracing
- [ ] Dashboard Grafana
- [ ] **Teste:** Carga de 100 eventos/hora

### Fase 4: Expansão (Mês 3+) - 🔮 PENDENTE
**Objetivo:** Mais fontes + melhorias

- [ ] Stripe webhook handler
- [ ] Slack webhook handler
- [ ] Auto-triage de issues (labels, assignees)
- [ ] Machine learning para detecção de issues "resolveíveis"

---

## 8. Success Metrics

### Métricas de Produto

| Métrica | Baseline | Mês 1 | Mês 3 | Mês 6 |
|---------|----------|-------|-------|-------|
| Issues resolvidas automaticamente | 0 | 50 | 200 | 500 |
| Tempo médio resposta (issue → PR) | 24h | 2h | 30min | 5min |
| Worktrees limpos sem intervenção | N/A | 80% | 90% | 95% |
| Eventos processados/dia | 0 | 20 | 50 | 100 |
| Fontes integradas | 0 | 1 | 3 | 5+ |

### Métricas Técnicas

| Métrica | Target |
|---------|--------|
| Uptime do webhook endpoint | 99.9% |
| Tempo resposta webhook | <200ms (aceita + processa async) |
| Taxa de sucesso de processamento | >95% |
| Memory usage por worktree | <100MB |
| Cleanup rate (worktrees removidos/criados) | >90% |

### Métricas de Negócio

| Métrica | Impacto |
|---------|---------|
| Tempo dev ganho/dia | +2h |
| Custo de desenvolvimento | -30% (issues auto-resolvidas) |
| Satisfação time (survey) | >8/10 |
| Redução de technical debt | +40% (issues rápidas não acumulam) |

---

## 9. Riscos e Mitigações

| Risco | Probabilidade | Impacto | Mitigação |
|-------|---------------|---------|-----------|
| Agente alucina (implementa errado) | Média | Alto | **Human-in-the-loop** (semi-auto primeiro) |
| Worktree sujo não removido (acúmulo) | Baixa | Médio | **GitExtractor + validação pré-cleanup** |
| GitHub rate limit | Média | Baixo | Exponential backoff + cache |
| Webhook spoofing | Baixa | Crítico | **HMAC signature verification** |
| Falha de API externa | Média | Médio | Retry + dead letter queue |
| Resistência da equipe | Média | Alto | **Começar com manual**, demonstrar valor |
| Dados sensíveis em worktrees | Baixa | Alto | **GitExtractor detecta secrets não commitados?** |

---

## 10. Próximos Passos

### Imediato (Esta semana)
1. ✅ **Estudo técnico** (`webhook-autonomous-agents-study.md`)
2. ✅ **PRD** (este documento)
3. 🔲 **Revisão com stakeholders**
4. 🔲 **Decisão: Go/No-Go**

### Curto Prazo (Se Go)
1. 🔲 **Proof of Concept** (Fase 0-1)
2. 🔲 **Teste com 10 issues reais**
3. 🔲 **Coleta de feedback**
4. 🔲 **Iteração baseada em aprendizados**

### Médio Prazo (Após validação)
1. 🔲 **ADR** - Documentar decisões arquiteturais
2. 🔲 **Implementação completa** (Fases 1-4)
3. 🔲 **Deploy em produção**
4. 🔲 **Monitoramento e ajustes**

---

## 11. Apêndice

### A. Exemplo de Payload GitHub

```json
{
  "action": "opened",
  "issue": {
    "number": 225,
    "title": "Fix: alinhar versões da CLI e API com ADR012",
    "body": "## Problema\nAs versões não estão centralizadas...",
    "labels": [{"name": "bug"}, {"name": "good-first-issue"}]
  },
  "repository": {
    "name": "skybridge",
    "full_name": "h4mn/skybridge"
  }
}
```

### B. Exemplo de Validação GitExtractor

```python
result = safe_worktree_cleanup("B:\\_repositorios\\skybridge-worktrees\\skybridge-github-issues-225-abc123", dry_run=True)

# Saída: Worktree limpo
{
  "can_remove": true,
  "message": "Worktree limpo (com 3 arquivos untracked)",
  "status": {
    "branch": "fix/issue-225",
    "clean": true,
    "unstaged": 0,
    "untracked": 3
  }
}
```

### C. Referências

- [Estudo Técnico](../report/webhook-autonomous-agents-study.md)
- [Worktree Validation Example](../report/worktree-validation-example.md)
- [GitHub Webhooks Best Practices](https://docs.github.com/en/webhooks)
- [FastAPI Webhooks Guide](https://neon.com/guides/fastapi-webhooks)

---

## Aprovações

| Papel | Nome | Data | Assinatura |
|-------|------|------|------------|
| Autor | Sky | 2026-01-07 | ✍️ |
| Tech Lead | ___________ | ___________ | ______ |
| Product Manager | ___________ | ___________ | ______ |
| Security Review | ___________ | ___________ | ______ |

---

> "A melhor forma de prever o futuro é criá-lo" – made by Sky 🚀

---

**Documento versão:** 1.3
**Última atualização:** 2026-01-10
**Status:** ✅ Phase 1 + SPEC008 Implementado
