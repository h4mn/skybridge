## 0. Testes FIRST (Pré-requisito Crítico)

- [x] 0.1 Escrever teste E2E do fluxo atual (chat + TTS)
- [x] 0.2 Capturar baseline de performance (tempo médio por turno)
- [x] 0.3 Documentar edge cases que funcionam hoje (para garantir regressão)
- [x] 0.4 Criar flag/feature toggle para alternar old/new implementation (N/A - troca direta com rollback rápido)

## 1. Infraestrutura de Eventos

- [x] 1.1 Criar `core/sy/events/__init__.py` com exports públicos
- [x] 1.2 Criar `core/sy/events/event_bus.py` com protocolo `EventBus`
- [x] 1.3 Criar `core/sy/events/in_memory_bus.py` implementando `EventBus`
- [x] 1.4 Criar `core/sy/chat/events.py` com eventos de domínio (`StreamChunkEvent`, `TurnStartedEvent`, `TurnCompletedEvent`, `TTSStartedEvent`, `TTSCompletedEvent`)
- [x] 1.5 Adicionar testes em `tests/unit/events/test_event_bus.py`

## 2. Serviço TTS Isolado

- [x] 2.1 Criar `core/sy/voice/tts_service.py` com classe `TTSService`
- [x] 2.2 Implementar métodos `start()`, `stop()`, `enqueue()`
- [x] 2.3 Implementar `_worker()` com lógica de buffer/fala (transferida de `MainScreen._tts_worker`)
- [x] 2.4 Adicionar tratamento de `CancelledError` silencioso
- [x] 2.5 Publicar `TTSStartedEvent`/`TTSCompletedEvent` durante fala
- [x] 2.6 Criar `core/sy/voice/__init__.py` com export `TTSService`
- [x] 2.7 Adicionar testes em `tests/unit/voice/test_tts_service.py`

## 3. Orquestrador de Chat

- [x] 3.1 Criar `core/sy/chat/orchestrator.py` com classe `ChatOrchestrator`
- [x] 3.2 Implementar `process_turn(message, turn_id)` retornando `AsyncIterator[StreamChunkEvent]`
- [x] 3.3 Publicar `TurnStartedEvent` no início
- [x] 3.4 Consumir `ClaudeChatAdapter.stream_response()` e publicar cada chunk
- [x] 3.5 Enviar eventos para `TTSService.enqueue()` (non-blocking)
- [x] 3.6 Publicar `TurnCompletedEvent` ao final
- [x] 3.7 Adicionar testes em `tests/unit/chat/test_orchestrator.py`

## 4. Container DI com Lifecycle

- [x] 4.1 Criar `core/sy/chat/container.py` com classe `ChatContainer`
- [x] 4.2 Implementar `ChatContainer.create()` factory method
- [x] 4.3 Implementar `shutdown()` para recursos em ordem reversa
- [x] 4.4 Implementar `__aenter__` e `__aexit__` para AsyncContextManager
- [x] 4.5 Criar `core/sy/chat/factory.py` com factory functions opcionais
- [x] 4.6 Adicionar testes de integração em `tests/integration/chat/test_container.py`

## 5. Integração com UI Textual (Migração Paralela)

- [x] 5.1 Modificar `src/core/sky/chat/textual_ui/screens/main.py`: adicionar `_container: ChatContainer | None`
- [x] 5.2 Criar método `_initialize_container()` para lazy initialization
- [x] 5.3 Criar `env var` ou flag para alternar entre old/new implementation
- [x] 5.4 Implementar `_processar_mensagem_new()` usando `container.orchestrator.process_turn()`
- [x] 5.5 Manter `_processar_mensagem_old()` como fallback durante migração
- [x] 5.6 Adicionar testes A/B comparando old vs new (mesma saída)
- [x] 5.7 Atualizar `on_unmount()` para chamar `container.shutdown()` apenas se container existir
- [x] 5.8 Validar que nova implementação produz mesmos resultados que old (testes A/B)

## 6. Componente Waveform UI

- [x] 6.1 Criar `src/core/sky/chat/textual_ui/widgets/header/waveform_controller.py`
- [x] 6.2 Implementar `WaveformController` como widget Textual
- [x] 6.3 Consumir `TTSStartedEvent`/`TTSCompletedEvent` via EventBus
- [x] 6.4 Atualizar header (`start_speaking`, `start_thinking`, `stop_waveform`)
- [x] 6.5 Adicionar `WaveformController` ao `MainScreen.compose()`

## 7. Limpeza de Código Legado

- [x] 7.1 Remover `MainScreen._tts_worker()` (~100 linhas)
- [x] 7.2 Remover `MainScreen._start_waveform()`, `_stop_waveform()`
- [x] 7.3 Remover `MainScreen._clean_text_for_speech()`
- [x] 7.4 Remover imports não utilizados relacionados a TTS
- [x] 7.5 Verificar que não há referências quebradas

## 8. Testes Abrangentes

- [x] 8.1 Completar testes de `EventBus` (publish/subscribe, multiple subscribers)
- [x] 8.2 Adicionar teste de limite de buffer (max 100 eventos)
- [x] 8.3 Adicionar teste de timeout (30s síntese, 60s fala)
- [x] 8.4 Completar testes de `TTSService` (lifecycle, enqueue, buffer logic)
- [x] 8.5 Completar testes de `ChatOrchestrator` (process_turn yield)
- [x] 8.6 Completar testes de integração do `ChatContainer`
- [x] 8.7 Executar benchmark de performance do EventBus (deve ser <1ms)
- [x] 8.8 Verificar coverage > 80% para novos componentes
- [x] 8.9 Testar fallback: se EventBus falhar, usa chamada direta

## 9. Documentação

- [x] 9.1 Criar `docs/architecture/chat-architecture.md` com diagrama de componentes
- [x] 9.2 Documentar fluxo de dados (User → Orchestrator → Chat/TTS → Events → UI)
- [x] 9.3 Documentar eventos em tabela (nome, quando, quem publica)
- [x] 9.4 Adicionar exemplos de uso (code snippets)
- [x] 9.5 Atualizar `README.md` se necessário

## 10. Validação Final e Rollback Plan

- [ ] 10.1 Executar testes: `pytest tests/unit/events/ tests/unit/voice/ tests/unit/chat/`
- [ ] 10.2 Executar testes de integração: `pytest tests/integration/chat/`
- [ ] 10.3 Executar testes A/B: old vs new implementation (deve ser idêntico)
- [ ] 10.4 Verificar que não há regressões: testar chat manualmente com flag new/old
- [ ] 10.5 Verificar que TTS funciona em texto final após AgenticLoop
- [ ] 10.6 Confirmar que não há mais erro "cancel scope in different task"
- [ ] 10.7 Medir performance: novo deve ser dentro de 5% do baseline
- [ ] 10.8 Testar rollback: reverter para código legado e confirmar que funciona
- [ ] 10.9 Documentar decisão final: (a) manter new como default, (b) manter old como fallback, ou (c) remover old
