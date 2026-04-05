# Spec: Mutation Testing

## ADDED Requirements

### Requirement: Integrar mutmut para mutation testing
Skylab DEVE usar mutmut para introduzir bugs no código e validar qualidade dos testes.

#### Scenario: Executa mutmut
- **WHEN** mutation testing é executado
- **THEN** mutmut introduz mutants no código
- **AND** roda testes para cada mutant
- **AND** classifica como killed/survived

### Requirement: Calcular Mutation Score
Skylab DEVE calcular mutation score baseado em mutants killed vs total.

#### Scenario: Score com 90% killed
- **WHEN** 45 mutants killed, 5 survived
- **THEN** Mutation score = 45 / 50 = 0.90

#### Scenario: Score com 100% killed
- **WHEN** todos os mutants são killed
- **THEN** Mutation score = 1.0

#### Scenario: Score com 0% killed
- **WHEN** nenhum mutant é killed
- **THEN** Mutation score = 0.0
- **AND** code health máximo fica limitado a 0.5

### Requirement: Classificar mutants
Skylab DEVE classificar mutants por tipo para análise estruturada.

#### Scenario: Tipos de mutants
- **WHEN** mutmut gera mutants
- **THEN** cada mutant é classificado: Boundary, Arithmetic, Comparison, Logical, etc.
- **AND** tipo é usado para debugging

#### Scenario: Lista survivors
- **WHEN** mutation testing completa
- **THEN** Skylab retorna lista de survivors com tipo, linha e descrição

### Requirement: Integrar com code health
Skylab DEVE usar mutation score como componente principal (50%) do code health.

#### Scenario: Mutation domina o score
- **WHEN** mutation score = 0.0
- **THEN** code health máximo = 0.5 (mesmo com outros perfeitos)
- **AND** Skylab penaliza testes que não matam mutants

### Requirement: Thresholds de qualidade
Skylab DEVE definir thresholds para mutation score.

#### Scenario: Score acima de 80%
- **WHEN** mutation score > 0.80
- **THEN** qualidade é considerada aceitável

#### Scenario: Score entre 60-80%
- **WHEN** mutation score entre 0.60 e 0.80
- **THEN** qualidade é considerada marginal
- **AND** sugere melhorar testes

#### Scenario: Score abaixo de 60%
- **WHEN** mutation score < 0.60
- **THEN** qualidade é considerada ruim
- **AND** Skylab alerta que testes não são efetivos

> "Teste que não mata mutant é inútil" – Sky 🧬
