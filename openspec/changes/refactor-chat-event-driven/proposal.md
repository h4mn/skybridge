## Why

O código atual do chat sofre de **race conditions** entre o stream do Claude Agent SDK e o worker TTS, causando erro `RuntimeError: Attempted to exit cancel scope in a different task`. Além disso, há **acoplamento forte** entre `MainScreen`, lógica de negócio e gerenciamento de workers, violando princípios de design (Single Responsibility, Dependency Inversion). A refatoração é necessária agora porque o problema está bloqueando funcionalidades críticas (TTS em texto final após AgenticLoop).

## What Changes

- **Introduz arquitetura Event-Driven** para desacoplar componentes via `EventBus`
- **Cria `TTSService`** isolado com lifecycle explícito (`start()`/`stop()`)
- **Cria `ChatOrchestrator`** para coordenar chat + TTS sem conhecer detalhes de UI
- **Cria `ChatContainer`** para gerenciar dependências e lifecycle com Dependency Injection
- **Remove código legado**: TTS worker de `MainScreen` (~100 linhas), estado mutável compartilhado
- **BREAKING**: `MainScreen._processar_mensagem` muda de implementação interna (interface pública mantida)

## Capabilities

### New Capabilities

- `event-bus`: Sistema de eventos assíncronos para comunicação loose-coupled entre componentes (chat, TTS, UI)
- `tts-service`: Serviço TTS isolado com lifecycle próprio, fila interna e worker dedicado
- `chat-orchestrator`: Orquestrador que coordena stream de chat com TTS em paralelo, publicando eventos de lifecycle

### Modified Capabilities

- `chat`: Comportamento de streaming muda internamente (usando orquestrador), mas interface `stream_response()` é mantida para compatibilidade

## Impact

- **Código afetado**: `src/core/sky/chat/textual_ui/screens/main.py` (~200 linhas removidas/transferidas)
- **Novos componentes**: `core/sy/events/`, `core/sy/chat/orchestrator.py`, `core/sy/voice/tts_service.py`, `core/sy/chat/container.py`
- **Dependencies**: Nenhuma dependência externa adicional (usa apenas asyncio padrão)
- **Sistemas**: Chat UI, TTS, Claude Agent SDK integration
- **Migração**: Retrocompatível via interface `stream_response()` mantida
