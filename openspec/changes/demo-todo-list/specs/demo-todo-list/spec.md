# Spec: Demo Todo List

## ADDED Requirements

### Requirement: Implementar Todo List como demo
Skylab DEVE incluir uma implementação completa de Todo List como validação do Skylab em modo Demo (código externo).

#### Scenario: Todo List funcional
- **GIVEN** Skylab está executando em modo Demo
- **WHEN** demo é executada com `run_skylab("demo-todo-list")`
- **THEN** Skylab implementa Todo List com CRUD completo
- **AND** todos os testes unitários passam
- **AND** code health atinge threshold mínimo (> 0.70)

### Requirement: CRUD completo da Todo List
A demo DEVE implementar todas as operações básicas de uma Todo List.

#### Scenario: Adicionar tarefa
- **GIVEN** Todo List está vazia
- **WHEN** usuário adiciona tarefa "Comprar leite"
- **THEN** tarefa aparece na lista com ID único
- **AND** status da tarefa é "pending"

#### Scenario: Listar tarefas
- **GIVEN** Todo List contém 3 tarefas
- **WHEN** usuário solicita lista de tarefas
- **THEN** todas as 3 tarefas são retornadas
- **AND** ordenação de inserção é preservada

#### Scenario: Marcar tarefa como done
- **GIVEN** Todo List contém tarefa "Comprar leite" com status "pending"
- **WHEN** usuário marca tarefa como done
- **THEN** status da tarefa muda para "done"
- **AND** tarefa permanece na lista

#### Scenario: Remover tarefa
- **GIVEN** Todo List contém tarefa "Comprar leite"
- **WHEN** usuário remove tarefa
- **THEN** tarefa não aparece mais na lista
- **AND** IDs das outras tarefas são preservados

### Requirement: Estrutura DDD modular
A demo DEVE seguir arquitetura Domain-Driven Design com camadas separadas.

#### Scenario: Camadas separadas
- **WHEN** código da demo é inspecionado
- **THEN** existe camada `domain/` com entidades e value objects
- **AND** existe camada `application/` com use cases
- **AND** existe camada `infrastructure/` com persistência (se aplicável)

### Requirement: Spec da Todo List
A demo DEVE seguir esta spec OpenSpec completa.

#### Scenario: Spec define requisitos
- **WHEN** spec da demo é lida
- **THEN** contém requisitos: adicionar, listar, marcar done, remover
- **AND** cada requisito tem cenários GIVEN/WHEN/THEN

### Requirement: Testes gerados automaticamente
A demo DEVE usar testes gerados a partir da spec.

#### Scenario: Testes TDD
- **WHEN** demo roda
- **THEN** testes são gerados da spec
- **AND** seguem ciclo RED → GREEN → REFACTOR
- **AND** primeiro teste falha (RED)
- **AND** implementação mínima faz teste passar (GREEN)

### Requirement: PBT aplicado
A demo DEVE validar com Property-Based Testing.

#### Scenario: Propriedades da Todo List
- **GIVEN** Todo List com N tarefas
- **WHEN** PBT roda com 1000 casos
- **THEN** propriedade "id único é preservado" é validada
- **AND** propriedade "ordenação é preservada" é validada
- **AND** propriedade "título não vazio" é validada
- **AND** todos os 1000 casos passam

### Requirement: Mutation testing aplicado
A demo DEVE validar qualidade dos testes com mutation.

#### Scenario: Mutation score da demo
- **WHEN** mutation testing roda
- **THEN** mutation score deve ser > 0.80
- **AND** survivors são analisados
- **AND** survivors críticos (boundary, logical) são reportados

### Requirement: Completa o loop
A demo DEVE demonstrar o loop completo de evolução.

#### Scenario: Loop Spec → TDD → Código → ...
- **WHEN** demo é executada
- **THEN** Skylab demonstra fluxo completo
- **AND** `results.tsv` é gerado com 20 colunas
- **AND** code health final é aceitável (> 0.70)
- **AND** pelo menos uma melhoria foi mantida (git commit)

### Requirement: Isolamento do target
A demo DEVE garantir que o agente modifica APENAS código do target.

#### Scenario: Scope validation
- **GIVEN** Skylab está rodando em modo Demo
- **WHEN** agente propõe mudança
- **THEN** apenas arquivos em `target/` são modificados
- **AND** arquivos em `core/`, `testing/`, `quality/` NUNCA são modificados
- **AND** violações de scope são revertidas automaticamente

### Requirement: Documentação
A demo DEVE incluir documentação de como rodar.

#### Scenario: README da demo
- **WHEN** demo é inspecionada
- **THEN** contém instruções: como rodar, como interpretar resultados
- **AND** exemplo de `results.tsv` gerado
- **AND** métricas esperadas (mutation > 0.80, PBT 1000 casos)

### Requirement: Registros independentes
A demo DEVE gerar registros estruturados em `results/`.

#### Scenario: Registros gerados
- **WHEN** demo completa uma iteração
- **THEN** `results/components/` contém snapshots de cada componente
- **AND** `results/drift/` contém diffs estruturados
- **AND** `results/review/` contém análise de survivors

> "Demo que funciona prova que o Skylab funciona" – made by Sky 🚀
