---
status: proposto
data: 2026-01-12
version: 1.0.0
---

# SPEC009 — Orquestração de Workflow Multi-Agente

**Status:** Proposto
**Data:** 2026-01-12
**Autor:** Sky
**Versão:** 1.0.0

---

## 1. Objetivo

Definir contrato de orquestração onde múltiplos agentes colaboram em sequência para resolver issues: **create** → **resolve** → **test** → **challenge**.

Esta especificação define como agentes coordenados pela **SPEC008 (AI Agent Interface)** trabalham juntos através de handoffs estruturados para garantir qualidade antes de produção.

---

## 2. Diferença entre SPEC008 e SPEC009

### SPEC008 — AI Agent Interface
- **Foco:** Contrato técnico individual de cada agente
- **Define:** Como um agente funciona (comunicação stdin/stdout, worktrees, estados do AGENTE)
- **Pergunta:** "Como um agente funciona individualmente?"

### SPEC009 — Orquestração de Workflow Multi-Agente
- **Foco:** Coordenação de múltiplos agentes
- **Define:** Como agentes colaboram (sequência, transições da ISSUE, handoffs, métricas de orquestração)
- **Pergunta:** "Como agentes trabalham JUNTOS para resolver issues?"

**Analogia:**
- SPEC008 = Instruções de uso de cada ferramenta (martelo, chave, serrote, inspetor)
- SPEC009 = Plano de construção que define a SEQUÊNCIA de uso das ferramentas

---

## 3. Atores

| Agente | Responsabilidade | Skill |
|--------|-----------------|--------|
| **Criador de Issue** | Analisa requisito, cria issue estruturada | `/create-issue` |
| **Resolvedor de Issue** | Recebe webhook, implementa solução | `/resolve-issue` |
| **Testador de Issue** | Valida solução, roda testes | `/test-issue` |
| **Desafiador de Qualidade** | **Ator adversarial que tenta quebrar o sistema** | `/challenge-quality` |

### 3.1 Desafiador de Qualidade — Detalhes

**Mentalidade:** "Isso vai quebrar. Deixa eu provar."

**Responsabilidades:**
- Pensar em edge cases e cenários de falha não considerados
- Testar adversarialmente (tentar quebrar propositalmente)
- Comprovar teorias com código e testes reais
- Se contrapor à documentação quando não reflete a realidade
- Encontrar discrepâncias entre "documentado" e "implementado"
- Melhorar qualidade através da adversariedade construtiva

**Categorias de Ataque:**

| Categoria | Exemplos |
|-----------|----------|
| **Boundary** | Inputs vazios, null, valores extremos |
| **Concurrency** | Race conditions, deadlocks, recursos compartilhados |
| **Security** | Injection, bypass de autenticação, overflow |
| **Performance** | Carga, estresse, memory leak |
| **Compatibility** | Versões antigas, ambientes diferentes |
| **Documentation** | Docs vs código inconsistente |

**Postura Adversarial:**
- Cético por padrão
- Assume que tudo pode falhar
- Encontra bugs antes de usuários reais
- Documenta cada cenário testado
- Propõe melhorias concretas (não só aponta problemas)

---

## 4. Fluxo de Estado da Issue

```
[Requisição do Usuário]
      ↓
[Criador de Issue] → issue: OPEN
      ↓ (webhook)
[Resolvedor de Issue] → issue: IN_PROGRESS
      ↓ (commit+PR)
[Testador de Issue] → issue: READY_FOR_TEST
      ↓ (testes passam)
[Desafiador de Qualidade] → issue: UNDER_CHALLENGE
      ↓ (ataca adversarialmente)
      ├── (encontra bug) → CRIA NOVA ISSUE para correção
      ├── (docs inconsistentes) → CRIA NOVA ISSUE para correção
      └── (tudo ok) → issue: AWAITING_HUMAN_APPROVAL
             ↓
        [Humano aprova] → issue: VERIFIED → issue: CLOSED
```

---

## 5. Transições da Issue

| Estado | Gatilho | Responsável | Ação |
|--------|----------|--------------|-------|
| `OPEN` | Issue criada | Criador de Issue | Posta webhook |
| `IN_PROGRESS` | Webhook recebido | Resolvedor de Issue | Cria worktree |
| `READY_FOR_TEST` | PR criada | Resolvedor de Issue | Notifica testador |
| `UNDER_CHALLENGE` | Testes passam | Desafiador de Qualidade | Inicia ataques adversariais |
| `AWAITING_HUMAN_APPROVAL` | Todos ataques falharam | Desafiador de Qualidade | Marca como aguardando aprovação |
| `APPROVED` | Humano aprovou | Humano | Libera issue |
| `VERIFIED` | Issue aprovada | Sistema | Fecha issue |
| `FAILED` | Testes falham | Testador de Issue | Reabre issue + comentário |

---

## 6. Mecanismo de Liberação Humana

### 6.1 Labels de Controle

| Label | Significado | Aplicado por |
|-------|-----------|-------------|
| `automated` | Issue gerada automaticamente | Sistema |
| `awaiting-approval` | Aguardando aprovação humana | Desafiador de Qualidade |
| `approved` | Issue aprovada por humano | Humano |
| `test-failed` | Testes falharam | Testador de Issue |

### 6.2 Fluxo de Aprovação

1. **Desafiador de Qualidade** aprova:
   - Adiciona label `awaiting-approval`
   - Adiciona comentário: "✅ Testes adversariais passaram. Aguardando aprovação humana."

2. **Humano aprova:**
   - Remove label `awaiting-approval`
   - Adiciona label `approved`
   - Adiciona comentário: "✅ Aprovado"
   - Issue → `VERIFIED` → `CLOSED`

3. **Humano rejeita:**
   - Remove label `awaiting-approval`
   - Adiciona comentário com motivo
   - Issue fica aberta para rework

---

## 7. Contrato de Issue

```yaml
issue_template:
  title: "<tipo>: <descrição sucinta>"
  labels: ["automated", "<tipo>"]
  body: |
    ## 1. Requisito Original
    <requisito original>

    ## 2. Análise (Criador)
    <análise do Criador>

    ## 3. Desenvolvimento (Resolvedor)
    <implementação>

    ## 4. Testes (Testador)
    <validação>

    ## 5. Desafio (Desafiador)
    <ataques adversariais tentados>
    <bugs encontrados (se houver)>
    <discrepâncias docs vs código (se houver)>

    ---
    Agentes: criador=<id>, resolvedor=<id>, testador=<id>, desafiador=<id>
```

---

## 8. Handoffs

### Criador → Resolvedor

```json
{
  "event": "issues.opened",
  "issue_number": 123,
  "agent_context": {
    "criador_tipo": "analysis",
    "prioridade": "high",
    "timeout": 600
  }
}
```

### Resolvedor → Testador

```json
{
  "event": "pull_request.opened",
  "pr_number": 45,
  "issue_number": 123,
  "changes": {
    "arquivos_criados": ["fix.py"],
    "arquivos_modificados": ["main.py"]
  }
}
```

### Testador → Desafiador

```json
{
  "event": "issue.testes_passaram",
  "issue_number": 123,
  "pr_number": 45,
  "test_results": {
    "unit": "passed",
    "integration": "passed",
    "coverage": "87%"
  },
  "challenge_context": {
    "attack_categories": ["boundary", "concurrency", "security", "performance"],
    "target_files": ["fix.py", "main.py"],
    "docs_to_verify": ["README.md", "docs/api/*.md"]
  }
}
```

---

## 9. Testes Automatizados

| Tipo | Runner | Critério | Responsável |
|------|---------|----------|-------------|
| Unit | pytest | Coverage > 80% | Testador de Issue |
| Integration | pytest | Scenarios passam | Testador de Issue |
| Lint | ruff/black | Zero erros | Testador de Issue |
| Typecheck | mypy | Zero erros | Testador de Issue |
| **Adversarial** | **custom** | **Zero exploits encontrados** | **Desafiador de Qualidade** |

### 9.1 Testes Adversariais (Desafiador de Qualidade)

| Categoria | Técnica | Sucesso = |
|-----------|---------|-----------|
| Boundary | Valores extremos, null, vazio | Nenhuma falha |
| Concurrency | Race conditions, deadlocks | Nenhum deadlock |
| Security | Fuzzing, injection, bypass | Nenhum exploit |
| Performance | Load test, stress test | <500ms p95 |
| Docs | Verificação docs vs código | 100% consistência |

---

## 10. Métricas de Orquestração

| Métrica | Labels | Descrição |
|---------|---------|-----------|
| `agent.handoff.duration` | source, dest | Tempo entre handoffs |
| `agent.cycle.time` | issue_type | Tempo total create→challenge |
| `agent.success.rate` | agent_type, skill | Taxa de sucesso |
| `agent.test.pass.rate` | issue_type | Pass rate dos testes |
| `agent.challenger.exploits_found` | issue_type, attack_cat | Exploits encontrados |
| `agent.challenger.false_positives` | issue_type | Teorias refutadas |
| `agent.docs.consistency` | issue_type | Docs vs código match % |
| `agent.human.approval.time` | issue_type | Tempo para aprovação humana |
| `agent.issues.created.by_challenger` | issue_type, reason | Issues criadas por desafiador |

---

## 11. Tratamento de Falhas

### 11.1 Se Testador de Issue falha

1. Reabre issue com label `test-failed`
2. Comenta: "❌ Testes falharam: <logs>"
3. Notifica Resolvedor para rework

### 11.2 Se Desafiador de Qualidade encontra bug

1. **CRIA NOVA ISSUE** com label `challenge-exploit`
2. Comenta: "🎯 BUG CRÍTICO: <categoria>\n**Proof of Concept:**\n```python\n<código do exploit>\n```\n**Resultado:** <comportamento inesperado>"
3. Anexa PR com reprodução do bug
4. Notifica Resolvedor para correção imediata
5. **Issue original fica aguardando correção da nova issue**

### 11.3 Se Desafiador de Qualidade encontra docs inconsistentes

1. Cria PR com correção da documentação
2. Comenta: "📚 Docs vs código mismatch:\n- **Doc diz:** X\n- **Código faz:** Y\n- **PR de correção:** #<numero>"
3. Cria issue de acompanhamento para validação após docs atualizadas
4. **Issue original fica aguardando validação da nova issue**

### 11.4 Se Desafiador de Qualidade não encontra problemas

1. Adiciona label `awaiting-approval`
2. Comenta: "✅ Testes adversariais passaram. Aguardando aprovação humana."
3. Issue aguarda aprovação humana
4. Após aprovação humana → Issue → `VERIFIED` → `CLOSED`

---

## 12. Integração

### 12.1 Especificações Relacionadas

- **SPEC008 — AI Agent Interface:** Define contrato técnico de cada agente individual
- **PRD013 — Webhook Autonomous Agents:** Define infraestrutura de webhook e handlers
- **ADR018 — Português Brasileiro:** Requer que textos legíveis estejam em pt-BR

### 12.2 Skills em Plugins

As skills dos agentes (`/create-issue`, `/resolve-issue`, `/test-issue`, `/challenge-quality`) são documentadas em:

```
.agents/repos/claude-code/plugins/skybridge-workflows/
├── .claude-plugin/plugin.json
├── README.md
└── skills/
    ├── create-issue/SKILL.md
    ├── resolve-issue/SKILL.md
    ├── test-issue/SKILL.md
    └── challenge-quality/
        ├── SKILL.md
        └── references/
            ├── attack-categories.md
            └── proof-of-exploit-template.md
```

---

## 13. Agentes Futuros

### 13.1 Agentes Planejados

| Agente | Status | Quando |
|--------|--------|--------|
| Criador de Issue | 🔮 Futuro | Phase 2 |
| Testador de Issue | 🔮 Futuro | Phase 2 |
| Desafiador de Qualidade | 🔮 Futuro | Phase 2 |

**Nota:** Resolvedor de Issue já está implementado em PRD013 Phase 1.

---

## 14. Observações de Implementação

### 14.1 Separação de Responsabilidades

- **SPEC008** define como cada agente funciona tecnicamente (infraestrutura, comunicação, estados)
- **SPEC009** define como agentes se coordenam (sequência, handoffs, transições de issue, métricas)

### 14.2 Estados da Issue vs Estados do Agente

| Conceito | Definido em | Exemplos |
|----------|-------------|-----------|
| **Estados do AGENTE** | SPEC008 | CREATED, RUNNING, COMPLETED, TIMED_OUT, FAILED |
| **Estados da ISSUE** | SPEC009 | OPEN, IN_PROGRESS, READY_FOR_TEST, UNDER_CHALLENGE, AWAITING_HUMAN_APPROVAL, VERIFIED, CLOSED |

Os dois conjuntos de estados são independentes e servem propósitos diferentes.

---

## 15. Roadmap de Implementação

### Phase 1: Foundation (Atual)
- [x] SPEC008 — AI Agent Interface (definição técnica de agentes)
- [x] PRD013 — Webhook Autonomous Agents (infraestrutura de webhook)
- [x] Skill `/resolve-issue` implementado

### Phase 2: Multi-Agente (Planejado)
- [ ] Skill `/create-issue`
- [ ] Skill `/test-issue`
- [ ] Skill `/challenge-quality`
- [ ] Orquestrador de workflow (coordena handoffs entre agentes)
- [ ] Mecanismo de aprovação humana (labels e webhook de comentário)
- [ ] Dashboard de orquestração (status de issues em cada estágio)

### Phase 3: Otimização (Futuro)
- [ ] Auto-triage de issues (classificação automática por tipo)
- [ ] Parallel execution (execução paralela de testes independentes)
- [ ] Learning from failures (melhoria automática de skills baseada em falhas)

---

> "Orquestração é a arte de coordenar talentos individuais em uma sinfonia coletiva." – made by Sky 🎼
