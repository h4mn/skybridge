---
name: Test Issue
description: Valida solução executando testes automatizados (unit, integration, lint, typecheck). Use esta skill quando uma pull request foi criada e precisa de validação antes do desafio de qualidade.
version: 1.0.0
---

# Test Issue

Esta skill valida a solução implementada rodando testes automatizados antes de passar para o Desafiador de Qualidade.

## Objetivo

Validar que a solução implementada atende aos critérios de qualidade através de testes automatizados:
- Testes unitários
- Testes de integração
- Lint (ruff/black)
- Typecheck (mypy)
- Coverage de código

## Quando Usar

Use esta skill quando:
- Pull request foi criada (`pull_request.opened`)
- Issue foi movida para estado `READY_FOR_TEST`
- Resolvedor de Issue finalizou implementação
- Código precisa ser validado antes de desafios adversariais

## Não Usar

Não use esta skill quando:
- Código ainda está em desenvolvimento
- Pull request ainda não foi criada
- Testes foram rodados recentemente sem mudanças

## Análise de Mudanças

### 1. Identificar Arquivos Afetados

```python
# Extrair do webhook
pr_files = payload["pull_request"]["files"]

# Classificar por tipo
arquivos_python = [f for f in pr_files if f["filename"].endswith(".py")]
arquivos_test = [f for f in pr_files if f["filename"].startswith("tests/")]
arquivos_doc = [f for f in pr_files if f["filename"].endswith(".md")]
```

### 2. Determinar Tipo de Teste

| Tipo de Mudança | Testes Obrigatórios |
|-----------------|-------------------|
| **Bug fix** | Unit + Integration + Lint + Typecheck |
| **Feature** | Unit + Integration + Lint + Typecheck + Coverage > 80% |
| **Refactor** | Unit + Lint + Typecheck + Coverage mantido |
| **Documentation** | Lint (apenas se mudou código) |

## Execução de Testes

### 1. Testes Unitários

```bash
# Rodar testes unitários
pytest tests/unit -v --cov=src --cov-report=term-missing

# Critério: Todos os testes devem passar
# Métrica: coverage report
```

### 2. Testes de Integração

```bash
# Rodar testes de integração
pytest tests/integration -v

# Critério: Todos os testes devem passar
```

### 3. Lint

```bash
# Ruff (fast Python linter)
ruff check src/ tests/

# Black (formatter)
black --check src/ tests/

# Critério: Zero erros, zero warnings
```

### 4. Typecheck

```bash
# mypy (type checking)
mypy src/

# Critério: Zero erros de tipo
```

### 5. Coverage de Código

```bash
# Gerar relatório de coverage
pytest --cov=src --cov-report=json

# Critério: Coverage > 80% (mínimo)
# Preferível: Coverage > 90%
```

## Resultados Esperados

### Sucesso (Todos os testes passam)

```json
{
  "test_results": {
    "unit": {
      "status": "passed",
      "tests_count": 42,
      "passed": 42,
      "failed": 0,
      "skipped": 0
    },
    "integration": {
      "status": "passed",
      "tests_count": 15,
      "passed": 15,
      "failed": 0
    },
    "lint": {
      "status": "passed",
      "ruff_errors": 0,
      "ruff_warnings": 0,
      "black_errors": 0
    },
    "typecheck": {
      "status": "passed",
      "mypy_errors": 0
    },
    "coverage": {
      "total_coverage": "87%",
      "meets_criteria": true
    }
  },
  "overall_status": "passed",
  "message": "Todos os testes passaram. Pronto para desafio de qualidade."
}
```

### Falha (Testes falharam)

```json
{
  "test_results": {
    "unit": {
      "status": "failed",
      "tests_count": 42,
      "passed": 40,
      "failed": 2,
      "failures": [
        {
          "test": "tests/unit/test_user_service.py::test_get_user_by_id",
          "error": "AssertionError: Expected 200, got 404",
          "traceback": "..."
        }
      ]
    },
    "integration": {
      "status": "passed",
      "tests_count": 15,
      "passed": 15,
      "failed": 0
    },
    "lint": {
      "status": "failed",
      "ruff_errors": 1,
      "ruff_warnings": 3,
      "errors": [
        {
          "file": "src/skybridge/api/users.py",
          "line": 45,
          "error": "F401: 'UserModel' imported but unused"
        }
      ]
    },
    "typecheck": {
      "status": "passed",
      "mypy_errors": 0
    },
    "coverage": {
      "total_coverage": "72%",
      "meets_criteria": false
    }
  },
  "overall_status": "failed",
  "message": "Testes falharam: 2 unitários + 1 lint error + coverage abaixo do mínimo (72% < 80%)."
}
```

## Tratamento de Falhas

### 1. Testes Unitários Falharam

**Ação:**
1. Reabre issue com label `test-failed`
2. Comenta na issue:

```markdown
❌ **Testes Unitários Falharam**

**Testes com falha:**
- `tests/unit/test_user_service.py::test_get_user_by_id`
- `tests/unit/test_auth.py::test_invalid_token`

**Erros:**
```
AssertionError: Expected 200, got 404
```

**Logs completos:**
[anexar logs do pytest]
```

3. Notifica Resolvedor para rework
4. Issue: `READY_FOR_TEST` → `FAILED`

### 2. Lint Falhou

**Ação:**
1. Reabre issue com label `test-failed`
2. Comenta:

```markdown
❌ **Lint Falhou**

**Erros encontrados:**
- `src/skybridge/api/users.py:45` — F401: 'UserModel' imported but unused
- `src/skybridge/api/auth.py:78` — E501: Line too long (88 > 79 characters)

**Ações necessárias:**
1. Remover imports não utilizados
2. Quebrar linhas longas
3. Rodar `ruff check` e `black --check` localmente
```

### 3. Typecheck Falhou

**Ação:**
1. Reabre issue com label `test-failed`
2. Comenta:

```markdown
❌ **Typecheck Falhou**

**Erros de tipo:**
```
src/skybridge/api/users.py:45: error: Incompatible return value type (got "str", expected "int")
```

**Ações necessárias:**
1. Corrigir anotações de tipo
2. Rodar `mypy src/` localmente
```

### 4. Coverage Abaixo do Mínimo

**Ação:**
1. Reabre issue com label `test-failed`
2. Comenta:

```markdown
⚠️ **Coverage Abaixo do Mínimo**

**Coverage atual:** 72%
**Coverage mínima exigida:** 80%

**Arquivos com baixa coverage:**
- `src/skybridge/service/payment.py` — 45% coverage
- `src/skybridge/utils/validation.py` — 30% coverage

**Ações necessárias:**
1. Adicionar testes para linhas não cobertas
2. Re-rodar `pytest --cov=src` após adicionar testes
```

## Handoff para Desafiador de Qualidade

### 1. Quando Testes Passam

Se todos os testes passam, postar webhook para Desafiador:

```json
{
  "event": "issue.testes_passaram",
  "issue_number": 123,
  "pr_number": 45,
  "agent_id": "sky-tester-001",
  "test_results": {
    "unit": "passed",
    "integration": "passed",
    "lint": "passed",
    "typecheck": "passed",
    "coverage": "87%"
  },
  "challenge_context": {
    "attack_categories": ["boundary", "concurrency", "security", "performance"],
    "target_files": ["fix.py", "main.py"],
    "docs_to_verify": ["README.md", "docs/api/*.md"]
  }
}
```

### 2. Transição de Estado

- Issue: `READY_FOR_TEST` → `UNDER_CHALLENGE`
- Desafiador de Qualidade é ativado
- Desafiador recebe contexto de testes e arquivos

## Métricas a Coletar

| Métrica | Tipo | Descrição |
|---------|------|-----------|
| `test.unit.duration` | histogram | Duração dos testes unitários |
| `test.integration.duration` | histogram | Duração dos testes de integração |
| `test.unit.pass.rate` | gauge | Taxa de sucesso unitários (passed/total) |
| `test.lint.errors` | counter | Total de erros de lint |
| `test.typecheck.errors` | counter | Total de erros de typecheck |
| `test.coverage.percentage` | gauge | Coverage de código total |

## Validação Final

Antes de passar para Desafiador, verifique:

- ✅ Todos os testes unitários passam
- ✅ Todos os testes de integração passam
- ✅ Zero erros de lint
- ✅ Zero erros de typecheck
- ✅ Coverage ≥ 80% (ou mantido para refactor)
- ✅ Webhook foi postado para Desafiador
- ✅ Issue está no estado `UNDER_CHALLENGE`

## Exemplo Prático

### Contexto

- PR #45: "Corrige bug na API de usuários"
- Arquivos: `src/skybridge/api/users.py`, `tests/unit/test_users.py`

### Execução

```bash
# 1. Testes unitários
pytest tests/unit/test_users.py -v
# Resultado: 12/12 passed

# 2. Testes de integração
pytest tests/integration/test_api_users.py -v
# Resultado: 5/5 passed

# 3. Lint
ruff check src/ tests/
# Resultado: 0 errors, 0 warnings

# 4. Typecheck
mypy src/
# Resultado: Success: no issues found

# 5. Coverage
pytest --cov=src --cov-report=term
# Resultado: 87% coverage
```

### Handoff para Desafiador

```json
{
  "event": "issue.testes_passaram",
  "issue_number": 123,
  "pr_number": 45,
  "test_results": {
    "unit": "passed (12/12)",
    "integration": "passed (5/5)",
    "lint": "passed",
    "typecheck": "passed",
    "coverage": "87%"
  },
  "challenge_context": {
    "target_files": ["src/skybridge/api/users.py"],
    "docs_to_verify": ["README.md", "docs/api/users.md"]
  }
}
```

## Transição de Estado

Após handoff para Desafiador:
1. Issue: `READY_FOR_TEST` → `UNDER_CHALLENGE`
2. Desafiador de Qualidade é ativado
3. Desafiador inicia ataques adversariais

## Referências

- [SPEC009 — Orquestração de Workflow Multi-Agente](../../../../docs/spec/SPEC009-orchestracao-workflow-multi-agente.md)
- [PRD013 — Webhook Autonomous Agents](../../../../docs/prd/PRD013-webhook-autonomous-agents.md)
- [Pytest Documentation](https://docs.pytest.org/)
- [Ruff Documentation](https://docs.astral.sh/ruff/)
- [Mypy Documentation](https://mypy.readthedocs.io/)

---

> "Testes que passam não significam ausência de bugs, mas reduzem drasticamente a probabilidade." – made by Sky 🧪
