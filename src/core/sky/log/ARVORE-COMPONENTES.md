# Árvore de Componentes - ChatLog 2.0

Documentação da estrutura de componentes do subsistema de log.

```
ChatLogPOC (App)
│
├── Header (textual.widgets)
│   └── Título + Subtítulo
│
├── LogToolbar (Vertical) - height: 5, dock: top
│   │
│   ├── Linha 1: LogSearch (Input)
│   │   ├── placeholder: "Buscar logs... (escopo, nível, texto)"
│   │   ├── reactive[search_term]
│   │   ├── debounce: 300ms
│   │   └── emite: SearchChanged(search_term)
│   │
│   └── Linha 2: Horizontal.buttons-row (layout: horizontal) - height: 3
│       │
│       ├── LogFilter (Horizontal) - width: 1fr, layout: horizontal
│       │   ├── LevelButton "A" (NOTSET/ALL)   - width: 1, margin-right: 1
│       │   ├── LevelButton "D" (DEBUG)        - width: 1, margin-right: 1
│       │   ├── LevelButton "I" (INFO)         - width: 1, margin-right: 1
│       │   ├── LevelButton "W" (WARNING)      - width: 1, margin-right: 1
│       │   ├── LevelButton "E" (ERROR)         - width: 1, margin-right: 1
│       │   ├── LevelButton "C" (CRITICAL)      - width: 1, margin-right: 1
│       │   └── emite: FilterChanged(level, scope)
│       │
│       ├── LogCopier (Button) - width: 1, margin-right: 1
│       │   ├── label: "C" (muda para ✓/✗/-)
│       │   └── recebe: VisibleEntriesChanged
│       │
│       └── LogClose (Button) - width: 1
│           ├── label: "X" (muda para R com filtro)
│           └── emite: FilterChanged + SearchChanged
│
├── ChatLog (VerticalScroll)
│   ├── deque[LogEntry] (ring buffer, maxlen: 1000)
│   ├── _min_level: int (filtro de nível)
│   ├── _scope_filter: LogScope
│   ├── _search_term: str
│   ├── _schedule_refresh() (batch flush 50ms)
│   │
│   └── [renderiza Static widgets para cada entry visível]
│       ├── Static "HH:MM:SS [LEVEL] SCOPE: message"
│       ├── classes: log-entry + log-entry-{level}
│       └── highlight: [reverse] para matches
│
└── Footer (textual.widgets)
    └── Keybindings + debug info
```

## Layout Visual

```
┌─────────────────────────────────────────────────────┐
│ Header: ChatLog 2.0 - POC                           │
├─────────────────────────────────────────────────────┤
│ LogToolbar (height: 5)                              │
│ ┌─────────────────────────────────────────────────┐ │
│ │ Buscar logs... (escopo, nível, texto)          │ │ ← LogSearch (height: 2)
│ ├─────────────────────────────────────────────────┤ │
│ │A│D│I│W│E│C││C││X│                             │ │ ← buttons-row (height: 3)
│ └─────────────────────────────────────────────────┘ │
├─────────────────────────────────────────────────────┤
│ ChatLog (VerticalScroll)                            │
│ 12:34:56 [INFO] SYSTEM: Inicializando componente   │
│ 12:34:58 [DEBUG] API: API request                  │
│ 12:35:00 [WARNING] DATABASE: Query lenta           │
│ ...                                                │
└─────────────────────────────────────────────────────┘
│ Footer (q:quit, etc)                                │
└─────────────────────────────────────────────────────┘
```

## Dimensões

| Componente | Width | Height | Notas |
|------------|-------|--------|-------|
| LogToolbar | 1fr | 5 | dock: top |
| LogSearch | 1fr | 2 | Input padrão |
| buttons-row | 1fr | 3 | Horizontal container |
| LogFilter | 1fr | auto | layout: horizontal |
| LevelButton | 1 | auto | margin-right: 1 |
| LogCopier | 1 | auto | margin-right: 1 |
| LogClose | 1 | auto | Último, sem margin-right |
| ChatLog | 1fr | 1fr | VerticalScroll |

## Eventos

### Eventos Emitidos

| Evento | Emissor | Dados | Handler |
|--------|--------|-------|---------|
| FilterChanged | LevelButton | level, scope | on_filter_changed |
| SearchChanged | LogSearch | search_term | on_search_changed |
| VisibleEntriesChanged | ChatLog | entries[] | LogCopier |

## Labels

### Filtros de Nível

| Letra | Nível | Descrição |
|-------|-------|-----------|
| A | NOTSET | ALL - Mostra tudo |
| D | DEBUG | Depuração |
| I | INFO | Informações |
| W | WARNING | Avisos |
| E | ERROR | Erros |
| C | CRITICAL | Críticos |

### Botões de Ação

| Botão | Estado Normal | Estado Ativo | Feedback |
|-------|--------------|--------------|----------|
| Copiar | C | - | ✓ (ok), ✗ (erro), - (vazio) |
| Limpar | X | R (reset) | R quando há filtro |

## CSS Classes

### LevelButton

- `.selected` - Botão ativo (text-style: bold reverse)

### LogEntry (ChatLog)

- `.log-entry` - Entrada de log base
- `.log-entry-debug` - Nível DEBUG (text-style: dim)
- `.log-entry-info` - Nível INFO (color: cyan)
- `.log-entry-warning` - Nível WARNING (color: yellow)
- `.log-entry-error` - Nível ERROR (color: red)
- `.log-entry-critical` - Nível CRITICAL (color: red, text-style: bold)
- `.highlight` - Match de busca (text-style: bold reverse)

> "A simplicidade é o último grau de sofisticação" – made by Sky 🌳
