# Plano de Teste: Orquestração Workflow Multi-Agente

**Objetivo:** Validar o fluxo create → resolve → test → challenge descrito na SPEC009

**Data:** 2026-01-12
**Duração Estimada:** 30-45 min
**Ambiente:** Skybridge local

---

## 1. Setup Inicial

```bash
# 1. Verificar worktrees limpas
git worktree list

# 2. Criar branch de teste
git checkout -b test/workflow-multi-agent

# 3. Verificar skills disponíveis
ls .agents/skills/
```

---

## 2. Cenário de Teste: Bug Simples

**Issue de Teste:**
```markdown
Title: fix: corrigir validação de input vazio em calculator.py

## Problema
A função `calculate()` não valida input vazio e levanta exceção.

## Reprodução
```python
from calculator import calculate
calculate("")  # Levanta ValueError não tratado
```

## Comportamento Esperado
Retornar 0 ou levantar exceção adequada com mensagem clara.
```

---

## 3. Fluxo Manual (Simulando cada agente)

### Passo 1: Issue Creator
**Manual:** Criar issue local

```bash
# Criar arquivo de issue
mkdir -p .test-run
cat > .test-run/issue.md << 'EOF'
# fix: corrigir validação de input vazio em calculator.py

## Problema
A função `calculate()` não valida input vazio e levanta exceção.

## Reprodução
```python
from calculator import calculate
calculate("")  # Levanta ValueError não tratado
```

## Comportamento Esperado
Retornar 0 ou levantar exceção adequada com mensagem clara.
EOF
```

**Verificar:**
- [ ] Issue criada em formato estruturado
- [ ] Labels aplicadas: `automated`, `bug`, `simple`

---

### Passo 2: Issue Resolver
**Skill:** `/resolve-issue` (ou execução manual simulada)

```bash
# Criar worktree para o resolver
git worktree add ../skybridge-test-resolver -b test/resolver-fix-calculator

# Entrar na worktree
cd ../skybridge-test-resolver

# Simular agente resolvendo
cat > src/calculator.py << 'EOF'
def calculate(input: str) -> float:
    if not input or not input.strip():
        raise ValueError("Input vazio não permitido")
    return float(input)
EOF

# Criar test
cat > tests/test_calculator.py << 'EOF'
import pytest
from calculator import calculate

def test_calculate_empty():
    with pytest.raises(ValueError, match="vazio"):
        calculate("")

def test_calculate_valid():
    assert calculate("42") == 42.0
EOF

# Commitar
git add .
git commit -m "fix: adicionar validação de input vazio em calculate()

- Levanta ValueError com mensagem clara
- Adiciona testes para edge case

Co-Authored-By: Claude <noreply@anthropic.com>"
```

**Verificar:**
- [ ] Worktree criada isoladamente
- [ ] Código implementado
- [ ] Testes criados
- [ ] Commit feito

---

### Passo 3: Issue Tester
**Skill:** `/test-issue` (ou execução manual)

```bash
# Na worktree do resolver
cd ../skybridge-test-resolver

# Rodar testes
pytest tests/test_calculator.py -v

# Verificar coverage
pytest tests/test_calculator.py --cov=. --cov-report=term-missing

# Lint
ruff check src/calculator.py

# Typecheck
mypy src/calculator.py
```

**Verificar:**
- [ ] Testes passam
- [ ] Coverage > 80%
- [ ] Zero erros de lint
- [ ] Zero erros de typecheck

**Se falhar:** Reabrir issue com label `test-failed`

---

### Passo 4: Quality Challenger
**Skill:** `/challenge-quality` (ataques adversariais)

```bash
# Na mesma worktree
cd ../skybridge-test-resolver

# === ATACAR: Boundary ===
python -c "
from calculator import calculate
test_cases = ['', '   ', '\n', '\t', None]
for case in test_cases:
    try:
        result = calculate(case)
        print(f'FAIL: {case!r} → {result} (deveria levantar erro)')
    except ValueError as e:
        print(f'PASS: {case!r} → ValueError: {e}')
    except Exception as e:
        print(f'BUG: {case!r} → {type(e).__name__}: {e}')
"

# === ATACAR: Type consistency ===
python -c "
from calculator import calculate
test_cases = ['123', '12.3', '0', '-5', '1e10']
for case in test_cases:
    try:
        result = calculate(case)
        print(f'{case!r} → {result!r} (type: {type(result).__name__})')
    except Exception as e:
        print(f'{case!r} → {type(e).__name__}: {e}')
"

# === ATACAR: Docs vs Código ===
echo "Verificando se README.md documenta a validação..."
grep -i "vazio\|empty\|validation" README.md || echo "BUG: Docs não mencionam validação"
```

**Verificar:**
- [ ] Boundary test passou
- [ ] Type consistency OK
- [ ] Docs consistentes com código

**Se encontrar bug:**
- Criar issue com label `challenge-exploit`
- Anexar POC

**Se docs inconsistentes:**
- Criar PR de correção
- Label `DOCS_MISMATCH`

---

## 4. Fluxo Completo com Webhook (Opcional)

Se o endpoint `/webhooks/github` estiver implementado:

```bash
# 1. Iniciar Skybridge
cd B:/_repositorios/skybridge
python -m skybridge

# 2. Enviar webhook manual
curl -X POST http://localhost:8000/webhooks/github \
  -H "Content-Type: application/json" \
  -H "X-GitHub-Event: issues" \
  -H "X-Hub-Signature-256: <calcular>" \
  -d @.test-run/webhook-payload.json

# 3. Observar worktree criada automaticamente
git worktree list

# 4. Verificar logs
tail -f .sky/agent.log
```

---

## 5. Checklist de Validação

### Fluxo Base
- [ ] Creator cria issue estruturada
- [ ] Resolver cria worktree isolada
- [ ] Resolver implementa solução
- [ ] Tester roda testes e valida
- [ ] Challenger ataca adversarialmente

### Handoffs
- [ ] Creator → Resolver: webhook com issue payload
- [ ] Resolver → Tester: PR aberta
- [ ] Tester → Challenger: testes passaram
- [ ] Challenger → Close: todos ataques falharam

### Estados da Issue
- [ ] `OPEN` → issue criada
- [ ] `IN_PROGRESS` → resolver trabalhando
- [ ] `READY_FOR_TEST` → PR aberta
- [ ] `UNDER_CHALLENGE` → tester passou
- [ ] `VERIFIED` → challenger aprovou
- [ ] `CLOSED` → fluxo completo

### Rollback
- [ ] `FAILED` → tester falha, volta para resolver
- [ ] `CHALLENGE_FAILED` → bug encontrado, volta para resolver
- [ ] `DOCS_MISMATCH` → docs atualizadas, reabre

---

## 6. Critérios de Sucesso

| Critério | Sucesso |
|----------|---------|
| Isolamento | Worktree separada para cada issue |
| Comunicação | Handoffs funcionam corretamente |
| Qualidade | Tester valida + Challenger ataca |
| Rollback | Falhas tratadas corretamente |
| Métricas | Cada fase gera métricas |

---

## 7. Limpeza

```bash
# Remover worktrees de teste
git worktree remove ../skybridge-test-resolver
git branch -D test/resolver-fix-calculator

# Remover arquivos de teste
rm -rf .test-run

# Voltar para branch original
git checkout main
```

---

## 8. Próximos Passos

Se teste **PASSAR**:
- Automatizar com skills reais
- Integrar com webhook system
- Adicionar métricas Prometheus

Se teste **FALHAR**:
- Documentar falha
- Ajustar SPEC009
- Corrigir implementação

---

> "Teste real é o único critério de verdade" – made by Sky 🧪
