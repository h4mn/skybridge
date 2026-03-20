# ChatLog 2.0 - Design Técnico (Revisão Final)

## Context

### Estado Atual

```
ChatLogger
    │ (chamada direta de método)
    ▼
ChatLog (VerticalScroll)
    ├── debug(), info(), error(), evento()
    ├── Buffer de 100 linhas quando fechado
    └── Fila de pendentes para flush em batch
```

**Problemas identificados:**
1. **Acoplamento forte**: `ChatLogger` conhece métodos específicos do `ChatLog`
2. **Violação do Textual**: Usa chamada direta em vez de `post_message()`
3. **Inflexibilidade**: Impossível trocar implementação visual
4. **Poluição de conceitos**: Logger decide formato visual (cores, markup)

### Restrições

- **Portabilidade**: Código deve poder ser movido para fora de `src/core/sky/` sem quebrar
- **TDD Estrito**: Projeto segue test-first (Red → Green → Refactor)
- **Textual 0.x**: Framework impõe certas limitações
- **Performance**: Logs não podem bloquear a UI principal (definido desde dia 1)
- **Acessibilidade**: Tema deve ser toggleável para usuários sensíveis

### Stakeholders

- **Desenvolvedores**: Precisam de debugging eficiente
- **Usuários finais**: Interface deve ser intuitiva e acessível
- **QA**: Testes devem ser determinísticos e reproduzíveis

---

## Goals / Non-Goals

**Goals:**

1. **Desacoplamento**: `ChatLogger` não deve conhecer implementações de UI
2. **Simplicidade**: Protocol direto, não Event Bus complexo
3. **Filtros poderosos**: Nível + escopo + busca reativa
4. **Estética distintiva**: Tema cyberpunk toggleável
5. **Performance**: Ring buffer + virtualização desde dia 1
6. **Portabilidade**: Injeção de dependências para mover código facilmente

**Non-Goals:**

- Event Bus complexo (usar Protocol simples)
- Persistir configurações de filtros
- Exportar para formatos diferentes de texto
- Logs distribuídos entre múltiplos processos

---

## Decisões Arquiteturais (Revistas)

### 1. Protocol `LogConsumer` (Simples e Type-Safe)

**Decisão**: Usar `typing.Protocol` ao invés de Event Bus complexo.

**Racional:**
- Type-safe (mypy valida em compile-time)
- Flexível - qualquer classe pode implementar
- Testável - `Mock(spec=LogConsumer)` funciona perfeitamente
- **Simples** - nenhum código de subscribe/unsubscribe/thread-safety

```python
@runtime_checkable
class LogConsumer(Protocol):
    def write_log(
        self,
        level: int,  # logging.INFO, logging.ERROR, etc.
        message: str,
        timestamp: datetime,
        scope: LogScope,
        context: dict[str, Any] | None = None
    ) -> None: ...
```

---

### 2. `logging` Padrão do Python

**Decisão**: Usar níveis padrão do módulo `logging`, não enum custom.

**Níveis:**
- `logging.DEBUG` (10)
- `logging.INFO` (20)
- `logging.WARNING` (30)
- `logging.ERROR` (40)
- `logging.CRITICAL` (50)

**Removido:** `LogLevel.EVENT` (usar `logging.INFO` com context apropriado)

---

### 3. Filtro por Escopo + Nível

**Decisão**: Dois eixos de filtro combinados.

**Escopos definidos:**
```python
class LogScope(Enum):
    ALL = "all"
    SYSTEM = "system"
    USER = "user"
    API = "api"
    DATABASE = "database"
    NETWORK = "network"
    VOICE = "voice"
    MEMORY = "memory"
```

**Filtro combinado:**
- Nível: `ERROR` mostra ERROR+CRITICAL
- Escopo: `VOICE` mostra apenas logs de voz
- Ambos aplicados juntos: `ERROR` + `VOICE` = apenas errors de voz

---

### 4. Tema Cyberpunk Toggleável

**Decisão**: Manter tema, mas permitir desabilitar efeitos problemáticos.

```python
class CyberpunkPreset(Enum):
    MINIMAL = auto()   # Apenas cores
    BALANCED = auto()  # Cores + glow sutil
    FULL = auto()      # Cores + glow + scanlines

@dataclass
class CyberpunkConfig:
    preset: CyberpunkPreset = CyberpunkPreset.BALANCED
    scanlines: bool | None = None
    phosphor_glow: bool | None = None
    flicker: bool = False  # Desligado por padrão (acessibilidade)
```

**TCSS modular:**
```css
ChatLog.cyberpunk { }           /* Base */
ChatLog.scanlines::before { }   /* Scanlines */
ChatLog.glow .log-line { }      /* Glow */
ChatLog.flicker { }             /* Flicker */
```

---

### 5. Performance Definida Desde Dia 1

**Decisão**: Ring buffer + virtualização desde o início.

```python
@dataclass
class ChatLogConfig:
    max_entries: int = 1000                # Ring buffer
    max_buffer_when_closed: int = 100     # Quando widget fechado
    virtualization_threshold: int = 200   # Ativa acima disso
    enable_virtualization: bool = True

class ChatLog(VerticalScroll):
    def __init__(self, config: ChatLogConfig | None = None):
        self._config = config or ChatLogConfig()
        self._entries: deque[LogEntry] = deque(maxlen=self._config.max_entries)
```

**Virtualização:**
- Renderiza apenas linhas visíveis + margem (50 acima/abaixo)
- Remove widgets fora do DOM (`remove()`)
- Ativa automaticamente acima de `virtualization_threshold`

---

### 6. Async-Safety (não Thread-Safety)

**Decisão**: Usar `asyncio.Lock` e `call_soon_threadsafe`.

**Racional:**
- Textual roda em event loop asyncio (single-threaded)
- `threading.Lock` é anti-pattern em código asyncio
- `call_soon_threadsafe()` para chamadas cross-thread

```python
class AsyncSafeLogConsumer:
    async def write_log_async(self, ...) -> None:
        async with self._lock:
            await loop.run_in_executor(None, self._consumer.write_log, ...)

    def write_log(self, ...) -> None:
        try:
            loop = asyncio.get_running_loop()
            loop.call_soon_threadsafe(self._consumer.write_log, ...)
        except RuntimeError:
            # Sem event loop - chamada direta
            self._consumer.write_log(...)
```

---

### 7. Clipboard - Lib Externa com Fallback

**Decisão**: Usar lib `clipboard` como preferência, com fallback vendored.

**Racional (POC invalidou vendored):**
- A POC demonstrou que a implementação vendored tem problemas de compatibilidade
- Lib `clipboard` é mais robusta e cross-platform
- Mantém fallback vendored para casos onde lib não está instalada

**Arquivo:** `src/core/sky/log/clipboard.py`

**Implementação:**
1. Primeiro tenta `import clipboard`
2. Se falha, usa implementação vendored (Windows/macOS/Linux)
3. Tenta `win32clipboard` ou subprocess no Windows
4. Tenta `pbcopy` no macOS
5. Tenta `xclip`, `wl-copy` no Linux

```python
def copy_to_clipboard(text: str) -> bool:
    """Copia texto para clipboard. Retorna True se sucesso.

    Tenta lib clipboard primeiro, depois fallback vendored.
    """
    try:
        import clipboard
        clipboard.copy(text)
        return True
    except ImportError:
        # Fallback para implementação vendored
        ...
```

---

### 8. POC como Validador Visual

**Decisão**: Manter `poc.py` como playground seguro.

**Fluxo:**
```
1. Desenvolver feature
2. Testar no poc.py (visual + interação)
3. SE gostar → integrar no MainScreen
   SE NÃO → descartar e iterar
```

**POC não é código de produção** - é experimentação.

---

### 9. 3 Widgets Separados (Coesão Funcional)

**Decisão**: Manter `LogFilter`, `LogSearch`, `LogCopier` separados.

**Racional:**
- Coesão funcional (responsabilidade única)
- Testabilidade (testar isolado)
- Composibilidade (pode usar apenas LogSearch)

**Container para uso conjunto:**
```python
class LogToolbar(Static):
    """Container que agrupa os 3 widgets."""
    def compose(self) -> ComposeResult:
        yield LogFilter()
        yield LogSearch()
        yield LogCopier()
```

---

## Arquitetura Final

```
┌─────────────────────────────────────────────────────────────────────────┐
│                    ChatLogger (Adapter Simples)                        │
│                    Conhece apenas LogConsumer Protocol                 │
└──────────────────────────────┬──────────────────────────────────────────┘
                               │ write_log()
                               │
                               ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                         ChatLog Widget                                  │
│                    ┌─────────────────────────────┐                    │
│                    │  deque[LogEntry] (ring)    │                    │
│                    │  Filtro: nível + escopo    │                    │
│                    │  Virtualização ativa       │                    │
│                    └─────────────────────────────┘                    │
└──────────────────────────────┬──────────────────────────────────────────┘
                               │
        ┌──────────────────────┼──────────────────────┐
        │                      │                      │
        ▼                      ▼                      ▼
┌─────────────┐   ┌─────────────┐   ┌─────────────┐
│ LogFilter   │   │ LogSearch   │   │ LogCopier   │
│ +Escopo     │   │ (debounce)  │   │ (clipboard)  │
└─────────────┘   └─────────────┘   └─────────────┘
```

---

## Estrutura de Módulos Final

```
src/core/sky/log/
├── __init__.py
├── poc.py                    # POC standalone (validador visual)
├── consumer.py               # LogConsumer Protocol
├── entry.py                  # LogEntry dataclass
├── scope.py                  # LogScope enum
├── clipboard.py              # pyperclip vendored
├── theme.py                  # CyberpunkConfig + TCSS
├── config.py                 # ChatLogConfig
└── widgets/
    ├── __init__.py
    ├── chat_log.py           # ChatLog principal
    ├── log_filter.py         # Filtro nível + escopo
    ├── log_toolbar.py        # Container dos 3 widgets
    ├── log_search.py         # Busca reativa
    └── log_copier.py         # Copiar clipboard
```

---

## Fluxo de Dados

```
1. Código chama: chat_logger.info("Mensagem", scope=LogScope.API)
2. ChatLogger cria: LogEntry(level=logging.INFO, message="Mensagem", ...)
3. ChatLogger chama: consumer.write_log(entry.level, entry.message, ...)
4. ChatLog recebe: _on_log_entry(entry)
5. ChatLog aplica: filtro nível + escopo
6. ChatLog renderiza: com tema cyberpunk (se ativo)
7. Virtualização: remove widgets fora do DOM
```

---

## Especificação de Widgets (Revista)

### LogFilter (Nível + Escopo)

```python
class LogFilter(Static):
    """Filtro combinado: Nível + Escopo."""

    class FilterChanged(Message):
        level: int | None           # None = ALL
        scope: LogScope | None      # LogScope.ALL = todos

    # Níveis: ALL, ERROR, WARNING, INFO, DEBUG
    # Escopos: ALL, SYSTEM, USER, API, DATABASE, NETWORK, VOICE, MEMORY
```

### LogSearch

```python
class LogSearch(Input):
    """Input com debounce 300ms."""

    search_term = reactive("")

    def _debounce_search(self) -> None:
        self.set_interval(0.3, self._execute_search)
```

### LogCopier

```python
class LogCopier(Button):
    """Copia logs filtrados para clipboard."""

    async def on_click(self) -> None:
        from core.sky.log.clipboard import copy_to_clipboard
        text = self._get_filtered_text()
        success = copy_to_clipboard(text)
```

### ChatLog 2.0

```python
class ChatLog(VerticalScroll):
    """Widget com ring buffer, virtualização e filtros."""

    def __init__(
        self,
        config: ChatLogConfig | None = None,
        cyberpunk: CyberpunkConfig | None = None,
    ):
        self._config = config or ChatLogConfig()
        self._cyberpunk = cyberpunk or CyberpunkConfig()
        self._entries: deque[LogEntry] = deque(maxlen=self._config.max_entries)
        self._filter_level: int | None = None
        self._filter_scope: LogScope = LogScope.ALL
```

---

## Tema Cyberpunk (Toggleável)

### Presets

```python
class CyberpunkPreset(Enum):
    MINIMAL = auto()   # Apenas cores (sem efeitos)
    BALANCED = auto()  # Cores + glow sutil
    FULL = auto()      # Cores + glow + scanlines + flicker
```

### TCSS Modular

```css
/* Base - cores apenas */
ChatLog.cyberpunk {
    background: #0a0a0f;
    border-top: thick #1a1a2e;
}

/* Scanlines - opcional */
ChatLog.cyberpunk.scanlines::before {
    background: repeating-linear-gradient(...);
}

/* Phosphor glow - opcional */
ChatLog.cyberpunk.glow .log-line {
    text-shadow: 0 0 2px currentColor;
}

/* Flicker - opcional e desligado por padrão */
ChatLog.cyberpunk.flicker {
    animation: subtle-flicker 10s infinite;
}
```

---

## Performance: Definições Desde Dia 1

### Ring Buffer

```python
self._entries: deque[LogEntry] = deque(maxlen=1000)  # Auto-descarta
```

### Virtualização

```python
def _enable_virtualization(self) -> None:
    """Renderiza apenas linhas visíveis + margem."""
    visible_range = self._get_visible_range()

    # Remove widgets fora do range
    for widget in self.query(Static):
        if widget._line_number not in visible_range:
            widget.remove()
```

### Configuração

```python
@dataclass
class ChatLogConfig:
    max_entries: int = 1000                # Ring buffer
    virtualization_threshold: int = 200   # Ativa acima disso
    enable_virtualization: bool = True

    @classmethod
    def for_development(cls) -> "ChatLogConfig":
        return cls(max_entries=500, virtualization_threshold=100)
```

---

## Risks / Trade-offs (Revisto)

| Risk | Mitigação |
|------|-----------|
| **Performance**: Milhares de logs travam UI | Virtualização desde dia 1, ring buffer |
| **Compatibilidade**: Código legado quebra | Adapter em `ChatLogger`, testes de regressão |
| **Tema ilegível**: Scanlines/glow atrapalham | Toggleável, presets, flicker desligado por padrão |
| **Clipboard**: Compatibilidade OS | Código vendored com fallbacks |
| **AsyncIO complexity**: Locks podem deadlock | Usar apenas `asyncio.Lock`, testar exaustivamente |

---

## POC como Ferramenta de Validação

**Uso:**
```bash
# Desenvolvimento com validação visual
textual run --dev src/core/sky/log/poc.py minimal
textual run --dev src/core/sky/log/poc.py balanced
textual run --dev src/core/sky/log/poc.py full

# Testes automatizados
pytest tests/unit/core/sky/log/poc_test.py --snapshot
```

**Critério de integração:**
- POC funciona bem visualmente → integrar no MainScreen
- POC não funciona → descartar e iterar

---

## Open Questions (Revisto)

1. **Tamanho ideal do buffer**: Configurável, medir em produção
2. **Escopos adicionais**: Extensível via enum, adicionar conforme necessidade

---

## Referências

- Textual Docs: https://textual.textualize.io/
- pytest-textual: https://github.com/Textualize/pytest-textual
- Protocol PEP 544: https://peps.python.org/pep-0544/
- Python logging: https://docs.python.org/3/library/logging.html
