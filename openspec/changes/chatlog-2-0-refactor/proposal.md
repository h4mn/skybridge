# ChatLog 2.0 - Refatoração com Event Bus e UI Cyberpunk

## Why

O widget `ChatLog` atual está **fortemente acoplado** ao `ChatLogger` - o logger chama métodos diretamente no widget (`debug()`, `info()`, `error()`, `evento()`), violando princípios de arquitetura limpa e o sistema de mensagens do Textual. Isso torna impossível:

- Trocar a implementação visual sem alterar o logger
- Ter múltiplos consumidores de logs (UI, arquivo, métricas)
- Testar componentes isoladamente

Além disso, o ChatLog carece de funcionalidades essenciais para debugging:
- **Sem filtro por nível** (ERROR, WARNING, INFO, etc.)
- **Sem busca** em tempo real
- **Sem copiar** logs filtrados para clipboard

A mudança é necessária agora porque:
1. O código atual está se tornando um gargalo para evolução da UI
2. A equipe precisa de ferramentas de debugging mais poderosas
3. A arquitetura atual não escala para novos requisitos (métricas, múltiplos sinks, etc.)

## What Changes

### Novo Módulo `src/core/sky/log/`

- **Event Bus + Streams**: Arquitetura pub/sub com `LogEventBus` central
- **Consumidores pluggable**: `FileLogConsumer`, `MetricsLogConsumer`, `ChatLogConsumer`
- **3 novos widgets**:
  - `LogFilter`: Botões rádio para filtro por nível (ALL, ERROR, WARNING, INFO, EVENT, DEBUG)
  - `LogSearch`: Input com busca reativa e highlight de matches
  - `LogCopier`: Botão para copiar logs filtrados para clipboard

### Refatoração do `ChatLog`

- Migração de `src/core/sky/chat/textual_ui/widgets/common/log.py` → `src/core/sky/log/widgets/chat_log.py`
- Adoção do sistema de mensagens do Textual (`post_message()`)
- Render com tema **Cyberpunk Terminal** (scanlines, phosphor glow)

### Integração Incremental

- `ChatLogger` atual (`src/core/sky/chat/logging.py`) **continua funcionando** como adapter sobre `LogEventBus`
- Sem breaking changes durante transição
- Depreciação gradual após migração completa

### POC para Desenvolvimento

- `src/core/sky/log/poc.py`: App Textual standalone para desenvolvimento iterativo
- `tests/unit/core/sky/log/poc_test.py`: Testes com `pytest-textual`

## Capabilities

### New Capabilities

- **log-event-bus**: Sistema pub/sub central para distribuição de eventos de log
- **log-consumer**: Interface para consumidores de log (arquivo, UI, métricas)
- **log-filter**: Filtro por nível de log (ALL, ERROR, WARNING, INFO, EVENT, DEBUG)
- **log-search**: Busca reativa em logs com highlight em tempo real
- **log-copier**: Cópia de logs filtrados para clipboard
- **cyberpunk-theme**: Tema visual CRT/terminal com scanlines e phosphor glow

### Modified Capabilities

- **chat-logger**: Adapter sobre `LogEventBus` (sem mudança de comportamento visível ao usuário)

## Impact

### Afetado

- **Código**:
  - Novo: `src/core/sky/log/` (módulo completo)
  - Modificado: `src/core/sky/chat/logging.py` (adapter)
  - Depreciado: `src/core/sky/chat/textual_ui/widgets/common/log.py` (manter durante transição)

- **Tests**:
  - Novo: `tests/unit/core/sky/log/` (todos componentes)
  - Modificado: `tests/unit/core/sky/chat/textual_ui/widgets/test_chat_widgets.py` (atualizar imports)

- **Dependencies**:
  - `pytest-textual`: Para testes visuais e snapshot
  - `pyperclip` ou clipboard nativo: Para função de copiar

- **APIs**:
  - Nova: `LogEventBus`, `LogConsumer` protocol
  - Mantida: `ChatLogger.info()`, `.debug()`, `.error()`, `.evento()` (compatibilidade)

### Não Afetado

- Comportamento visível ao usuário final
- Integração com `MainScreen`
- Redirecionamento de stdout/stderr
- Arquivo de log em disco
