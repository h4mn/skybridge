# Comparação: Ideation e Insight - Auto-Claude vs Skybridge

**Data:** 2026-01-14
**Analista:** Sky
**Foco:** Funcionalidades de ideação, descoberta e extração de insights

---

## 1. Visão Geral

### Auto-Claude: Sistema Completo de Ideation & Insight
- **Ideation**: AI-powered ideation generator com múltiplos tipos de ideias
- **Insight**: Extração automática de insights de sessões de codificação
- **Discovery**: Análise automatizada de projeto para descobrir melhorias
- **Analysis**: Múltiplos analizadores especializados (security, test, CI, etc)

### Skybridge: Não Implementado
- **Ideation**: ❌ Não existe
- **Insight**: ❌ Não existe
- **Discovery**: ⚠️ Parcial (snapshot scoring via ADR000)
- **Analysis**: ❌ Não existe (apenas estrutura de observabilidade)

---

## 2. Arquitetura de Ideation (Auto-Claude)

```
┌─────────────────────────────────────────────────────────────────┐
│                    Ideation Orchestrator                      │
│                 (ideation/runner.py)                         │
└─────────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────────┐
│                    Phase 1: Project Index                   │
│              (project_index_phase.py)                          │
│  - Analisa estrutura do projeto                             │
│  - Cria índice de arquivos e diretórios                  │
│  - Identifica tecnologias e frameworks                       │
└─────────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────────┐
│               Phase 2: Context & Graph Hints                │
│              (phase_executor.py - PARALLEL)                   │
│                                                              │
│  Context:                                                    │
│  - Coleta contexto do projeto                                │
│  - Analiza roadmap (se habilitado)                           │
│  - Analiza kanban board (se habilitado)                      │
│                                                              │
│  Graph Hints:                                                │
│  - Busca insights no Graphiti (memory)                        │
│  - Contextualiza com histórico de ideias                      │
│  - Graceful degradation (não falha se Graphiti indisponível)   │
└─────────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────────┐
│              Phase 3: Ideation Generation (PARALLEL)         │
│              (generator.py - 6 tipos de ideias)              │
│                                                              │
│  Cada tipo roda em agente separado em paralelo:              │
│  1. code_improvements       - Melhorias de código          │
│  2. ui_ux_improvements      - Melhorias de UI/UX          │
│  3. documentation_gaps       - Gaps de documentação       │
│  4. security_hardening       - Hardening de segurança      │
│  5. performance_optimizations - Otimizações de performance │
│  6. code_quality             - Qualidade e refactoring    │
│                                                              │
│  Cada agente:                                                │
│  - Usa prompt específico (prompts/ideation_*.md)            │
│  - Analiza contexto do projeto                               │
│  - Gera até N ideias (configurável)                        │
│  - Saída em JSON estruturado                               │
│  - Validação automática da saída                             │
│  - Recovery agent se validação falhar                          │
└─────────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────────┐
│                   Phase 4: Merge & Finalize                  │
│              (formatter.py + merge)                           │
│  - Combina todas ideias em arquivo único                     │
│  - Formata para consumo humano/máquina                       │
│  - Cria resumo por tipo                                    │
│  - Preserva ideias existentes (modo append)                  │
│  - Gera ideation.json final                                │
└─────────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────────┐
│                    Output: ideation.json                      │
│  .auto-claude/ideation/ideation.json                       │
│                                                              │
│  {                                                          │
│    "ideas": [                                                │
│      {                                                        │
│        "id": "uuid",                                         │
│        "type": "code_improvements",                           │
│        "title": "Add type hints",                             │
│        "description": "...",                                   │
│        "priority": "high",                                   │
│        "effort": "medium",                                   │
│        "impact": "high",                                     │
│        "files_affected": ["src/*.py"],                         │
│        "tags": ["type-hints", "typing"]                        │
│      },                                                       │
│      ...                                                      │
│    ],                                                         │
│    "summary": {                                               │
│      "total": 30,                                            │
│      "by_type": {                                             │
│        "code_improvements": 5,                                │
│        "ui_ux_improvements": 5,                              │
│        ...                                                    │
│      }                                                        │
│    }                                                          │
│  }                                                          │
└─────────────────────────────────────────────────────────────────┘
```

**Componentes Principais:**

1. **IdeationOrchestrator** (`runner.py`)
   - Coordena todas as fases
   - Gerencia configuração
   - Executa em paralelo (context, hints, ideation)
   - Imprime progresso em tempo real

2. **ProjectIndexPhase** (`project_index_phase.py`)
   - Analisa estrutura do projeto
   - Cria índice de arquivos
   - Identifica tecnologias
   - Cache de indexação

3. **IdeationGenerator** (`generator.py`)
   - Executa agentes para cada tipo de ideia
   - Usa prompts especializados
   - Gera JSON estruturado
   - Recovery agent para correção de erros

4. **IdeaPrioritizer** (`prioritizer.py`)
   - Valida saída JSON
   - Verifica schema
   - Corrige erros de estrutura
   - Prioriza ideias

5. **IdeationFormatter** (`formatter.py`)
   - Combina múltiplas saídas
   - Gera ideation.json unificado
   - Formata para leitura humana
   - Preserva ideias existentes (append)

6. **PhaseExecutor** (`phase_executor.py`)
   - Executa fases em paralelo
   - Gerencia retries
   - Coordena context e hints
   - Gerencia output streaming

---

## 3. Tipos de Ideação (Auto-Claude)

### 3.1 Code Improvements

**Prompt:** `prompts/ideation_code_improvements.md`

**Foco:**
- Refactoring opportunities
- Code smells
- Design patterns não utilizados
- Redundancies e duplicações
- Complexidade ciclomática alta

**Exemplo de Saída:**
```json
{
  "code_improvements": [
    {
      "id": "code-001",
      "type": "code_improvements",
      "title": "Replace magic numbers with constants",
      "description": "The codebase contains multiple instances of magic numbers...",
      "priority": "medium",
      "effort": "low",
      "impact": "medium",
      "files_affected": [
        "src/calculations.py",
        "src/utils/math.py"
      ],
      "tags": ["constants", "readability"],
      "estimated_complexity": 2,
      "suggested_approach": "Create constants.py module and define..."
    }
  ]
}
```

---

### 3.2 UI/UX Improvements

**Prompt:** `prompts/ideation_ui_ux.md`

**Foco:**
- Usabilidade da interface
- Acessibilidade (WCAG)
- Consistência visual
- Feedback do usuário
- Responsividade
- Animações e transições

**Exemplo de Saída:**
```json
{
  "ui_ux_improvements": [
    {
      "id": "ui-001",
      "type": "ui_ux_improvements",
      "title": "Add keyboard navigation support",
      "description": "Users cannot navigate the application using keyboard only...",
      "priority": "high",
      "effort": "medium",
      "impact": "high",
      "components": [
        "SettingsPage",
        "KanbanBoard",
        "AgentTerminal"
      ],
      "tags": ["accessibility", "keyboard"],
      "wcag_criteria": ["2.1.1 Keyboard"]
    }
  ]
}
```

---

### 3.3 Documentation Gaps

**Prompt:** `prompts/ideation_documentation.md`

**Foco:**
- APIs não documentadas
- Funções complexas sem docs
- README incompleto
- Falta de exemplos
- Diagramas de arquitetura ausentes
- Contributing指南 incompleto

**Exemplo de Saída:**
```json
{
  "documentation_gaps": [
    {
      "id": "doc-001",
      "type": "documentation_gaps",
      "title": "Document webhook endpoints",
      "description": "The webhook endpoints (/webhooks/github) have no documentation...",
      "priority": "high",
      "effort": "low",
      "impact": "high",
      "files_to_document": [
        "src/core/contexts/webhooks/handlers.py",
        "src/core/contexts/webhooks/processor.py"
      ],
      "suggested_format": "OpenAPI/Swagger",
      "doc_location": "docs/api/webhooks.md"
    }
  ]
}
```

---

### 3.4 Security Hardening

**Prompt:** `prompts/ideation_security.md`

**Foco:**
- Vulnerabilidades de segurança
- Dependências desatualizadas
- Secrets não protegidos
- Injeção de código (SQL, XSS, etc)
- Autenticação fraca
- Headers de segurança ausentes
- Rate limiting ausente

**Exemplo de Saída:**
```json
{
  "security_hardening": [
    {
      "id": "sec-001",
      "type": "security_hardening",
      "title": "Add rate limiting to webhook endpoint",
      "description": "The webhook endpoint has no rate limiting, allowing...",
      "priority": "high",
      "effort": "medium",
      "impact": "high",
      "cwe": "CWE-770",
      "owasp": "API4:2023 - Unrestricted Resource Consumption",
      "files_affected": [
        "src/apps/server/main.py"
      ],
      "tags": ["rate-limiting", "dos"],
      "suggested_solution": "Implement token bucket rate limiter..."
    }
  ]
}
```

---

### 3.5 Performance Optimizations

**Prompt:** `prompts/ideation_performance.md`

**Foco:**
- N+1 queries
- Consultas lentas
- Algoritmos ineficientes
- Cache ausente
- Redes não otimizadas
- Asset bundling lento
- Memory leaks

**Exemplo de Saída:**
```json
{
  "performance_optimizations": [
    {
      "id": "perf-001",
      "type": "performance_optimizations",
      "title": "Add database query caching",
      "description": "Repeated queries for the same data are being executed...",
      "priority": "high",
      "effort": "medium",
      "impact": "high",
      "current_performance": "Response time: 500ms avg",
      "expected_improvement": "50-100ms with cache",
      "files_affected": [
        "src/database/repository.py",
        "src/api/endpoints.py"
      ],
      "tags": ["caching", "database"],
      "suggested_approach": "Use Redis or in-memory cache"
    }
  ]
}
```

---

### 3.6 Code Quality & Refactoring

**Prompt:** `prompts/ideation_code_quality.md`

**Foco:**
- Code smells
- Technical debt
- Violations de SOLID
- DRY violations
- Naming conventions
- Type hints ausentes
- Test coverage baixo

**Exemplo de Saída:**
```json
{
  "code_quality": [
    {
      "id": "quality-001",
      "type": "code_quality",
      "title": "Add type hints to all public functions",
      "description": "Many public functions lack type hints, making IDE support...",
      "priority": "medium",
      "effort": "medium",
      "impact": "medium",
      "affected_modules": [
        "src/core/contexts/webhooks/",
        "src/core/contexts/fileops/"
      ],
      "tags": ["type-hints", "python"],
      "suggested_tool": "mypy --strict"
    }
  ]
}
```

---

## 4. Arquitetura de Insight Extraction (Auto-Claude)

```
┌─────────────────────────────────────────────────────────────────┐
│                 After Coding Session Completes                │
└─────────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────────┐
│              Insight Extractor Triggered                    │
│           (analysis/insight_extractor.py)                     │
│                                                              │
│  Input Gathering:                                            │
│  - Subtask description (do que foi feito)                    │
│  - Git diff (changes made)                                  │
│  - Changed files list                                        │
│  - Commit messages                                          │
│  - Attempt history (se falhou e recuperou)                  │
│  - Session number                                           │
│  - Success/failure flag                                      │
└─────────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────────┐
│              Prompt Construction                             │
│                                                              │
│  Prompt Template:                                            │
│  """                                                        │
│  # Session Insight Extraction                                   │
│                                                              │
│  ## What was done                                            │
│  {subtask_description}                                        │
│                                                              │
│  ## Session Results                                           │
│  Success: {success}                                          │
│  Attempt #{session_num}                                        │
│                                                              │
│  ## Changes Made                                             │
│  {diff} (truncated if too large)                              │
│                                                              │
│  ## Files Changed                                            │
│  {changed_files}                                             │
│                                                              │
│  ## Commit Messages                                          │
│  {commit_messages}                                           │
│                                                              │
│  ## Attempt History (if applicable)                            │
│  {attempt_history}                                           │
│                                                              │
│  ## Your Task                                                │
│  Extract structured insights from this session:                   │
│  1. Patterns discovered                                     │
│  2. Gotchas (traps to avoid)                               │
│  3. Architectural decisions made                             │
│  4. Lessons learned                                        │
│  5. Code smells detected                                   │
│  6. Dependencies discovered                              │
│  7. Performance findings                                   │
│  """                                                       │
└─────────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────────┐
│              Claude Agent Execution                           │
│              (claude-agent-sdk)                              │
│                                                              │
│  Model: claude-3-5-haiku-latest (fast & cheap)             │
│  - Analiza diff e inputs                                   │
│  - Extrai insights estruturados                            │
│  - Formata em JSON                                         │
│                                                              │
│  Graceful Degradation:                                       │
│  - Se SDK não disponível: usa insights genéricos            │
│  - Se falha: não bloqueia build (não é crítico)           │
└─────────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────────┐
│              Output: insights.json                          │
│  .auto-claude/specs/XXX/graphiti/insights.json            │
│                                                              │
│  {                                                          │
│    "insights": [                                              │
│      {                                                        │
│        "type": "pattern",                                       │
│        "title": "Use dependency injection for services",           │
│        "description": "Multiple places directly instantiate...",    │
│        "code_example": "Before: Service()\nAfter: Service(...)", │
│        "files": ["src/auth/service.py", "src/user/service.py"]   │
│      },                                                       │
│      {                                                        │
│        "type": "gotcha",                                        │
│        "title": "Worktree cleanup requires staged commit",          │
│        "description": "Git worktrees cannot be removed if...",     │
│        "solution": "Always create a dummy commit before cleanup"     │
│      },                                                       │
│      {                                                        │
│        "type": "architectural_decision",                          │
│        "title": "Use JSON-RPC for all internal communication",     │
│        "description": "ADR004 decision to adopt JSON-RPC..."     │
│      },                                                       │
│      {                                                        │
│        "type": "code_smell",                                    │
│        "title": "Deep nesting in webhook handlers",                │
│        "description": "Handlers have 5+ levels of nesting..."      │
│      },                                                       │
│      {                                                        │
│        "type": "dependency",                                    │
│        "title": "graphiti-core requires Python 3.12+",            │
│        "description": "LadybugDB only works on Python 3.12+"      │
│      }                                                        │
│    ]                                                          │
│  }                                                          │
└─────────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────────┐
│              Ingest to Graphiti Memory                     │
│  (integrations/graphiti/memory.py)                          │
│                                                              │
│  - Cria nós no graph database                                │
│  - Indexa por embeddings (semantic search)                     │
│  - Contextualiza com histórico de projeto                     │
│  - Disponível para próximas sessões (memory.get_context)       │
└─────────────────────────────────────────────────────────────────┘
```

**Tipos de Insights Extraídos:**

1. **Patterns** - Padrões de código e arquitetura
2. **Gotchas** - Armadilhas e pitfalls comuns
3. **Architectural Decisions** - Decisões técnicas importantes
4. **Lessons Learned** - Lições aprendidas
5. **Code Smells** - Odores de código detectados
6. **Dependencies** - Dependências descobertas
7. **Performance Findings** - Descobertas de performance

---

## 5. Discovery & Analysis (Auto-Claude)

### 5.1 Security Scanner

**Arquivo:** `analysis/security_scanner.py`

**Funcionalidades:**
- Scan por secrets (API keys, tokens, passwords)
- Scan por vulnerabilidades conhecidas
- Análise de dependências
- Configurações de segurança
- Headers HTTP de segurança
- Validations de input

**Output:**
```json
{
  "security_findings": [
    {
      "type": "secret",
      "severity": "high",
      "file": ".env.example",
      "line": 42,
      "pattern": "sk-.*",
      "description": "Potential API key leaked in .env.example"
    },
    {
      "type": "vulnerability",
      "severity": "medium",
      "package": "requests",
      "version": "2.25.0",
      "cve": "CVE-2023-32681"
    }
  ]
}
```

---

### 5.2 Test Discovery

**Arquivo:** `analysis/test_discovery.py`

**Funcionalidades:**
- Descobre testes existentes
- Identifica código sem testes
- Calcula coverage (se disponível)
- Descobre frameworks de teste
- Identifica testes broken
- Sugere novos testes

**Output:**
```json
{
  "test_summary": {
    "total_tests": 245,
    "passed": 230,
    "failed": 15,
    "coverage": 78.5
  },
  "uncovered_modules": [
    "src/core/contexts/webhooks/",
    "src/platform/observability/"
  ],
  "suggested_tests": [
    {
      "module": "webhook_processor.py",
      "test_type": "unit",
      "description": "Test webhook signature verification"
    }
  ]
}
```

---

### 5.3 CI Discovery

**Arquivo:** `analysis/ci_discovery.py`

**Funcionalidades:**
- Descobre workflows de CI/CD
- Identifica GitHub Actions, GitLab CI, CircleCI, etc
- Analiza configurações
- Identifica steps de build/test/deploy
- Detecta problemas de configuração

**Output:**
```json
{
  "ci_system": "GitHub Actions",
  "workflows": [
    {
      "name": "ci.yml",
      "triggers": ["push", "pull_request"],
      "steps": ["checkout", "setup-python", "test", "lint"]
    }
  ],
  "issues": [
    {
      "severity": "medium",
      "description": "No caching configured for dependencies"
    }
  ]
}
```

---

### 5.4 Risk Classifier

**Arquivo:** `analysis/risk_classifier.py`

**Funcionalidades:**
- Classifica risco de tasks
- Analiza complexidade
- Avalia impacto
- Categoriza risks
- Sugere mitigações

**Output:**
```json
{
  "risk_assessment": {
    "overall_risk": "medium",
    "complexity": "high",
    "impact": "medium",
    "factors": [
      {"name": "Legacy code", "weight": 0.7},
      {"name": "No tests", "weight": 0.9}
    ],
    "mitigation_suggestions": [
      "Add comprehensive tests first",
      "Create feature branch for safety"
    ]
  }
}
```

---

### 5.5 Project Analyzer

**Arquivo:** `analysis/project_analyzer.py` + `analyzers/`

**Funcionalidades:**
- Detecta linguagens utilizadas
- Identifica frameworks
- Detecta banco de dados
- Descobre APIs/rotas
- Analiza dependências
- Detecta configurações
- Identifica arquitetura (monolith, microservices, etc)

**Analyzers Especializados:**
- `framework_analyzer.py` - Frameworks web, UI, etc
- `database_detector.py` - PostgreSQL, MySQL, MongoDB, etc
- `route_detector.py` - API routes, controllers
- `service_analyzer.py` - Serviços e microserviços
- `port_detector.py` - Portas expostas
- `project_analyzer_module.py` - Analisador geral

**Output:**
```json
{
  "languages": ["Python", "TypeScript", "JavaScript"],
  "frameworks": {
    "backend": ["FastAPI", "Pydantic"],
    "frontend": ["React", "Electron"]
  },
  "databases": ["PostgreSQL"],
  "architecture": "Monolith with Electron frontend",
  "api_routes": [
    { "path": "/webhooks/github", "method": "POST" },
    { "path": "/qry/health", "method": "GET" }
  ],
  "dependencies": {
    "python": ["fastapi", "uvicorn", "pydantic"],
    "javascript": ["react", "@anthropic-ai/claude-code"]
  }
}
```

---

## 6. Comparação Detalhada

### 6.1 Ideation System

| Aspecto | Auto-Claude | Skybridge |
|----------|-------------|-----------|
| **Implementado** | ✅ Completo | ❌ Não existe |
| **Tipos de Ideias** | 6 tipos especializados | N/A |
| **Execução** | Paralela (6 agentes simultâneos) | N/A |
| **Contexto** | Project index + Graphiti hints | N/A |
| **Validação** | JSON schema + recovery agent | N/A |
| **Persistência** | ideation.json estruturado | N/A |
| **Merge de Ideias** | Combina múltiplas fontes | N/A |
| **Priorização** | priority, effort, impact | N/A |
| **Append Mode** | Preserva ideias existentes | N/A |

---

### 6.2 Insight Extraction

| Aspecto | Auto-Claude | Skybridge |
|----------|-------------|-----------|
| **Implementado** | ✅ Completo | ❌ Não existe |
| **Trigger** | Após cada sessão de codificação | N/A |
| **Modelo** | Claude Haiku (rápido/barato) | N/A |
| **Inputs** | Diff, files, commits, attempt history | N/A |
| **Tipos de Insights** | 7 tipos (pattern, gotcha, etc) | N/A |
| **Memory** | Graphiti (long-term, searchable) | N/A |
| **Graceful Degradation** | Insights genéricos se falhar | N/A |
| **Blocking** | Não bloqueia build | N/A |

---

### 6.3 Discovery & Analysis

| Aspecto | Auto-Claude | Skybridge |
|----------|-------------|-----------|
| **Security Scanner** | ✅ Completo (secrets, CVEs) | ❌ Não existe |
| **Test Discovery** | ✅ Completo (coverage, gaps) | ❌ Não existe |
| **CI Discovery** | ✅ Completo (workflows, issues) | ❌ Não existe |
| **Risk Classifier** | ✅ Completo (factors, mitigation) | ❌ Não existe |
| **Project Analyzer** | ✅ Completo (tech stack, architecture) | ⚠️ Parcial (snapshot apenas) |
| **Framework Detection** | ✅ 50+ frameworks | ❌ Não existe |
| **Database Detection** | ✅ 10+ databases | ❌ Não existe |
| **Route Detection** | ✅ API routes automatic | ❌ Não existe |

---

### 6.4 Snapshot & Scoring (Skybridge)

**Implementado:** ADR000 - Descoberta via Score de Snapshot

**Arquitetura:**
```
Snapshot → GitExtractor → Snapshot Score → Registry
```

**Funcionalidades:**
- Extrai snapshot (metadata, stats, structure)
- Calcula score de snapshot
- Armazena em Registry
- Score-based discovery (ADRs)

**Diferença para Auto-Claude:**
- Skybridge: Snapshot-based (estado atual)
- Auto-Claude: Analysis-based (deep dive em múltiplas dimensões)

---

## 7. Fluxo de Uso Comparado

### 7.1 Ideation - Auto-Claude

```bash
# Executa ideation completa
cd apps/backend
python -m ideation.runner \
  --project-dir /path/to/project \
  --output-dir .auto-claude/ideation \
  --types code_improvements,security_hardening \
  --max-ideas 10 \
  --include-roadmap \
  --include-kanban

# Output: .auto-claude/ideation/ideation.json
```

**Workflow:**
1. Análise de projeto (index)
2. Coleta de contexto em paralelo
3. Geração de 6 tipos de ideias em paralelo
4. Merge e finalização
5. Ideias prontas para uso

---

### 7.2 Ideation - Skybridge

```bash
# NÃO EXISTE
# Apenas ADR000 snapshot scoring
```

**Alternativa Atual:**
- Snapshot scoring via GitExtractor
- Manual discovery por ADRs

---

### 7.3 Insight Extraction - Auto-Claude

```python
# Executa automaticamente após cada sessão
# Em: memory_manager.py

async def extract_session_insights(
    spec_dir: Path,
    project_dir: Path,
    subtask_id: str,
    session_num: int,
    commit_before: str,
    commit_after: str,
    success: bool,
):
    """Extrai insights e ingere no Graphiti"""
    inputs = gather_extraction_inputs(
        spec_dir, project_dir, subtask_id, session_num,
        commit_before, commit_after, success, recovery_manager
    )

    insights = await run_insight_extraction(inputs)

    # Ingest no Graphiti
    memory.add_session_insights(insights)

    return insights
```

**Trigger:** Automático após cada subtask completion

---

### 7.4 Insight Extraction - Skybridge

```bash
# NÃO EXISTE
# Apenas snapshot antes/depois
```

**Alternativa Atual:**
- Snapshot inicial antes de job
- Diff manual (se necessário)
- Preservação de worktree para inspeção

---

## 8. Comparação de Capacidades

### 8.1 Matriz de Funcionalidades

| Funcionalidade | Auto-Claude | Skybridge | Gap |
|---------------|-------------|-----------|------|
| **Ideation** |
| Geração de ideias de código | ✅ | ❌ | Completo |
| Melhorias de UI/UX | ✅ | ❌ | Completo |
| Gaps de documentação | ✅ | ❌ | Completo |
| Hardening de segurança | ✅ | ❌ | Completo |
| Otimizações de performance | ✅ | ❌ | Completo |
| Qualidade de código | ✅ | ❌ | Completo |
| **Insight Extraction** |
| Padrões de código | ✅ | ❌ | Completo |
| Gotchas (armadilhas) | ✅ | ❌ | Completo |
| Decisões arquiteturais | ✅ | ❌ | Completo |
| Lições aprendidas | ✅ | ❌ | Completo |
| Code smells | ✅ | ❌ | Completo |
| Dependências | ✅ | ❌ | Completo |
| Findings de performance | ✅ | ❌ | Completo |
| **Discovery** |
| Scanner de segurança | ✅ | ❌ | Completo |
| Descoberta de testes | ✅ | ❌ | Completo |
| Descoberta de CI/CD | ✅ | ❌ | Completo |
| Classificação de risco | ✅ | ❌ | Completo |
| Análise de projeto | ✅ | ⚠️ Parcial | Alto |
| Detecção de frameworks | ✅ | ❌ | Completo |
| Detecção de banco de dados | ✅ | ❌ | Completo |
| Detecção de rotas API | ✅ | ❌ | Completo |
| **Memory** |
| Long-term memory (Graphiti) | ✅ | ❌ | Completo |
| Semantic search | ✅ | ❌ | Completo |
| Cross-session context | ✅ | ❌ | Completo |
| **Skybridge Exclusivo** |
| Snapshot scoring | ❌ | ✅ | N/A |
| GitExtractor | ❌ | ✅ | N/A |
| Worktree preservation | ⚠️ Remove | ✅ Preserva | Reverso |

---

### 8.2 Prós e Contras

#### Auto-Claude

**Prós:**
✅ 6 tipos de ideação especializados
✅ Execução paralela (rápida)
✅ Contexto enriquecido (Graphiti)
✅ Extração automática de insights
✅ Long-term memory (Graphiti)
✅ Multiple analyzers (security, test, CI, risk)
✅ Graceful degradation (não bloqueia)
✅ Recovery agents (auto-correção)
✅ Validated JSON output
✅ Append mode (preserva ideias)

**Contras:**
❌ Remove worktree após sucesso (Skybridge preserva)
❌ Alta complexidade (múltiplos módulos)
❌ Dependência de Graphiti (obrigatório)
❌ Sem snapshot scoring (Skybridge tem)

---

#### Skybridge

**Prós:**
✅ Snapshot scoring (descoberta baseada em estado)
✅ Worktree preservation (inspeção fácil)
✅ Arquitetura simples
✅ GitExtractor robusto
✅ Sem dependência externa de memory

**Contras:**
❌ Sem ideation (não gera ideias)
❌ Sem insight extraction (não aprende)
❌ Sem discovery tools (não analiza projeto)
❌ Sem long-term memory (perde contexto)
❌ Manual discovery (ADRs only)
❌ Nenhum analyzer especializado

---

## 9. Recomendações de Evolução

### 9.1 Para Skybridge

**Prioridade Alta:**

1. **Implementar Ideation Básico**
   - Criar `ideation/` module
   - Implementar 1-2 tipos de ideias (code_improvements, security_hardening)
   - Usar prompts simples
   - Output: JSON estruturado

2. **Implementar Insight Extraction**
   - Criar `insight_extractor.py`
   - Trigger após cada job completion
   - Coletar: diff, files changed, commit messages
   - Extrair: patterns, gotchas, lessons learned
   - Persistir: `.auto-claude/insights.json` (temporário)

3. **Implementar Project Analyzer**
   - Criar `project_analyzer.py`
   - Detectar: linguagens, frameworks, databases
   - Usar heurísticas simples (package.json, requirements.txt, etc)
   - Output: JSON com stack tecnológico

**Prioridade Média:**

4. **Implementar Security Scanner Básico**
   - Scan por secrets em arquivos
   - Verificar .env, .env.example
   - Patterns: API keys, tokens, passwords
   - Output: findings.json

5. **Implementar Test Discovery Básico**
   - Descobrir arquivos de teste
   - Identificar módulos sem testes
   - Calcular coverage simples (se pytest disponível)
   - Output: test_summary.json

**Prioridade Baixa:**

6. **Expandir Ideation para 6 tipos**
   - Adicionar: ui_ux_improvements, documentation_gaps, performance_optimizations, code_quality
   - Criar prompts específicos
   - Paralelizar execução

7. **Integrar Memory System**
   - Considerar Graphiti ou similar
   - Persistir insights long-term
   - Habilitar semantic search

---

### 9.2 Para Auto-Claude

**Oportunidade:**

1. **Adotar Snapshot Scoring**
   - Implementar GitExtractor-style snapshot
   - Calcular score de mudança
   - Usar para priorizar ideias
   - Combinar com ideation existente

2. **Preservar Worktrees**
   - Adicionar flag para preservar worktree
   - Útil para debugging e inspeção
   - Similar ao RF005 do Skybridge

---

## 10. Conclusão

### 10.1 Resumo Executivo

**Ideation & Insight:**
- **Auto-Claude:** Sistema completo, maduro, com 6 tipos de ideação, extração automática de insights, multiple analyzers e long-term memory (Graphiti)
- **Skybridge:** Não implementado. Apenas snapshot scoring via ADR000.

**Gap Crítico:**
- Skybridge não possui nenhuma funcionalidade de ideation ou insight extraction
- Skybridge não tem discovery tools (security, test, CI analyzers)
- Skybridge perde contexto entre sessões (sem long-term memory)

**Vantagem Única do Skybridge:**
- Snapshot scoring e worktree preservation (Auto-Claude remove worktree)

---

### 10.2 Quando Usar Qual

**Use Auto-Claude se:**
- Precisa de ideias de melhoria automáticas
- Quer aprender com sessões anteriores (insights)
- Precisa descobrir segurança, testes, CI issues
- Quer long-term memory (Graphiti)
- Precisa de múltiplos analyzers especializados

**Use Skybridge se:**
- Quer snapshot scoring (estado atual)
- Prefere worktree preservado (inspeção manual)
- Arquitetura simples é prioridade
- Não precisa de ideation/insight (ainda)

---

### 10.3 Caminho de Evolução Sugerido

**Skybridge → Auto-Claude Features:**

```mermaid
graph LR
    A[Skybridge Atual] --> B[Phase 1: Insight Básico]
    B --> C[Phase 2: Ideation Básica]
    C --> D[Phase 3: Discovery Básico]
    D --> E[Phase 4: Memory System]
    E --> F[Auto-Claude Parity]

    style A fill:#f99
    style B fill:#ff9
    style C fill:#ff6
    style D fill:#ff3
    style E fill:#fc0
    style F fill:#9c0
```

**Phase 1 (1-2 semanas):**
- Insight extraction básica (patterns, gotchas, lessons)
- Trigger após job completion
- Persistir em JSON local

**Phase 2 (2-3 semanas):**
- Ideation básica (1-2 tipos)
- code_improvements + security_hardening
- Contexto simples (project index)

**Phase 3 (2-3 semanas):**
- Security scanner básico
- Test discovery básico
- Project analyzer (tech stack detection)

**Phase 4 (3-4 semanas):**
- Memory system (Graphiti ou similar)
- Long-term insights
- Semantic search

**Phase 5 (4-6 semanas):**
- Expandir para 6 tipos de ideation
- Multiple analyzers (CI, risk, etc)
- Full parity com Auto-Claude

---

## 11. Referências

### Auto-Claude
- **Ideation Orchestrator:** B:\_repositorios\auto-claude\apps\backend\ideation\runner.py
- **Ideation Generator:** B:\_repositorios\auto-claude\apps\backend\ideation\generator.py
- **Insight Extractor:** B:\_repositorios\auto-claude\apps\backend\analysis\insight_extractor.py
- **Security Scanner:** B:\_repositorios\auto-claude\apps\backend\analysis\security_scanner.py
- **Test Discovery:** B:\_repositorios\auto-claude\apps\backend\analysis\test_discovery.py
- **CI Discovery:** B:\_repositorios\auto-claude\apps\backend\analysis\ci_discovery.py
- **Risk Classifier:** B:\_repositorios\auto-claude\apps\backend\analysis\risk_classifier.py
- **Project Analyzer:** B:\_repositorios\auto-claude\apps\backend\analysis\project_analyzer.py

### Skybridge
- **ADR000 (Snapshot Discovery):** B:\_repositorios\skybridge\docs\adr\ADR000-Descoberta-via-Score-de-Snapshot.md
- **Git Extractor:** B:\_repositorios\skybridge\src\skybridge\platform\observability\snapshot\extractors\git_extractor.py
- **Snapshot:** B:\_repositorios\skybridge\src\skybridge\platform\observability\snapshot\domain\snapshot.py

---

> "Ideação gera o quê; Insight extrai o como; Discovery revela o porquê." – made by Sky 💡
