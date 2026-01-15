# Guia de Pesquisa: QA Loop - Auto-Claude → Skybridge

**Data:** 2026-01-14
**Analista:** Sky
**Objetivo:** Pesquisa profunda para implementar o recurso de QA Loop do Auto-Claude na Skybridge

---

## 1. Visão Geral do QA Loop

### 1.1 Conceito

O **QA Loop** (Quality Assurance Loop) é um sistema de validação automática e self-correcting que:

1. **Valida** implementações contra acceptance criteria
2. **Detecta** bugs, vulnerabilidades e regressões
3. **Aplica correções** automaticamente
4. **Revalida** até aprovação ou limite de iterações
5. **Escalona** para humanos quando necessário

**Princípio Chave:** "You are the last line of defense. If you approve, feature ships."

---

### 1.2 Arquitetura de Auto-Claude

```
┌─────────────────────────────────────────────────────────────────┐
│              Build Completa (Coders)                    │
└──────────────────────┬──────────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────────────┐
│         QA Validation Loop (qa/loop.py)                  │
│                                                              │
│  ┌──────────────────────────────────────────────────────┐    │
│  │  Iteration 1│  │  Iteration N │    │
│  └──┬──────────────────┬───────────────────┘    │
│       │                  │                         │
│       ▼                  ▼                         │
│  ┌──────────────┐    ┌──────────────┐           │
│  │ QA Reviewer │    │ QA Fixer  │   (Loop)    │
│  │ (reviewer.py)│    │ (fixer.py)   │           │
│  └──────┬───────┘    └──────┬───────┘           │
│         │                     │                         │
│         │                     ▼                         │
│         │              ┌─────────────────┐               │
│         │              │  Fixed Issues │               │
│         │              └───────┬───────┘               │
│         │                      │                         │
│         ▼                      ▼                         │
│  ┌──────────────────────────────────────────────┐           │
│  │  Approved?                                     │           │
│  │    ├── YES → Sign-off (Pronto para merge)    │           │
│  │    └── NO → Re-validar              │           │
│  └──────────────────────────────────────────────┘           │
│                        │                                     │
│                        ▼                                     │
│              ┌─────────────────────────────┐                │
│              │  Max Iterations?        │                │
│              │    └── YES → Escalate          │                │
│              │       (Human Review)        │                │
│              └─────────────────────────────┘                │
└─────────────────────────────────────────────────────────────────┘
```

---

## 2. Componentes Principais

### 2.1 QA Loop Orchestrator (`qa/loop.py`)

**Responsabilidades:**
- Coordenar loop de iterações (max: 50)
- Gerenciar estados de QA (pending, in_progress, approved, rejected)
- Controlar consecutive errors (max: 3)
- Emitir eventos de fase (QA_REVIEW, QA_FIXING, COMPLETE, FAILED)
- Integrar com Linear (opcional)

**Funções Principais:**

```python
async def run_qa_validation_loop(
    project_dir: Path,
    spec_dir: Path,
    model: str,
    verbose: bool = False,
) -> bool:
    """
    Loop principal de QA.

    Retorna: True se aprovado, False caso contrário
    """
    # 1. Verifica se build está completa
    # 2. Processa feedback humano (se existir)
    # 3. Detecta projetos sem testes
    # 4. Inicia loop de iterações
    #    4.1. Executa QA Reviewer
    #    4.2. Se rejeitado → Executa QA Fixer
    #    4.3. Detecta issues recorrentes
    #    4.4. Escalona se necessário
    #    4.5. Se aprovado → Sign-off
    # 5. Atualiza Linear (se habilitado)
```

**Constants de Configuração:**
- `MAX_QA_ITERATIONS = 50` - Máximo de iterações
- `MAX_CONSECUTIVE_ERRORS = 3` - Erros consecutivos sem progresso

---

### 2.2 QA Reviewer Agent (`qa/reviewer.py`)

**Responsabilidades:**
- Carregar contexto de memória (Graphiti)
- Validar acceptance criteria completas
- Executar testes automatizados (unit, integration, E2E)
- Verificar segurança, padrões, regressões
- Gerar relatório de QA (`qa_report.md`)
- Atualizar `implementation_plan.json` com status

**Funções Principais:**

```python
async def run_qa_agent_session(
    client: ClaudeSDKClient,
    project_dir: Path,
    spec_dir: Path,
    qa_session: int,
    max_iterations: int,
    verbose: bool = False,
    previous_error: dict | None = None,  # Para auto-correção
) -> tuple[str, str]:
    """
    Executa sessão de QA reviewer.

    Retorna: (status, response_text)
    - status: "approved", "rejected", ou "error"
    - response_text: Conteúdo da resposta do agente
    """
    # 1. Carrega prompt com tools dinâmicos (Electron, Puppeteer, etc)
    # 2. Recupera contexto de memória (Graphiti)
    # 3. Executa query com Claude SDK
    # 4. Stream resposta em tempo real
    # 5. Verifica se implement_plan.json foi atualizado
    # 6. Salva descobertas na memória
```

**Prompt Estrutura (`prompts/qa_reviewer.md`):**

```
## PHASE 0: LOAD CONTEXT (MANDATORY)
- spec.md
- implementation_plan.json
- project_index.json
- build-progress.txt
- git diff
- acceptance criteria

## PHASE 1: VERIFY ALL SUBTASKS COMPLETED
- Contagem de subtasks: completed/pending/in_progress

## PHASE 2: START DEVELOPMENT ENVIRONMENT
- Inicia serviços (init.sh)
- Verifica healthy status

## PHASE 3: RUN AUTOMATED TESTS
### 3.1: Unit Tests
- Executa unit tests para serviços afetados
- Documenta resultados: PASS/FAIL (X/Y)

### 3.2: Integration Tests
- Executa testes de integração entre serviços
- Documenta resultados: PASS/FAIL (X/Y)

### 3.3: End-to-End Tests
- Executa E2E tests (Playwright, Cypress, etc.)
- Usa browser automation
- Documenta resultados: PASS/FAIL (X/Y)

## PHASE 4: BROWSER VERIFICATION (Se Frontend)
### 4.1: Navigate and Screenshot
- Navega para URL
- Tira screenshot
- Verifica visual elements
- Testa interações

### 4.2: Console Error Check
- Verifica erros JavaScript
- Verifica warnings
- Verifica network requests falhadas

## PHASE 5: DATABASE VERIFICATION (Se Aplicável)
### 5.1: Check Migrations
- Verifica se migrations existem e foram aplicadas

### 5.2: Verify Schema
- Verifica schema do banco de dados

## PHASE 6: CODE REVIEW
### 6.0: Third-Party API/Library Validation (Use Context7)
- Valida uso de bibliotecas contra docs oficiais
- Verifica assinaturas de funções
- Verifica patterns de inicialização

### 6.1: Security Review
- Busca vulnerabilidades comuns (eval, innerHTML, exec, shell)
- Busca secrets hardcoded (password, api_key, token)

### 6.2: Pattern Compliance
- Verifica compliance com padrões estabelecidos

## PHASE 7: REGRESSION CHECK
### 7.1: Run Full Test Suite
- Executa TODOS os testes, não apenas novos

### 7.2: Check Key Existing Functionality
- Verifica que features existentes não foram quebradas

## PHASE 8: GENERATE QA REPORT
- Tabela resumo por categoria
- Lista de issues encontradas (Critical, Major, Minor)
- Recommended fixes

## PHASE 9: UPDATE IMPLEMENTATION PLAN
### Se APROVADO:
```json
{
  "qa_signoff": {
    "status": "approved",
    "timestamp": "[ISO timestamp]",
    "qa_session": [session-number],
    "report_file": "qa_report.md",
    "tests_passed": {
      "unit": "X/Y",
      "integration": "X/Y",
      "e2e": "X/Y"
    },
    "verified_by": "qa_agent"
  }
}
```

### Se REJEITADO:
```json
{
  "qa_signoff": {
    "status": "rejected",
    "timestamp": "[ISO timestamp]",
    "qa_session": [session-number],
    "issues_found": [
      {
        "type": "critical",
        "title": "[issue]",
        "location": "[file:line]",
        "fix_required": "[description]"
      }
    ],
    "fix_request_file": "QA_FIX_REQUEST.md"
  }
}
```
```

---

### 2.3 QA Fixer Agent (`qa/fixer.py`)

**Responsabilidades:**
- Ler `QA_FIX_REQUEST.md` (issues a corrigir)
- Aplicar fixes uma por uma
- Verificar cada fix localmente
- Executar testes após cada fix
- Atualizar `implementation_plan.json` com status `fixes_applied`
- Não introduzir novos bugs

**Funções Principais:**

```python
async def run_qa_fixer_session(
    client: ClaudeSDKClient,
    spec_dir: Path,
    fix_session: int,
    verbose: bool = False,
    project_dir: Path | None = None,
) -> tuple[str, str]:
    """
    Executa sessão de QA fixer.

    Retorna: (status, response_text)
    - status: "fixed" ou "error"
    - response_text: Conteúdo da resposta
    """
    # 1. Verifica que QA_FIX_REQUEST.md existe
    # 2. Carrega prompt do fixer
    # 3. Recupera contexto de memória (Graphiti)
    # 4. Executa query com Claude SDK
    # 5. Aplica fixes uma por uma
    # 6. Verifica cada fix
    # 7. Atualiza implementation_plan.json
```

**Prompt Estrutura (`prompts/qa_fixer.md`):**

```
## PHASE 0: LOAD CONTEXT (MANDATORY)
- QA_FIX_REQUEST.md (issues a corrigir)
- qa_report.md (contexto completo dos issues)
- spec.md (requisitos)
- implementation_plan.json (qa_signoff status)

## PHASE 1: PARSE FIX REQUIREMENTS
- Extrai lista de issues de QA_FIX_REQUEST.md
- Para cada issue: título, localização, problema, fix esperado

## PHASE 2: START DEVELOPMENT ENVIRONMENT
- Inicia serviços se necessário

## 🚨 CRITICAL: PATH CONFUSION PREVENTION 🚨
- O agente SEMPRE deve verificar cwd antes de comandos
- Usa caminhos relativos se estiver em subdiretório
- Verifica que arquivos existem antes de operar

## PHASE 3: FIX ISSUES ONE BY ONE
- Para cada issue:
  1. Ler arquivo/área do problema
  2. Entender o que está errado
  3. Implementar fix mínimo necessário
  4. Não refatorar código ao redor
  5. Não adicionar features
  6. Testar fix localmente

## PHASE 4: RUN TESTS
- Executa full test suite após todos os fixes
- Executa testes específicos que falharam

## PHASE 5: SELF-VERIFICATION
- Verifica cada fix da QA_FIX_REQUEST.md
- Confirma que issue foi resolvido

## PHASE 6: COMMIT FIXES
- Atualiza implementation_plan.json:
```json
{
  "qa_signoff": {
    "status": "fixes_applied",
    "timestamp": "[ISO timestamp]",
    "fix_session": [session-number],
    "issues_fixed": [
      {
        "title": "[issue title]",
        "fix_commit": "[commit hash]"
      }
    ],
    "ready_for_qa_revalidation": true
  }
}
```

## COMMON FIX PATTERNS
- Missing Migration
- Failing Test
- Console Error
- Security Issue
- Pattern Violation
```

---

### 2.4 Criteria & Status Management (`qa/criteria.py`)

**Responsabilidades:**
- Gerenciar acceptance criteria
- Ler/escrever `implementation_plan.json`
- Determinar se QA deve rodar
- Verificar status atual (approved/rejected/fixes_applied)

**Funções Principais:**

```python
# Status Checks
def is_qa_approved(spec_dir: Path) -> bool:
    """QA aprovou build?"""
    return qa_signoff.get("status") == "approved"

def is_qa_rejected(spec_dir: Path) -> bool:
    """QA rejeitou build (precisa de fixes)?"""
    return qa_signoff.get("status") == "rejected"

def is_fixes_applied(spec_dir: Path) -> bool:
    """Fixes foram aplicados e pronto para re-validação?"""
    return qa_signoff.get("status") == "fixes_applied"

# Readiness Checks
def should_run_qa(spec_dir: Path) -> bool:
    """QA deve rodar?"""
    return is_build_complete(spec_dir) and not is_qa_approved(spec_dir)

def should_run_fixes(spec_dir: Path) -> bool:
    """QA fixer deve rodar?"""
    return is_qa_rejected(spec_dir) and iterations < MAX_QA_ITERATIONS

# Iteration Counting
def get_qa_iteration_count(spec_dir: Path) -> int:
    """Quantas iterações de QA já rodaram?"""
    return qa_signoff.get("qa_session", 0)

# Status Display
def print_qa_status(spec_dir: Path) -> None:
    """Imprime status atual de QA"""
```

---

### 2.5 Report & Issue Tracking (`qa/report.py`)

**Responsabilidades:**
- Rastrear histórico de iterações
- Detectar issues recorrentes (3+ ocorrências)
- Calcular similaridade entre issues (threshold: 0.8)
- Criar relatórios de escalonamento (`QA_ESCALATION.md`)
- Criar planos de teste manual (`MANUAL_TEST_PLAN.md`)

**Funções Principais:**

```python
# Iteration History
def get_iteration_history(spec_dir: Path) -> list[dict]:
    """Retorna histórico completo de iterações"""

def record_iteration(
    spec_dir: Path,
    iteration: int,
    status: str,  # "approved", "rejected", "error"
    issues: list[dict],
    duration_seconds: float | None = None,
) -> bool:
    """Registra iteração no histórico"""

# Recurring Issue Detection
def has_recurring_issues(
    current_issues: list[dict],
    history: list[dict],
    threshold: int = 3,
) -> tuple[bool, list[dict]]:
    """
    Detecta issues que aparecem 3+ vezes.

    Usa SequenceMatcher para similaridade (threshold: 0.8)
    """

def _normalize_issue_key(issue: dict) -> str:
    """
    Cria chave normalizada: "titulo|arquivo|linha"

    Remove prefixos comuns: "error:", "issue:", "bug:", "fix:"
    """

def _issue_similarity(issue1: dict, issue2: dict) -> float:
    """
    Calcula similaridade entre dois issues.

    Combina título + localização.
    Retorna score 0.0-1.0.
    """

def get_recurring_issue_summary(history: list[dict]) -> dict:
    """
    Analisa histórico para issues mais comuns.

    Retorna:
    - total_issues: Total de issues encontradas
    - unique_issues: Issues únicas
    - most_common: Top 5 issues mais comuns
    - iterations_approved/rejected
    - fix_success_rate
    """

# Escalation
async def escalate_to_human(
    spec_dir: Path,
    recurring_issues: list[dict],
    iteration: int,
) -> None:
    """
    Cria QA_ESCALATION.md quando issues recorrem.
    """

# No-Test Project
def is_no_test_project(spec_dir: Path, project_dir: Path) -> bool:
    """
    Detecta se projeto NÃO tem infraestrutura de testes.

    Se true, cria MANUAL_TEST_PLAN.md.
    """

def create_manual_test_plan(spec_dir: Path, spec_name: str) -> Path:
    """
    Cria plano de teste manual quando sem automação.
    """
```

---

### 2.6 Acceptance Criteria (Definidos em spec.md)

Exemplo de critérios de aceitação em spec:

```markdown
## QA Acceptance Criteria

### 1. Core Functionality
- [ ] Feature works as described in spec
- [ ] All edge cases handled
- [ ] Error states display appropriate messages

### 2. Testing
- [ ] Unit tests pass (80%+ coverage)
- [ ] Integration tests pass
- [ ] E2E tests pass (for UI projects)

### 3. Code Quality
- [ ] No console errors
- [ ] No warnings
- [ ] Follows project patterns
- [ ] No hardcoded secrets

### 4. Security
- [ ] Input sanitization implemented
- [ ] No SQL injection vulnerabilities
- [ ] No XSS vulnerabilities
- [ ] Authentication/authorization correct

### 5. Performance
- [ ] Response time < 500ms (for APIs)
- [ ] No excessive memory usage
- [ ] No memory leaks

### 6. Documentation
- [ ] API documented (OpenAPI/Swagger)
- [ ] README updated
- [ ] Inline code comments for complex logic
```

---

### 2.7 Memory Integration (Graphiti)

**Responsabilidades:**
- Recuperar contexto de sessões anteriores
- Salvar descobertas de QA (patterns, gotchas, issues)
- Indexar por embeddings (busca semântica)
- Disponibilizar para próximas sessões

**Funções (em `agents/memory_manager.py`):**

```python
async def get_graphiti_context(
    spec_dir: Path,
    project_dir: Path,
    context_request: dict,
) -> str:
    """
    Recupera contexto de Graphiti para sessão.

    Retorna: String com contexto relevante
    """

async def save_session_memory(
    spec_dir: Path,
    project_dir: Path,
    subtask_id: str,
    session_num: int,
    success: bool,
    subtasks_completed: list[str],
    discoveries: dict,
) -> bool:
    """
    Salva memória da sessão no Graphiti.

    discoveries: {
      "files_understood": {},
      "patterns_found": ["Pattern 1", "Pattern 2"],
      "gotchas_encountered": ["Gotcha 1", "Gotcha 2"]
    }
    """
```

**Tipos de Descobertas Salvas:**
- **Patterns**: Padrões de código e arquitetura
- **Gotchas**: Armadilhas e pitfalls encontrados
- **Files Understood**: Arquivos lidos e compreendidos

---

### 2.8 E2E Testing (Electron MCP)

**Habilitado quando:**
- `ELECTRON_MCP_ENABLED=true` no `.env`
- Projeto detectado como Electron

**Ferramentas Disponíveis (injetadas automaticamente no prompt):**

```
# MCP: Electron (para apps Electron)
mcp__electron__get_electron_window_info
mcp__electron__take_screenshot
mcp__electron__send_command_to_electron

Comandos disponíveis via send_command_to_electron:
- click_by_text - Clica botão por texto visível
- click_by_selector - Clica elemento por CSS selector
- fill_input - Preenche campo (placeholder ou selector)
- select_option - Seleciona dropdown
- send_keyboard_shortcut - Envia atalho (Enter, Ctrl+N, etc)
- navigate_to_hash - Navega para rota (#settings, #create)
- get_page_structure - Estrutura organizada da página
- verify_form_state - Verifica estado de formulário
- eval - Executa JavaScript arbitrário
```

**Fluxo E2E Típico:**

```python
# 1. QA toma screenshot
agent: "Take a screenshot to see the current UI"
# Usa: mcp__electron__take_screenshot

# 2. QA inspeciona página
agent: "Get page structure to find available buttons"
# Usa: mcp__electron__send_command_to_electron (command: "get_page_structure")

# 3. QA clica botão
agent: "Click the 'Create New Spec' button"
# Usa: mcp__electron__send_command_to_electron (
#      command: "click_by_text",
#      args: {"text": "Create New Spec"}
# )

# 4. QA preenche formulário
agent: "Fill the task description field"
# Usa: mcp__electron__send_command_to_electron (
#      command: "fill_input",
#      args: {"placeholder": "Describe your task", "value": "Add login feature"}
# )

# 5. QA submete e verifica
agent: "Click Submit and verify success"
# Usa: click_by_text + take_screenshot
```

---

## 3. Fluxo Completo de Execução

### 3.1 Inicialização

```
1. Coder Agent completa todos subtasks
2. Build marked as "complete"
3. QA Loop iniciado automaticamente
4. Verifica se já aprovado (skip se sim)
5. Verifica feedback humano (QA_FIX_REQUEST.md)
```

### 3.2 Iteração de QA

```
Iteração N:
├── 1. Carregar contexto
│    ├── spec.md
│    ├── implementation_plan.json
│    ├── project_index.json
│    ├── Graphiti memory (patterns, gotchas)
│    └── previous_error (se falhou antes)
│
├── 2. Executar QA Reviewer
│    ├── Phase 0: Load Context
│    ├── Phase 1: Verify subtasks
│    ├── Phase 2: Start services
│    ├── Phase 3: Run tests
│    │    ├── Unit tests
│    │    ├── Integration tests
│    │    └── E2E tests (Electron MCP)
│    ├── Phase 4: Browser verification (se aplicável)
│    ├── Phase 5: Database verification (se aplicável)
│    ├── Phase 6: Code review
│    ├── Phase 7: Regression check
│    ├── Phase 8: Generate QA report
│    └── Phase 9: Update implementation_plan.json
│
├── 3. Checar resultado
│    ├── Se approved → Sign-off (termina)
│    ├── Se rejected → Ir para QA Fixer
│    └── Se error → Auto-correção na próxima iteração
│
└── 4. Detectar issues recorrentes
     ├── Se 3+ ocorrências → Escalonar para humano
     └── Criar QA_ESCALATION.md
```

### 3.3 Iteração de Fixer

```
Se QA rejeitou:
├── 1. Carregar contexto
│    ├── QA_FIX_REQUEST.md (issues a corrigir)
│    ├── qa_report.md (detalhes dos issues)
│    ├── spec.md (requisitos)
│    └── Graphiti memory (fixes anteriores)
│
├── 2. Executar QA Fixer
│    ├── Phase 0: Load Context
│    ├── Phase 1: Parse fix requirements
│    ├── Phase 2: Start services
│    ├── Phase 3: Fix issues one by one
│    ├── Phase 4: Run tests
│    ├── Phase 5: Self-verification
│    ├── Phase 6: Commit fixes
│    └── Phase 7: Update implementation_plan.json
│
└── 3. Loop volta para QA Reviewer
```

### 3.4 Escalonamento

```
Critérios de Escalonamento:
├── 3+ ocorrências do mesmo issue (similarity >= 0.8)
├── Max iterações atingida (50)
└── Erros consecutivos sem progresso (3)

Ações ao Escalonar:
├── Criar QA_ESCALATION.md com:
│    ├── Lista de issues recorrentes
│    ├── Contagem de iterações
│    ├── Taxa de sucesso de fixes
│    └── Issues mais comuns (top 5)
│
├── Atualizar Linear (se habilitado):
│    ├── "QA max iterations reached"
│    └── "Needs human intervention"
│
└── Terminar QA loop com status "failed"
```

---

## 4. Estrutura de Arquivos

### 4.1 Diretório de Spec

```
.auto-claude/specs/XXX-feature/
├── spec.md                          # Especificação original
├── implementation_plan.json            # Plano de implementação
│   ├── phases: [...]
│   ├── qa_signoff: {
│   │   ├── status: "approved" | "rejected" | "fixes_applied"
│   │   ├── timestamp: "2026-01-14T..."
│   │   ├── qa_session: 5
│   │   ├── tests_passed: {unit, integration, e2e}
│   │   ├── issues_found: [...]
│   │   └── report_file: "qa_report.md"
│   ├── qa_iteration_history: [...]     # Histórico completo
│   └── qa_stats: {
│       ├── total_iterations: 5
│       ├── last_iteration: 5
│       ├── last_status: "approved"
│       └── issues_by_type: {critical: 2, major: 3, minor: 5}
├── qa_report.md                   # Relatório de QA
├── QA_FIX_REQUEST.md              # Issues para corrigir (se rejeitado)
├── QA_ESCALATION.md              # Escalonamento (se recorrente)
└── MANUAL_TEST_PLAN.md            # Plano manual (sem testes)
```

---

## 5. Integrações Externas

### 5.1 Linear (Opcional)

**Funções (`linear_updater.py`):**

```python
# Estados de Linear
async def linear_qa_started(spec_dir: Path):
    """Move task para "In Review" no Linear"""

async def linear_qa_approved(spec_dir: Path):
    """Move task para "QA Approved, Awaiting Human Review" no Linear"""

async def linear_qa_rejected(spec_dir: Path, issues_count: int, iteration: int):
    """Move task para "Rejected" no Linear com contagem de issues"""

async def linear_qa_max_iterations(spec_dir: Path, iteration: int):
    """Move task para "Needs Human Intervention (Recurring Issues)" no Linear"""

class LinearTaskState:
    """Classe para carregar/linear-task.json"""
    task_id: str
    state: str
    last_updated: str
```

---

## 6. Diferenças para Skybridge

### 6.1 O que Skybridge JÁ TEM

| Componente | Auto-Claude | Skybridge | Gap |
|------------|-------------|-----------|------|
| **Worktree Management** | ✅ Sim | ✅ Sim | Nenhuma |
| **Snapshot Captura** | ✅ Sim (não integrado) | ✅ Sim (GitExtractor) | Skybridge mais robusto |
| **Job Queue** | ✅ Sim | ✅ Sim | Similar |
| **Agent Framework** | ✅ Sim (SDK) | ✅ Sim (ClaudeCodeAdapter) | Similar |
| **Memory** | ✅ Graphiti | ❌ Não | Completo |

---

### 6.2 O que Skybridge NÃO TEM (GAP)

| Componente | Auto-Claude | Skybridge | Gap |
|------------|-------------|-----------|------|
| **QA Loop** | ✅ Completo | ❌ Não | CRÍTICO |
| **QA Reviewer Agent** | ✅ Sim | ❌ Não | CRÍTICO |
| **QA Fixer Agent** | ✅ Sim | ❌ Não | CRÍTICO |
| **Criteria Management** | ✅ Sim | ❌ Não | ALTO |
| **Iteration History** | ✅ Sim | ❌ Não | ALTO |
| **Recurring Issues Detection** | ✅ Sim | ❌ Não | ALTO |
| **Escalation Logic** | ✅ Sim | ❌ Não | ALTO |
| **E2E Testing** | ✅ Electron MCP | ❌ Não | MÉDIO |
| **Memory Integration** | ✅ Graphiti | ❌ Não | MÉDIO |
| **Linear Integration** | ✅ Sim | ❌ Não | BAIXO |
| **No-Test Handling** | ✅ Sim | ❌ Não | BAIXO |
| **Manual Test Plans** | ✅ Sim | ❌ Não | BAIXO |

---

## 7. Guia de Implementação - Skybridge

### 7.1 Estrutura Sugerida

```
src/skybridge/core/contexts/qa/
├── __init__.py                    # Export público
├── loop.py                        # Orquestrador principal
├── reviewer.py                    # Agente QA reviewer
├── fixer.py                      # Agente QA fixer
├── criteria.py                   # Gerenciamento de critérios
├── report.py                     # Rastreamento e relatórios
└── prompts/
    ├── qa_reviewer.md            # Prompt do reviewer
    └── qa_fixer.md              # Prompt do fixer

src/skybridge/core/contexts/validation/
├── __init__.py
├── acceptance_criteria.py        # Definição de critérios
└── test_runner.py             # Runner de testes (unit, integration)
```

---

### 7.2 Arquitetura de Componentes

#### 7.2.1 QA Loop Orchestrator (`qa/loop.py`)

```python
"""
QA Validation Loop - Skybridge Adaptation
=====================================

Orquestra validação de QA até aprovação ou limite.
"""

from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from skybridge.core.contexts.webhooks.ports.job_queue_port import JobQueuePort
    from skybridge.core.contexts.webhooks.domain.webhook_job import WebhookJob

from skybridge.kernel.contracts.result import Result
from skybridge.platform.observability.logger import get_logger


# Configuração
MAX_QA_ITERATIONS = 50
MAX_CONSECUTIVE_ERRORS = 3


class QALoopOrchestrator:
    """
    Orquestrador do QA Loop.

    Responsabilidades:
    - Coordenar iterações de QA
    - Gerenciar reviewer e fixer
    - Rastrear histórico
    - Detectar issues recorrentes
    - Escalonar para humanos
    """

    def __init__(
        self,
        job_queue: "JobQueuePort",
        agent_adapter,  # ClaudeCodeAdapter
        project_dir: Path,
    ):
        self.job_queue = job_queue
        self.agent_adapter = agent_adapter
        self.project_dir = project_dir
        self.logger = get_logger()

    async def run_qa_validation_loop(
        self,
        spec_dir: Path,
        job: WebhookJob,
        model: str = "sonnet",
        max_iterations: int = MAX_QA_ITERATIONS,
    ) -> Result[bool, str]:
        """
        Executa loop completo de QA.

        Retorna: Result com sucesso/fracasso e mensagem
        """
        # 1. Verificar se build está completa
        # 2. Iniciar iterações
        # 3. Para cada iteração:
        #    3.1. Executar QA Reviewer
        #    3.2. Se approved → sign-off
        #    3.3. Se rejected → QA Fixer
        #    3.4. Se error → auto-correção
        #    3.5. Detectar issues recorrentes
        # 4. Escalonar se necessário

        pass  # Implementação detalhada abaixo

    async def _run_qa_reviewer(
        self,
        spec_dir: Path,
        iteration: int,
        job: WebhookJob,
        previous_error: dict | None = None,
    ) -> Result[bool, str]:
        """
        Executa agente QA reviewer.
        """
        pass

    async def _run_qa_fixer(
        self,
        spec_dir: Path,
        iteration: int,
        job: WebhookJob,
    ) -> Result[bool, str]:
        """
        Executa agente QA fixer.
        """
        pass

    def _should_escalate(
        self,
        current_issues: list[dict],
        history: list[dict],
    ) -> tuple[bool, list[dict]]:
        """
        Verifica se deve escalonar (3+ ocorrências).
        """
        pass

    async def _escalate_to_human(
        self,
        spec_dir: Path,
        recurring_issues: list[dict],
        iteration: int,
    ) -> None:
        """
        Cria arquivo de escalonamento.
        """
        pass
```

---

#### 7.2.2 QA Reviewer Agent (`qa/reviewer.py`)

```python
"""
QA Reviewer Agent - Skybridge Adaptation
======================================

Valida implementação contra acceptance criteria.
"""

from pathlib import Path
from skybridge.core.client import create_client  # Ajustar conforme Skybridge
from skybridge.kernel.contracts.result import Result


async def run_qa_reviewer_session(
    client,  # ClaudeSDKClient
    project_dir: Path,
    spec_dir: Path,
    qa_session: int,
    max_iterations: int,
    verbose: bool = False,
    previous_error: dict | None = None,
) -> tuple[str, str]:
    """
    Executa sessão de QA reviewer.

    Retorna: (status, response_text)
    - status: "approved", "rejected", ou "error"
    """
    # 1. Carregar prompt (qa_reviewer.md)
    # 2. Carregar contexto de memória (se disponível)
    # 3. Executar query com cliente
    # 4. Stream resposta
    # 5. Verificar se qa_signoff foi atualizado
    # 6. Retornar status

    pass
```

---

#### 7.2.3 QA Fixer Agent (`qa/fixer.py`)

```python
"""
QA Fixer Agent - Skybridge Adaptation
===================================

Corrige issues encontradas pelo QA reviewer.
"""

from pathlib import Path
from skybridge.core.client import create_client
from skybridge.kernel.contracts.result import Result


async def run_qa_fixer_session(
    client,
    spec_dir: Path,
    fix_session: int,
    verbose: bool = False,
    project_dir: Path | None = None,
) -> tuple[str, str]:
    """
    Executa sessão de QA fixer.

    Retorna: (status, response_text)
    - status: "fixed" ou "error"
    """
    # 1. Verificar QA_FIX_REQUEST.md
    # 2. Carregar prompt (qa_fixer.md)
    # 3. Executar query com cliente
    # 4. Aplicar fixes
    # 5. Testar cada fix
    # 6. Atualizar qa_signoff (fixes_applied)

    pass
```

---

#### 7.2.4 Criteria Management (`qa/criteria.py`)

```python
"""
QA Acceptance Criteria - Skybridge Adaptation
==========================================

Gerencia acceptance criteria e status de QA.
"""

import json
from pathlib import Path
from skybridge.kernel.contracts.result import Result


# Implementação Plan I/O
def load_implementation_plan(spec_dir: Path) -> dict | None:
    """Carrega implementation_plan.json"""
    plan_file = spec_dir / "implementation_plan.json"
    if not plan_file.exists():
        return None
    try:
        with open(plan_file) as f:
            return json.load(f)
    except (OSError, json.JSONDecodeError):
        return None


def save_implementation_plan(spec_dir: Path, plan: dict) -> Result[None, str]:
    """Salva implementation_plan.json"""
    plan_file = spec_dir / "implementation_plan.json"
    try:
        with open(plan_file, "w") as f:
            json.dump(plan, f, indent=2)
        return Result.ok(None)
    except OSError as e:
        return Result.err(f"Failed to save: {str(e)}")


# QA Sign-off Status
def get_qa_signoff_status(spec_dir: Path) -> dict | None:
    """Retorna status atual de QA sign-off"""
    plan = load_implementation_plan(spec_dir)
    if not plan:
        return None
    return plan.get("qa_signoff")


def is_qa_approved(spec_dir: Path) -> bool:
    """QA aprovou build?"""
    status = get_qa_signoff_status(spec_dir)
    if not status:
        return False
    return status.get("status") == "approved"


def is_qa_rejected(spec_dir: Path) -> bool:
    """QA rejeitou build (precisa de fixes)?"""
    status = get_qa_signoff_status(spec_dir)
    if not status:
        return False
    return status.get("status") == "rejected"


def is_fixes_applied(spec_dir: Path) -> bool:
    """Fixes foram aplicados?"""
    status = get_qa_signoff_status(spec_dir)
    if not status:
        return False
    return status.get("status") == "fixes_applied"


def get_qa_iteration_count(spec_dir: Path) -> int:
    """Contagem de iterações de QA"""
    status = get_qa_signoff_status(spec_dir)
    if not status:
        return 0
    return status.get("qa_session", 0)


# Readiness Checks
def should_run_qa(spec_dir: Path) -> bool:
    """QA deve rodar?"""
    # Verificar se build está completa (usar lógica do job)
    # Verificar se ainda não aprovou
    return True  # Placeholder


def should_run_fixes(spec_dir: Path) -> bool:
    """QA fixer deve rodar?"""
    return is_qa_rejected(spec_dir) and get_qa_iteration_count(spec_dir) < MAX_QA_ITERATIONS
```

---

#### 7.2.5 Report & Issue Tracking (`qa/report.py`)

```python
"""
QA Report & Issue Tracking - Skybridge Adaptation
=============================================

Rastreamento de iterações e detecção de issues recorrentes.
"""

from pathlib import Path
from datetime import datetime, timezone
from difflib import SequenceMatcher
from collections import Counter
from skybridge.kernel.contracts.result import Result


# Configuração
RECURRING_ISSUE_THRESHOLD = 3
ISSUE_SIMILARITY_THRESHOLD = 0.8


def get_iteration_history(spec_dir: Path) -> list[dict]:
    """Retorna histórico de iterações"""
    plan = load_implementation_plan(spec_dir)
    if not plan:
        return []
    return plan.get("qa_iteration_history", [])


def record_iteration(
    spec_dir: Path,
    iteration: int,
    status: str,
    issues: list[dict],
    duration_seconds: float | None = None,
) -> Result[None, str]:
    """Registra iteração no histórico"""
    plan = load_implementation_plan(spec_dir)
    if not plan:
        plan = {}

    if "qa_iteration_history" not in plan:
        plan["qa_iteration_history"] = []

    record = {
        "iteration": iteration,
        "status": status,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "issues": issues,
    }

    if duration_seconds is not None:
        record["duration_seconds"] = round(duration_seconds, 2)

    plan["qa_iteration_history"].append(record)

    # Atualizar stats
    if "qa_stats" not in plan:
        plan["qa_stats"] = {}

    plan["qa_stats"]["total_iterations"] = len(plan["qa_iteration_history"])
    plan["qa_stats"]["last_iteration"] = iteration
    plan["qa_stats"]["last_status"] = status

    # Salvar
    result = save_implementation_plan(spec_dir, plan)
    return result


def _normalize_issue_key(issue: dict) -> str:
    """Normaliza chave de issue"""
    title = (issue.get("title") or "").lower().strip()
    file = (issue.get("file") or "").lower().strip()
    line = issue.get("line") or ""

    for prefix in ["error:", "issue:", "bug:", "fix:"]:
        if title.startswith(prefix):
            title = title[len(prefix):].strip()

    return f"{title}|{file}|{line}"


def _issue_similarity(issue1: dict, issue2: dict) -> float:
    """Calcula similaridade entre issues"""
    key1 = _normalize_issue_key(issue1)
    key2 = _normalize_issue_key(issue2)

    return SequenceMatcher(None, key1, key2).ratio()


def has_recurring_issues(
    current_issues: list[dict],
    history: list[dict],
    threshold: int = RECURRING_ISSUE_THRESHOLD,
) -> tuple[bool, list[dict]]:
    """Detecta issues recorrentes (3+ ocorrências)"""
    if not history:
        return False, []

    historical_issues = []
    for record in history:
        historical_issues.extend(record.get("issues", []))

    if not historical_issues:
        return False, []

    recurring = []

    for current in current_issues:
        occurrence_count = 1

        for historical in historical_issues:
            similarity = _issue_similarity(current, historical)
            if similarity >= ISSUE_SIMILARITY_THRESHOLD:
                occurrence_count += 1

        if occurrence_count >= threshold:
            recurring.append({**current, "occurrence_count": occurrence_count})

    return len(recurring) > 0, recurring


def get_recurring_issue_summary(history: list[dict]) -> dict:
    """Analisa histórico para issues mais comuns"""
    all_issues = []
    for record in history:
        all_issues.extend(record.get("issues", []))

    if not all_issues:
        return {"total_issues": 0, "unique_issues": 0, "most_common": []}

    # Agrupar issues similares
    issue_groups = {}
    for issue in all_issues:
        key = _normalize_issue_key(issue)
        matched = False

        for existing_key in issue_groups:
            if SequenceMatcher(None, key, existing_key).ratio() >= ISSUE_SIMILARITY_THRESHOLD:
                issue_groups[existing_key].append(issue)
                matched = True
                break

        if not matched:
            issue_groups[key] = [issue]

    # Top 5 mais comuns
    sorted_groups = sorted(issue_groups.items(), key=lambda x: len(x[1]), reverse=True)

    most_common = []
    for key, issues in sorted_groups[:5]:
        most_common.append({
            "title": issues[0].get("title", key),
            "file": issues[0].get("file"),
            "occurrences": len(issues),
        })

    # Estatísticas
    approved_count = sum(1 for r in history if r.get("status") == "approved")
    rejected_count = sum(1 for r in history if r.get("status") == "rejected")

    return {
        "total_issues": len(all_issues),
        "unique_issues": len(issue_groups),
        "most_common": most_common,
        "iterations_approved": approved_count,
        "iterations_rejected": rejected_count,
        "fix_success_rate": approved_count / len(history) if history else 0,
    }
```

---

### 7.3 Prompts Base (Adaptados para Skybridge)

#### 7.3.1 QA Reviewer Prompt (`prompts/qa_reviewer.md`)

```markdown
## YOUR ROLE - QA REVIEWER AGENT

You are **Quality Assurance Agent** in Skybridge development process. Your job is to validate that implementation is complete, correct, and production-ready before final sign-off.

**Key Principle**: You are the last line of defense. Be thorough.

---

## WHY QA VALIDATION MATTERS

The Agent may have:
- Completed all subtasks but missed edge cases
- Written code without necessary validation
- Introduced security vulnerabilities
- Broken existing functionality

Your job is to catch ALL of these before sign-off.

---

## PHASE 0: LOAD CONTEXT (MANDATORY)

```bash
# 1. Read spec
cat spec.md

# 2. Read worktree snapshot
cat .skybridge/worktree_snapshot.json

# 3. Read git diff from snapshot
# (Snapshot contains diff between initial and final state)
```

---

## PHASE 1: VERIFY SUBTASKS COMPLETED

Check if all subtasks in the job are marked as completed:
- Agent tasks completed
- Files modified
- Changes committed to worktree

---

## PHASE 2: CODE REVIEW

### 2.1: Security Review
Check for common vulnerabilities:
- SQL injection
- XSS (if web frontend)
- Hardcoded secrets (passwords, api_keys, tokens)
- Input validation

```bash
# Security checks
grep -rE "(password|secret|api_key|token)\s*=\s*['\"][^'\"]+['\"]" --include="*.py"
```

### 2.2: Code Quality
- Follows Skybridge patterns (Result, Envelope, Registry)
- Proper error handling
- Type hints present
- No debug prints in production code

### 2.3: Functional Verification
- Core functionality works as per spec
- Edge cases handled
- Error states return proper errors

---

## PHASE 3: GENERATE QA REPORT

Create comprehensive report:

```markdown
# QA Validation Report

## Summary
| Category | Status | Details |
|----------|--------|---------|
| Subtasks Complete | ✓/✗ | X/Y completed |
| Code Quality | ✓/✗ | [summary] |
| Security | ✓/✗ | [summary] |
| Functional | ✓/✗ | [summary] |

## Issues Found

### Critical (Blocks Sign-off)
1. [Issue description] - [File/Location]
2. [Issue description] - [File/Location]

### Major (Should Fix)
1. [Issue description] - [File/Location]

### Minor (Nice to Fix)
1. [Issue description] - [File/Location]

## Verdict

**SIGN-OFF**: [APPROVED / REJECTED]

**Reason**: [Explanation]

**Next Steps**:
- [If approved: Ready for merge to main branch]
- [If rejected: List of fixes needed, QA will re-run]
```

---

## PHASE 4: UPDATE IMPLEMENTATION PLAN

### If APPROVED:
```json
{
  "qa_signoff": {
    "status": "approved",
    "timestamp": "[ISO timestamp]",
    "qa_session": [session-number],
    "report_file": "qa_report.md",
    "verified_by": "qa_agent"
  }
}
```

### If REJECTED:
```json
{
  "qa_signoff": {
    "status": "rejected",
    "timestamp": "[ISO timestamp]",
    "qa_session": [session-number],
    "issues_found": [
      {
        "type": "critical|major|minor",
        "title": "[issue title]",
        "location": "[file:line]",
        "fix_required": "[description]"
      }
    ],
    "fix_request_file": "QA_FIX_REQUEST.md"
  }
}
```

---

## KEY REMINDERS

### Be Thorough
- Don't assume Agent did everything right
- Check EVERYTHING in spec
- Look for what's MISSING, not just what's wrong

### Be Specific
- Exact file paths (relative to worktree root)
- Reproducible steps for issues
- Clear fix instructions

### Be Fair
- Minor style issues don't block sign-off
- Focus on functionality and correctness
- Consider spec requirements, not perfection

### Document Everything
- Every check you run
- Every issue you find
- Every decision you make

---

## BEGIN
```

---

#### 7.3.2 QA Fixer Prompt (`prompts/qa_fixer.md`)

```markdown
## YOUR ROLE - QA FIX AGENT

You are **QA Fix Agent** in Skybridge development process. The QA Reviewer has found issues that must be fixed before sign-off. Your job is to fix ALL issues efficiently and correctly.

**Key Principle**: Fix what QA found. Don't introduce new issues. Get to approval.

---

## WHY QA FIX EXISTS

The QA Agent found issues that block sign-off:
- Missing validation
- Security vulnerabilities
- Code quality issues
- Missing functionality

You must fix these issues so QA can approve.

---

## PHASE 0: LOAD CONTEXT (MANDATORY)

```bash
# 1. Read QA fix request
cat QA_FIX_REQUEST.md

# 2. Read QA report
cat qa_report.md

# 3. Read spec
cat spec.md

# 4. Read worktree snapshot
cat .skybridge/worktree_snapshot.json
```

---

## PHASE 1: PARSE FIX REQUIREMENTS

From `QA_FIX_REQUEST.md`, extract:
- Issue titles
- File locations
- Problems
- Required fixes
- Verification criteria

Create mental checklist - you must address EVERY issue.

---

## PHASE 2: FIX ISSUES ONE BY ONE

For each issue:
1. Read problem area
2. Understand what's wrong
3. Implement minimal fix needed
4. Test locally (run tests if available)
5. Verify fix

**Follow these rules:**
- Make MINIMAL change needed
- Don't refactor surrounding code
- Don't add features
- Match Skybridge patterns (Result, Envelope)
- Test after each fix

---

## PHASE 3: RUN TESTS

After all fixes are applied:
- Run test suite (pytest, etc)
- Verify all tests pass
- Check for regressions

---

## PHASE 4: COMMIT FIXES

```bash
# Add all changes (excluding .skybridge/)
git add ':!.skybridge'

# Commit with message
git commit -m "fix: Address QA issues (qa-requested)"
```

---

## PHASE 5: UPDATE IMPLEMENTATION PLAN

```json
{
  "qa_signoff": {
    "status": "fixes_applied",
    "timestamp": "[ISO timestamp]",
    "fix_session": [session-number],
    "issues_fixed": [
      {
        "title": "[issue title]",
        "fix_commit": "[commit hash]"
      }
    ],
    "ready_for_qa_revalidation": true
  }
}
```

---

## COMMON FIX PATTERNS

### Missing Validation
- Add input validation checks
- Add error handling for edge cases
- Validate user inputs

### Security Issue
- Remove hardcoded secrets
- Add sanitization for inputs
- Implement proper authentication

### Code Quality
- Follow Skybridge patterns
- Add type hints
- Remove debug prints
- Improve error messages

---

## KEY REMINDERS

### Fix What Was Asked
- Don't add features
- Don't refactor
- Just fix the issues

### Be Thorough
- Every issue in QA_FIX_REQUEST.md
- Verify each fix

### Test After Fixes
- Run full test suite
- Check for regressions

### Don't Break Other Things
- Run full test suite to catch regressions
- Verify existing functionality still works

---

## BEGIN
```

---

### 7.3.3 Integração com JobOrchestrator

```python
"""
Job Orchestrator com QA Loop - Skybridge Adaptation
=====================================================

Integra QA Loop como fase pós-execução de job.
"""

from pathlib import Path
from skybridge.core.contexts.qa.loop import QALoopOrchestrator
from skybridge.core.contexts.webhooks.application.job_orchestrator import JobOrchestrator


class QADrivenJobOrchestrator(JobOrchestrator):
    """
    Orquestrador de jobs com QA Loop.

    Workflow:
    1. JobOrchestrator executa job padrão
    2. Após completion, inicia QA Loop
    3. QA Loop valida e corrige até aprovação
    4. Se aprovado → sign-off (pronto para merge)
    5. Se falhou → worktree preservado para inspeção
    """

    async def execute_job(self, job_id: str) -> Result[dict, str]:
        """
        Executa job completo com QA Loop.

        Fluxo:
        1. Executar job padrão (agent, worktree, snapshot)
        2. Verificar se job completou com sucesso
        3. Iniciar QA Loop
        4. Retornar resultado final
        """
        # 1. Executar job padrão
        result = await super().execute_job(job_id)

        if result.is_err:
            return result

        # 2. Iniciar QA Loop se job completou
        job = await self.job_queue.get_job(job_id)
        if job.status != "completed":
            return Result.ok({
                "message": "Job não completado, QA não iniciado",
                "qa_status": "not_run"
            })

        # 3. Iniciar QA Loop
        qa_loop = QALoopOrchestrator(
            job_queue=self.job_queue,
            agent_adapter=self.agent_adapter,
            project_dir=self.project_dir,
        )

        qa_approved = await qa_loop.run_qa_validation_loop(
            spec_dir=job.worktree_path,
            model="sonnet",
        )

        # 4. Retornar resultado
        return Result.ok({
            "message": "Job completado com QA",
            "qa_status": "approved" if qa_approved else "failed",
            "worktree_preserved": True,
        })
```

---

## 8. Roadmap de Implementação

### 8.1 Phase 1: MVP (1-2 semanas)

**Objetivo:** QA Loop básico com validação e correção

**Entregáveis:**
- [x] QA Loop Orchestrator básico
- [x] QA Reviewer Agent simples
- [x] QA Fixer Agent simples
- [x] Criteria Management (approved/rejected)
- [x] Iteration History tracking
- [x] Relatórios de QA (qa_report.md)
- [x] QA Fix Request (QA_FIX_REQUEST.md)
- [ ] Recurring issue detection
- [ ] Escalation logic

**Critérios de Sucesso:**
- [x] Loop roda iterações
- [x] Rejected → Fixer → Re-review
- [x] Approved → Sign-off
- [x] Atualiza implementation_plan.json

---

### 8.2 Phase 2: Enhanced (2-3 semanas)

**Objetivo:** Detecção de issues recorrentes e escalonamento

**Entregáveis:**
- [x] Recurring issue detection (SequenceMatcher)
- [x] Issue similarity scoring (threshold 0.8)
- [x] Escalation (QA_ESCALATION.md)
- [x] Iteration statistics
- [x] Most common issues tracking

**Critérios de Sucesso:**
- [x] Detecta issues que aparecem 3+ vezes
- [x] Escalona automaticamente
- [x] Cria relatório detalhado

---

### 8.3 Phase 3: Memory Integration (3-4 semanas)

**Objetivo:** Integração com sistema de memória (Graphiti ou similar)

**Entregáveis:**
- [ ] Memory context retrieval (patterns, gotchas)
- [ ] Session insights saving
- [ ] Cross-session learning

**Critérios de Sucesso:**
- [ ] Recupera contexto antes de cada sessão QA
- [ ] Salva descobertas após sessão
- [ ] Usa contexto em próximas sessões

---

### 8.4 Phase 4: E2E Testing (4-5 semanas)

**Objetivo:** Testing E2E automático para web frontends

**Entregáveis:**
- [ ] Browser automation (Puppeteer)
- [ ] Screenshot capture
- [ ] Form interaction testing
- [ ] Console error checking

**Critérios de Sucesso:**
- [ ] QA toma screenshots antes/depois
- [ ] QA interage com UI via comandos
- [ ] Verifica console errors
- [ ] Documenta findings

---

### 8.5 Phase 5: No-Test Handling (5-6 semanas)

**Objetivo:** Criar planos de teste manual para projetos sem testes

**Entregáveis:**
- [ ] No-test project detection
- [ ] Manual test plan generation
- [ ] Test framework scanning (pytest, jest, vitest)

**Critérios de Sucesso:**
- [ ] Detecta ausência de testes
- [ ] Cria MANUAL_TEST_PLAN.md
- [ ] Sugere testes manuais

---

### 8.6 Phase 6: Linear Integration (6-7 semanas, opcional)

**Objetivo:** Integração com Linear para rastreamento de tasks

**Entregáveis:**
- [ ] Linear client wrapper
- [ ] Task state management
- [ ] Status updates (In Review, Approved, Failed)

**Critérios de Sucesso:**
- [ ] Atualiza status no Linear
- [ ] Cria task de QA no Linear
- [ ] Rastreia iterações

---

## 9. Diferenças de Implementação

### 9.1 Skybridge vs Auto-Claude

| Aspecto | Auto-Claude | Skybridge (Alvo) | Diferença |
|----------|-------------|-------------------|------------|
| **Claude Client** | SDK customizado | ClaudeCodeAdapter | Similiar |
| **Prompt Loading** | Prompts estáticos | Mesma abordagem |
| **Memory** | Graphiti obrigatório | Opcional (fase 3) |
| **E2E Testing** | Electron MCP | Puppeteer/Playwright |
| **Git Operations** | Direto no worktree | Através de worktree_manager |
| **Linear** | Integrado | Opcional |
| **Spec Structure** | .auto-claude/specs/ | Worktree direto |

---

### 9.2 Adaptações Necessárias para Skybridge

**Claude Client:**
- Skybridge usa `ClaudeCodeAdapter` (infra/agents/claude_agent.py)
- Auto-Claude usa `create_client()` (core/client.py)
- **Ação:** Usar ClaudeCodeAdapter ou adaptar create_client

**Worktree:**
- Skybridge já tem worktree_manager
- Auto-Claude usa git diretamente no worktree
- **Ação:** Integrar com worktree_manager existente

**Snapshot:**
- Skybridge tem GitExtractor (snapshot inicial)
- Auto-Claude não tem snapshot formal
- **Ação:** Capturar snapshot antes de QA (já existe, só adicionar pós-QA)

**Memory:**
- Skybridge não tem Graphiti
- Auto-Claude Graphiti é obrigatório
- **Ação:** Implementar sistema de memória simples (JSON + embeddings) ou esperar Graphiti

**Spec Directory:**
- Skybridge usa worktree_path como spec_dir
- Auto-Claude usa .auto-claude/specs/
- **Ação:** Passar worktree_path diretamente para QA agents

---

## 10. Teste e Validação

### 10.1 Critérios de Aceitação de QA

Para validar implementação, verificar:

**MVP (Phase 1):**
- [ ] QA Loop inicia após job completion
- [ ] Iteração 1 executa QA Reviewer
- [ ] Se rejeitado, QA Fixer corrige issues
- [ ] Iteração 2 revalida
- [ ] Continua até approved ou max 50 iterações
- [ ] Implementation plan atualizado com status

**Enhanced (Phase 2):**
- [ ] Issues recorrentes detectados (3+ ocorrências)
- [ ] Escalona para humano quando recorrentes
- [ ] QA_ESCALATION.md criado
- [ ] Iteration statistics calculadas

---

### 10.2 Casos de Teste

**Cenário 1: Approved na primeira iteração**
```
1. Job executa agent (/resolve-issue)
2. Worktree criado e modificado
3. QA Reviewer valida
4. Todos critérios passam
5. Status: "approved"
6. Sign-off gravado em implementation_plan.json
7. Worktree preservado para merge manual
```

**Cenário 2: Rejeitado na primeira, aprovado na segunda**
```
1. QA Reviewer encontra issue
2. Status: "rejected"
3. QA Fixer corrige issue
4. Status: "fixes_applied"
5. QA Reviewer re-valida
6. Todos critérios passam
7. Status: "approved"
8. Sign-off gravado
```

**Cenário 3: Issues recorrentes**
```
1. Issue aparece 3 vezes (iterações 1, 3, 5)
2. Detecção de recurring issue acionada
3. QA_ESCALATION.md criado
4. Loop termina com status "failed"
5. Worktree preservado para inspeção manual
```

**Cenário 4: Erro consecutivo (3 vezes)**
```
1. QA Reviewer falha 3 vezes sem progresso
2. Detecta MAX_CONSECUTIVE_ERRORS atingido
3. Loop termina com status "failed"
4. Erros documentados em iteration history
```

---

### 10.3 Métricas de Sucesso

**Quantitativas:**
- Taxa de aprovação em primeiras 3 iterações
- Número médio de iterações até aprovação
- Percentual de issues recorrentes
- Tempo médio por iteração

**Qualitativas:**
- QA está detectando bugs reais?
- QA está criando falsos positivos?
- Fixes estão resolvendo issues?
- Escalonamento está apropriado?

---

## 11. Recomendações Finais

### 11.1 Prioridade de Implementação

**CRÍTICO (implementar primeiro):**
1. QA Loop básico (reviewer + fixer)
2. Criteria management
3. Iteration history tracking
4. Status persistence (implementation_plan.json)

**ALTA (implementar depois):**
5. Recurring issue detection
6. Escalation logic
7. Memory integration básica (JSON local)
8. E2E testing (Puppeteer/Playwright)

**MÉDIA (implementar depois):**
9. Graphiti memory integration
10. Linear integration
11. Advanced QA features (test framework detection, manual test plans)

**BAIXA (implementar depois):**
12. Electron MCP (se Skybridge tiver Electron frontend)

---

### 11.2 Boas Práticas

**Design:**
- Separar concerns: reviewer (validação) vs fixer (correção)
- Usar Result pattern para error handling
- Manter state em JSON (implementation_plan.json)
- Logging detalhado para debugging

**Segurança:**
- Validar todos os fixes antes de aprovação
- Verificar regressões após cada fix
- Não permitir que QA fixer introduza novos bugs

**Performance:**
- Limitar número de iterações (max: 50)
- Timeout em cada sessão de QA
- Early termination se sem progresso

**Experiência do Desenvolvedor:**
- Worktree sempre preservado (Skybridge RF005)
- Logs detalhados de cada iteração
- Relatórios em Markdown legíveis
- Mensagens claras de progresso

---

## 12. Referências

### 12.1 Auto-Claude

- **QA Loop:** `apps/backend/qa/loop.py`
- **Reviewer:** `apps/backend/qa/reviewer.py`
- **Fixer:** `apps/backend/qa/fixer.py`
- **Criteria:** `apps/backend/qa/criteria.py`
- **Report:** `apps/backend/qa/report.py`
- **Prompts:**
  - `apps/backend/prompts/qa_reviewer.md`
  - `apps/backend/prompts/qa_fixer.md`
- **Memory:** `apps/backend/agents/memory_manager.py`

---

### 12.2 Skybridge

- **Worktree Manager:** `src/skybridge/core/contexts/webhooks/application/worktree_manager.py`
- **Job Orchestrator:** `src/skybridge/core/contexts/webhooks/application/job_orchestrator.py`
- **Agent Facade:** `src/skybridge/core/contexts/webhooks/infrastructure/agents/claude_agent.py`
- **Snapshot Extractor:** `src/skybridge/platform/observability/snapshot/extractors/git_extractor.py`
- **Domain:** `src/skybridge/core/contexts/webhooks/domain/`
- **Ports:** `src/skybridge/core/contexts/webhooks/ports/`

---

## 13. Conclusão

### 13.1 Resumo Executivo

O **QA Loop** do Auto-Claude é um sistema robusto de validação automática com:

**Componentes Principais:**
1. QA Loop Orchestrator - Coordena iterações até aprovação/limite
2. QA Reviewer Agent - Valida acceptance criteria, executa testes
3. QA Fixer Agent - Corrige issues encontradas pelo reviewer
4. Criteria Management - Gerencia acceptance criteria e status
5. Report & Tracking - Rastreia histórico, detecta issues recorrentes
6. Memory Integration - Graphiti para contexto cross-session
7. E2E Testing - Electron MCP para validação de UI

**Principais Vantagens:**
- ✅ Self-validating (detecta e corrige automaticamente)
- ✅ Iteration tracking (histórico completo)
- ✅ Recurring issue detection (3+ ocorrências)
- ✅ Escalation automática (humano quando necessário)
- ✅ Memory integration (aprende com sessões anteriores)
- ✅ Graceful degradation (não trava sem memory)

---

### 13.2 Skybridge - Estado Atual

**O que Skybridge JÁ tem:**
- ✅ Worktree management
- ✅ Snapshot captura (GitExtractor)
- ✅ Job queue assíncrona
- ✅ Agent framework (ClaudeCodeAdapter)

**O que Skybridge NÃO tem (GAP):**
- ❌ QA Loop orchestration
- ❌ QA reviewer agent
- ❌ QA fixer agent
- ❌ Criteria management system
- ❌ Iteration history tracking
- ❌ Recurring issue detection
- ❌ Escalation logic
- ❌ QA reports (qa_report.md)
- ❌ Memory integration
- ❌ E2E testing

---

### 13.3 Caminho de Implementação

**Fase 1 (1-2 semanas):** QA Loop básico
- Criar estrutura de módulo QA
- Implementar QA reviewer agent (validação simples)
- Implementar QA fixer agent (correção simples)
- Implementar criteria management (approved/rejected)
- Criar iteration history tracking
- Integrar com JobOrchestrator (pós-execução de job)

**Fase 2 (2-3 semanas):** Recurring issues & escalonamento
- Implementar recurring issue detection (SequenceMatcher)
- Criar lógica de escalonamento
- Criar relatórios de escalonamento (QA_ESCALATION.md)
- Adicionar statistics de iterações

**Fase 3 (3-4 semanas):** Memory integration
- Implementar sistema de memória local (JSON + embeddings)
- Ou integrar com Graphiti (se disponível)
- Context retrieval antes de sessões QA
- Session insights saving após sessões

**Fase 4 (4-5 semanas):** E2E testing
- Implementar browser automation (Puppeteer/Playwright)
- Criar screenshot capture
- Implementar form interaction testing
- Integrar com QA reviewer prompts

**Fase 5 (5-6 semanas):** Avançado
- Test framework detection
- Manual test plans
- Graphiti memory
- Linear integration (opcional)

---

> "QA automático é a linha de defesa que protege produção de bugs." – made by Sky 🛡️
