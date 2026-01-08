# PRD001: Webhook-Driven Autonomous Agents para Skybridge

**Status:** 📝 Proposta
**Data:** 2026-01-07
**Autor:** Sky
**Versão:** 1.0

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
  "source": "github",
  "event_type": "issues",
  "issue_number": 225,
  "action": "resolve"
}

# 3. Worktree criado
git worktree add ../skybridge-fix-225 -b fix/issue-225

# 4. GitExtractor captura snapshot inicial
initial_snapshot = git_extractor.capture("../skybridge-fix-225")
# Salva: branch=fix/issue-225, hash=abc123, staged=[], unstaged=[]

# 5. Subagente trabalha
cd ../skybridge-fix-225
[agente lê issue, implementa solução, testa]
git add .
git commit -m "fix: resolve issue #225"
git push

# 6. PR criada
gh pr create --title "Fix #225" --body "Resolves issue #225"

# 7. Validação PRÉ-cleanup
can_remove, message, status = git_extractor.validate_worktree("../skybridge-fix-225")

if can_remove:
    # ✅ Worktree limpo, pode remover
    git worktree remove ../skybridge-fix-225
else:
    # ⚠️ Worktree sujo, mantém para investigação
    notify(f"⚠️ {message}")

# 8. Fim
PR criada, worktree limpo, zero resíduo
```

---

## 4. Requisitos Funcionais

### RF001: Receber Webhooks de Múltiplas Fontes
- **Descrição:** Sistema deve aceitar webhooks de GitHub, Discord, YouTube, Stripe, Slack
- **Entrada:** `POST /webhooks/{source}` com payload específico
- **Saída:** Job enfileirado para processamento
- **Prioridade:** Alta

### RF002: Processar Webhooks de Forma Assíncrona
- **Descrição:** Worker background deve processar webhooks sem bloquear resposta
- **Entrada:** Job da fila
- **Saída:** Worktree criado + subagente spawnado
- **Prioridade:** Alta

### RF003: Criar Worktrees Isolados por Evento
- **Descrição:** Cada evento deve ter seu próprio worktree isolado
- **Formato:** `skybridge-{source}-{id}` (ex: `skybridge-github-225`)
- **Prioridade:** Alta

### RF004: Spawnar Subagentes com Contexto Específico
- **Descrição:** Task tool deve spawnar subagente no worktree com contexto do evento
- **Entrada:** Worktree path + issue/event details
- **Saída:** Subagente executando ação específica
- **Prioridade:** Alta

### RF005: Validar Worktree Antes de Cleanup
- **Descrição:** GitExtractor deve validar se worktree pode ser removido com segurança
- **Validação:** Staged files? Unstaged? Conflicts?
- **Saída:** `can_remove + mensagem detalhada`
- **Prioridade:** Alta

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

### Fase 0: Proof of Concept (Semana 1)
**Objetivo:** Validar ideia com stakeholders

- [ ] Criar PRD (este documento)
- [ ] Apresentar para equipe/stakeholders
- [ ] Feedback e ajustes
- [ ] **Decisão: Go/No-Go**

### Fase 1: MVP GitHub (Semana 2-3)
**Objetivo:** Primeira fonte funcionando end-to-end

- [ ] `POST /webhooks/github` com signature verification
- [ ] Background worker com fila em memória
- [ ] GitExtractor para validação
- [ ] Skill `/resolve-issue` manual
- [ ] **Teste:** 10 issues reais resolvidas

### Fase 2: Multi-Source (Semana 4-5)
**Objetivo:** Adicionar 2 fontes (Discord, YouTube)

- [ ] Discord webhook handler
- [ ] YouTube PubSubHubbub handler
- [ ] Skills `/respond-discord`, `/summarize-video`
- [ ] **Teste:** 20 eventos processados

### Fase 3: Produção (Semana 6-8)
**Objetivo:** Hardening + observabilidade

- [ ] Redis para fila persistente
- [ ] Prometheus metrics
- [ ] OpenTelemetry tracing
- [ ] Dashboard Grafana
- [ ] **Teste:** Carga de 100 eventos/hora

### Fase 4: Expansão (Mês 3+)
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
result = safe_worktree_cleanup("../skybridge-fix-225", dry_run=True)

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

**Documento versão:** 1.0
**Última atualização:** 2026-01-07
**Status:** 📝 Aguardando revisão
