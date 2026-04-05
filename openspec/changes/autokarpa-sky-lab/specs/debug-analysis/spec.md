# Spec: Debug Analysis

## ADDED Requirements

### Requirement: Analisar mutants sobreviventes
Skylab DEVE fornecer análise estruturada para mutants que sobreviveram aos testes.

#### Scenario: Classifica por tipo
- **WHEN** mutant sobreviveu
- **THEN** Skylab classifica tipo: Boundary, Arithmetic, Comparison, Logical, etc.
- **AND** fornece padrão de correção para cada tipo

#### Scenario: Sugere teste específico
- **WHEN** mutant sobreviveu
- **THEN** Skylab sugere teste pronto para copiar/colar
- **AND** teste é específico para matar aquele tipo de mutant

### Requirement: Padrões de correção por tipo
Skylab DEVE fornecer orientação específica para cada tipo de mutant.

#### Scenario: Mutant Boundary
- **WHEN** mutant é do tipo Boundary (ex: `>` → `>=`)
- **THEN** Skylab sugere teste que exercita o limite
- **AND** exemplo: `assert process(0) == resultado_limite`

#### Scenario: Mutant Arithmetic
- **WHEN** mutant é do tipo Arithmetic (ex: `+` → `-`)
- **THEN** Skylab sugere teste que valida operação
- **AND** exemplo: `assert a + b == resultado_correto`

#### Scenario: Mutant Comparison
- **WHEN** mutant é do tipo Comparison (ex: `==` → `!=`)
- **THEN** Skylab sugere teste que valida comparação
- **AND** exemplo: `assert x == y quando devem ser iguais`

#### Scenario: Mutant Logical
- **WHEN** mutant é do tipo Logical (ex: `and` → `or`)
- **THEN** Skylab sugere teste que valida lógica
- **AND** exemplo: teste que cobre ambos os branches

### Requirement: Priorizar correção
Skylab DEVE priorizar mutants por impacto.

#### Scenario: Ordena por severidade
- **WHEN** múltiplos survivors existem
- **THEN** Skylab ordena por tipo e impacto
- **AND** Boundary/Logical têm prioridade alta

### Requirement: Rastrear correções
Skylab DEVE permitir rastrear quais mutants foram corrigidos.

#### Scenario: Marca mutant como corrigido
- **WHEN** usuário adiciona teste que mata mutant
- **THEN** Skylab atualiza status do mutant
- **AND** mutation score é recalculado

> "Cada mutant conta uma história sobre o que seu teste não cobre" – Sky 🔍
