## ADDED Requirements

### Requirement: Program representa instruções do program.md
O sistema SHALL representar o arquivo `program.md` como value object imutável contendo: instruções textuais (string), restrições (lista de strings), e a métrica alvo.

#### Scenario: Criar Program com instruções e restrições
- **WHEN** um Program é criado com instruções "Otimize learning rate" e restrições ["não mudar arquitetura", "manter batch size"]
- **THEN** ambos os campos ficam acessíveis e imutáveis

#### Scenario: Criar Program sem restrições
- **WHEN** um Program é criado apenas com instruções
- **THEN** restrições é uma lista vazia por padrão

### Requirement: Program referencia métrica alvo
O Program SHALL referenciar um objeto Metrics que define como medir o sucesso dos experimentos.

#### Scenario: Program com métrica associada
- **WHEN** um Program é criado com métrica "loss" (lower_is_better, threshold 0.01)
- **THEN** a métrica fica acessível via `program.metrics`

#### Scenario: Program sem métrica
- **WHEN** se tenta criar um Program sem métrica
- **THEN** o sistema SHALL lançar erro de validação

### Requirement: Program é imutável
Uma vez criado, o objeto Program SHALL ter seus campos imutáveis (frozen).

#### Scenario: Tentativa de alterar instruções
- **WHEN** se tenta alterar o campo `instructions` de um Program existente
- **THEN** o sistema SHALL gerar `FrozenInstanceError`

### Requirement: Program valida instruções não vazias
O campo de instruções SHALL ser obrigatório e NÃO PODE ser string vazia ou apenas whitespace.

#### Scenario: Criar Program com instruções vazias
- **WHEN** se tenta criar um Program com instruções ""
- **THEN** o sistema SHALL lançar `ValueError`

#### Scenario: Criar Program com instruções apenas whitespace
- **WHEN** se tenta criar um Program com instruções "   "
- **THEN** o sistema SHALL lançar `ValueError`
