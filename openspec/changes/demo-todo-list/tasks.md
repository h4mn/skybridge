# Tasks: Demo Todo List

## Progresso: 0/18 tarefas (0%)

## 1. Setup Estrutura

- [ ] 1.1 Criar bounded context `src/core/autokarpa/programs/demo-todo-list/`
- [ ] 1.2 Criar estrutura `target/` com camadas DDD (domain, application, infrastructure)
- [ ] 1.3 Criar diretório de testes `tests/core/autokarpa/programs/demo-todo-list/`
- [ ] 1.4 Criar `results/` para snapshots, diffs e reviews

## 2. Domain Layer

- [ ] 2.1 Criar entidade `Todo` com atributos: id, title, status, created_at
- [ ] 2.2 Criar value object `TodoStatus` (enum: PENDING, DONE)
- [ ] 2.3 Criar value object `TodoId` (UUID ou incremento)
- [ ] 2.4 Escrever testes da camada de domínio

## 3. Application Layer

- [ ] 3.1 Criar use case `AddTodo` - adiciona nova tarefa
- [ ] 3.2 Criar use case `ListTodos` - lista todas as tarefas
- [ ] 3.3 Criar use case `MarkDone` - marca tarefa como concluída
- [ ] 3.4 Criar use case `RemoveTodo` - remove tarefa
- [ ] 3.5 Criar `TodoService` como orquestrador dos use cases
- [ ] 3.6 Escrever testes da camada de application

## 4. Infrastructure Layer

- [ ] 4.1 Criar `TodoRepository` (in-memory para demo)
- [ ] 4.2 Implementar métodos: save, find_all, find_by_id, delete
- [ ] 4.3 Escrever testes do repositório

## 5. Property-Based Testing

- [ ] 5.1 Implementar propriedade "IDs são únicos"
- [ ] 5.2 Implementar propriedade "ordenação é preservada"
- [ ] 5.3 Implementar propriedade "título não vazio"
- [ ] 5.4 Validar 1000 casos do Hypothesis passando

## 6. Mutation Testing

- [ ] 6.1 Rodar mutation testing inicial
- [ ] 6.2 Analisar survivors críticos (boundary, logical)
- [ ] 6.3 Adicionar testes para matar survivors críticos
- [ ] 6.4 Validar mutation score > 0.80

## 7. Skylab Integration

- [ ] 7.1 Configurar `run_skylab("demo-todo-list", iterations=100)`
- [ ] 7.2 Validar que Skylab lê proposal, specs, design, tasks
- [ ] 7.3 Executar loop de evolução
- [ ] 7.4 Validar code health final > 0.70

## 8. Validação de Isolamento

- [ ] 8.1 Validar que agente modificou APENAS `target/`
- [ ] 8.2 Validar que `core/`, `testing/`, `quality/` NÃO foram modificados
- [ ] 8.3 Validar que violações de scope foram revertidas

## 9. Registros e Resultados

- [ ] 9.1 Validar que `results.tsv` foi gerado com 20 colunas
- [ ] 9.2 Validar que `results/components/` contém snapshots
- [ ] 9.3 Validar que `results/drift/` contém diffs estruturados
- [ ] 9.4 Validar que `results/review/` contém análise de survivors

## 10. Documentação

- [ ] 10.1 Criar README.md em `src/core/autokarpa/programs/demo-todo-list/`
- [ ] 10.2 Documentar como rodar: `run_skylab("demo-todo-list")`
- [ ] 10.3 Documentar como interpretar `results.tsv`
- [ ] 10.4 Documentar métricas esperadas (mutation > 0.80, PBT 1000 casos)

## 11. Testes Finais

- [ ] 11.1 Rodar todos os testes: `pytest tests/core/autokarpa/programs/demo-todo-list/`
- [ ] 11.2 Validar que todos os testes passam
- [ ] 11.3 Validar PBT com 1000 casos
- [ ] 11.4 Validar mutation score > 0.80
- [ ] 11.5 Validar code health > 0.70

> "Demo que funciona prova que o Skylab funciona" – made by Sky 🚀
