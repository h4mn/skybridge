# ChatLog 2.0 - Lista de Tarefas (Revisão Final)

## 1. Fundações - Estrutura e Protocol

- [x] 1.1 Criar estrutura de diretórios `src/core/sky/log/`
- [x] 1.2 Criar estrutura de diretórios `tests/unit/core/sky/log/`
- [x] 1.3 Implementar `LogScope` enum (ALL, SYSTEM, USER, API, DATABASE, NETWORK, VOICE, MEMORY)
- [x] 1.4 Implementar `LogEntry` (frozen dataclass com level/logging, message, timestamp, scope, context)
- [x] 1.5 Implementar `LogConsumer` Protocol (método write_log simples)
- [x] 1.6 Implementar método `matches_filter()` em LogEntry (level + scope)
- [x] 1.7 Testes unitários para `LogScope` (enum values)
- [x] 1.8 Testes unitários para `LogEntry` (imutabilidade, matches_filter)
- [x] 1.9 Testes unitários para `LogConsumer` Protocol (type-checking)

## 2. Clipboard (lib externa + fallback vendored)

- [x] 2.1 Criar `src/core/sky/log/clipboard.py` (lib clipboard como preferência, fallback vendored)
- [x] 2.2 Implementar detecção de SO (Windows/macOS/Linux)
- [x] 2.3 Implementar `copy_to_clipboard()` com `import clipboard` como primeira opção
- [x] 2.4 Implementar fallback vendored para Windows (win32clipboard ou subprocess)
- [x] 2.5 Implementar fallback vendored para macOS (pbcopy)
- [x] 2.6 Implementar fallback vendored para Linux (xclip, wl-copy, fallback arquivo)
- [x] 2.7 Testes unitários para clipboard (mock)

## 3. Widgets - LogFilter (Nível + Escopo)

- [x] 3.1 Criar `src/core/sky/log/widgets/` estrutura
- [x] 3.2 Implementar `LogFilter` widget com dois eixos (nível e escopo)
- [x] 3.3 Implementar botões de nível: ALL, DEBUG, INFO, WARNING, ERROR, CRITICAL (logging padrão)
- [x] 3.4 Implementar botões de escopo: ALL, SYSTEM, USER, API, DATABASE, NETWORK, VOICE, MEMORY
- [x] 3.5 Implementar mensagem `FilterChanged(level, scope)` emitida ao mudar seleção
- [x] 3.6 Implementar contador de mensagens visíveis (X/total)
- [x] 3.7 Implementar métodos `set_level()`, `set_scope()`, `clear_filters()`
- [x] 3.8 Testes unitários para `LogFilter` (seleção, emissão de eventos, contadores)

## 4. Widgets - LogSearch

- [x] 4.1 Implementar `LogSearch` widget (Input com busca reativa)
- [x] 4.2 Adicionar reactive attribute `search_term`
- [x] 4.3 Implementar debounce de 300ms (usar set_interval do Textual)
- [x] 4.4 Implementar highlight de matches (style="reverse")
- [x] 4.5 Implementar busca case-insensitive
- [x] 4.6 Adicionar indicador de "X matches encontrados"
- [x] 4.7 Implementar botão de limpar busca (X)
- [x] 4.8 Adicionar suporte a curingas (* e ?)
- [x] 4.9 Implementar navegação Next/Previous entre matches
- [x] 4.10 Testes unitários para `LogSearch` (debounce, highlight, contadores)

## 5. Widgets - LogCopier

- [x] 5.1 Implementar `LogCopier` widget (Button com ícone de clipboard)
- [x] 5.2 Implementar cópia respeitando filtros ativos (nível + escopo + busca)
- [x] 5.3 Adicionar formatação de linhas copiadas (timestamp + nível + scope)
- [x] 5.4 Implementar notificação de sucesso ("X linhas copiadas!")
- [x] 5.5 Implementar tratamento de erro quando clipboard falha
- [x] 5.6 Usar `copy_to_clipboard()` vendorizado
- [x] 5.7 Testes unitários para `LogCopier` (cópia, filtros, notificações)

## 6. Widgets - LogToolbar

- [x] 6.1 Implementar `LogToolbar` container (agrupa Filter + Search + Copier)
- [x] 6.2 Layout horizontal com tamanhos proporcionais
- [x] 6.3 Testes unitários para `LogToolbar` (composição, layout)

## 7. ChatLog 2.0 - Core Widget

- [x] 7.1 Implementar `ChatLogConfig` dataclass (max_entries, buffer_when_closed, virtualization_threshold)
- [x] 7.2 Implementar `ChatLog` widget herdando de VerticalScroll
- [x] 7.3 Implementar ring buffer `collections.deque(maxlen=config.max_entries)`
- [x] 7.4 Implementar virtualização desde dia 1 (renderiza visíveis + margem)
- [x] 7.5 Implementar接收 de logs via `write_log()` do consumidor
- [x] 7.6 Implementar filtro por nível (respeitar logging.INFO >= min_level)
- [x] 7.7 Implementar filtro por escopo (respeitar LogScope)
- [x] 7.8 Implementar highlight de matches de busca durante render
- [x] 7.9 Implementar buffer when_closed (max_buffer_when_closed configurável)
- [x] 7.10 Implementar flush em batch para evitar flicker
- [x] 7.11 Testes unitários para `ChatLog` (ring buffer, virtualização, filtros)

## 8. Tema Cyberpunk (Toggleável) 🚫 MOVIDO PARA FUTURO

**NOTA:** Fase completa movida para versão futura. O ChatLog 2.0 funcional será entregue sem tema cyberpunk, usando estilo padrão do Textual.

Tasks futuras (12):
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

- [x] 9.1 Criar `src/core/sky/log/poc.py` (App Textual standalone)
- [x] 9.2 Compor POC com LogToolbar e ChatLog
- [x] 9.3 Adicionar logs de exemplo para teste visual (todos os níveis e escopos)
- [x] 9.4 Implementar geração de logs com timestamp realista
- [ ] 9.5 Implementar argumento de linha de comando para preset (minimal/balanced/full) - MOVIDO PARA FUTURO (Fase 8)
- [ ] 9.6 Adicionar tema cyberpunk ao POC com preset selecionado - MOVIDO PARA FUTURO (Fase 8)
- [ ] 9.7 Criar `tests/unit/core/sky/log/poc_test.py` com pytest-textual snapshot - MOVIDO PARA FUTURO (Fase 8)
- [x] 9.8 Executar POC localmente e validar visualmente

## 10. Integração - ChatLogger Adapter

- [x] 10.1 Modificar `src/core/sky/chat/logging.py` para usar `LogConsumer` Protocol
- [x] 10.2 Implementar adapter simples: `ChatLogger` chama `consumer.write_log()`
- [x] 10.3 Marcar método `evento()` como DEPRECATED (usa `info()` com context apropriado)
- [x] 10.4 Manter compatibilidade com métodos existentes (debug, info, warning, error)
- [x] 10.5 Converter chamadas de `evento()` para `info()` com context={"type": "event", ...}
- [ ] 10.6 Testes de integração para `ChatLogger` com `ChatLog` como consumidor

## 11. Integração - MainScreen

- [ ] 11.1 Atualizar `src/core/sky/chat/textual_ui/screens/main.py` para usar novo `ChatLog`
- [ ] 11.2 Substituir import antigo por novo módulo `src/core/sky/log/`
- [ ] 11.3 Instanciar `ChatLogConfig` apropriado
- [ ] 11.4 Instanciar `CyberpunkConfig` (preset BALANCED por padrão) - MOVIDO PARA FUTURO (Fase 8)
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

- [x] 13.1 Atualizar `src/core/sky/log/__init__.py` com exports públicos
- [x] 13.2 Adicionar docstrings completas em todos os módulos
- [x] 13.3 Criar README em `src/core/sky/log/README.md` (uso, exemplos, configuração)
- [ ] 13.4 Documentar `CyberpunkConfig` (presets, acessibilidade) - MOVIDO PARA FUTURO (Fase 8)
- ~~13.5 Atualizar CLAUDE.md~~ - REMOVIDA (README basta)
- [x] 13.6 Marcar `src/core/sky/chat/textual_ui/widgets/common/log.py` como DEPRECATED

---

**Status Atual:** 68/98 tarefas completas (69%)

**Mudanças Recentes (2026-03-19):**
- ✅ Task 4.9: Navegação Next/Previous implementada (F3/Shift+F3)
- ✅ Fase 10 parcial: ChatLogger integrado com LogConsumer Protocol
- ✅ C1 corrigido: Bug AttributeError no ChatLog._refresh()
- ✅ Fase 13 documentação: README criado, docstrings completadas
- ✅ Task 13.5 removida: README basta (CLAUDE.md não necessário)
- 🚫 Fase 8 movida para versão futura: Tema Cyberpunk (12 tasks)
- 📝 Tasks 9.5-9.7, 11.4, 13.4 atualizadas para refletir dependência da Fase 8

**Total de tarefas:** ~85 tarefas ativas (Fase 8 movida para futuro)

**Estimativa de esforço:** 2-3 sprints (sem Fase 8)

**Principais simplificações:**
- Protocol simples ao invés de Event Bus complexo
- logging padrão do Python ao invés de LogLevel custom
- Clipboard vendorizado (sem dependências externas)
- Virtualização desde dia 1 (implementada em 7.4)
- Buffer when_closed para economia de memória (implementado em 7.9)

> "A persistência é o caminho do êxito" – made by Sky 🚀
