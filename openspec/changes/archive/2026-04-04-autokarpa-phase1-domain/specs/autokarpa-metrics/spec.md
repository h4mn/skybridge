## ADDED Requirements

### Requirement: Metrics define score, comparador e threshold de melhora
O sistema SHALL representar a configuração de métricas como value object imutável contendo: o nome da métrica, o comparador (`lower_is_better` ou `higher_is_better`), e o threshold mínimo de melhora.

#### Scenario: Criar métrica com lower_is_better
- **WHEN** uma métrica é criada com comparador `lower_is_better` e threshold 0.01
- **THEN** ela indica que scores menores são melhores e melhora mínima é 0.01

#### Scenario: Criar métrica com higher_is_better
- **WHEN** uma métrica é criada com comparador `higher_is_better` e threshold 0.005
- **THEN** ela indica que scores maiores são melhores e melhora mínima é 0.005

### Requirement: Metrics avalia se um score é melhora sobre o anterior
O Metrics SHALL ter método que compara dois scores e retorna se houve melhora significativa (acima do threshold).

#### Scenario: Lower is better com melhora significativa
- **WHEN** comparador é `lower_is_better`, threshold 0.01, score anterior 0.95, novo score 0.93
- **THEN** `is_improvement(0.95, 0.93)` retorna `True`

#### Scenario: Lower is better sem melhora significativa
- **WHEN** comparador é `lower_is_better`, threshold 0.01, score anterior 0.95, novo score 0.945
- **THEN** `is_improvement(0.95, 0.945)` retorna `False` (diferença 0.005 < threshold 0.01)

#### Scenario: Higher is better com melhoria
- **WHEN** comparador é `higher_is_better`, threshold 0.01, score anterior 0.80, novo score 0.85
- **THEN** `is_improvement(0.80, 0.85)` retorna `True`

#### Scenario: Mesmo score não é melhora
- **WHEN** score anterior e novo são iguais (0.95)
- **THEN** `is_improvement` retorna `False` independente do comparador

### Requirement: Metrics é imutável
Uma vez criado, o objeto Metrics SHALL ter seus campos imutáveis (frozen).

#### Scenario: Tentativa de alterar campo
- **WHEN** se tenta alterar o campo `threshold` de um Metrics existente
- **THEN** o sistema SHALL gerar `FrozenInstanceError`
