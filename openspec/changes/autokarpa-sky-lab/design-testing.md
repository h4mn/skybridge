# Design: Autokarpa Sky Lab - Testing

## Decisões de Testing

### D4: Property-Based Testing - Hypothesis

**Decisão:** Usar Hypothesis (Python) para PBT, gerando **1000 casos** por teste.

**Racional:**
- **Encontra edge cases não pensados**: Gera casos aleatórios automaticamente
- **Shrinking**: Reduz caso de falha ao mínimo reprodutível
- **Estado da arte**: Padrão em 2026 para Python
- **Substitui testes manuais**: Mais eficiente que escrever casos "na mão"

**Alternativas consideradas:**
- **Testes manuais**: Rejeitado - Não escala, propenso a erro humano
- **Fuzzing (libFuzzer)**: Rejeitado - Mais complexo, Hypothesis suficiente
- **Só unit tests**: Rejeitado - Não cobre edge cases adequadamente

**Conflitos conhecidos + Soluções:**
- `@given` com `pytest.mark.parametrize`: Usar `@given` por fora
- Multiprocessamento: Usar `derandomize=True`
- Settings globais: Configurar por teste

### D6: Debug Estruturado - Por Tipo de Mutant

**Decisão:** Debugger classifica mutants por tipo (Boundary, Arithmetic, Comparison, Logical) e sugere teste específico.

**Racional:**
- **Raciocínio estruturado**: Cada tipo tem padrão de correção
- **Ação concreta**: Sugere teste pronto para copiar/colar
- **Previne erro humano**: Guia desenvolvedor na correção

**Alternativas consideradas:**
- **Lista crua de survivors**: Rejeitado - Não ajuda a corrigir
- **Sugestão genérica**: Rejeitado - Não é acionável
- **Sem debug**: Rejeitado - Usuário perdido com survivors

## Módulos de Testing

### testing/pbt.py - Property-Based Testing

```python
from hypothesis import given, settings, strategies as st

@settings(max_examples=1000, derandomize=True)
@given(st.lists(st.integers(), min_size=0, max_size=100))
def test_sort_preserves_length(values):
    """Property: sort não altera tamanho da lista."""
    result = sort(values[:])
    assert len(result) == len(values)

@settings(max_examples=1000, derandomize=True)
@given(st.lists(st.integers()))
def test_sort_is_sorted(values):
    """Property: resultado está ordenado."""
    result = sort(values[:])
    assert result == sorted(result)
```

**Orçamento fixo:**
- `MAX_EXAMPLES = 1000` por teste
- `TIMEOUT = 30` segundos por teste
- `SHRINK_STEPS = 100` para reduzir falhas

### testing/mutation.py - Mutation Testing

**IMPORTANTE: Windows-Friendly**

Mutation testing em Python puro (sem mutmut):

```python
# Tipos de mutation suportados
MUTATION_TYPES = {
    "arithmetic": [
        (" + ", " - "),
        (" - ", " + "),
        (" * ", " / "),
    ],
    "comparison": [
        (" > ", " < "),
        (" < ", " > "),
        (" >= ", " <= "),
        (" <= ", " >= "),
        (" == ", " != "),
        (" != ", " == "),
    ],
    "logical": [
        (" and ", " or "),
        (" or ", " and "),
        ("not ", ""),  # Remove not
    ],
    "boundary": [
        # constantes ± 1
        (r"\b(\d+)\b", lambda m: str(int(m.group(1)) + 1)),
    ],
}

def run_mutation(target_dir: Path, budget: int = 50) -> Dict:
    """
    Executa mutation testing com orçamento fixo.

    Args:
        target_dir: Diretório com código a mutar
        budget: Máximo de mutants a testar (amostra se > budget)

    Returns:
        Dict: {total, killed, survived, by_type}
    """
    mutants = generate_mutants(target_dir)
    total = len(mutants)

    # Amostra se exceder budget
    if total > budget:
        mutants = random.sample(mutants, budget)

    results = {"killed": 0, "survived": 0, "by_type": defaultdict(int)}

    for mutant in mutants:
        if test_kills_mutant(mutant):
            results["killed"] += 1
        else:
            results["survived"] += 1
            results["by_type"][mutant.type] += 1

    results["total"] = total
    return results
```

**Vantagens vs Mutmut:**
- ✅ Funciona em Windows nativo
- ✅ Sem dependências externas
- ✅ Controle total sobre tipos de mutation
- ✅ Integração direta com testes

### testing/debug.py - Survivor Analysis

```python
def suggest_test_for_survivor(survivor: Mutant) -> str:
    """
    Sugere teste específico baseado no tipo de mutant.

    Pattern matching por tipo:
    """
    if survivor.type == "boundary":
        return f"""
# Teste para matar mutant de boundary em {survivor.function}

@given(st.integers(min_value={survivor.value - 2},
                   max_value={survivor.value + 2}))
def test_{survivor.function}_boundary_{survivor.value}(value):
    result = {survivor.function}(value)
    assert result == expected_value
"""

    elif survivor.type == "comparison":
        return f"""
# Teste para matar mutant de comparison em {survivor.function}

def test_{survivor.function}_boundary_case():
    # O mutant mudou {survivor.original_op} para {survivor.mutated_op}
    # Teste o caso limite onde isso importa
    result = {survivor.function}({survivor.test_value})
    assert result == {survivor.expected}
"""

    # ... mais tipos
```

**Prioridade de correção:**
1. **Boundary/Logical** - Mais fáceis de matar, alto impacto
2. **Comparison** - Média dificuldade
3. **Arithmetic** - Mais difíceis, podem ser equivalentes matemáticos

## Integração com Loop

```
TDD → Código → REFACTOR → PBT (Hypothesis) → Mutation (Python puro) → Medição
                          ↓
                    1000 casos    ↓
                              50 mutants (budget)
```

> "Testes que não matam mutants são inúteis" – Sky 🔬
