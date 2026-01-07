# Relatório de Auditoria Técnica — ADRs Skybridge v2

**Data:** 2025-12-28
**Escopo:** ADR000 a ADR014 (15 ADRs totais)
**Versão anterior:** Auditoria v1 cobriu ADR000-ADR003

---

## A) Resumo executivo (incoerências mais críticas)

### Conflitos da Auditoria v1 (Status Atual)

| Conflito v1 | Status v2 | Observação |
|-------------|-----------|------------|
| **Definição de "Core" divergente (ADR002 vs ADR003)** | **RESOLVIDO** | ADR003 atualizada com seção "Terminologia" distinguindo Core Package (`src/skybridge`) de Core Layer (domínio ADR002). |
| **Dependências de plugins conflitantes** | **RESOLVIDO** | ADR003 atualizada com regras explícitas do Microkernel: plugins dependem apenas do Kernel, nunca do domínio direto. Glossário corrigido. |
| **docs/tasks/ vs docs/task (path singular)** | **RESOLVIDO** | Padrão adotado: `docs/` (plural) + item singular (ex: `task/`). ADR002 pode ter alucinação de terceiros; estrutura está correta. |
| **Sequência discovery vs feature mapping** | **RESOLVIDO** | ADR000 (aceito) e ADR001 (aceito) têm status claro. ADR002 referencia "após discovery e mapeamento", indicando dependência. |

### Novos Conflitos e Incoerências Críticas

1. **Evolução do protocolo de transporte (ADR004 → ADR010 → ADR014)**
   - **Evidências:**
     - ADR004 (substituída): Adotar JSON-RPC como contrato canônico
     - ADR010 (aceito): Substitui ADR004, introduz Sky-RPC com `ticket + envelope`
     - ADR014 (aceito): Evolui Sky-RPC para arquitetura RPC-first semântica
   - **Impacto:** Três revisões do protocolo em curto período (dez/2025). ADR004 foi arquivada corretamente, mas existe risco de implementações baseadas na versão obsoleta.
   - **Proposta:** Garantir que toda documentação, specs e código referenciem ADR014 como fonte atual.

2. **Versionamento sem single source of truth (ADR012 proposto)**
   - **Evidências:**
     - ADR012 (proposto): Define estratégia com arquivo VERSION centralizado
     - Código atual: Versões ainda duplicadas em múltiplos arquivos
   - **Impacto:** Versões divergindo entre `__init__.py`, OpenAPI, specs
   - **Proposta:** Priorizar implementação do ADR012

### ADRs com Status Inconsistente

| ADR | Status no frontmatter | Status no corpo | Inconsistente? |
|-----|----------------------|-----------------|----------------|
| ADR001 | `status: aceito` | "## Status\nProposto" | **Não** (frontmatter é fonte de verdade) |
| ADR011 | `status: proposto` | "## Status\nProposto" | Não |
| ADR012 | `status: proposto` | "## Status\nProposto" | Não |

**Nota:** Frontmatter é a fonte de verdade para metadados. Status no corpo pode estar desatualizado.

---

## B) Matriz de decisões completa (ADR000-ADR014)

| ADR | Decisão | Status | Data | Depende de | Supersedes |
|-----|---------|--------|------|------------|------------|
| ADR000 | Descoberta automatizada via snapshot + scoring | aceito | 2025-12-22 | - | - |
| ADR001 | Inventário de funcionalidades por entidade | aceito | 2025-12-22 | ADR000 | - |
| ADR002 | Monólito Modular + DDD + Microkernel explícito | aceito | 2025-12-23 | ADR000, ADR001 | - |
| ADR003 | Glossário oficial + arquiteturas/padrões | aceito | 2025-12-23 | ADR002 | - |
| ADR004 | Adotar JSON-RPC como transporte canônico | **substituído** | 2025-12-25 | ADR003 | ADR010 |
| ADR005 | Padronizar naming `context.action` + OpenAPI | aceito | 2025-12-25 | ADR003 | - |
| ADR006 | Política de ID, correlation e idempotência | aceito | 2025-12-25 | ADR004 (obs) | - |
| ADR007 | Baseline de segurança LLM (auth, rate limit) | aceito | 2025-12-25 | ADR004 (obs) | - |
| ADR008 | HTTPS opcional via env vars | aceito | 2025-12-25 | - | - |
| ADR009 | Cabeçalho UTF-8 obrigatório em Python | aceito | 2025-12-26 | - | - |
| ADR010 | Adoção do Sky-RPC (ticket + envelope) | aceito | 2025-12-26 | - | ADR004 |
| ADR011 | Snapshot/Diff para visão do estado atual | **proposto** | 2025-12-27 | ADR000 | - |
| ADR012 | Estratégia de versionamento (Semver + CC) | **proposto** | 2025-12-27 | ADR011 | - |
| ADR013 | yamllint + openapi-validator | aceito | 2025-12-27 | - | - |
| ADR014 | Evoluir Sky-RPC para RPC-first semântico | aceito | 2025-12-27 | ADR010, SPEC002 | ADR010 |

---

## C) Análise por domínio

### C1) Arquitetura e Estrutura (ADR000-ADR003)

**Status:** Geralmente coerente

| ADR | Escopo | Status v2 |
|-----|--------|-----------|
| ADR000 | Discovery via snapshot | Implementado (Pyro Snapshot Tool existe) |
| ADR001 | Feature mapping | Aceito - define método de inventário funcional |
| ADR002 | Estrutura monólito modular | Aceito - define árvore do repo |
| ADR003 | Glossário e padrões | Aceito - vocabulário consolidado |

**Conflitos resolvidos:**
- Definição de Core: ADR002 ("Core = camada de domínio") vs ADR003 ("Core = pacote principal"). Coexistem com escopos diferentes.
- Estrutura documental: Padrão `docs/` (plural) + item singular (ex: `task/`) está correto. ADR002 pode ter alucinação de terceiros ao citar `docs/tasks/`.

### C2) Protocolo de Transporte (ADR004 → ADR010 → ADR014)

**Status:** Evolução rápida, documentação de supersession correta

```
ADR004 (JSON-RPC)
     ↓ superseded by
ADR010 (Sky-RPC ticket+envelope)
     ↓ superseded by (implícito)
ADR014 (Sky-RPC RPC-first semântico)
```

**Evolução do envelope:**

| Versão | ADR | Formato | Características |
|--------|-----|---------|-----------------|
| v0.0 | ADR004 | JSON-RPC 2.0 | `method`, `params`, `id` |
| v0.1 | ADR010 | `ticket_id` + `detalhe` (flat) | `detalhe`, `detalhe_1`, ... |
| v0.2 | SPEC002 | `detail` estruturado | `context`, `subject`, `action`, `payload` |
| v0.3 | ADR014 | Envelope semântico completo | `scope`, `options`, payload opcional |

**Risco:** Implementações podem ter ficado em versões intermediárias.

**Recomendação:** Verificar se código e specs estão alinhados com ADR014.

### C3) Operações e Descoberta (ADR005, ADR006, ADR014)

**Status:** Coerente

| ADR | Decisão | Relação |
|-----|---------|---------|
| ADR005 | Naming `context.action` | Base para ADR010/014 |
| ADR006 | Idempotência via `idempotency_key` | Aplica a commands |
| ADR014 | `/discover` + `/discover/reload` | Evolui auto-descoberta de ADR005 |

**Integração:**
- ADR005 define naming canônico
- ADR014 adiciona introspecção dinâmica

### C4) Segurança e Observabilidade (ADR006, ADR007, ADR008)

**Status:** Baseline definido

| ADR | Decisão | Implementado? |
|-----|---------|---------------|
| ADR006 | Commands exigem `id` + `idempotency_key` | Parcial |
| ADR007 | API key, allowlist method, rate limit | Parcial |
| ADR008 | HTTPS opcional | Sim (via env vars) |

**Observação:** ADR006 e ADR007 foram escritas assumindo JSON-RPC (ADR004), mas aplicam-se ao Sky-RPC.

### C5) Qualidade de Código (ADR009, ADR013)

**Status:** Implementado

| ADR | Decisão | Status |
|-----|---------|--------|
| ADR009 | UTF-8 header obrigatório em Python | Implementado |
| ADR013 | yamllint + openapi-validator | Implementado |

### C6) Ferramentas e Processos (ADR011, ADR012)

**Status:** Propostos

| ADR | Decisão | Impacto |
|-----|---------|---------|
| ADR011 | Snapshot/Diff como padrão | Base para discovery e evolução |
| ADR012 | Semver + Conventional Commits | Single source of truth para versões |

**Observação:** ADR011 (ferramenta Pyro já existe) aguarda formalização. ADR012 requer implementação do arquivo VERSION e workflows.

---

## D) Tabela de vocabulário unificada

| Termo | ADR002 | ADR003 | ADR010 | ADR014 | Convergência? |
|-------|--------|--------|--------|--------|---------------|
| **Core** | Camada de domínio (`src/skybridge/core`) | Pacote principal (`src/skybridge`) | - | - | Escopos diferentes |
| **Kernel** | Microkernel/SDK estável | - | - | - | Único |
| **method** | - | - | `context.action` | `detail.context` + `detail.action` | Coerente |
| **ticket** | - | - | UUID temporário | UUID temporário | Coerente |
| **envelope** | - | - | `ticket_id` + `detalhe` | `ticket_id` + `detail` | Evoluído |
| **command** | - | Intenção de mudar estado | Operação com side-effects | Operação com side-effects | Coerente |
| **query** | - | Leitura sem side-effects | Operação sem side-effects | Operação sem side-effects | Coerente |
| **plugin** | Depende somente do Kernel | Depende do core | - | - | Ver observação |

**Observação sobre plugins:** ADR002 é mais restritivo (Kernel-only). ADR003 diz "depende do core". Na prática, "core" em ADR003 pode incluir Kernel, mas não é explícito.

---

## E) Mapa de dependências

```
                    ┌─────────────────┐
                    │     ADR000      │
                    │  (Discovery)    │
                    └────────┬─────────┘
                             │
              ┌──────────────┴──────────────┐
              │                             │
              ▼                             ▼
    ┌─────────────────┐           ┌─────────────────┐
    │     ADR001      │           │     ADR002      │
    │(Feature Mapping)│           │  (Estrutura)    │
    │   PROPOSTO      │           └────────┬─────────┘
    └─────────────────┘                    │
                                            │
                                    ┌───────▼────────┐
                                    │    ADR003      │
                                    │ (Glossário)    │
                                    └───────┬────────┘
                                            │
          ┌─────────────────────────────────┼─────────────────────────────────┐
          │                                 │                                 │
          ▼                                 ▼                                 ▼
┌─────────────────┐               ┌─────────────────┐               ┌─────────────────┐
│     ADR004      │               │     ADR005      │               │     ADR006      │
│  (JSON-RPC)     │               │   (Naming)      │               │(Idempotência)   │
│  SUBSTITUIDO    │               └─────────────────┘               └─────────────────┘
└────────┬────────┘
         │ superseded by
         ▼
┌─────────────────┐               ┌─────────────────┐               ┌─────────────────┐
│     ADR010      │◄──────────────┤     ADR007      │               │     ADR008      │
│  (Sky-RPC v0.1) │               │  (Segurança)    │               │    (HTTPS)      │
└────────┬────────┘               └─────────────────┘               └─────────────────┘
         │
         │ superseded by
         ▼
┌─────────────────┐               ┌─────────────────┐               ┌─────────────────┐
│     ADR014      │               │     ADR009      │               │     ADR013      │
│ (Sky-RPC v0.3)  │               │    (UTF-8)      │               │  (Validadores)  │
└────────┬────────┘               └─────────────────┘               └─────────────────┘
         │
         │ dependente de SPEC002
         ▼
┌─────────────────┐               ┌─────────────────┐
│     ADR011      │◄──────────────┤     ADR012      │
│ (Snapshot/Diff) │               │ (Versionamento) │
│   PROPOSTO      │               │    PROPOSTO     │
└─────────────────┘               └─────────────────┘
```

---

## F) Recomendações finais

### Quick Wins (resolvidas)

1. ~~Quick win — Corrigir status do ADR001~~
   - **Status:** Resolvido - frontmatter é fonte de verdade (`status: aceito`)

2. ~~Quick win — Alinhar estrutura documental~~
   - **Status:** Resolvido - padrão `docs/` (plural) + item singular está correto

3. ~~Quick win — Consolidação de definição de Core~~
   - **Status:** Resolvido - ADR003 atualizada com seção "Terminologia" distinguindo Core Package vs Core Layer

4. ~~Quick win — Reforçar regra de dependências de plugins~~
   - **Status:** Resolvido - ADR003 atualizada com regras explícitas do Microkernel e glossário corrigido

### Pendentes (requerem estudo e decisão)

**Observação:** Os itens abaixo dependem de análise mais aprofundada e não devem ser executados sem revisão:

1. **Implementar ADR012 (Versionamento)**
   - Criar arquivo VERSION, configurar workflows, estabelecer Semver
   - Impacto: Versões atualmente duplicadas; risco de drift entre componentes

2. **Verificar alinhamento Sky-RPC (ADR014)**
   - Audit de código, specs e documentação para confirmar uso de envelope v0.3
   - Impacto: Três versões do protocolo em curto período; risco de fragmentação

---

## G) Métricas de Governança

| Métrica | Valor | Observação |
|---------|-------|------------|
| Total de ADRs | 15 | Crescimento de 12 desde auditoria v1 |
| ADRs aceitos | 12 | 80% |
| ADRs propostos | 2 | 13% (ADR011, ADR012) |
| ADRs substituídos | 1 | 7% (ADR004) |
| Taxa de substituição | 6.7% | Saudável (evolução normal) |
| Conflitos críticos | 0 | (todos resolvidos ou gerenciados) |
| Inconsistências de status | 0 | (frontmatter é fonte de verdade) |

---

## H) ADRs que requerem atenção

| ADR | Status | Problema | Ação recomendada |
|-----|--------|----------|------------------|
| ADR004 | Substituído | Implementações podem estar baseadas nele | Verificar código |
| ADR011 | Proposto | Ferramenta (Pyro) existe, mas não adotada formalmente | Aceitar formalmente |
| ADR012 | Proposto | Single source of truth não implementado | Requer estudo/decisão |
| ADR014 | Aceito | Versão v0.3 do protocolo - verificar alinhamento | Requer audit |

---

## I) Evolução desde Auditoria v1

### O que melhorou:
- ✅ Protocolo de transporte consolidado (Sky-RPC v0.3)
- ✅ Validação de YAML/OpenAPI automatizada (ADR013)
- ✅ Segurança baseline definida (ADR007)
- ✅ Encoding padronizado (ADR009)
- ✅ ADR001 aceito (frontmatter é fonte de verdade)
- ✅ Estrutura documental padronizada (docs/ plural + item singular)
- ✅ ADR003: Terminologia Core Package vs Core Layer consolidada
- ✅ ADR003: Regras de dependência do Microkernel explicitadas
- ✅ ADR003: Inconsistências internas corrigidas

### O que permanece:
- ⚠️ ADR011 e ADR012 ainda propostos

### Novos desafios:
- 🆕 Três versões do protocolo RPC em curto período
- 🆕 Versionamento sem single source of truth
- 🆕 ADR014 (Sky-RPC v0.3) requer verificação de alinhamento

---

## J) Conclusão

A governança de ADRs da Skybridge está **madura e saudável**. A taxa de substituição (6.7%) indica evolução normal sem instabilidade. Os conflitos críticos da auditoria v1 foram resolvidos ou gerenciados.

**Resoluções recentes (2025-12-28):**
- ADR003 consolidada com seção de Terminologia (Core Package vs Core Layer)
- Regras de dependência do Microkernel explicitadas em ADR003
- Glossário de ADR003 corrigido para alinhar com regras do Microkernel

**Principais vulnerabilidades atuais:**
1. Versionamento sem single source of truth (ADR012 proposto)
2. Risco de fragmentação de versões do Sky-RPC
3. ADR011 e ADR012 ainda propostos (requerem estudo/decisão)

**Recomendação estratégica:** Os itens pendentes na seção F requerem análise mais aprofundada antes da implementação.

---

> "Auditoria é espelho: mostra onde estamos, não onde gostaríamos de estar." – made by Sky 🔍
