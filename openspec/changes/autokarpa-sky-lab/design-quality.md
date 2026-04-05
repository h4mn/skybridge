# Design: Autokarpa Sky Lab - Quality

## Decisão de Quality

### D5: Refactoring Obrigatório - Antes de PBT

**Decisão:** Refactoring é **OBRIGATÓRIO** após Green, antes de PBT/Mutation.

```
TDD → Código → REFACTOR → PBT → Mutation → Medição
```

**Racional:**
- **Martin Fowler (2023)**: "Negligenciar o terceiro passo é a forma mais comum de errar TDD"
- **Previne código espaguete**: Complexidade controlada antes de validar
- **Complexidade < 10**: Threshold aceitável (radon)

**Alternativas consideradas:**
- **Refactoring opcional**: Rejeitado - Código acumula debt
- **Refactoring após tudo**: Rejeitado - Muito tarde, código já complexo
- **Sem refactoring**: Rejeitado - Viola princípio TDD

## Módulos de Quality

### quality/complexity.py - Análise de Complexidade

```python
import radon
from radon.complexity import cc_visit

def calculate_complexity(target_dir: Path) -> Dict:
    """
    Calcula complexidade ciclomática média.

    Returns:
        Dict: {avg, max, worst_function, by_file}
    """
    results = []

    for py_file in target_dir.rglob("*.py"):
        for result in cc_visit(py_file.read_text()):
            results.append({
                "file": str(py_file),
                "function": result.name,
                "complexity": result.complexity,
            })

    if not results:
        return {"avg": 0, "max": 0, "worst_function": None}

    complexities = [r["complexity"] for r in results]
    worst = max(results, key=lambda x: x["complexity"])

    return {
        "avg": sum(complexities) / len(complexities),
        "max": max(complexities),
        "worst_function": f"{worst['function']} in {worst['file']}",
        "by_file": group_by_file(results),
    }

def calculate_complexity_score(avg_complexity: float) -> float:
    """
    Score baseado em complexidade média.

    Fórmula: 1 - (avg / 20)

    Complexidade 0 → score 1.0
    Complexidade 10 → score 0.5 (threshold)
    Complexidade 20+ → score 0.0
    """
    return max(0.0, 1.0 - (avg_complexity / 20.0))
```

### quality/refactor.py - Controle Automático

```python
class RefactorController:
    """
    Controla refactoring obrigatório após GREEN.

    Fluxo:
    1. Testes passam? → GREEN
    2. Complexidade < 10? → SIM: Pula refactoring
                         → NÃO: EXIGE refactoring
    3. Refactoring feito? → Continua para PBT/Mutation
    """

    COMPLEXITY_THRESHOLD = 10

    def __init__(self, target_dir: Path):
        self.target_dir = target_dir
        self.last_complexity = None

    def should_refactor(self, test_results: Dict) -> tuple[bool, str]:
        """
        Verifica se refactoring é necessário.

        Returns:
            (must_refactor, reason)
        """
        if not test_results["success"]:
            return False, "Tests failing - não chegou no GREEN"

        complexity = calculate_complexity(self.target_dir)

        if complexity["avg"] >= self.COMPLEXITY_THRESHOLD:
            return True, f"Complexidade {complexity['avg']:.1f} >= {self.COMPLEXITY_THRESHOLD}"

        if self.last_complexity and complexity["avg"] > self.last_complexity:
            return True, f"Complexidade aumentou {self.last_complexity:.1f} → {complexity['avg']:.1f}"

        return False, "Complexidade OK"

    def enforce_refactoring(self) -> str:
        """
        Bloqueia loop até refactoring ser feito.

        Returns:
            Mensagem de erro ou sucesso
        """
        must_refactor, reason = self.should_refactor({})

        if must_refactor:
            raise RefactoringRequiredError(
                f"Refactoring OBRIGATÓRIO: {reason}\n"
                f"Pior função: {calculate_complexity(self.target_dir)['worst_function']}\n"
                f"Extraia funções, reduza nesting, simplifique lógica."
            )

        return "Refactoring não necessário"
```

### Fluxo Completo com Quality

```python
# evolution.py

def run_evolution(change_name: str, iterations: int = 100):
    refactor_controller = RefactorController(target_dir)

    for i in range(iterations):
        # 1. Gerar testes das specs (RED)
        generate_tests_from_specs()

        # 2. Agente implementa (GREEN)
        agent_implements()

        test_results = run_tests()
        if not test_results["success"]:
            continue  # Agente falhou, próxima iteração

        # 3. REFACTOR OBRIGATÓRIO ← NOVO
        try:
            refactor_controller.enforce_refactoring()
        except RefactoringRequiredError as e:
            # Notifica agente que precisa refatorar
            notify_refactoring_required(e.message)
            continue  # Agente refatora na próxima iteração

        # 4. PBT + Mutation (só depois de refactoring)
        pbt_results = run_pbt()
        mutation_results = run_mutation()

        # 5. Calcular code health
        code_health = calculate_code_health(
            mutation=mutation_results["score"],
            unit=test_results["score"],
            pbt=pbt_results["score"],
            complexity=calculate_complexity_score(...),
        )

        # 6. Decidir keep/discard
        ...
```

## Prioridades de Refactoring

**Quando complexidade > 10:**

1. **Extrair função**: Bloco longo → função nomeada
2. **Reduzir nesting**: if/else aninhado → early return
3. **Simplificar condição**: expressão complexa → variável
4. **Separar responsabilidades**: função faz coisas demais → split

**Exemplo:**

```python
# ANTES (complexidade 12)
def process(data):
    if data is not None:
        if len(data) > 0:
            for item in data:
                if item is not None:
                    if item.valid:
                        # ... 20 linhas ...
                    else:
                        # ... 10 linhas ...
                else:
                    # ...
    # ...

# DEPOIS (complexidade 4)
def process(data):
    if not _is_valid_data(data):
        return []

    return [_process_item(item) for item in data if item is not None]

def _is_valid_data(data):
    return data is not None and len(data) > 0

def _process_item(item):
    if not item.valid:
        return default_value()
    return _transform_item(item)

def _transform_item(item):
    # ... lógica principal ...
```

> "Código complexo tem bugs complexos" – Sky 🔬
