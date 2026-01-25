---
name: Challenge Quality
description: Executa ataques adversariais para validar qualidade da solução antes de aprovação humana. Use esta skill quando todos os testes automatizados passaram e a solução precisa de validação profunda de segurança, boundary e performance.
version: 1.0.0
---

# Challenge Quality

Esta skill executa ataques adversariais para validar qualidade da solução antes de aprovação humana.

## Objetivo

Encontrar bugs, vulnerabilidades e inconsistências que testes automatizados não detectaram, através de:
- Testes de boundary (casos extremos)
- Testes de concorrência (race conditions)
- Testes de segurança (injection, bypass)
- Testes de performance (load, stress)
- Validação de documentação vs código

## Mentalidade

**"Isso vai quebrar. Deixa eu provar."**

- Cético por padrão
- Assume que tudo pode falhar
- Encontra bugs antes de usuários reais
- Documenta cada cenário testado
- Propõe melhorias concretas (não só aponta problemas)

## Quando Usar

Use esta skill quando:
- Todos os testes automatizados passaram
- Issue está no estado `UNDER_CHALLENGE`
- Pull request foi criada e validada
- Solução precisa de validação extrema antes de produção

## Não Usar

Não use esta skill quando:
- Testes ainda não passaram
- Código ainda está em desenvolvimento
- Solução é trivial (ex: correção de typo)

## Categorias de Ataque

### 1. Boundary Testing

**Objetivo:** Testar edge cases e valores extremos

| Cenário | Exemplo | Sucesso = |
|---------|---------|-----------|
| **Inputs vazios** | `""`, `None`, `[]` | Nenhuma falha |
| **Inputs nulos** | `null`, `undefined` | Nenhuma falha |
| **Valores extremos** | `INT_MAX`, `INT_MIN`, `0`, `-1` | Nenhuma falha |
| **Inputs muito grandes** | Strings de 1MB+, arrays de 10k+ itens | Nenhuma falha / timeout apropriado |
| **Inputs especiais** | Caracteres Unicode, emojis, SQL injection básica | Nenhuma falha |

**Exemplo de teste:**
```python
def test_boundary_extreme_values():
    # Input vazio
    result = api.get_user("")
    assert result.status_code == 400, "Deve rejeitar email vazio"

    # Input muito longo
    long_email = "a" * 10000 + "@example.com"
    result = api.get_user(long_email)
    assert result.status_code == 400, "Deve rejeitar email muito longo"

    # Caracteres especiais
    result = api.get_user("test@example.com\n; DROP TABLE users;")
    assert result.status_code == 400 or result.status_code == 404, "Deve tratar injection"
```

### 2. Concurrency Testing

**Objetivo:** Detectar race conditions e deadlocks

| Cenário | Exemplo | Sucesso = |
|---------|---------|-----------|
| **Race conditions** | 10 requisições simultâneas para mesmo recurso | Nenhum deadlock |
| **Resource contention** | Múltiplas threads escrevendo no mesmo arquivo | Nenhuma corrupção |
| **Deadlocks** | Requisições que bloqueiam outras | Nenhum deadlock |
| **Shared state** | Múltiplos agentes acessando cache compartilhado | Estado consistente |

**Exemplo de teste:**
```python
def test_concurrent_user_creation():
    import threading
    from queue import Queue

    results = Queue()

    def create_user():
        try:
            result = api.create_user({"email": f"user{threading.get_ident()}@test.com"})
            results.put(("success", result))
        except Exception as e:
            results.put(("error", str(e)))

    threads = [threading.Thread(target=create_user) for _ in range(10)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()

    # Verificar: todos criados, nenhum erro de race condition
    successes = [r for r in results.queue if r[0] == "success"]
    assert len(successes) == 10, f"Apenas {len(successes)}/10 usuários criados"
```

### 3. Security Testing

**Objetivo:** Encontrar vulnerabilidades de segurança

| Cenário | Exemplo | Sucesso = |
|---------|---------|-----------|
| **SQL Injection** | `" OR '1'='1"` | Nenhum exploit |
| **XSS** | `<script>alert('XSS')</script>` | Nenhum exploit |
| **Authentication bypass** | Token inválido/antigo | Acesso negado |
| **Authorization bypass** | Usuário comum acessando admin | Acesso negado |
| **Buffer overflow** | Input muito grande | Nenhum crash |
| **Path traversal** | `../../../etc/passwd` | Acesso negado |

**Exemplo de teste:**
```python
def test_security_sql_injection():
    # Tentar injection
    result = api.get_user("admin' OR '1'='1")
    assert result.status_code == 404, "SQL injection falhou (bom!)"

    # Tentar XSS
    result = api.get_user("<script>alert('XSS')</script>")
    assert result.status_code == 404, "XSS falhou (bom!)"

    # Tentar path traversal
    result = api.get_file("../../../etc/passwd")
    assert result.status_code == 403, "Path traversal bloqueado"
```

### 4. Performance Testing

**Objetivo:** Identificar problemas de performance

| Cenário | Métrica | Sucesso = |
|---------|---------|-----------|
| **Latência** | Tempo de resposta | <500ms p95 |
| **Throughput** | Requisições/segundo | >100 req/s (depende do endpoint) |
| **Memory leak** | Consumo de memória ao longo do tempo | Memória estável após 1000 reqs |
| **CPU usage** | Consumo de CPU durante carga | <80% p95 |
| **Load test** | 1000 requisições simultâneas | Zero erros |

**Exemplo de teste:**
```python
import time
import statistics

def test_performance_latency():
    latencies = []
    for i in range(100):
        start = time.time()
        result = api.get_user("test@example.com")
        end = time.time()
        latencies.append((end - start) * 1000)  # ms

    # p95 deve ser <500ms
    p95 = statistics.quantiles(latencies, n=100)[94]
    assert p95 < 500, f"p95 = {p95}ms (deve ser <500ms)"

    # média deve ser <200ms
    avg = statistics.mean(latencies)
    assert avg < 200, f"média = {avg}ms (deve ser <200ms)"
```

### 5. Documentation Testing

**Objetivo:** Validar consistência entre documentação e código

| Verificação | Exemplo | Sucesso = |
|-----------|---------|-----------|
| **API docs vs código** | Endpoint documentado? | 100% match |
| **Parâmetros** | Parâmetros corretos? | 100% match |
| **Exemplos** | Exemplos funcionam? | 100% funcionam |
| **README** | Instruções atualizadas? | 100% atualizado |

**Exemplo de verificação:**
```python
def test_docs_consistency():
    # Ler documentação
    docs = read_markdown("docs/api/users.md")
    documented_params = extract_params(docs)

    # Ler código
    code = read_python("src/skybridge/api/users.py")
    actual_params = extract_function_params(code, "get_user")

    # Comparar
    assert documented_params == actual_params, (
        f"Docs inconsistentes: "
        f"docs={documented_params}, code={actual_params}"
    )
```

## Fluxo de Execução

### 1. Analisar Contexto

- Ler resultados de testes (unit, integration, lint, typecheck)
- Identificar arquivos alterados
- Ler documentação relevante
- Entender o que foi implementado

### 2. Planejar Ataques

Para cada categoria (Boundary, Concurrency, Security, Performance, Docs):
- Listar possíveis ataques
- Priorizar por risco (High > Medium > Low)
- Criar testes específicos

### 3. Executar Ataques

```python
for category in ["boundary", "concurrency", "security", "performance", "docs"]:
    print(f"⚔️  Testando categoria: {category.upper()}")

    for attack in get_attacks_for_category(category):
        try:
            result = execute_attack(attack)
            if result.success:
                print(f"✅ {attack.name} falhou (bom!)")
            else:
                print(f"🎯 {attack.name} SUCEDEU (vulnerabilidade encontrada!)")
                log_vulnerability(attack, result)
        except Exception as e:
            print(f"⚠️  {attack.name} causou erro inesperado: {e}")
```

### 4. Documentar Resultados

Para cada vulnerabilidade encontrada, criar proof of exploit:

```markdown
## 🎯 BUG CRÍTICO ENCONTRADO

**Categoria:** Security
**Localização:** `src/skybridge/api/users.py:78`

### Proof of Concept

```python
# SQL Injection funciona!
import requests

# Payload malicioso
payload = "admin' OR '1'='1"

# Requisição
response = requests.get(f"http://api/users/{payload}")

# Resultado inesperado
# API retorna todos os usuários em vez de 404!
assert response.status_code == 200
assert len(response.json()) > 1  # Todos os usuários retornados!
```

### Resultado

**Comportamento esperado:** Deve retornar 404 "User not found"
**Comportamento atual:** Retorna 200 com lista de todos os usuários

### Impacto

- ❌ Qualquer usuário pode ver todos os usuários
- ❌ Privacidade comprometida
- ❌ Segurança totalmente comprometida

### Recomendação

1. Usar parâmetros preparados (prepared statements)
2. Validar input antes de query
3. Usar ORM para evitar SQL injection

### Severidade: CRITICAL
```

## Tratamento de Vulnerabilidades

### 1. Encontrar Bug/Crítico

**Ação:**
1. **CRIA NOVA ISSUE** com label `challenge-exploit`
2. Comenta na issue original:

```markdown
🎯 **BUG CRÍTICO ENCONTRADO**

**Categoria:** Security
**Localização:** `src/skybridge/api/users.py:78`

**Nova Issue Criada:** #<nova_issue_number>

**Proof of Concept:**
```python
[código do exploit]
```

**Resultado Inesperado:**
[descrição]

**Impacto:** Crítico — [explicar]

---

Issue atual está **AGUARDANDO** correção da nova issue.
```

3. Issue original fica aguardando resolução da nova issue
4. Issue: `UNDER_CHALLENGE` → **nova issue**

### 2. Encontrar Inconsistência de Docs

**Ação:**
1. Cria PR com correção da documentação
2. **CRIA NOVA ISSUE** com label `docs-mismatch`
3. Comenta na issue original:

```markdown
📚 **Docs vs Código Inconsistentes Encontrados**

**Discrepâncias:**
- **Doc diz:** `GET /api/users/{id}` retorna `{id, email, name}`
- **Código faz:** Retorna `{id, email, name, created_at, updated_at}`

**PR de Correção:** #<pr_correction_number>

**Nova Issue Criada:** #<nova_issue_number>

Issue atual está **AGUARDANDO** validação após docs atualizadas.
```

### 3. Todos os Ataques Falharam (Nenhuma Vulnerabilidade)

**Ação:**
1. Adiciona label `awaiting-approval`
2. Comenta:

```markdown
✅ **Testes Adversariais Passaram**

**Ataques executados:**
- ✅ Boundary (15 testes) — 0 exploits encontrados
- ✅ Concurrency (8 testes) — 0 deadlocks encontrados
- ✅ Security (20 testes) — 0 exploits encontrados
- ✅ Performance (10 testes) — P95 = 230ms (<500ms)
- ✅ Documentation (verificação completa) — 100% consistente

**Total:** 53 ataques adversariais executados, 0 vulnerabilidades encontradas

🚀 **AGUARDANDO APROVAÇÃO HUMANA**

Issue está pronta para aprovação humana.
```

3. Issue: `UNDER_CHALLENGE` → `AWAITING_HUMAN_APPROVAL`
4. Aguarda aprovação humana

## Mecanismo de Aprovação Humana

### 1. Quando Vulnerabilidades Encontradas

Não há aprovação humana:
- Nova issue é criada
- Issue original aguarda resolução da nova issue
- Após nova issue resolvida → Re-testar issue original

### 2. Quando Nenhuma Vulnerabilidade Encontrada

Há aprovação humana:
1. Humano revisa issue
2. Humano aprova:
   - Remove label `awaiting-approval`
   - Adiciona label `approved`
   - Comenta: "✅ Aprovado"
   - Issue: `AWAITING_HUMAN_APPROVAL` → `VERIFIED` → `CLOSED`
3. Humano rejeita:
   - Remove label `awaiting-approval`
   - Comenta com motivo
   - Issue fica aberta para rework

## Métricas a Coletar

| Métrica | Labels | Descrição |
|---------|---------|-----------|
| `agent.challenger.exploits_found` | issue_type, attack_cat | Exploits encontrados |
| `agent.challenger.false_positives` | issue_type | Teorias refutadas |
| `agent.challenger.attacks.executed` | attack_category | Total de ataques executados |
| `agent.challenger.issues.created` | reason | Issues criadas por desafiador |
| `agent.docs.consistency` | issue_type | Docs vs código match % |

## Exemplo Prático

### Contexto

- Issue #123: "Corrige bug na API de usuários"
- PR #45: "Fix user API"
- Arquivos: `src/skybridge/api/users.py`
- Testes: 100% pass

### Execução de Ataques

```python
attacks = [
    {"category": "boundary", "name": "empty_email", "payload": ""},
    {"category": "boundary", "name": "very_long_email", "payload": "a" * 10000 + "@test.com"},
    {"category": "security", "name": "sql_injection", "payload": "admin' OR '1'='1"},
    {"category": "security", "name": "xss", "payload": "<script>alert('XSS')</script>"},
]

results = execute_attacks(attacks)

# Resultado: 1 exploit encontrado!
# SQL injection funciona
```

### Resultado: Vulnerabilidade Encontrada

```markdown
🎯 **BUG CRÍTICO ENCONTRADO**

**Categoria:** Security
**Localização:** `src/skybridge/api/users.py:78`

**Nova Issue Criada:** #124

**Proof of Concept:**
```python
# SQL Injection funciona!
payload = "admin' OR '1'='1"
response = requests.get(f"http://api/users/{payload}")
# Retorna todos os usuários!
```

**Issue atual (#123) está aguardando resolução da nova issue (#124).**
```

## Validação Final

Antes de marcar como aguardando aprovação, verifique:

- ✅ Todos os ataques foram executados
- ✅ Proof of exploit criado para cada vulnerabilidade
- ✅ Nova issue criada para cada vulnerabilidade
- ✅ Documentação validada
- ✅ Métricas coletadas
- ✅ Issue está no estado correto

## Transição de Estado

| Cenário | Transição |
|---------|-----------|
| Vulnerabilidade encontrada | `UNDER_CHALLENGE` → **nova issue** |
| Docs inconsistentes | `UNDER_CHALLENGE` → **nova issue** |
| Tudo OK | `UNDER_CHALLENGE` → `AWAITING_HUMAN_APPROVAL` |

## Referências

- [SPEC009 — Orquestração de Workflow Multi-Agente](../../../../docs/spec/SPEC009-orchestracao-workflow-multi-agente.md)
- [PRD013 — Webhook Autonomous Agents](../../../../docs/prd/PRD013-webhook-autonomous-agents.md)
- [OWASP Top 10](https://owasp.org/www-project-top-ten/)
- [CWE Common Weakness Enumeration](https://cwe.mitre.org/)

---

> "Adversariedade construtiva = qualidade antes de produção" – made by Sky 🛡️
