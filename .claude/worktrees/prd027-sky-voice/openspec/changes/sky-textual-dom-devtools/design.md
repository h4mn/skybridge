# Design: SkyTextualDOM - Arquitetura Técnica

## Context

### Estado Atual

A TUI do Skybridge usa Textual com uma hierarquia complexa de widgets:

```
ChatScreen
├── ChatHeader → AnimatedTitle → AnimatedVerb (EstadoLLM)
├── ChatScroll → Turn (UserBubble, SkyBubble, ThinkingPanel)
├── ChatTextArea
└── ChatLog
```

**Mecanismos atuais de inspeção:**
- Tooltips (hover em widgets)
- Modals (clique em AnimatedVerb mostra EstadoModal)
- ChatLog (Ctrl+L para toggle)

**Limitações:**
- Sem visibilidade da árvore completa
- Sem histórico de mudanças de estado
- Sem diff temporal
- Sem queries estilo CSS
- Inspeção é manual e pontual

### Constraints

- **Performance:** Overhead mínimo, não pode afetar UX da TUI
- **Isolamento:** DevTools é opcional, TUI funciona sem ela
- **Compatibilidade:** Funciona com Textual 1.x+ atual
- **Memória:** Históricos limitados, buffer circular para eventos

### Stakeholders

- **Desenvolvedores:** Debugging rápido de estados complexos
- **UX:** Inspeção visual sem modificar código
- **QA:** Reprodução de bugs baseada em snapshots

---

## Goals / Non-Goals

### Goals

1. **Registro global O(1):** Widgets podem ser registrados/desregistrados com custo constante
2. **Queries estilo CSS:** Busca flexível por classe, ID, estado
3. **Histórico de mudanças:** Props reactive têm histórico configurável
4. **DevTools Screen:** Interface dedicada com 3 painéis
5. **Snapshots + Diff:** Captura e comparação de estado completo
6. **Event Tracer:** Log automático de todos os eventos Textual

### Non-Goals

- **Modificação de widgets:** DevTools apenas observa, não modifica
- **Hot reload de código:** Fora do escopo (ferramenta separada)
- **Profiling de performance:** Apenas logs básicos, não profiling profundo
- **Debug remoto:** Tudo é local, sem conectividade network

---

## Decisions

### D1: Singleton Global vs. Injeção de Dependência

**Decisão:** Singleton `SkyTextualDOM` com registro global.

**Racional:**
- ✅ Simples de usar: `SkyTextualDOM.get(id)` de qualquer lugar
- ✅ Não requer mudar estrutura de widgets existentes
- ✅ Padrão bem estabelecido (React DevTools, Browser DevTools)
- ❌ DI seria mais verboso e complexo para o caso de uso

**Alternativas rejeitadas:**
- **Injeção de dependência:** Seria necessário passar DOM para todos os widgets
- **Context manager:** Não se adapta bem ao ciclo de vida do Textual

---

### D2: Auto-registro via Mixin vs. Decorador

**Decisão:** Mixin `SkyWidgetMixin` com auto-registro no `on_mount`.

**Racional:**
- ✅ Não interfere na herança de widgets Textual (múltipla herança funciona)
- ✅ Opcional: widgets sem mixin funcionam normalmente
- ✅ Auto-desregistro no `on_unmount` é simétrico
- ❌ Decorador não funcionaria bem com classes Textual que já têm decoradores

```python
class AnimatedVerb(Static, SkyWidgetMixin):  # mixin adicionado
    def on_mount(self):
        super().on_mount()  # SkyWidgetMixin.register() é chamado aqui
```

**Alternativas rejeitadas:**
- **Decorador `@register_widget`:** Não executa no momento certo (mount vs init)
- **Manual explícito:** Esquecimento humano seria fonte de bugs

---

### D3: Thread-safety com Lock vs. Lock-free

**Decisão:** Usar `threading.RLock` apenas para operações de registro/desregistro.

**Racional:**
- ✅ Textual roda em single-thread principal, risco é baixo
- ✅ Lock apenas em mutate operations (register/unregister)
- ✅ Queries são lock-free (leitura não precisa de lock)
- ❌ Lock-free completo seria mais complexo sem benefício real

**Padrão:**
```python
class SkyTextualDOM:
    _lock = RLock()  # Reentrant lock

    def register(self, widget):
        with self._lock:
            # mutate registry
            pass

    def get(self, dom_id):
        # lock-free read
        return self._registry.get(dom_id)
```

---

### D4: Histórico de Props: Deque vs. Lista Circular

**Decisão:** `collections.deque` com `maxlen` para histórico de props.

**Racional:**
- ✅ O(1) para append em ambas as pontas
- ✅ Descarta automaticamente itens antigos (FIFO)
- ✅ Nativo do Python, sem dependências
- ❌ Lista circular manual seria mais verboso e propenso a bugs

```python
from collections import deque

class DOMNode:
    def __init__(self, history_limit: int = 50):
        self._prop_history = defaultdict(lambda: deque(maxlen=history_limit))
```

---

### D5: Snapshots: Deep Copy vs. Serialização JSON

**Decisão:** Serialização JSON com `dataclasses.asdict()` + custom encoder.

**Racional:**
- ✅ JSON é legível por humanos e editável
- ✅ Pode ser salvo em disco e compartilhado
- ✅ Deep copy preserva referências de objetos (não queremos isso)
- ✅ Serialização é mais lenta, mas snapshot não é operação hot path

**Encoder customizado:**
```python
class DOMJSONEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, EstadoLLM):
            return asdict(obj)
        if hasattr(obj, '__dom_state__'):
            return obj.__dom_state__()
        return super().default(obj)
```

---

### D6: Event Tracer: Buffer Circular vs. Append-only Log

**Decisão:** Buffer circular implementado com `deque` + buffer secundário para eventos críticos.

**Racional:**
- ✅ Memória limitada (não cresce indefinidamente)
- ✅ Eventos críticos (ERROR, CRITICAL) nunca são descartados
- ✅ Fácil de exportar (iterate sobre deque)
- ❌ Append-only log pode explodir memória em apps de longa duração

**Arquitetura:**
```
tracer._buffer      = deque(maxlen=1000)      # eventos normais
tracer._critical    = deque(maxlen=100)       # erros críticos
tracer._subscribers = []                       # callbacks em tempo real
```

---

### D7: DevTools Screen: Polling vs. Reactive Updates

**Decisão:** Updates reativos via `Textual.timer` + `reactive` props.

**Racional:**
- ✅ Textual já tem infraestrutura reativa built-in
- ✅ Polling é ineficiente (muitas renders desnecessárias)
- ✅ Timer de 100ms é bom balanço entre responsividade e CPU
- ❌ Polling curto (10ms) gastaria muita CPU

```python
class DevToolsScreen(Screen):
    _tree_state: reactive = reactive({})
    _selected_widget: reactive = reactive(None)

    def on_mount(self):
        self.set_interval(0.1, self._refresh_from_dom)
```

---

### D8: Diff de Estado: Custom vs. Biblioteca externa

**Decisão:** Implementação customizada simples focada nos casos de uso.

**Racional:**
- ✅ Casos de uso são bem definidos (dicts, dataclasses, primitives)
- ✅ Sem dependências externas
- ✅ Diff customizado pode formatar saída para DevTools
- ❌ `deepdiff` ou similar seria overkill e mais dependência

**Algoritmo de diff:**
```python
def diff_state(old: Any, new: Any, path: str = "") -> dict:
    if isinstance(old, dict) and isinstance(new, dict):
        return _diff_dicts(old, new, path)
    if isinstance(old, (list, tuple)):
        return _diff_sequences(old, new, path)
    if old != new:
        return {path: {"old": old, "new": new}}
    return {}
```

---

### D9: Queries CSS-like: Parser Customizado vs. Biblioteca

**Decisão:** Parser customizado simples com suporte limitado de seletores.

**Racional:**
- ✅ Casos de uso são limitados (classe, ID, attr selectors)
- ✅ Parser CSS completo seria overkill
- ✅ Sintaxe simples: `ClassName`, `#id`, `[attr=val]`

**Gramática suportada:**
```
selector    := class_selector | id_selector | attr_selector | compound
class_selector := ClassName (ex: AnimatedVerb)
id_selector   := #dom_id (ex: #AnimatedVerb_123)
attr_selector := [attr=value] | [attr] (ex: [estado=DONE])
compound      := class_selector[attr=value] (ex: Turn[estado=DONE])
```

---

### D10: Persistência: JSON vs. SQLite vs. Pickle

**Decisão:** JSON para snapshots, sem persistência automática para estado runtime.

**Racional:**
- ✅ JSON é legível e portável
- ✅ Runtime state não precisa ser persistido (reinicia limpo é bom)
- ✅ Snapshots manuais podem ser salvos onde usuário quiser
- ❌ SQLite seria overkill para 2-3 snapshots por sessão
- ❌ Pickle não é seguro (code injection ao carregar)

---

## Arquitetura de Módulos

```
src/core/sky/chat/textual_ui/dom/
├── __init__.py              # SkyTextualDOM singleton + API pública
├── node.py                  # DOMNode dataclass
├── registry.py              # Registro global + thread-safety
├── watcher.py               # ReactiveWatcher + introspecção
├── differ.py                # Diff de estado
├── tracer.py                # EventTracer + buffer circular
├── snapshot.py              # DOMSnapshot + export/import
├── mixin.py                 # SkyWidgetMixin
└── screens/
    └── devtools.py          # DevToolsScreen (3 painéis)
```

### Fluxo de Dados

```
┌─────────────────┐     register      ┌──────────────┐
│  Widget Textual │ ──────────────────>│ SkyTextualDOM│
└─────────────────┘                   └──────┬───────┘
                                             │
                              ┌──────────────┼──────────────┐
                              ▼              ▼              ▼
                        ┌─────────┐   ┌─────────┐   ┌──────────┐
                        │Registry │   │Watcher  │   │ Tracer  │
                        └─────────┘   └─────────┘   └──────────┘
                              │              │              │
                              └──────────────┼──────────────┘
                                             ▼
                                    ┌────────────────┐
                                    │    DOMNode     │
                                    │  (estado +     │
                                    │   histórico)   │
                                    └────────────────┘
                                             │
                                             ▼ query/devtools
                                    ┌────────────────┐
                                    │ DevToolsScreen │
                                    └────────────────┘
```

---

## Estruturas de Dados

### DOMNode
```python
@dataclass
class DOMNode:
    dom_id: str
    widget: Widget
    parent: DOMNode | None
    children: list[DOMNode]

    # Estado serializável
    state: dict[str, Any]              # metadata (class, visible, etc)
    reactive_props: dict[str, Any]     # valores atuais de reactive()

    # Histórico (configurável)
    prop_history: dict[str, deque]     # prop -> deque de mudanças

    # Metadata
    class_name: str
    is_visible: bool
    is_focused: bool
    position: tuple[int, int, int, int]  # x, y, w, h
```

### DOMSnapshot
```python
@dataclass
class DOMSnapshot:
    snapshot_id: str
    timestamp: datetime
    name: str | None
    description: str | None

    nodes: dict[str, dict]  # dom_id -> estado serializado do DOMNode
    structure: dict         # árvore hierárquica (parent -> children)
    metadata: dict          # session_id, git_commit, widget_count
```

### EventEntry
```python
@dataclass
class EventEntry:
    event_id: str
    timestamp: datetime
    event_type: EventType  # MOUNT, UNMOUNT, INTERACTION, PROP_CHANGED, ERROR

    widget_dom_id: str | None
    widget_class: str | None

    data: dict[str, Any]   # dados específicos do tipo
```

---

## Protocolos e Interfaces

### SkyWidgetMixin Protocol
```python
class SkyWidgetMixin(Protocol):
    _dom_id: str | None

    def on_mount(self) -> None:
        """Auto-registra no SkyTextualDOM."""

    def on_unmount(self) -> None:
        """Auto-desregistra do SkyTextualDOM."""

    def _get_dom_parent(self) -> Widget | None:
        """Retorna self.parent se também registrado."""
```

### ReactiveWatcher Protocol
```python
class ReactiveWatcher(Protocol):
    def watch_widget(self, node: DOMNode) -> None:
        """Configura watch_ methods para props reactive."""

    def get_history(self, dom_id: str, prop: str) -> deque:
        """Retorna histórico de mudanças da prop."""
```

---

## Performance Considerations

### Overhead por Widget
| Operação | Complexidade | Notas |
|----------|--------------|-------|
| Register | O(1) | Apenas dict lookup |
| Query by ID | O(1) | Hash lookup |
| Query CSS | O(n) | Varre todos os nodes (n = widgets registrados) |
| Prop change | O(1) | Append em deque |
| Snapshot | O(n) | Deep copy de todos os nodes |

### Otimizações
- **Lazy evaluation:** Queries CSS são lazy generator quando possível
- **Selective watch:** Apenas props explicitamente reativas são observadas
- **Buffer sizing:** Histórico limitado impede crescimento indefinido
- **Async write:** Event tracer write é async (não bloqueia UI)

---

## Migration Plan

### Fase 1: Core Infrastructure (Sem breaking changes)
1. Criar módulos `dom/registry.py`, `dom/node.py`, `dom/mixin.py`
2. Implementar `SkyTextualDOM` singleton
3. Adicionar mixin em widgets existentes (opcional)
4. Testes unitários de registro/queries

### Fase 2: Reactive Watching
1. Implementar `ReactiveWatcher`
2. Integrar com `DOMNode` no registro
3. Testar introspecção de props reactive
4. Benchmark de overhead

### Fase 3: Snapshots + Diff
1. Implementar `DOMSnapshot` + export/import
2. Algoritmo de diff customizado
3. Testes de snapshots grandes (100+ widgets)

### Fase 4: Event Tracer
1. Implementar `EventTracer` com buffer circular
2. Hooks para eventos Textual (mount, unmount, click, etc.)
3. Exportação (JSON, CSV)

### Fase 5: DevTools UI
1. Criar `DevToolsScreen` com 3 painéis
2. Conectar com `SkyTextualDOM` (queries, snapshots, tracer)
3. Atalho `Ctrl+D` no `ChatScreen`
4. Testes E2E de navegação

### Rollback Strategy
- DevTools é completamente isolado: remover `import` e tudo volta ao normal
- Mixin é opcional: widgets funcionam sem ele
- Nenhuma mudança em código existente é necessária

---

## Open Questions

1. **Q:** Snapshot de 100+ widgets pode ser lento (>100ms)?
   **A:** Implementar `incremental=True` para snapshots parciais.

2. **Q:** Histórico de props pode consumir muita memória?
   **A:** Configurar `history_limit` baixo (10-20) por padrão.

3. **Q:** Queries CSS podem ser lentas com muitos widgets?
   **A:** Indexar por classe em registry para O(1) queries por classe.

---

> "Design é a arte dos trade-offs conscientes" – made by Sky 🎨
