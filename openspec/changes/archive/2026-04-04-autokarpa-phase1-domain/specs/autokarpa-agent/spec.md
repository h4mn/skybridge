## ADDED Requirements

### Requirement: AutoResearchAgent mantém estado e histórico de experimentos
O sistema SHALL representar o agente de Auto Research como entidade de domínio com estado (`idle`, `running`, `stopped`) e histórico de experimentos executados.

#### Scenario: Criar agente no estado idle
- **WHEN** um novo AutoResearchAgent é criado
- **THEN** o estado é `idle` e o histórico de experimentos está vazio

#### Scenario: Agente inicia ciclo de experimentos
- **WHEN** o agente no estado `idle` inicia um ciclo
- **THEN** o estado muda para `running`

#### Scenario: Agente para ciclo de experimentos
- **WHEN** o agente no estado `running` recebe comando de parada
- **THEN** o estado muda para `stopped`

#### Scenario: Agente registra experimento no histórico
- **WHEN** um experimento é concluído (completed ou failed) durante execução do agente
- **THEN** o experimento é adicionado ao histórico do agente

### Requirement: AutoResearchAgent rastreia melhor score encontrado
O agente SHALL manter registro do melhor score encontrado durante o ciclo, incluindo qual experimento o alcançou.

#### Scenario: Primeiro experimento com sucesso
- **WHEN** o primeiro experimento é completed com score 0.95
- **THEN** o melhor score do agente é 0.95 e referencia esse experimento

#### Scenario: Novo score é pior que o melhor
- **WHEN** um experimento é completed com score 1.2 e o melhor atual é 0.95
- **THEN** o melhor score permanece 0.95

#### Scenario: Novo score supera o melhor
- **WHEN** um experimento é completed com score 0.80 e o melhor atual é 0.95 (menor é melhor)
- **THEN** o melhor score é atualizado para 0.80

### Requirement: AutoResearchAgent contabiliza experimentos por status
O agente SHALL prover contadores de experimentos por status (completed, failed) e total.

#### Scenario: Contagem após múltiplos experimentos
- **WHEN** o agente tem 3 completed e 1 failed no histórico
- **THEN** total é 4, completed é 3, failed é 1
