---
name: Resolve Issue
description: Analyze GitHub issue and implement solution following Skybridge multi-agent workflow. Use this skill when an issue webhook is received and needs to be resolved with a pull request.
version: 1.0.0
---

# Resolve Issue

Esta skill analisa issue recebida via webhook e implementa a solução criando uma pull request.

## Objetivo

Receber webhook de issue aberta (`issues.opened`), analisar o requisito e implementar solução em worktree isolado, criando pull request para aprovação.

## Quando Usar

Use esta skill quando:
- Webhook de issue aberta é recebido (`issues.opened`)
- Issue precisa ser resolvida com implementação de código
- Requisito está claro e bem estruturado
- Issue faz parte do workflow multi-agente (SPEC009)

## Não Usar

Não use esta skill quando:
- Issue é ambígua demais para implementação direta
- Issue requer apenas documentação (usar skill específica)
- Issue é apenas pergunta/discussão (não requer implementação)

## Análise de Issue

### 1. Ler Contexto da Issue

```python
# Extrair do webhook
issue = webhook["issue"]
issue_number = issue["number"]
title = issue["title"]
body = issue["body"]
labels = [label["name"] for label in issue["labels"]]

print(f"Issue #{issue_number}: {title}")
print(f"Labels: {labels}")
```

### 2. Identificar Tipo de Tarefa

| Tipo | Descrição | Exemplos |
|------|-----------|----------|
| **Bug fix simples** | Correção trivial em uma função | "Fix typo", "Add missing import" |
| **Bug fix complexo** | Correção envolve múltiplos arquivos | "Fix race condition", "Refactor authentication" |
| **Feature simples** | Nova funcionalidade pequena | "Add user search by email" |
| **Feature complexa** | Nova funcionalidade com múltiplas partes | "Add OAuth2 authentication" |
| **Refactor** | Melhoria de código sem mudar comportamento | "Extract service layer" |
| **Documentation** | Adição ou correção de documentação | "Update README", "Add API docs" |

### 3. Validar Completude

Verifique se a issue contém:

- ✅ Título claro
- ✅ Descrição detalhada
- ✅ Critérios de aceitação (quando aplicável)
- ✅ Contexto suficiente (por que é necessário?)
- ✅ Exemplos (quando aplicável)

Se faltar informações:
1. Comentar na issue solicitando esclarecimento
2. Não criar worktree até ter informações suficientes

## Implementação

### 1. Criar Worktree

```bash
# Formato: skybridge-{source}-{event_type}-{issue_id}-{short_id}
WORKTREE_PATH="B:/_repositorios/skybridge-auto/skybridge-github-issues-${ISSUE_NUMBER}-${SHORT_ID}"
BRANCH_NAME="webhook/github/issue/${ISSUE_NUMBER}/${SHORT_ID}"

# Criar worktree
git worktree add "${WORKTREE_PATH}" -b "${BRANCH_NAME}"
cd "${WORKTREE_PATH}"
```

### 2. Snapshot Inicial

```python
# Capturar estado antes da implementação
from skybridge.platform.observability.snapshot import FileOpsExtractor

extractor = FileOpsExtractor()
snapshot_before = extractor.capture(
    target=".",
    depth=5,
    include_extensions=[".py", ".md", ".json"]
)

print(f"Snapshot before: {snapshot_before.metadata.snapshot_id}")
```

### 3. Análise de Código

Ler e analisar código existente relacionado ao problema:

```python
# Identificar arquivos afetados
if "API" in title or "endpoint" in body:
    files_to_analyze = glob("src/skybridge/api/*.py")
elif "database" in title or "model" in body:
    files_to_analyze = glob("src/skybridge/models/*.py")

# Ler e analisar
for file_path in files_to_analyze:
    content = read_file(file_path)
    # Analisar estrutura, imports, funções
```

### 4. Implementar Solução

**Princípios:**
- **Usar INFERÊNCIA, nunca heurísticas** (SPEC008)
- Ler código antes de modificar
- Seguir padrões do projeto (conforme ADR003)
- Adicionar testes para nova funcionalidade
- Manter consistência com código existente

**Exemplo de implementação (Bug fix):**

```python
# Antes (bug)
def get_user(user_id: int) -> dict:
    query = f"SELECT * FROM users WHERE id = {user_id}"
    result = db.execute(query)
    return result.fetchone()

# Depois (corrigido)
def get_user(user_id: int) -> dict | None:
    query = "SELECT * FROM users WHERE id = %s"
    cursor = db.cursor()
    cursor.execute(query, (user_id,))
    result = cursor.fetchone()
    return dict(result) if result else None
```

### 5. Rodar Testes

```bash
# Testes unitários
pytest tests/unit/ -v

# Testes de integração
pytest tests/integration/ -v

# Lint
ruff check src/
black --check src/

# Typecheck
mypy src/
```

Se testes falharem:
1. Corrigir implementação
2. Re-rodar testes
3. Não criar PR até todos passarem

### 6. Commit Changes

```bash
# Adicionar arquivos
git add .

# Commit com mensagem padronizada
git commit -m "fix: resolve issue #${ISSUE_NUMBER}

- Corrige [descrição do bug]
- Adiciona [descrição da correção]
- Adiciona testes para [cenário]

Closes #${ISSUE_NUMBER}"
```

### 7. Push e Criar PR

```bash
# Push
git push -u origin "${BRANCH_NAME}"

# Criar PR
gh pr create \
  --title "[FIX/FEATURE] ${title}" \
  --body "Closes #${ISSUE_NUMBER}" \
  --label "automated"
```

## Template de Pull Request

```markdown
## Descrição

Implementa solução para #${ISSUE_NUMBER}: "${title}"

## Mudanças

### Arquivos Adicionados
- `src/skybridge/feature.py`

### Arquivos Modificados
- `src/skybridge/api/users.py`

### Arquivos Removidos
- Nenhum

## Testes

- [x] Testes unitários adicionados/atualizados
- [x] Testes de integração adicionados/atualizados
- [x] Todos os testes passam (pytest)
- [x] Coverage ≥ 80%

## Checklist

- [x] Código segue padrões do projeto (ADR003)
- [x] Código documentado com docstrings
- [x] Lint passou (ruff, black)
- [x] Typecheck passou (mypy)
- [x] Snapshot antes/depois capturados
- [x] Worktree limpo (no staged/unstaged changes)

## Snapshot Diff

**Antes:**
- Files: 150
- Git hash: abc123

**Depois:**
- Files: 151
- Git hash: def456
- Changes: +150 lines, -20 lines

---

## Requisitos da Issue

### 1. Requisito Original
[Copiar da issue]

### 2. Análise (Criador)
[Copiar da issue]

### 3. Critérios de Aceitação
- [x] Critério 1
- [x] Critério 2
- [x] Critério 3

## Agentes

- Criador: [ID do Creator]
- Resolvedor: [ID do Resolver - este agente]
- Testador: [ID do Testador - pendente]
- Desafiador: [ID do Desafiador - pendente]
```

## Snapshot Final

```python
# Capturar estado após implementação
snapshot_after = extractor.capture(
    target=".",
    depth=5,
    include_extensions=[".py", ".md", ".json"]
)

print(f"Snapshot after: {snapshot_after.metadata.snapshot_id}")

# Gerar diff
from skybridge.platform.observability.snapshot import DiffService

diff_service = DiffService()
diff = diff_service.compare(
    old=snapshot_before,
    new=snapshot_after
)

print(f"Changes: {diff.summary}")
```

## Validação de Worktree

```python
# Validar se worktree está limpo
from skybridge.core.contexts.webhooks.application.worktree_manager import GitExtractor

extractor = GitExtractor()
can_remove, message, status = extractor.validate_worktree(WORKTREE_PATH)

if can_remove:
    print("✅ Worktree limpo, pode ser removido")
    git worktree remove "${WORKTREE_PATH}"
else:
    print(f"⚠️  {message}")
    print(f"Status: {status}")
    # Mantém worktree para investigação
```

## Handoff para Testador de Issue

Após criar PR, postar webhook para iniciar testes:

```json
{
  "event": "pull_request.opened",
  "pr_number": 45,
  "issue_number": 123,
  "agent_id": "sky-resolver-001",
  "changes": {
    "files_created": ["src/skybridge/feature.py"],
    "files_modified": ["src/skybridge/api/users.py"],
    "files_deleted": []
  },
  "pr_url": "https://github.com/h4mn/skybridge/pull/45"
}
```

## Transição de Estado

Após criar PR:
1. Issue: `IN_PROGRESS` → `READY_FOR_TEST`
2. Webhook é postado para iniciar testes
3. Testador de Issue é ativado
4. Testador valida solução (testes, lint, typecheck, coverage)

## Métricas a Coletar

| Métrica | Tipo | Descrição |
|---------|------|-----------|
| `agent.resolve.duration` | histogram | Duração da implementação |
| `agent.resolve.files.created` | counter | Arquivos criados |
| `agent.resolve.files.modified` | counter | Arquivos modificados |
| `agent.resolve.lines.added` | histogram | Linhas adicionadas |
| `agent.resolve.lines.deleted` | histogram | Linhas removidas |
| `agent.resolve.test.pass.rate` | gauge | Taxa de sucesso dos testes |
| `agent.resolve.coverage.percentage` | gauge | Coverage de código |

## Validação Final

Antes de postar webhook para testador, verifique:

- ✅ Implementação completa
- ✅ Todos os testes passam
- ✅ Lint passou (ruff, black)
- ✅ Typecheck passou (mypy)
- ✅ Coverage ≥ 80% (ou mantido)
- ✅ PR criada com template completo
- ✅ Snapshot antes/depois capturados
- ✅ Worktree validado (limpo)
- ✅ Webhook foi postado

## Exemplo Prático

### Contexto

- Issue #123: "Corrige bug na API de usuários - retorna HTML ao buscar usuário inexistente"
- Labels: `automated`, `bug`, `high-priority`

### Execução

```bash
# 1. Criar worktree
git worktree add B:/_repositorios/skybridge-auto/skybridge-github-issues-123-abc123 -b webhook/github/issue/123/abc123
cd B:/_repositorios/skybridge-auto/skybridge-github-issues-123-abc123

# 2. Snapshot inicial
python -c "from skybridge.platform.observability.snapshot import FileOpsExtractor; FileOpsExtractor().capture('.', 5).save()"

# 3. Analisar código
read src/skybridge/api/users.py

# 4. Implementar correção
# ... [código] ...

# 5. Testes
pytest tests/unit/test_users.py -v
# Resultado: 12/12 passed

# 6. Commit
git add .
git commit -m "fix: return JSON instead of HTML for non-existent users

- Changes get_user to return JSON 404 response
- Removes HTML error page from user lookup
- Adds tests for 404 scenario

Closes #123"

# 7. Push + PR
git push -u origin webhook/github/issue/123/abc123
gh pr create --title "fix: return JSON instead of HTML for non-existent users" --body "Closes #123"
```

### Handoff

```json
{
  "event": "pull_request.opened",
  "pr_number": 45,
  "issue_number": 123,
  "changes": {
    "files_modified": ["src/skybridge/api/users.py"],
    "files_created": ["tests/unit/test_users_404.py"]
  },
  "pr_url": "https://github.com/h4mn/skybridge/pull/45"
}
```

## Transição de Estado

Após handoff:
1. Issue: `IN_PROGRESS` → `READY_FOR_TEST`
2. Testador de Issue é ativado
3. Testador inicia validação (testes, lint, typecheck, coverage)

## Referências

- [SPEC008 — AI Agent Interface](../../../../docs/spec/SPEC008-AI-Agent-Interface.md)
- [SPEC009 — Orquestração de Workflow Multi-Agente](../../../../docs/spec/SPEC009-orchestracao-workflow-multi-agente.md)
- [PRD013 — Webhook Autonomous Agents](../../../../docs/prd/PRD013-webhook-autonomous-agents.md)
- [ADR003 — Glossário, Arquiteturas e Padrões Oficiais](../../../../docs/adr/ADR003-Glossario_Arquiteturas_e_Padroes_Oficiais.md)

---

> "Uma implementação bem testada é metade do caminho para a qualidade." – made by Sky ✅
