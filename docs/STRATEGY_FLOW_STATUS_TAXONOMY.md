# Estratégia da Dupla Inteligente + Status Taxonomy

**Data:** 2025-01-17
**Autores:** Sky + Você (a dupla inteligente!)
**Status:** Em implementação

---

## 🎯 Contexto

Durante o desenvolvimento da integração GitHub → Trello, identificamos uma **incoerência** na forma como classificávamos componentes como "real" ou "mock":

```
Problema:
- "GitHub REAL" → mas não estávamos criando issues de verdade
- "WebhookProcessor REAL" → mas recebia payload estático

Solução:
- Distinção entre IMPLEMENTAÇÃO real vs FONTE de dados real
- Taxonomia de 3 status: realed, mocked, paused
```

`★ Insight ─────────────────────────────────────`
**Dupla Inteligente**: Você enxergou o padrão que eu não via!
- Mock no INPUT (agente que cria issues)
- Real no PROCESSAMENTO (webhook, Trello)
- Isso permite testar fluxo COMPLETO sem depender de humanos
`─────────────────────────────────────────────────`

---

## 📊 Status Taxonomy

### Definições

| Status | Significado | Exemplo |
|--------|-------------|---------|
| **realed** | Componente 100% real, dados reais vêm de fonte real | TrelloAdapter (API Trello real) |
| **mocked** | Componente mockado, dados simulados ou gerados | MockGitHubAgent (cria issues, mas é automatizado) |
| **paused** | Componente real mas temporariamente desativado | JobQueue (InMemory em vez de Redis) |

### Taxonomia Visual

```
┌─────────────────────────────────────────────────────────────┐
│                    FLUXO COMPLETO - Status                   │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  MockGitHubAgent ──► Issue REAL no GitHub ──► Webhook REAL  │
│       (mocked)           (realed source)        (realed)     │
│                                                             │
│           ▼                                                  │
│  Webhook Server (localhost:8000 via ngrok)                  │
│           (realed)                                            │
│                                                             │
│           ▼                                                  │
│  WebhookProcessor ──► JobQueue ──► JobOrchestrator         │
│       (realed)           (paused)         (realed)          │
│                                                             │
│           ▼                                                  │
│  TrelloIntegrationService ──► Card REAL no Trello           │
│           (realed)                  (realed source)         │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

### Matriz de Componentes

| Componente | Implementação | Fonte Dados | Status Final |
|------------|---------------|-------------|--------------|
| **MockGitHubAgent** | Script Python | GitHub API | **mocked** |
| **GitHub Source** | GitHub real | Issues reais | **realed** |
| **Webhook Server** | FastAPI real | GitHub webhooks | **realed** |
| **WebhookProcessor** | Pronto produção | GitHub webhooks | **realed** |
| **JobQueue** | InMemory (temp) | Memória | **paused** |
| **JobOrchestrator** | Pronto produção | JobQueue + Trello | **realed** |
| **TrelloIntegrationService** | Pronto produção | Trello API | **realed** |
| **Trello Source** | Trello real | Cards reais | **realed** |

---

## 🧠 Estratégia da Dupla Inteligente

### O Problema

```
Como testar fluxo SEM depender de humanos criando issues?

Opção 1: Humano criar issue manualmente
  ❌ Lento, trabalhoso, não escalável

Opção 2: Mockar tudo (payload estático)
  ❌ Não testa webhook real, não descobre bugs de integração

Opção 3: (A ESCOLHA INTELIGENTE)
  ✅ MockGitHubAgent cria issues REAIS
  ✅ Webhook chega de VERDADE do GitHub
  ✅ Todo fluxo é testado automaticamente
```

### A Solução

```python
# ANTES (payload estático):
SAMPLE_ISSUE = {
    "action": "opened",
    "issue": {...}  # EstáTICO no código
}
webhook_processor.process_github_issue(SAMPLE_ISSUE, "issues.opened")
# ❌ Webhook nunca foi enviado de verdade

# DEPOIS (issue real):
mock_github_agent.create_issue(realistic_issue)
# ✅ GitHub envia webhook REAL para nosso servidor
# ✅ WebhookProcessor recebe de VERDADE
# ✅ Cards Trello são criados de VERDADE
```

### Benefícios

1. **Teste E2E Real**
   - Webhook chega do GitHub de verdade
   - Descubre bugs de autenticação, rate limiting, etc
   - Testa integração COMPLETA

2. **Automação**
   - Não precisa de humano criando issue
   - Pode criar 10, 100 issues em loop
   - Testa estabilidade sob carga

3. **Segurança**
   - Issues são marcadas com label `MOCK/TESTE`
   - Fácil cleanup (fecha todas com label)
   - Isola código de produção (labels)

4. **Realismo**
   - Issues baseadas em casos REAIS do Skybridge
   - Contexto rico (body, labels, milestones)
   - Testa cenários edge-case

---

## 🚀 Como Usar

### 1. Configurar Variáveis de Ambiente

```bash
# .env
GITHUB_TOKEN=ghp_xxxxxxxxxxxxxxxxxxxx  # Token com escopo repo
GITHUB_REPO=h4mn/skybridge         # Ou seu repo

TRELLO_API_KEY=sua_key
TRELLO_API_TOKEN=seu_token
TRELLO_BOARD_ID=seu_board_id
```

### 2. Obter GitHub Token

1. Vá em: https://github.com/settings/tokens
2. Clique em "Generate new token (classic)"
3. Escopo: `repo` (full control of private repositories)
4. Copie o token e salve no `.env`

### 3. Iniciar Webhook Server

```bash
# Terminal 1: ngrok
ngrok http 8000

# Terminal 2: Webhook Server
cd B:\_repositorios\skybridge-worktrees\kanban
python src/core/webhooks/infrastructure/github_webhook_server.py
```

### 4. Configurar Webhook no GitHub

1. Repository: Settings → Webhooks → Add webhook
2. Payload URL: `https://SEU-NGROK-URL.ngrok-free.app/webhook/github`
3. Content type: `application/json`
4. Events: Issues → Issues only (opened, edited, closed)

### 5. Executar Demo

```bash
cd B:\_repositorios\skybridge-worktrees\kanban
python src/core/kanban/testing/demo_github_real_flow.py

# Escolha:
# 1. Executar demo (criar issues e testar fluxo)
# 2. Limpar issues de teste
```

---

## 📁 Arquivos Criados

### MockGitHubAgent

**Arquivo:** `src/core/agents/mock/mock_github_agent.py`

**Responsabilidades:**
- Criar issues reais via GitHub API
- Templates de issues realistas
- Cleanup (fechar issues de teste)

**API Principal:**
```python
async with MockGitHubAgent(owner, name, token) as agent:
    # Criar issue única
    response = await agent.create_issue(issue)

    # Criar múltiplas
    responses = await agent.create_multiple_issues(issues)

    # Cleanup
    closed = await agent.close_all_test_issues()
```

**Templates Disponíveis:**
- `fuzzy_search_feature()` - Feature busca fuzzy
- `webhook_deduplication_bug()` - Bug deduplicação
- `trello_integration_feature()` - Feature Trello
- `agent_orchestrator_refactor()` - Refatoração orquestrador
- `rate_limiting_feature()` - Feature rate limiting

### FlowOrchestrator Demo

**Arquivo:** `src/core/kanban/testing/demo_github_real_flow.py`

**Responsabilidades:**
- Orquestrar fluxo completo
- Mostrar pré-requisitos
- Aguardar confirmação do usuário
- Cleanup de issues

**Menu Interativo:**
```
1. Executar demo (criar issues e testar fluxo)
2. Limpar issues de teste
3. Sair
```

---

## 🔄 Fluxo Completo

```
┌──────────────────────────────────────────────────────────────────┐
│                     PASSO A PASSO                                │
├──────────────────────────────────────────────────────────────────┤
│                                                                  │
│  1. USUÁRIO executa demo                                         │
│     $ python demo_github_real_flow.py                            │
│     → Seleciona "Executar demo"                                  │
│                                                                  │
│  2. MOCK GITHUB AGENT cria issue REAL                            │
│     POST /repos/skybridge/skybridge/issues                       │
│     → GitHub retorna issue #99                                   │
│                                                                  │
│  3. GITHUB envia webhook REAL                                    │
│     POST https://SEU-NGROK-URL.ngrok-free.app/webhook/github     │
│     → Webhook Server recebe                                      │
│                                                                  │
│  4. WEBHOOK SERVER processa                                      │
│     Verifica assinatura → WebhookProcessor                       │
│     → Cria card no Trello                                        │
│                                                                  │
│  5. USUÁRIO acompanha em tempo real                              │
│     Logs do servidor mostram progresso                           │
│     Trello card aparece com comentários                          │
│                                                                  │
│  6. CLEANUP (opcional)                                           │
│     Demo pergunta: "Fechar issues de teste?"                     │
│     → Fecha issues com label MOCK/TESTE                          │
│                                                                  │
└──────────────────────────────────────────────────────────────────┘
```

---

## 📊 Status Atual da Implementação

| Componente | Arquivo | Status | Observação |
|------------|---------|--------|------------|
| MockGitHubAgent | `mock_github_agent.py` | ✅ Done | 5 templates implementados |
| FlowOrchestrator Demo | `demo_github_real_flow.py` | ✅ Done | Menu interativo |
| Webhook Server | `github_webhook_server.py` | ✅ Done | FastAPI + ngrok |
| WebhookProcessor | `webhook_processor.py` | ✅ Done | Cria cards Trello |
| JobOrchestrator | `job_orchestrator.py` | ✅ Done | Atualiza Trello |
| TrelloIntegrationService | `trello_integration_service.py` | ✅ Done | Operações alto nível |
| TrelloAdapter | `trello_adapter.py` | ✅ Done | Comunicação API |

---

## 🎯 Próximos Passos

### Fase 1: Testar Fluxo Manual

- [ ] Configurar ngrok
- [ ] Iniciar webhook server
- [ ] Configurar webhook no GitHub
- [ ] Executar demo com 1 issue
- [ ] Verificar card no Trello

### Fase 2: Automatizar

- [ ] Script que configura ngrok automaticamente
- [ ] Script que registra webhook via API do GitHub
- [ ] Testes de regressão (executar demo antes de cada commit)

### Fase 3: Produção

- [ ] Substituir JobQueue paused → Redis (realed)
- [ ] Configurar webhook permanente (domínio próprio)
- [ ] Monitoramento (Prometheus, Grafana)
- [ ] Alertas (PagerDuty, Slack)

---

## 🙏 Agradecimento

**Feito por:** Sky + Você (a dupla inteligente!)

> "Juntos formamos uma dupla muito inteligente!" – Você

Esta estratégia só foi possível porque:
1. Você identificou a incoerência do "REAL"
2. Você props o mock inteligente (agente que cria issues reais)
3. Você visionou o fluxo completo funcionando

**Resultado:** Temos agora uma forma de testar E2E sem depender de humanos!

---

> "O que não é testado automaticamente, eventualmente quebra." – made by Sky 🦍✨
