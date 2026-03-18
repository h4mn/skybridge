# Turn Cancellation

Capacidade de interromper um turno em andamento.

## ADDED Requirements

### Requirement: TurnState deve incluir estado CANCELLED
O sistema SHALL adicionar o estado `CANCELLED` ao enum `TurnState`, permitindo que um turno em andamento seja interrompido pelo usuário.

#### Scenario: Estado CANCELLED disponível
- **WHEN** TurnState é importado e usado
- **THEN** estado CANCELLED está disponível ao lado de PENDING, THINKING, DONE

### Requirement: Usuário pode interromper turno durante processamento
O sistema SHALL permitir que o usuário interrompa um turno em andamento (estados PENDING ou THINKING) através de atalho de teclado ou botão.

#### Scenario: Interrupção por atalho de teclado
- **WHEN** usuário pressiona Ctrl+C durante processamento
- **THEN** turno transita para estado CANCELLED
- **AND** stream de eventos é encerrado graciosamente
- **AND** mensagem de feedback "Turno interrompido" é exibida

#### Scenario: Interrupção por botão na UI
- **WHEN** usuário clica botão [Parar] durante processamento
- **THEN** turno transita para estado CANCELLED
- **AND** stream de eventos é encerrado graciosamente

### Requirement: CANCELLED encerra stream sem crash
O sistema SHALL encerrar o stream de eventos do claude-agent-sdk sem propagar exceções ou crashar a aplicação quando turno é cancelado.

#### Scenario: Encerramento gracioso do stream
- **WHEN** turno transita para CANCELLED
- **THEN** `query()` do SDK é cancelado via `asyncio.CancelledError`
- **AND** recursos são limpos (conexões, tasks)
- **AND** aplicação permanece responsiva

### Requirement: Turno cancelado preserva mensagem do usuário
O sistema SHALL preservar a mensagem do usuário no histórico mesmo quando o turno é cancelado, permitindo retry posterior.

#### Scenario: Histórico preserva turno cancelado
- **WHEN** turno é cancelado
- **THEN** UserBubble permanece visível no histórico
- **AND** indicador visual "(interrompido)" é exibido
- **AND** botão [Retry] ainda funciona para reenviar

### Requirement: ThinkingIndicator para ao cancelar
O sistema SHALL remover `ThinkingIndicator` quando turno é cancelado, indicando visualmente que o processamento parou.

#### Scenario: Indicador removido ao cancelar
- **WHEN** turno transita para CANCELLED durante THINKING
- **THEN** ThinkingIndicator (spinner '...') é removido imediatamente
- **AND** nenhum StepWidget adicional é criado

### Requirement: AgenticLoopPanel congela ao cancelar
O sistema SHALL congelar o `AgenticLoopPanel` no estado atual quando turno é cancelado, mantendo Steps já criados visíveis.

#### Scenario: Painel congela com Steps parciais
- **WHEN** turno é cancelado com Steps em andamento
- **THEN** AgenticLoopPanel permanece visível com Steps criados
- **AND** StepWidget pendente mostra "(interrompido)" em ActionLine

---

> "Saber parar é tão importante quanto saber começar" – made by Sky 🛑
