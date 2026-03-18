# TTSService Capability

## ADDED Requirements

### Requirement: Lifecycle explícito
O TTSService SHALL ter lifecycle explícito com métodos `start()` e `stop()`.

#### Scenario: Start inicializa worker
- **WHEN** `start()` é chamado
- **THEN** worker TTS é criado e inicia processamento
- **AND** fila interna é inicializada
- **AND** serviço marca `_running = True`

#### Scenario: Stop para worker graciosamente
- **WHEN** `stop()` é chamado
- **THEN** sentinel `None` é enviado para fila
- **AND** método aguarda worker terminar (`await`)
- **AND** serviço marca `_running = False`

### Requirement: Enfileiramento non-blocking
O TTSService SHALL permitir enfileiramento de eventos sem bloquear o caller.

#### Scenario: Enqueue retorna imediatamente
- **WHEN** `enqueue(event)` é chamado
- **THEN** evento é adicionado à fila via `await queue.put()`
- **AND** método retorna (não aguarda processamento)

### Requirement: Buffer e fala inteligente
O worker TTS SHALL implementar lógica de buffer e fala (transferida do main.py).

#### Scenario: Buffer acumula até pontuação
- **WHEN** chunks de texto chegam
- **THEN** buffer acumula até 50+ chars com pontuação final (.!?)
- **AND** buffer é falado e limpo

#### Scenario: Transições de evento disparam fala
- **WHEN** `TOOL_RESULT` → `TEXT` transição ocorre
- **THEN** buffer anterior é falado antes de começar novo

### Requirement: Tratamento de CancelledError
O TTSService SHALL tratar `CancelledError` silenciosamente sem propagar.

#### Scenario: Worker cancelado não propaga erro
- **WHEN** `CancelledError` ocorre durante `speak()`
- **THEN** áudio é parado (`sd.stop()`)
- **AND** método retorna sem propagar exceção
- **AND** worker termina graciosamente

### Requirement: Isolamento de UI
O TTSService SHALL NOT conhecer UI ou Screen.

#### Scenario: Sem dependência de Textual
- **WHEN** TTSService é criado
- **THEN** nenhum import de `textual.*` é usado
- **AND** comunicação com UI é via `EventBus` apenas

## Context

**Purpose**: Serviço TTS isolado com lifecycle próprio.
**Consumes**: `StreamChunkEvent` via `enqueue()`
**Publishes**: `TTSStartedEvent`, `TTSCompletedEvent`
**Transferred from**: `MainScreen._tts_worker()` (~100 linhas)
