# Spec: Demo Todo List

## ADDED Requirements

### Requirement: Implementar Todo List como demo
Skylab DEVE incluir uma implementação completa de Todo List como validação do Skylab.

#### Scenario: Todo List funcional
- **WHEN** demo é executada
- **THEN** Skylab implementa Todo List com CRUD
- **AND** todos os testes passam
- **AND** code health atinge threshold mínimo

### Requirement: Spec da Todo List
A demo DEVE seguir uma spec OpenSpec completa.

#### Scenario: Spec define requisitos
- **WHEN** spec da demo é lida
- **THEN** contém requisitos: adicionar, listar, marcar done, remover
- **AND** cada requisito tem cenários WHEN/THEN

### Requirement: Testes gerados automaticamente
A demo DEVE usar testes gerados a partir da spec.

#### Scenario: Testes TDD
- **WHEN** demo roda
- **THEN** testes são gerados da spec
- **AND** seguem ciclo RED → GREEN → REFACTOR

### Requirement: PBT aplicado
A demo DEVE validar com Property-Based Testing.

#### Scenario: Propriedades da Todo List
- **WHEN** PBT roda
- **THEN** testa propriedades: id único, ordenação preservada, etc.
- **AND** 1000 casos são gerados

### Requirement: Mutation testing aplicado
A demo DEVE validar qualidade dos testes com mutation.

#### Scenario: Mutation score da demo
- **WHEN** mutation testing roda
- **THEN** mutation score deve ser > 0.80
- **AND** survivors são analisados

### Requirement: Completa o loop
A demo DEVE demonstrar o loop completo de evolução.

#### Scenario: Loop Spec → TDD → Código → ...
- **WHEN** demo é executada
- **THEN** Skylab demonstra fluxo completo
- **AND** `results.tsv` é gerado
- **AND** code health final é aceitável

### Requirement: Documentação
A demo DEVE incluir documentação de como rodar.

#### Scenario: README da demo
- **WHEN** demo é inspecionada
- **THEN** contém instruções: como rodar, como interpretar resultados
- **AND** exemplo de `results.tsv` gerado

> "Demo que funciona prova que o Skylab funciona" – Sky ✅
