# EventBus Capability

## ADDED Requirements

### Requirement: Async publish-subscribe pattern
O EventBus SHALL implementar padrão publish-subscribe assíncrono para comunicação loose-coupled entre componentes.

#### Scenario: Publicar evento
- **WHEN** um componente chama `publish(event)`
- **THEN** o evento é enfileirado para todos os subscribers
- **AND** o publish retorna imediatamente (non-blocking)

#### Scenario: Subscrever recebe eventos
- **WHEN** um componente subscreve via `subscribe(event_type)`
- **THEN** todos os eventos daquele tipo são recebidos via async iterator
- **AND** múltiplos subscribers podem existir para o mesmo evento

### Requirement: Type-safe event delivery
O EventBus SHALL garantir type-safety na entrega de eventos.

#### Scenario: Apenas eventos do tipo solicitado
- **WHEN** subscriber se inscreve para `StreamChunkEvent`
- **THEN** apenas `StreamChunkEvent` são entregues
- **AND** outros tipos de eventos são ignorados

### Requirement: Thread-safe operations
O EventBus SHALL ser thread-safe para uso em ambiente asyncio.

#### Scenario: Concorrência de publishes
- **WHEN** múltiplas tasks publicam eventos simultaneamente
- **THEN** nenhum evento é perdido
- **AND** todos os subscribers recebem na ordem de publicação

### Requirement: Graceful shutdown
O EventBus SHALL suportar shutdown gracioso.

#### Scenario: Shutdown aguarda delivery
- **WHEN** shutdown é solicitado
- **THEN** eventos enfileirados são entregues antes de fechar
- **AND** novos publishes após shutdown são ignorados silenciosamente

## Context

**Purpose**: Desacoplar chat, TTS e UI via pub/sub.
**Consumers**: `ChatOrchestrator`, `TTSService`, `WaveformController`
**Events**: `StreamChunkEvent`, `TurnStartedEvent`, `TurnCompletedEvent`, `TTSStartedEvent`, `TTSCompletedEvent`
