# Design: Demo Todo List

## Context

Skylab já está implementado e validado no modo Auto-Meta (self-hosting). Esta Demo valida que Skylab funciona evoluindo **código externo** - um produto separado com estrutura DDD modular.

## Goals

1. **Validar modo Demo**: Provar que Skylab evolui código fora de `programs/skylab/`
2. **Validar isolamento**: Agente modifica APENAS `target/`, nunca `core/testing/quality/`
3. **Validar métricas**: Mutation score > 0.80, PBT 1000 casos, Code Health > 0.70
4. **Demonstrar loop completo**: Spec → TDD → Código → Refactor → PBT → Mutation

## Decisões

### D1: Estrutura DDD Simplificada
**Decisão**: Todo List usa DDD com 3 camadas (domain, application, infrastructure)

**Justificativa**:
- DDD é padrão da indústria para sistemas complexos
- Separação clara de responsabilidades facilita testing
- Infrastructure pode ser mockada para testes unitários

**Estrutura**:
```
src/core/autokarpa/programs/demo-todo-list/
└── target/
    ├── domain/
    │   ├── entities.py        # Todo (id, title, status, created_at)
    │   └── value_objects.py   # TodoStatus (enum), TodoId (value object)
    ├── application/
    │   ├── use_cases.py       # AddTodo, ListTodos, MarkDone, RemoveTodo
    │   └── services.py        # TodoService (orchestrator)
    └── infrastructure/
        └── repository.py      # TodoRepository (in-memory para demo)
```

### D2: Persistência In-Memory
**Decisão**: Demo usa repositório in-memory, sem banco de dados

**Justificativa**:
- Demo deve ser simples o suficiente para rápida implementação
- Persistência em disco distrai do objetivo principal (validar Skylab)
- Repository pattern permite trocar facil para PostgreSQL no futuro

### D3: Testes Especificam Comportamento
**Decisão**: Testes são a especificação viva da Todo List

**Justificativa**:
- Segue princípio TDD estrito do projeto
- Testes espelham a spec OpenSpec 1:1
- Nomes de testes descritivos documentam comportamento

**Exemplo**:
```python
def test_adicionar_tarefa_cria_nova_todo_com_id_unico():
    """
    Spec: Requirement "Adicionar tarefa"
    GIVEN Todo List vazia
    WHEN adiciona "Comprar leite"
    THEN tarefa aparece com ID único e status pending
    """
    todo_list = TodoList()
    todo = todo_list.add("Comprar leite")

    assert todo.id is not None
    assert todo.title == "Comprar leite"
    assert todo.status == TodoStatus.PENDING
```

### D4: PBT Valida Propriedades Invariantes
**Decisão**: Hypothesis valida 3 propriedades: id único, ordenação preservada, título não vazio

**Justificativa**:
- PBT encontra edge cases que testes de exemplo não encontram
- 1000 casos gerados automaticamente cobrem combinações improváveis
- Propriedades invariantes documentam contratos do domínio

**Propriedades**:
```python
@given(st.lists(st.builds(Todo, ...)))
def test_ids_sao_unicos(todos):
    """IDs gerados são sempre únicos."""
    assert len(set(t.id for t in todos)) == len(todos)

@given(st.lists(st.builds(Todo, ...)))
def test_ordenacao_eh_preservada(todos):
    """Ordem de inserção é preservada."""
    todos_list = TodoList()
    for todo in todos:
        todos_list.add(todo)
    assert todos_list.all() == todos
```

### D5: Mutation Score > 0.80
**Decisão**: Testes devem matar pelo menos 80% dos mutants

**Justificativa**:
- Mutation score é a métrica mais forte para qualidade de testes
- Previne overfitting (agentes não podem "trapacear" com `return True`)
- 80% é threshold rigoroso mas alcançável para código simples

**Análise de Survivors**:
- Survivors críticos (boundary mutants: `==` → `!=`, `>` → `>=`) exigem testes extras
- Survivors não-críticos podem ser ignorados (ex: `log()` → `log("extra")`)

### D6: Refactoring Obrigatório
**Decisão**: Se complexidade ciclomática > 10, refactoring é obrigatório

**Justificativa**:
- Código espaguete é inaceitável mesmo que funcione
- Complexidade > 10 indica necessidade de extração de método
- Skylab deve demonstrar que melhora código, não apenas funcionalidade

## Fluxo Principal

```
1. Spec (demo-todo-list/spec.md)
   ↓
2. TDD - Testes gerados da spec (RED)
   ↓
3. Código mínimo para passar (GREEN)
   ↓
4. REFACTOR se complexidade > 10
   ↓
5. PBT - 1000 casos gerados
   ↓
6. Mutation - Score calculado
   ↓
7. Code Health = (mutation * 0.5) + (unit * 0.2) + (pbt * 0.15) + (complexity * 0.15)
   ↓
8. Keep (se melhorou) ou Discard (se piorou)
   ↓
9. Repita
```

## Modo Demo

**Execução**:
```python
run_skylab("demo-todo-list", iterations=100)
```

**O que acontece**:
1. Skylab lê `openspec/changes/demo-todo-list/proposal.md`
2. Skylab lê `openspec/changes/demo-todo-list/specs/demo-todo-list/spec.md`
3. Skylab lê `openspec/changes/demo-todo-list/design.md`
4. Skylab lê `openspec/changes/demo-todo-list/tasks.md`
5. Skylab gera testes em `tests/core/autokarpa/programs/demo-todo-list/`
6. Skylab evolui código em `src/core/autokarpa/programs/demo-todo-list/target/`
7. Skylab gera `results.tsv` com 20 colunas
8. Skylab mantém melhorias com `git commit`

**Isolamento**:
- Skylab (`programs/skylab/core/testing/quality/`) → FIXO, não modificado
- Todo List (`programs/demo-todo-list/target/`) → VARIÁVEL, modificado pelo agente

## Riscos Mitigados

| Risco | Mitigação |
|-------|-----------|
| DDD complexo distrai do objetivo | Estrutura simplificada, apenas 3 camadas |
| Performance com target maior | Demo é pequena (Todo List simples) |
| Agents trapaceam a métrica | Mutation score 50% domina code health |

## Success Criteria

1. ✅ Todos os testes passam
2. ✅ Mutation score > 0.80
3. ✅ PBT com 1000 casos passando
4. ✅ Code Health > 0.70
5. ✅ Agente modificou APENAS `target/`
6. ✅ `results.tsv` gerado com 20 colunas

> "Spec → Teste → Código → REFACTOR → PBT → Mutation → Snapshot → Diff → Medição → Repita" – Sky 🔬
