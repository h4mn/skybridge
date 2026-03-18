# ChatLog 2.0 - Lista de Tarefas

## 1. Fundações - Estrutura e Event Bus

- [ ] 1.1 Criar estrutura de diretórios `src/core/sky/log/`
- [ ] 1.2 Criar estrutura de diretórios `tests/unit/core/sky/log/`
- [ ] 1.3 Implementar `LogLevel` enum com hierarquia (DEBUG < INFO < EVENT < WARNING < ERROR)
- [ ] 1.4 Implementar `LogEntry` (dataclass imutável com level, message, timestamp, metadata)
- [ ] 1.5 Implementar `LogEventBus` (pub/sub com subscribe/unsubscribe/publish)
- [ ] 1.6 Adicionar thread-safety ao `LogEventBus` (usar threading.Lock ou asyncio.Lock)
- [ ] 1.7 Implementar estatísticas no `LogEventBus` (contador de eventos publicados)
- [ ] 1.8 Testes unitários para `LogLevel` (comparações, hierarquia)
- [ ] 1.9 Testes unitários para `LogEntry` (imutabilidade, criação, metadados)
- [ ] 1.10 Testes unitários para `LogEventBus` (pub/sub, thread-safety, estatísticas)

## 2. Consumers

- [ ] 2.1 Definir Protocol `LogConsumer` (interface com método write_log)
- [ ] 2.2 Implementar `FileLogConsumer` (escrita em arquivo com rotação)
- [ ] 2.3 Implementar rotação de arquivo no `FileLogConsumer` (tamanho máximo, backup .1, .2, etc.)
- [ ] 2.4 Implementar `MetricsLogConsumer` (contadores por nível)
- [ ] 2.5 Implementar `BufferConsumer` (buffer circular em memória)
- [ ] 2.6 Implementar `TeeConsumer` (envia para múltiplos consumidores)
- [ ] 2.7 Testes unitários para `FileLogConsumer` (escrita, rotação)
- [ ] 2.8 Testes unitários para `MetricsLogConsumer` (contadores, reset)
- [ ] 2.9 Testes unitários para `BufferConsumer` (buffer circular, get_entries)
- [ ] 2.10 Testes unitários para `TeeConsumer` (encadeamento de consumidores)

## 3. Widgets - LogFilter

- [ ] 3.1 Criar `src/core/sky/log/widgets/` estrutura
- [ ] 3.2 Implementar `LogFilter` widget (botões rádio ALL/ERROR/WARNING/INFO/EVENT/DEBUG)
- [ ] 3.3 Implementar mensagem `FilterChanged` emitida ao mudar seleção
- [ ] 3.4 Adicionar contador de mensagens visíveis (X/total)
- [ ] 3.5 Implementar métodos `set_level()` e `clear_filter()`
- [ ] 3.6 Testes unitários para `LogFilter` (seleção, emissão de eventos, contadores)

## 4. Widgets - LogSearch

- [ ] 4.1 Implementar `LogSearch` widget (Input com busca reativa)
- [ ] 4.2 Adicionar reactive attribute `search_term`
- [ ] 4.3 Implementar debounce de 300ms (usar set_interval do Textual)
- [ ] 4.4 Implementar highlight de matches (style="inverse")
- [ ] 4.5 Implementar busca case-insensitive
- [ ] 4.6 Adicionar indicador de "X matches encontrados"
- [ ] 4.7 Implementar botão de limpar busca (X)
- [ ] 4.8 Adicionar suporte a curingas (* e ?)
- [ ] 4.9 Implementar navegação Next/Previous entre matches
- [ ] 4.10 Testes unitários para `LogSearch` (debounce, highlight, contadores)

## 5. Widgets - LogCopier

- [ ] 5.1 Implementar `LogCopier` widget (Button com ícone de clipboard)
- [ ] 5.2 Implementar cópia respeitando filtro ativo
- [ ] 5.3 Implementar cópia respeitando busca ativa
- [ ] 5.4 Adicionar formatação de linhas copiadas (timestamp + nível)
- [ ] 5.5 Implementar notificação de sucesso ("X linhas copiadas!")
- [ ] 5.6 Implementar tratamento de erro quando clipboard não disponível
- [ ] 5.7 Adicionar fallback para clipboard nativo do Textual (se pyperclip não disponível)
- [ ] 5.8 Testes unitários para `LogCopier` (cópia, filtros, notificações)

## 6. ChatLog 2.0 - Core Widget

- [ ] 6.1 Implementar `ChatLog` widget que herda de VerticalScroll
- [ ] 6.2 Integrar com `LogEventBus` (subscribe no on_mount, unsubscribe no on_unmount)
- [ ] 6.3 Implementar armazenamento de `_entries` (list de LogEntry)
- [ ] 6.4 Implementar filtro por nível (respeitar LogFilter.FilterChanged)
- [ ] 6.5 Implementar busca (respeitar LogSearch.SearchChanged)
- [ ] 6.6 Implementar highlight de matches durante render
- [ ] 6.7 Implementar buffer de 100 linhas quando widget está fechado
- [ ] 6.8 Implementar flush em batch para evitar flicker
- [ ] 6.9 Testes unitários para `ChatLog` (event bus, filtros, render)

## 7. Tema Cyberpunk

- [ ] 7.1 Criar `src/core/sky/log/theme.py` com definição de cores
- [ ] 7.2 Implementar paleta cyberpunk (#0a0a0f bg, #00ff41 text, #ff0055 error, etc.)
- [ ] 7.3 Criar TCSS com efeito scanline (repeating-linear-gradient)
- [ ] 7.4 Adicionar efeito phosphor glow (text-shadow)
- [ ] 7.5 Configurar fonte monoespaçada (JetBrains Mono ou similar)
- [ ] 7.6 Mapear cores por nível (DEBUG cinza, INFO ciano, EVENT verde, etc.)
- [ ] 7.7 Adicionar animação de fade-in para novas linhas
- [ ] 7.8 Adicionar efeito flicker opcional (muito sutil)
- [ ] 7.9 Testes visuais com pytest-textual snapshot

## 8. POC - App de Desenvolvimento

- [ ] 8.1 Criar `src/core/sky/log/poc.py` (App Textual standalone)
- [ ] 8.2 Compor POC com LogFilter, LogSearch, LogCopier, ChatLog
- [ ] 8.3 Adicionar logs de exemplo para teste visual (todos os níveis)
- [ ] 8.4 Implementar interação entre widgets (filtro → chatlog, busca → chatlog)
- [ ] 8.5 Adicionar tema cyberpunk ao POC
- [ ] 8.6 Criar `tests/unit/core/sky/log/poc_test.py` com pytest-textual
- [ ] 8.7 Executar POC localmente e validar visualmente

## 9. Integração - ChatLogger Adapter

- [ ] 9.1 Modificar `src/core/sky/chat/logging.py` para usar `LogEventBus`
- [ ] 9.2 Implementar adapter: `ChatLogger` publica eventos no bus
- [ ] 9.3 Manter compatibilidade com métodos existentes (info, debug, error, evento)
- [ ] 9.4 Conectar `FileLogConsumer` ao bus (logs em arquivo continuam funcionando)
- [ ] 9.5 Testes de integração para `ChatLogger` + `LogEventBus`

## 10. Integração - MainScreen

- [ ] 10.1 Atualizar `src/core/sky/chat/textual_ui/screens/main.py` para usar novo `ChatLog`
- [ ] 10.2 Substituir import antigo por novo módulo `src/core/sky/log/`
- [ ] 10.3 Compor LogFilter, LogSearch, LogCopier na MainScreen
- [ ] 10.4 Conectar eventos FilterChanged/SearchChanged ao ChatLog
- [ ] 10.5 Testes end-to-end da MainScreen com novos widgets

## 11. Testes de Regressão

- [ ] 11.1 Atualizar `tests/unit/core/sky/chat/textual_ui/widgets/test_chat_widgets.py`
- [ ] 11.2 Executar suite de testes completa e garantir 100% passing
- [ ] 11.3 Validar que nenhuma funcionalidade existente quebrou
- [ ] 11.4 Testar redirecionamento de stdout/stderr ainda funciona
- [ ] 11.5 Testar arquivo de log em disco ainda é escrito

## 12. Documentação e Finalização

- [ ] 12.1 Atualizar `src/core/sky/log/__init__.py` com exports públicos
- [ ] 12.2 Adicionar docstrings completas em todos os módulos
- [ ] 12.3 Criar README em `src/core/sky/log/README.md` (uso, exemplos)
- [ ] 12.4 Atualizar CLAUDE.md com notas sobre novo subsistema de log
- [ ] 12.5 Marcar `src/core/sky/chat/textual_ui/widgets/common/log.py` como DEPRECATED
- [ ] 12.6 Limpar código legado após período de transição (task futura)

---

**Total de tarefas:** ~100 tarefas distribuídas em 12 fases

**Estimativa de esforço:** 4-5 sprints (considerando TDD estrito e testes completos)
