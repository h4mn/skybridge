# ChatOrchestrator Capability

## ADDED Requirements

### Requirement: Orquestração de chat + TTS
O ChatOrchestrator SHALL coordenar stream de chat com TTS em paralelo.

#### Scenario: Process turn yield eventos
- **WHEN** `process_turn(message, turn_id)` é chamado
- **THEN** `TurnStartedEvent` é publicado
- **AND** stream de chat é consumido
- **AND** cada `StreamChunkEvent` é publicado
- **AND** eventos são enviados para TTS (non-blocking)
- **AND** eventos são yielded para caller
- **AND** `TurnCompletedEvent` é publicado ao final

### Requirement: Publicação de eventos de lifecycle
O ChatOrchestrator SHALL publicar eventos de início/fim de turno.

#### Scenario: TurnStartedEvent no início
- **WHEN** `process_turn()` inicia
- **THEN** `TurnStartedEvent` é publicado com `turn_id` e `user_message`
- **AND** timestamp é incluído

#### Scenario: TurnCompletedEvent no fim
- **WHEN** stream termina (todos os chunks consumidos)
- **THEN** `TurnCompletedEvent` é publicado com `final_text` e `duration_ms`
- **AND** timestamp é incluído

### Requirement: Alimentação non-blocking de TTS
O ChatOrchestrator SHALL alimentar TTS sem bloquear o stream.

#### Scenario: TTS enqueue não bloqueia
- **WHEN** `StreamChunkEvent` é recebido do chat
- **THEN** evento é publicado
- **AND** evento é enviado para TTS via `enqueue()`
- **AND** próximo chunk é processado imediatamente (não aguarda TTS)

### Requirement: Isolamento de UI
O ChatOrchestrator SHALL NOT conhecer UI Textual.

#### Scenario: Sem dependência de Screen
- **WHEN** ChatOrchestrator é criado
- **THEN** nenhum import de `textual.*` é usado
- **AND** comunicação com UI é via eventos yieldados

### Requirement: Delega para ClaudeChatAdapter
O ChatOrchestrator SHALL delegar lógica de chat para `ClaudeChatAdapter`.

#### Scenario: Stream do chat é delegado
- **WHEN** `process_turn()` é chamado
- **THEN** `ClaudeChatAdapter.stream_response()` é usado
- **AND** orquestrador apenas adiciona lifecycle/events

## Context

**Purpose**: Coordenar chat + TTS sem conhecer detalhes de UI.
**Inputs**: `user_message`, `turn_id`
**Outputs**: `AsyncIterator[StreamChunkEvent]`
**Dependencies**: `ClaudeChatAdapter`, `TTSService`, `EventBus`
**Transferred from**: `MainScreen._processar_mensagem()` (~200 linhas de lógica)
