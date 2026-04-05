# Design: Autokarpa Sky Lab - Integration

## Decisão de Integration

### D7: Results.tsv Expandido + Registros Independentes

**Decisão:** `results.tsv` tem 20 colunas organizadas em 6 grupos. Registros independentes (JSON/MD) guardam detalhes quando necessário.

**Racional:**
- **Redundância útil**: Componentes individuais permitem debugging rápido sem recalcular
- **Análise de padrões**: "Mutation sempre baixo", "Muitos arquivos criados = estagnação"
- **Drift auditável**: Guardar quando stagnation/decline ocorreu permite análise de saúde do loop
- **TSV não explode**: Detalhes pesados vão para arquivos separados (JSON/MD)

**Alternativas consideradas:**
- **Apenas code_health**: Rejeitado - Impossível saber onde está o problema
- **Apenas components sem drift**: Rejeitado - Perde visibilidade da saúde do loop
- **Tudo em JSON único**: Rejeitado - Difícil de fazer queries rápidas
- **Apenas registros independentes**: Rejeitado - Perde visão rápida do histórico

### Estrutura de 20 colunas em 6 grupos

| Grupo | Colunas | Propósito |
|-------|---------|-----------|
| **Score (1)** | `code_health` | Decisão keep/discard |
| **Components (4)** | `mutation`, `unit`, `pbt`, `complexity` | Gargalos de qualidade |
| **Drift (3)** | `stagnation`, `decline`, `repetition` | Saúde do loop |
| **Diff (7)** | `added_files`, `modified_files`, `removed_files`, `moved_files`, `added_dirs`, `removed_dirs`, `size_delta` | Mudanças estruturais |
| **Metadata (3)** | `commit`, `memory_gb`, `status` | Identificação |
| **Descritores (2)** | `description`, `diff_path` | Contexto |

### Registros Independentes

| Registro | Quando | Formato | Conteúdo |
|----------|--------|---------|----------|
| `results/components/N.json` | Sempre | JSON | Detalhes granulares (mutants por tipo, survivors, etc.) |
| `results/drift/N.json` | Apenas se detectado | JSON | Janela, scores históricos, ação tomada |
| `results/review/N.md` | Sempre | Markdown | Diff estruturado navegável |

## Snapshot + Diff Estruturado

### Integração com Snapshot System

Skylab usa o sistema de snapshot existente em `src/runtime/observability/snapshot/` para rastrear mudanças estruturais.

### Fluxo por iteração

```python
# Antes da iteração
snapshot_before = capture_snapshot(
    subject="skylab",
    target="target/",
    depth=10,
    metadata={"iteration": i}
)

# ┏━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓
# ┃  AGENTE implementa mudança em target/    ┃
# ┗━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┛

# Depois da iteração
snapshot_after = capture_snapshot(
    subject="skylab",
    target="target/",
    depth=10,
    metadata={"iteration": i, "agent_description": description}
)

# Diff estruturado
diff = compare_snapshots(snapshot_before, snapshot_after)

# Renderiza para review
diff_markdown = render_diff(diff, format="markdown")
save_diff(diff, format="markdown", report=diff_markdown)
```

### O que o diff mostra

```markdown
# diff_20260405_042

## Resumo
- Arquivos adicionados: 1
- Arquivos modificados: 2
- Arquivos removidos: 0
- Delta de tamanho: +1024 bytes

## Mudanças
- **added**: `target/domain.py`
- **modified**: `target/solution.py`
- **modified**: `target/application.py`

## Resumo de mudanças (solution.py)
```python
+ def process(items: List[Item]) -> Result:
+     # Nova função de processamento
+     ...
```
```

## Integração Git

### Padrão Karpathy: results.tsv + Tags + Branches

```python
# core/git_integration.py

def create_experiment_branch(date_str: str) -> str:
    """
    Cria branch `autoresearch/<data>-0` no início.

    IMPORTANTE: Usa hífen, não colchetes.
    [N] causa glob expansion no bash.
    """
    branch_name = f"autoresearch/{date_str}-0"
    subprocess.run(["git", "checkout", "-b", branch_name])
    return branch_name

def rename_branch_on_improvement(iteration: int, branch_name: str) -> str:
    """
    Renomeia branch quando melhoria é encontrada.
    `autoresearch/abr05-0` → `autoresearch/abr05-42`
    """
    suffix = f"-{iteration}"
    new_name = branch_name.rsplit("-", 1)[0] + suffix

    subprocess.run(["git", "branch", "-m", new_name])
    return new_name

def record_iteration(results: Dict, iteration: int):
    """
    Registra iteração com timing correto.

    IMPORTANTE: Gravar ANTES do git reset.
    O hash do commit persiste mesmo após reset.
    """
    commit_hash = get_current_commit_hash()

    # Gravar ANTES do reset
    write_results_tsv({
        "commit": commit_hash,
        "code_health": results["code_health"],
        # ... outras colunas ...
        "status": "keep",  # ou "discard", "crash"
        "description": results["description"],
    })

    # Depois decide keep/discard
    if results["code_health"] < best_health:
        subprocess.run(["git", "reset", "--hard", "HEAD~1"])
```

## Integrações Opcionais

### Uso Direto (Padrão)

```python
from skylab import run_skylab

results = run_skylab("autokarpa-sky-lab", iterations=100)
print(f"Code Health final: {results['best_code_health']}")
```

### Ralph Loop (Opcional - Multi-sessão)

```python
from ralph_loop import run_ralph

run_ralph(
    program="skylab",
    input_change="autokarpa-sky-lab",
    iterations=1000,
    persist_state=True,  # Salva a cada iteração
)
```

**Vantagens:**
- Persistência de estado entre sessões
- Retomada após crash/pausa
- Checkpoint automático

### Autogrind (Opcional - Conveniência)

```bash
/autogrind skylab autokarpa-sky-lab
```

**Observação:** Skylab tem loop próprio. Autogrind é apenas wrapper redundante para conveniência.

### Skill Wrapper (Opcional)

```bash
/evolve autokarpa-sky-lab
```

**Observação:** Skill `/evolve` seria apenas wrapper para `run_skylab()`.

## Detecção de Drift

### Tipos de Drift

| Tipo | Detecção | Ação |
|------|----------|------|
| **Stagnation** | Variância < 0.01 nas últimas N iterações | Compactar contexto |
| **Decline** | Segunda metade da janela 10% pior que a primeira | Reinjetar prompt |
| **Repetition** | Similaridade > 0.9 nos últimos snippets | Aumentar temperatura |

### Registro de Drift

```json
// results/drift/iteration_042.json
{
  "iteration": 42,
  "drift_type": "stagnation",
  "window": "iterations 20-42",
  "scores": [0.45, 0.46, 0.45, 0.45, 0.46],
  "variance": 0.002,
  "action": "compact_context",
  "reason": "Variance < 0.01 threshold",
  "context_after": {
    "kept_iterations": 20,
    "tokens_saved": 45000
  }
}
```

> "O que não é medido não pode ser melhorado" – Sky 🔬
