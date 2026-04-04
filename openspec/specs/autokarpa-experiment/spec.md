# autokarpa-experiment Specification

## Purpose
TBD - created by archiving change autokarpa-phase1-domain. Update Purpose after archive.
## Requirements
### Requirement: Experiment tem ciclo de vida com estados definidos
O sistema SHALL representar um experimento como entidade de domínio com ciclo de vida: `proposed` → `running` → `completed` ou `failed`. Cada transição de estado DEVE ser válida — transições inválidas SHALL gerar erro.

#### Scenario: Criar experimento no estado proposed
- **WHEN** um novo Experiment é criado com código de mudança e descrição
- **THEN** o experimento está no estado `proposed` com timestamp de criação preenchido

#### Scenario: Transição proposed para running
- **WHEN** um experimento no estado `proposed` recebe o comando de iniciar execução
- **THEN** o estado muda para `running` e o timestamp de início é registrado

#### Scenario: Transição running para completed com score
- **WHEN** um experimento `running` é finalizado com sucesso com um score numérico
- **THEN** o estado muda para `completed`, o score e timestamp de fim são registrados

#### Scenario: Transição running para failed com motivo
- **WHEN** um experimento `running` falha durante execução
- **THEN** o estado muda para `failed` com mensagem de erro e timestamp de fim registrados

#### Scenario: Transição inválida gera erro
- **WHEN** se tenta transicionar de `completed` para `running`
- **THEN** o sistema SHALL lançar `ValueError` e manter o estado original

### Requirement: Experiment armazena código e descrição da mudança proposta
O Experiment SHALL conter o código da mudança proposta (string) e uma descrição legível da mudança. Esses campos são obrigatórios na criação.

#### Scenario: Criar experimento sem código
- **WHEN** se tenta criar um Experiment sem o campo de código
- **THEN** o sistema SHALL lançar erro de validação

#### Scenario: Criar experimento com código e descrição
- **WHEN** um Experiment é criado com código e descrição
- **THEN** ambos os campos ficam acessíveis na entidade

### Requirement: Experiment opcionalmente referencia experimento anterior
Um Experiment SHALL PODE referenciar o ID do experimento anterior na cadeia, formando um histórico encadeado.

#### Scenario: Criar experimento com referência ao anterior
- **WHEN** um Experiment é criado informando `previous_experiment_id`
- **THEN** a referência fica registrada e acessível

#### Scenario: Criar primeiro experimento sem referência
- **WHEN** um Experiment é criado sem `previous_experiment_id`
- **THEN** o campo é `None`

