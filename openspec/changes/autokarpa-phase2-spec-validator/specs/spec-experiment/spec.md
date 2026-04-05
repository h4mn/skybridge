## ADDED Requirements

### Requirement: Spec Experiment estende Experiment com domínio de specs
O `SpecExperiment` SHALL herdar de `Experiment` e adicionar campos específicos: `spec_requirement` (SpecRequirement) e `generated_test` (str).

#### Scenario: Criação com spec associada
- **WHEN** um SpecExperiment é criado com SpecRequirement e código de teste
- **THEN** o experimento contém referência ao requisito e o teste gerado

### Requirement: Spec Experiment rastreia resultado do teste
O experimento SHALL armazenar `test_passed` (bool | None) indicando se o teste gerado passou.

#### Scenario: Teste passou marca passed
- **WHEN** o Test Runner retorna sucesso
- **THEN** `test_passed` é True

#### Scenario: Teste falhou marca failed
- **WHEN** o Test Runner retorna falha
- **THEN** `test_passed` é False

### Requirement: Spec Experiment rastreia solução proposta
Quando o teste falha, o experimento SHALL armazenar `proposed_solution` (str | None) com o código corrigido proposto pela LLM.

#### Scenario: Solução proposta após falha
- **WHEN** Solution Generator retorna correção
- **THEN** `proposed_solution` contém o código Python corrigido
