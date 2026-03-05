# Tasks: SkyTextualDOM - Implementação

## 1. Setup e Infraestrutura

- [x] 1.1 Criar estrutura de diretórios `src/core/sky/chat/textual_ui/dom/`
- [x] 1.2 Criar `dom/__init__.py` com imports públicos
- [x] 1.3 Criar `dom/screens/` para DevToolsScreen
- [x] 1.4 Adicionar entrypoint no `__init__.py` do `textual_ui`

## 2. DOMNode (dom/node.py)

- [x] 2.1 Implementar dataclass `DOMNode` com campos básicos
- [x] 2.2 Adicionar método `to_dict()` para serialização
- [x] 2.3 Implementar `get_state_snapshot()` que extrai estado do widget
- [x] 2.4 Adicionar `add_prop_change(prop, old, new)` para histórico
- [x] 2.5 Implementar `get_prop_history(prop)` que retorna deque
- [x] 2.6 Testes unitários de DOMNode

## 3. Registry (dom/registry.py)

- [x] 3.1 Implementar classe `SkyTextualDOM` singleton
- [x] 3.2 Método `register(widget, parent=None)` → cria DOMNode
- [x] 3.3 Método `unregister(dom_id)` → remove DOMNode e children
- [x] 3.4 Método `get(dom_id)` → retorna DOMNode ou None
- [x] 3.5 Método `query(selector)` → parser CSS simples
- [x] 3.6 Método `tree()` → retorna string formatada da árvore
- [x] 3.7 Thread-safety com `threading.RLock` em register/unregister
- [x] 3.8 Testes de registro, queries, thread-safety

## 4. SkyWidgetMixin (dom/mixin.py)

- [x] 4.1 Implementar `SkyWidgetMixin` class
- [x] 4.2 `on_mount()` chama `SkyTextualDOM.register(self, self.parent)`
- [x] 4.3 `on_unmount()` chama `SkyTextualDOM.unregister(self._dom_id)`
- [x] 4.4 `_dom_id` gerado automaticamente se não fornecido
- [x] 4.5 Testes de auto-registro/desregistro

## 5. ReactiveWatcher (dom/watcher.py)

- [x] 5.1 Implementar `ReactiveWatcher` class
- [x] 5.2 `_discover_reactive_props(widget)` via introspecção
- [x] 5.3 Instalar `watch_` methods dinâmicos no DOMNode
- [x] 5.4 Histórico com `collections.deque(maxlen=limit)`
- [x] 5.5 Método `trace(dom_id, prop=None)` para habilitar log
- [x] 5.6 Método `untrace(dom_id)` para desabilitar
- [x] 5.7 Detecção de loops (100+ mudanças em 1s)
- [x] 5.8 Testes de introspecção, histórico, loops

## 6. State Diff (dom/differ.py)

- [x] 6.1 Função `diff_state(old, new, path="")` base
- [x] 6.2 `_diff_dicts(old, new, path)` para dicts
- [x] 6.3 `_diff_sequences(old, new, path)` para listas/tuples
- [x] 6.4 `_diff_dataclass(old, new, path)` para dataclasses
- [x] 6.5 Método `format_diff()` para saída colorida
- [x] 6.6 Testes de diff para todos os tipos

## 7. Snapshot (dom/snapshot.py)

- [x] 7.1 Dataclass `DOMSnapshot` com metadata
- [x] 7.2 `SkyTextualDOM.snapshot(name, desc)` → captura estado completo
- [x] 7.3 `snapshot.save(path)` → export JSON
- [x] 7.4 `SkyTextualDOM.load_snapshot(path)` → import JSON
- [x] 7.5 `SkyTextualDOM.list_snapshots()` → lista todos
- [x] 7.6 `SkyTextualDOM.diff_snapshots(a, b)` → compara dois
- [x] 7.7 Custom `DOMJSONEncoder` para dataclasses
- [x] 7.8 Testes de snapshot, export/import, diff

## 8. Event Tracer (dom/tracer.py)

- [x] 8.1 Dataclass `EventEntry` com timestamp, tipo, dados
- [x] 8.2 `EventTracer` class com buffer circular (deque maxlen=1000)
- [x] 8.3 Buffer secundário para eventos críticos (ERROR)
- [x] 8.4 Métodos `capture_event(event_type, **data)`
- [x] 8.5 `filter(event_types, widget, since, until)` → lista filtrada
- [x] 8.6 `search(text, prop=None, regex=False)` → busca textual
- [x] 8.7 `export(fmt="json")` → exportação
- [x] 8.8 `subscribe(callback, filter=None)` → stream em tempo real
- [x] 8.9 Detecção de padrões (ERROR_BURST, EVENT_SPAM, NEW_EVENT_TYPE)
- [x] 8.10 Testes de captura, filtros, export, alertas

## 9. Hooks de Eventos Textual

- [x] 9.1 Hook global para `on_mount` → captura MOUNT events
- [x] 9.2 Hook global para `on_unmount` → captura UNMOUNT events
- [x] 9.3 Hook para eventos de interação (CLICK, SUBMIT, KEY)
- [x] 9.4 Hook para eventos customizados (`post_message`)
- [x] 9.5 Integração com `EventTracer` em todos os hooks
- [x] 9.6 Testes de hooks + tracer

## 10. DevTools Screen (dom/screens/devtools.py)

### 10.1 Estrutura da Screen

- [x] 10.1.1 Criar `DevToolsScreen(Screen)` class
- [x] 10.1.2 Layout com 3 painéis (Tree, State, Events)
- [x] 10.1.3 Header com título e botões (Pause, Reset)
- [x] 10.1.4 Footer com atalhos descritos
- [x] 10.1.5 `BINDINGS = [("ctrl+d", "app.pop_screen"), ...]`

### 10.2 Painel Tree

- [x] 10.2.1 Widget `TreePanel` com `TreeView` ou lista customizada
- [x] 10.2.2 Renderizar árvore com indentação e caracteres `├─ └─ │`
- [x] 10.2.3 Ícones por tipo de widget (📺 Screen, 🎨 Widget, ⚡ AnimatedVerb)
- [ ] 10.2.4 Navegação por setas (↑↓) e Enter para expandir/colapsar
- [ ] 10.2.5 Filtro por texto (digita para filtrar)
- [ ] 10.2.6 Seleção de widget atualiza painel State

### 10.3 Painel State

- [ ] 10.3.1 Widget `StatePanel` com display de estado
- [ ] 10.3.2 Mostrar dom_id, class_name, visible, focused, position
- [ ] 10.3.3 Tabela de props reactive com valor atual
- [ ] 10.3.4 Indicador visual (●) para props que mudaram recentemente
- [ ] 10.3.5 Expansão de dataclasses (EstadoLLM → campos)
- [ ] 10.3.6 Barras de progresso para valores numéricos (0.0-1.0)
- [ ] 10.3.7 Mini-gráfico de histórico das últimas 10 mudanças
- [ ] 10.3.8 Botão `[+] Trace` / `[-] Untrace` para o widget

### 10.4 Painel Events

- [x] 10.4.1 Widget `EventsPanel` com lista timeline
- [x] 10.4.2 Eventos em ordem reversa (recente no topo)
- [x] 10.4.3 Timestamp HH:MM:SS.mmm em cada entrada
- [x] 10.4.4 Formato: `[tipo] widget → dados`
- [ ] 10.4.5 Filtros por tipo (MOUNT, PROP_CHANGED, ERROR, etc)
- [ ] 10.4.6 Filtro por widget (quando Tree tem seleção)
- [ ] 10.4.7 Toggle "Todos os widgets" vs "Widget selecionado"
- [ ] 10.4.8 Scroll automático para novo evento

### 10.5 Atualização em Tempo Real

- [x] 10.5.1 Timer de 100ms para refresh de painéis
- [x] 10.5.2 `_refresh_from_dom()` lê estado atual do SkyTextualDOM
- [x] 10.5.3 Update reativo de painéis quando estado muda
- [x] 10.5.4 `Ctrl+P` para Pause/Resume de atualizações
- [x] 10.5.5 Badge "PAUSED" no header quando pausado

### 10.6 Atalhos e Interações

- [x] 10.6.1 `Tab` para ciclar entre painéis
- [ ] 10.6.2 `/` para focar campo de filtro
- [ ] 10.6.3 `Ctrl+F` para modal de busca de widget
- [ ] 10.6.4 `Alt+↑↓` para navegar parent/children
- [ ] 10.6.5 `Ctrl+S` para snapshot rápido
- [x] 10.6.6 `Ctrl+R` para reset de layout/filtros

### 10.7 Persistência

- [ ] 10.7.1 Salvar layout em `~/.skybridge/devtools-state.json`
- [ ] 10.7.2 Salvar filtros de Events e Tree
- [ ] 10.7.3 Carregar estado ao montar DevToolsScreen
- [ ] 10.7.4 Reset remove arquivo de estado

### 10.8 Testes da DevToolsScreen

- [ ] 10.8.1 Teste de montagem da screen
- [ ] 10.8.2 Teste de navegação na Tree
- [ ] 10.8.3 Teste de seleção de widget → State atualiza
- [ ] 10.8.4 Teste de filtros de Events
- [ ] 10.8.5 Teste de atalhos de teclado
- [ ] 10.8.6 Teste de persistência de estado

## 11. Integração com ChatScreen

- [x] 11.1 Adicionar binding `Ctrl+D` no ChatScreen
- [x] 11.2 Action `action_open_devtools(self)` → `self.app.push_screen(DevToolsScreen())`
- [ ] 11.3 Integrar SkyWidgetMixin em widgets principais:
  - [ ] 11.3.1 ChatScreen
  - [ ] 11.3.2 ChatHeader
  - [ ] 11.3.3 AnimatedTitle
  - [ ] 11.3.4 AnimatedVerb
  - [ ] 11.3.5 ChatScroll
  - [ ] 11.3.6 Turn
- [ ] 11.4 Testes de integração E2E (ChatScreen + DevTools)

## 12. CLI e API Pública

- [x] 12.1 `SkyTextualDOM.print()` → print da árvore no terminal
- [x] 12.2 `SkyTextualDOM.trace(dom_id, prop)` → inicia tracing
- [x] 12.3 `SkyTextualDOM.untrace(dom_id)` → para tracing
- [x] 12.4 `SkyTextualDOM.configure(history_limit, buffer_size)` → config global
- [x] 12.5 Testes da API pública

## 13. Documentação

- [x] 13.1 Docstrings completa em todas as classes/métodos públicos
- [x] 13.2 README em `dom/README.md` com visão geral
- [x] 13.3 Exemplos de uso da API
- [x] 13.4 Guia de atalhos da DevToolsScreen

## 14. Testes Finais e Benchmark

- [ ] 14.1 Teste de performance: registro de 100 widgets <100ms
- [ ] 14.2 Teste de memória: histórico de 50 props não vaza memória
- [ ] 14.3 Teste de thread-safety: 10 threads registrando simultaneamente
- [ ] 14.4 Teste de snapshot: 100 widgets em <200ms
- [ ] 14.5 Teste E2E completo: ChatScreen + DevTools + 5 minutos de uso
- [ ] 14.6 Validação de todos os 5 specs (dom-registry, reactive-watcher, devtools-ui, state-snapshot, event-tracer)

---

## Estimativas

| Fase | Tasks | Estimativa |
|------|-------|------------|
| Setup e Infraestrutura | 1.1-1.4 | 1h |
| DOMNode | 2.1-2.6 | 3h |
| Registry | 3.1-3.8 | 4h |
| SkyWidgetMixin | 4.1-4.5 | 2h |
| ReactiveWatcher | 5.1-5.8 | 6h |
| State Diff | 6.1-6.6 | 3h |
| Snapshot | 7.1-7.8 | 4h |
| Event Tracer | 8.1-8.10 | 6h |
| Hooks de Eventos | 9.1-9.6 | 3h |
| DevTools Screen | 10.1-10.8 | 12h |
| Integração ChatScreen | 11.1-11.4 | 3h |
| CLI e API | 12.1-12.5 | 2h |
| Documentação | 13.1-13.4 | 3h |
| Testes Finais | 14.1-14.6 | 4h |
| **TOTAL** | **~90 tasks** | **~56 horas** |

---

> "Cada tarefa completada é um tijolo na fundação da excelência" – made by Sky 🧱
