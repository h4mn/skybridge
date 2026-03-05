# SkyTextualDOM - Sistema DOM-like para Textual TUI

Sistema completo de inspeção para interfaces Textual, inspirado no React DevTools e Browser DevTools.

## 🎯 Funcionalidades

- **Registro Global**: Widgets são registrados automaticamente via `SkyWidgetMixin`
- **Queries CSS**: Busca flexível por classe, ID ou atributos
- **Estado Reactive**: Rastreamento automático de props reactive
- **Snapshots**: Captura e comparação de estado completo
- **Event Tracer**: Log de todos os eventos Textual
- **DevTools UI**: Interface visual (Ctrl+D)

## 🚀 Uso Básico

### Auto-registro com Mixin

```python
from textual.widgets import Static
from core.sky.chat.textual_ui.dom import SkyWidgetMixin

class MyWidget(Static, SkyWidgetMixin):
    # Widget é registrado automaticamente no on_mount()
    # E desregistrado no on_unmount()
    pass
```

### Queries

```python
from core.sky.chat.textual_ui.dom import SkyTextualDOM

dom = SkyTextualDOM()

# Buscar por ID
node = dom.get("AnimatedVerb_123")

# Query por classe
animated_verbs = dom.query("AnimatedVerb")

# Query com atributo
done_turns = dom.query("Turn[estado=DONE]")
```

### Árvore Visual

```python
# Imprimir no console
dom.print()

# Obter como string
tree = dom.tree()
print(tree)
```

### Snapshots

```python
# Criar snapshot
snapshot = dom.snapshot(name="antes-do-fix")

# Salvar em arquivo
snapshot.save("/tmp/snapshot.json")

# Carregar snapshot
loaded = dom.load_snapshot("/tmp/snapshot.json")

# Comparar snapshots
diff = dom.diff_snapshots(before, after)
```

### Tracing

```python
# Rastrear todas as props de um widget
dom.trace("AnimatedVerb_123")

# Rastrear prop específica
dom.trace("AnimatedVerb_123", "count")

# Parar tracing
dom.untrace("AnimatedVerb_123")
```

### Event Tracer

```python
# Capturar evento
dom.tracer.capture_event(
    EventType.ERROR,
    widget_dom_id="widget_123",
    error_message="Erro ao processar"
)

# Filtrar eventos
errors = dom.tracer.filter(event_types=[EventType.ERROR])

# Buscar textual
results = dom.tracer.search("widget_123")

# Exportar
json_str = dom.tracer.export(fmt="json")
```

## 🎨 DevTools (Ctrl+D)

Pressione `Ctrl+D` em qualquer lugar da aplicação para abrir a DevTools Screen:

### Painéis

1. **Tree**: Hierarquia completa de widgets registrados
2. **State**: Estado detalhado do widget selecionado
3. **Events**: Timeline de eventos recentes

### Atalhos

- `Ctrl+D`: Abrir/Fechar DevTools
- `Ctrl+P`: Pausar/Retomar atualizações
- `Ctrl+R`: Resetar layout
- `Escape`: Fechar DevTools

## 📊 Estrutura de Módulos

```
dom/
├── __init__.py       # API pública
├── node.py           # DOMNode dataclass
├── registry.py       # SkyTextualDOM singleton
├── watcher.py        # ReactiveWatcher
├── differ.py         # Diff de estado
├── tracer.py         # EventTracer
├── snapshot.py       # DOMSnapshot
├── mixin.py          # SkyWidgetMixin
└── screens/
    └── devtools.py   # DevToolsScreen
```

## 🔧 Configuração

```python
dom = SkyTextualDOM()

# Configurar limites
dom.configure(
    history_limit=50,      # Limite do histórico de props
    event_buffer_size=1000 # Tamanho do buffer de eventos
)
```

## 🧪 Exemplos Completos

### Registrar Widget Manualmente

```python
from textual.widgets import Static
from core.sky.chat.textual_ui.dom import SkyTextualDOM

widget = Static("Hello")
dom = SkyTextualDOM()

# Registrar sem mixin
node = dom.register(widget, dom_id="my_widget")

# Buscar depois
found = dom.get("my_widget")
assert found.widget is widget
```

### Hierarquia Parent-Child

```python
parent = Static("Parent")
child = Static("Child")

dom = SkyTextualDOM()
parent_node = dom.register(parent, dom_id="parent")
child_node = dom.register(child, parent=parent, dom_id="child")

# Child referencia parent
assert child_node.parent is parent_node
assert child_node in parent_node.children
```

## ⚠️ Limitações Conhecidas

- **Performance**: Queries CSS são O(n) onde n = número de widgets registrados
- **Memória**: Históricos e buffers crescem com o uso
- **Thread-safety**: Operações de registro são thread-safe, queries são lock-free

## 🔗 Links

- Specs: `openspec/changes/sky-textual-dom-devtools/specs/`
- Design: `openspec/changes/sky-textual-dom-devtools/design.md`
- Tasks: `openspec/changes/sky-textual-dom-devtools/tasks.md`

---

> "Ver é entender — uma ferramenta de inspeção transforma caos em clareza" – made by Sky 🔍
