# Skybridge Workflows Plugin

Conjunto de skills para orquestração de workflow multi-agente na Skybridge.

## Visão Geral

Este plugin define 4 skills que compõem o workflow de orquestração de issues:

1. **create-issue** — Analisa requisito e cria issue estruturada
2. **resolve-issue** — Recebe webhook e implementa solução
3. **test-issue** — Valida solução e roda testes automatizados
4. **challenge-quality** — Executa ataques adversariais para validar qualidade

## Instalação

1. Copie este plugin para `plugins/skybridge-workflows/`
2. O kernel do Skybridge detectará automaticamente o `manifest.yaml`
3. As skills estarão disponíveis para os agentes

## Arquitetura

### SPEC008 vs SPEC009

- **SPEC008 — AI Agent Interface:** Define contrato técnico individual de cada agente
- **SPEC009 — Orquestração de Workflow Multi-Agente:** Define como agentes se coordenam

Este plugin implementa as **SKILLS** definidas em SPEC009, mas cada agente segue a interface técnica definida em SPEC008.

## Workflow de Orquestração

```
[Requisição do Usuário]
      ↓
[create-issue] → issue: OPEN
      ↓ (webhook)
[resolve-issue] → issue: IN_PROGRESS
      ↓ (commit+PR)
[test-issue] → issue: READY_FOR_TEST
      ↓ (testes passam)
[challenge-quality] → issue: UNDER_CHALLENGE
      ↓ (ataca adversarialmente)
      ├── (encontra bug) → CRIA NOVA ISSUE para correção
      ├── (docs inconsistentes) → CRIA NOVA ISSUE para correção
      └── (tudo ok) → issue: AWAITING_HUMAN_APPROVAL
             ↓
        [Humano aprova] → issue: VERIFIED → issue: CLOSED
```

## Skills

### create-issue

**Responsável:** Criador de Issue

**Objetivo:** Analisar requisito e criar issue estruturada

**Entrada:**
- Requisição do usuário (texto, descrição, contexto)

**Saída:**
- Issue criada com template estruturado (ver SPEC009 seção 5)
- Labels: `["automated", "<tipo>"]`

**Transição:** `issue: OPEN`

**Status:** 🔮 **Planejado** (PRD013 Phase 2)

---

### resolve-issue

**Responsável:** Resolvedor de Issue

**Objetivo:** Receber webhook e implementar solução

**Entrada:**
- Webhook de issue aberta (`issues.opened`)
- Contexto completo da issue

**Saída:**
- PR criada com implementação
- Worktree limpo após implementação

**Transição:** `issue: IN_PROGRESS` → `issue: READY_FOR_TEST`

**Status:** ✅ **Já implementado** (conforme PRD013 Phase 1)

---

### test-issue

**Responsável:** Testador de Issue

**Objetivo:** Validar solução e rodar testes automatizados

**Entrada:**
- PR criada (`pull_request.opened`)
- Contexto de mudanças (arquivos criados/modificados)

**Saída:**
- Resultados de testes (unit, integration, coverage)
- Validação de lint e typecheck
- Se falhar → issue: `FAILED`
- Se passar → issue: `UNDER_CHALLENGE`

**Transição:** `issue: READY_FOR_TEST` → `issue: UNDER_CHALLENGE`

**Status:** 🔮 **Planejado** (PRD013 Phase 2)

---

### challenge-quality

**Responsável:** Desafiador de Qualidade

**Objetivo:** Executar ataques adversariais para validar qualidade

**Mentalidade:** "Isso vai quebrar. Deixa eu provar."

**Categorias de Ataque:**
- **Boundary** — Inputs vazios, null, valores extremos
- **Concurrency** — Race conditions, deadlocks
- **Security** — Injection, bypass, overflow
- **Performance** — Load test, stress test
- **Documentation** — Docs vs código inconsistente

**Entrada:**
- Resultados de testes (`testes pass`)
- Contexto de arquivos alterados
- Documentação para validar

**Saída:**
- Se encontrar bug → **CRIA NOVA ISSUE** com proof of exploit
- Se encontrar docs inconsistentes → CRIA NOVA ISSUE para correção
- Se tudo ok → `issue: AWAITING_HUMAN_APPROVAL`

**Transição:**
- `issue: UNDER_CHALLENGE` → `issue: AWAITING_HUMAN_APPROVAL` (se OK)
- `issue: UNDER_CHALLENGE` → **nova issue** (se bug/docs)

**Status:** 🔮 **Planejado** (PRD013 Phase 2)

---

## Estados da Issue vs Estados do Agente

| Conceito | Definido em | Exemplos |
|----------|-------------|-----------|
| **Estados do AGENTE** | SPEC008 | CREATED, RUNNING, COMPLETED, TIMED_OUT, FAILED |
| **Estados da ISSUE** | SPEC009 | OPEN, IN_PROGRESS, READY_FOR_TEST, UNDER_CHALLENGE, AWAITING_HUMAN_APPROVAL, VERIFIED, CLOSED |

**Nota:** Os dois conjuntos de estados são independentes e servem propósitos diferentes.

## Métricas de Orquestração

As seguintes métricas devem ser coletadas (conforme SPEC009):

| Métrica | Labels | Descrição |
|---------|---------|-----------|
| `agent.handoff.duration` | source, dest | Tempo entre handoffs |
| `agent.cycle.time` | issue_type | Tempo total create→challenge |
| `agent.success.rate` | agent_type, skill | Taxa de sucesso |
| `agent.test.pass.rate` | issue_type | Pass rate dos testes |
| `agent.challenger.exploits_found` | issue_type, attack_cat | Exploits encontrados |
| `agent.human.approval.time` | issue_type | Tempo para aprovação humana |
| `agent.issues.created.by_challenger` | issue_type, reason | Issues criadas por desafiador |

## Roadmap de Implementação

| Fase | Status | Descrição |
|------|--------|-----------|
| Phase 1 | ✅ Completo | SPEC008 + Skill `/resolve-issue` |
| Phase 2 | 🔮 Planejado | Skills `/create-issue`, `/test-issue`, `/challenge-quality` |
| Phase 3 | 🔮 Futuro | Orquestrador de workflow + aprovação humana + dashboard |

## Estrutura do Plugin

```
skybridge-workflows/
├── manifest.yaml
├── README.md
└── src/
    └── skybridge_workflows/
        ├── __init__.py
        └── skills/
            ├── create-issue.md
            ├── resolve-issue.md
            ├── test-issue.md
            └── challenge-quality.md
```

## Referências

- [SPEC008 — AI Agent Interface](../../../docs/spec/SPEC008-AI-Agent-Interface.md)
- [SPEC009 — Orquestração de Workflow Multi-Agente](../../../docs/spec/SPEC009-orchestracao-workflow-multi-agente.md)
- [PRD013 — Webhook Autonomous Agents](../../../docs/prd/PRD013-webhook-autonomous-agents.md)
- [ADR018 — Português Brasileiro](../../../docs/adr/ADR018-linguagem-portugues-brasil-codebase.md)

---

> "Orquestração é a arte de coordenar talentos individuais em uma sinfonia coletiva." – made by Sky 🎼
