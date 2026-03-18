# ChatLog 2.0 - Lista de Tarefas (Revisão Final)

## 1. Fundações - Estrutura e Protocol

- [ ] 1.1 Criar estrutura de diretórios `src/core/sky/log/`
- [ ] 1.2 Criar estrutura de diretórios `tests/unit/core/sky/log/`
- [ ] 1.3 Implementar `LogScope` enum (ALL, SYSTEM, USER, API, DATABASE, NETWORK, VOICE, MEMORY)
- [ ] 1.4 Implementar `LogEntry` (frozen dataclass com level/logging, message, timestamp, scope, context)
- [ ] 1.5 Implementar `LogConsumer` Protocol (método write_log simples)
- [ ] 1.6 Implementar método `matches_filter()` em LogEntry (level + scope)
- [ ] 1.7 Testes unitários para `LogScope` (enum values)
- [ ] 1.8 Testes unitários para `LogEntry` (imutabilidade, matches_filter)
- [ ] 1.9 Testes unitários para `LogConsumer` Protocol (type-checking)

## 2. Clipboard Vendorizado

- [ ] 2.1 Criar `src/core/sky/log/clipboard.py` (implementação vendored do pyperclip)
- [ ] 2.2 Implementar detecção de SO (Windows/macOS/Linux)
- [ ] 2.3 Implementar `copy_to_clipboard()` para Windows (win32clipboard ou subprocess)
- [ ] 2.4 Implementar `copy_to_clipboard()` para macOS (pbcopy)
- [ ] 2.5 Implementar `copy_to_clipboard()` para Linux (xclip, wl-copy, fallback arquivo)
- [ ] 2.6 Testes unitários para clipboard (mock subprocess)

## 3. Widgets - LogFilter (Nível + Escopo)

- [ ] 3.1 Criar `src/core/sky/log/widgets/` estrutura
- [ ] 3.2 Implementar `LogFilter` widget com dois eixos (nível e escopo)
- [ ] 3.3 Implementar botões de nível: ALL, DEBUG, INFO, WARNING, ERROR, CRITICAL (logging padrão)
- [ ] 3.4 Implementar botões de escopo: ALL, SYSTEM, USER, API, DATABASE, NETWORK, VOICE, MEMORY
- [ ] 3.5 Implementar mensagem `FilterChanged(level, scope)` emitida ao mudar seleção
- [ ] 3.6 Implementar contador de mensagens visíveis (X/total)
- [ ] 3.7 Implementar métodos `set_level()`, `set_scope()`, `clear_filters()`
- [ ] 3.8 Testes unitários para `LogFilter` (seleção, emissão de eventos, contadores)

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
- [ ] 5.2 Implementar cópia respeitando filtros ativos (nível + escopo + busca)
- [ ] 5.3 Adicionar formatação de linhas copiadas (timestamp + nível + scope)
- [ ] 5.4 Implementar notificação de sucesso ("X linhas copiadas!")
- [ ] 5.5 Implementar tratamento de erro quando clipboard falha
- [ ] 5.6 Usar `copy_to_clipboard()` vendorizado
- [ ] 5.7 Testes unitários para `LogCopier` (cópia, filtros, notificações)

## 6. Widgets - LogToolbar

- [ ] 6.1 Implementar `LogToolbar` container (agrupa Filter + Search + Copier)
- [ ] 6.2 Layout horizontal com tamanhos proporcionais
- [ ] 6.3 Testes unitários para `LogToolbar` (composição, layout)

## 7. ChatLog 2.0 - Core Widget

- [ ] 7.1 Implementar `ChatLogConfig` dataclass (max_entries, buffer_when_closed, virtualization_threshold)
- [ ] 7.2 Implementar `ChatLog` widget herdando de VerticalScroll
- [ ] 7.3 Implementar ring buffer `collections.deque(maxlen=config.max_entries)`
- [ ] 7.4 Implementar virtualização desde dia 1 (renderiza visíveis + margem)
- [ ] 7.5 Implementar接收 de logs via `write_log()` do consumidor
- [ ] 7.6 Implementar filtro por nível (respeitar logging.INFO >= min_level)
- [ ] 7.7 Implementar filtro por escopo (respeitar LogScope)
- [ ] 7.8 Implementar highlight de matches de busca durante render
- [ ] 7.9 Implementar buffer when_closed (max_buffer_when_closed configurável)
- [ ] 7.10 Implementar flush em batch para evitar flicker
- [ ] 7.11 Testes unitários para `ChatLog` (ring buffer, virtualização, filtros)

## 8. Tema Cyberpunk (Toggleável)

- [ ] 8.1 Criar `src/core/sky/log/theme.py` com `CyberpunkConfig` e `CyberpunkPreset`
- [ ] 8.2 Implementar presets: MINIMAL, BALANCED, FULL
- [ ] 8.3 Implementar paleta cyberpunk (#0a0a0f bg, #00ff41 text, #ff0055 error, etc.)
- [ ] 8.4 Criar TCSS com classes modulares: .cyberpunk, .scanlines, .glow, .flicker
- [ ] 8.5 Implementar efeito scanline (repeating-linear-gradient)
- [ ] 8.6 Implementar efeito phosphor glow (text-shadow)
- [ ] 8.7 Configurar fonte monoespaçada (JetBrains Mono ou similar)
- [ ] 8.8 Mapear cores por nível (DEBUG cinza, INFO ciano, WARNING âmbar, ERROR vermelho)
- [ ] 8.9 Remover mapeamento de EVENT (não existe mais)
- [ ] 8.10 Implementar flicker como opcional e desligado por padrão (acessibilidade)
- [ ] 8.11 Adicionar animação de fade-in para novas linhas
- [ ] 8.12 Testes visuais com pytest-textual snapshot

## 9. POC - App de Desenvolvimento

- [ ] 9.1 Criar `src/core/sky/log/poc.py` (App Textual standalone)
- [ ] 9.2 Compor POC com LogToolbar e ChatLog
- [ ] 9.3 Adicionar logs de exemplo para teste visual (todos os níveis e escopos)
- [ ] 9.4 Implementar geração de logs com timestamp realista
- [ ] 9.5 Implementar argumento de linha de comando para preset (minimal/balanced/full)
- [ ] 9.6 Adicionar tema cyberpunk ao POC com preset selecionado
- [ ] 9.7 Criar `tests/unit/core/sky/log/poc_test.py` com pytest-textual snapshot
- [ ] 9.8 Executar POC localmente e validar visualmente

## 10. Integração - ChatLogger Adapter

- [ ] 10.1 Modificar `src/core/sky/chat/logging.py` para usar `LogConsumer` Protocol
- [ ] 10.2 Implementar adapter simples: `ChatLogger` chama `consumer.write_log()`
- [ ] 10.3 Remover método `evento()` (usar `info()` com context apropriado)
- [ ] 10.4 Manter compatibilidade com métodos existentes (debug, info, warning, error)
- [ ] 10.5 Converter chamadas de `evento()` para `info()` com context={"type": "event", ...}
- [ ] 10.6 Testes de integração para `ChatLogger` com `ChatLog` como consumidor

## 11. Integração - MainScreen

- [ ] 11.1 Atualizar `src/core/sky/chat/textual_ui/screens/main.py` para usar novo `ChatLog`
- [ ] 11.2 Substituir import antigo por novo módulo `src/core/sky/log/`
- [ ] 11.3 Instanciar `ChatLogConfig` apropriado
- [ ] 11.4 Instanciar `CyberpunkConfig` (preset BALANCED por padrão)
- [ ] 11.5 Compor LogToolbar na MainScreen
- [ ] 11.6 Conectar eventos FilterChanged/SearchChanged ao ChatLog
- [ ] 11.7 Testes end-to-end da MainScreen com novos widgets

## 12. Testes de Regressão

- [ ] 12.1 Atualizar `tests/unit/core/sky/chat/textual_ui/widgets/test_chat_widgets.py`
- [ ] 12.2 Executar suite de testes completa e garantir 100% passing
- [ ] 12.3 Validar que nenhuma funcionalidade existente quebrou
- [ ] 12.4 Testar redirecionamento de stdout/stderr ainda funciona
- [ ] 12.5 Testar arquivo de log em disco ainda é escrito

## 13. Documentação

- [ ] 13.1 Atualizar `src/core/sky/log/__init__.py` com exports públicos
- [ ] 13.2 Adicionar docstrings completas em todos os módulos
- [ ] 13.3 Criar README em `src/core/sky/log/README.md` (uso, exemplos, configuração)
- [ ] 13.4 Documentar `CyberpunkConfig` (presets, acessibilidade)
- [ ] 13.5 Atualizar CLAUDE.md com notas sobre novo subsistema de log
- [ ] 13.6 Marcar `src/core/sky/chat/textual_ui/widgets/common/log.py` como DEPRECATED

---

**Total de tarefas:** ~85 tarefas distribuídas em 13 fases

**Estimativa de esforço:** 3-4 sprints (simplificado vs plano original)

**Principais simplificações:**
- Protocol simples ao invés de Event Bus complexo
- logging padrão do Python ao invés de LogLevel custom
- Clipboard vendorizado (sem dependências externas)
- Virtualização desde dia 1 (não "futuro")
