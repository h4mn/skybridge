# Spec: Refactoring Automation

## ADDED Requirements

### Requirement: Obrigar refactoring após Green
Skylab DEVE exigir refactoring após código passar nos testes, antes de PBT/Mutation.

#### Scenario: Fluxo TDD completo
- **WHEN** testes passam (Green)
- **THEN** Skylab executa análise de complexidade
- **AND** SE complexidade > threshold: exige refactoring
- **AND** SÓ DEPOIS executa PBT/Mutation

### Requirement: Calcular complexidade ciclomática
Skylab DEVE calcular complexidade ciclomática usando radon.

#### Scenario: Complexidade abaixo do threshold
- **WHEN** complexidade média ≤ 10
- **THEN** código é considerado aceitável
- **AND** refactoring é opcional

#### Scenario: Complexidade acima do threshold
- **WHEN** complexidade média > 10
- **THEN** Skylab exige refactoring
- **AND** loop não avança até complexidade ser reduzida

### Requirement: Calcular Complexity Score
Skylab DEVE calcular score de complexidade para o code health.

#### Scenario: Score com complexidade baixa
- **WHEN** complexidade média = 5
- **THEN** Complexity score = 1 - (5 / 20) = 0.75

#### Scenario: Score com complexidade alta
- **WHEN** complexidade média = 15
- **THEN** Complexity score = 1 - (15 / 20) = 0.25

#### Scenario: Score máximo
- **WHEN** complexidade média = 0
- **THEN** Complexity score = 1.0

#### Scenario: Score mínimo
- **WHEN** complexidade média ≥ 20
- **THEN** Complexity score = 0.0

### Requirement: Threshold obrigatório
Skylab DEVE definir threshold de complexidade como obrigatório.

#### Scenario: Threshold de 10
- **WHEN** analisando código
- **THEN** Skylab usa threshold = 10 (radon)
- **AND** complexidade > 10 exige refactoring

### Requirement: Prevenir código espaguete
Skylab DEVE evitar que código acumule complexidade ao longo das iterações.

#### Scenario: Detecta aumento de complexidade
- **WHEN** iteração aumenta complexidade vs anterior
- **THEN** Skylab alerta sobre code smell
- **AND** sugere refactoring antes de continuar

> "Código complexo é bug em potencial" – Sky 🧹
