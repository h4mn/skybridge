# Spec: PBT Testing

## ADDED Requirements

### Requirement: Integrar Hypothesis para PBT
Skylab DEVE usar Hypothesis (Python) para Property-Based Testing.

#### Scenario: Gera 1000 casos por teste
- **WHEN** teste PBT é executado
- **THEN** Hypothesis gera 1000 casos automaticamente
- **AND** casos são aleatórios mas reproduzíveis (seed fixo)

#### Scenario: Usa estratégias do Hypothesis
- **WHEN** definindo propriedades
- **THEN** Skylab usa `@given(st.anything())` ou estratégias específicas
- **AND** configura `@settings(max_examples=1000, derandomize=True)`

### Requirement: Executar suítes PBT
Skylab DEVE executar testes PBT e retornar resultados agregados.

#### Scenario: Todos os casos PBT passam
- **WHEN** Hypothesis executa com todos os casos passando
- **THEN** retorna `{"passed": 1000, "failed": 0, "total": 1000, "success": true}`

#### Scenario: Alguns casos PBT falham
- **WHEN** Hypothesis encontra caso de falha
- **THEN** retorna `{"passed": X, "failed": Y, "total": X+Y, "success": false}`
- **AND** inclui caso reduzido (shrink) no resultado

### Requirement: Calcular PBT Score
Skylab DEVE calcular score PBT baseado em casos passando vs total.

#### Scenario: Score com 100% passing
- **WHEN** todos os 1000 casos passam
- **THEN** PBT score = 1.0

#### Scenario: Score com falhas
- **WHEN** 950 casos passam, 50 falham
- **THEN** PBT score = 950 / 1000 = 0.95

### Requirement: Detectar edge cases
Skylab DEVE usar PBT para encontrar edge cases não previstos manualmente.

#### Scenario: Encontra input vazio
- **WHEN** Hypothesis gera input vazio (None, "", [])
- **THEN** teste deve validar comportamento correto
- **AND** falha indica bug no tratamento de edge case

#### Scenario: Encontra input gigante
- **WHEN** Hypothesis gera input muito grande (ex: string de 1M chars)
- **THEN** teste deve validar que Skylab não crasha
- **OR** Skylab deve falhar graciosamente

#### Scenario: Encontra input malicioso
- **WHEN** Hypothesis gera input com padrões suspeitos (ex: SQL injection)
- **THEN** teste deve validar que Skylab é seguro
- **AND** falha indica vulnerabilidade

### Requirement: Shrink failures
Skylab DEVE usar o shrinking do Hypothesis para reduzir casos de falha ao mínimo.

#### Scenario: Falha é reduzida
- **WHEN** Hypothesis encontra falha com input complexo
- **THEN** Skylab reduz ao menor input reproduzível
- **AND** desenvolvedor recebe caso minimal para debug

### Requirement: Reprodutibilidade
Skylab DEVE garantir que testes PBT são reproduzíveis.

#### Scenario: Usa seed fixo
- **WHEN** executando testes PBT
- **THEN** Hypothesis usa seed fixo (ex: `--hypothesis-seed=0`)
- **AND** mesma execução produz mesmos casos

### Requirement: Integração com pytest
Skylab DEVE integrar PBT com pytest para execução unificada.

#### Scenario: Executa pytest com PBT
- **WHEN** usuário roda `pytest`
- **THEN** testes PBT são executados junto com unit tests
- **AND** resultados são agregados

> "1000 casos aleatórios > 10 casos manuais" – Sky 🎲
