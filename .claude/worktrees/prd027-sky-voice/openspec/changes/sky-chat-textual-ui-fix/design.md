# Design: Sky Chat Textual UI Fix

## Context

### Estado Atual

A change `sky-chat-textual-ui` foi implementada com arquitetura modular correta (separação em screens, widgets, workers), mas o componente principal de **título animado está quebrado**. A animação de "color sweep" especificada não funciona — a implementação usa apenas markup estático com CSS fade simples.

Uma **PoC funcional em `src/core/sky/chat/poc/app.py`** demonstra a implementação correta e completa da UI Textual, com:
- Animação de color sweep **verdadeira** (gradiente percorrendo letras)
- Sistema de estado emocional `EstadoLLM`
- Paletas de cores dinâmicas por emoção
- `ChatTextArea` customizado com Enter envia, Shift+Enter nova linha
- Modal de inspeção de estado
- Log estruturado para debug (`PocLog`)

### Problema

A implementação quebrada da change **não consegue entregar a UI especificada**:
- `AnimatedTitle` usa `render()` retornando string estática
- `ChatHeader._update_title()` usa `mount()` acumulando widgets
- `AnimatedVerb` não existe (animação programática ausente)
- `ChatTextArea` não existe (usa `Input` padrão)
- Sistema de paletas de cores não existe

### Objetivo

**Portar TODA a UI funcional da PoC para a arquitetura modular da change**, mantendo o visual bonito e detalhado da PoC, mas organizado em módulos coerentes.

---

## Goals / Non-Goals

**Goals:**
1. ✅ Portar `AnimatedVerb` com animação color sweep programática completa
2. ✅ Portar `EstadoLLM` e sistema de paletas de cores por emoção
3. ✅ Portar `ChatTextArea` customizado com Enter envia, Shift+Enter nova linha
4. ✅ Portar `EstadoModal` para inspeção de estado interno
5. ✅ Corrigir `AnimatedTitle` para usar `compose()` com widgets filhos
6. ✅ Corrigir `ChatHeader._update_title()` para não acumular widgets
7. ✅ Manter arquitetura modular da change (separação screens/widgets/workers)
8. ✅ Integrar workers assíncronos existentes com a nova UI
9. ✅ Adicionar `PocLog` renomeado como `ChatLog` para observabilidade
10. ✅ Criar WelcomeScreen com banner ASCII art "SkyBridge"

**Non-Goals:**
- ❌ Recriar a arquitetura monolítica da PoC (manter estrutura modular)
- ❌ Remover workers assíncronos existentes (são essenciais para Claude/RAG)
- ❌ Modificar screens secundárias (Help, Config, SessionSummary)
- ❌ Alterar estrutura de comandos (`/new`, `/help`, `/sair`)

---

## Arquitetura

### Estrutura de Módulos

```
src/core/sky/chat/textual_ui/
│
├── __init__.py                 # TextualChatApp (entry point)
├── screens/                    # Telas da aplicação
│   ├── __init__.py
│   ├── welcome.py              # WelcomeScreen (primeira tela)
│   ├── chat.py                 # ChatScreen (tela principal) ← MODIFICAR
│   ├── help.py                 # HelpScreen (comandos)
│   ├── config.py               # ConfigScreen (configurações)
│   └── session_summary.py      # SessionSummaryScreen (resumo)
│
├── widgets/                    # Widgets customizados
│   ├── __init__.py
│   ├── animated_verb.py        # NOVO: AnimatedVerb + EstadoLLM + Paletas
│   ├── chat_text_area.py       # NOVO: ChatTextArea customizado
│   ├── title.py                # MODIFICAR: AnimatedTitle com compose()
│   ├── header.py               # MODIFICAR: ChatHeader sem mount()
│   ├── bubbles.py              # SkyBubble, UserBubble (já existe)
│   ├── thinking.py             # ThinkingIndicator (já existe)
│   ├── context_bar.py          # ContextBar (já existe)
│   ├── toast.py                # ToastNotification (já existe)
│   ├── modal.py                # ConfirmModal (já existe)
│   ├── tool_feedback.py        # ToolFeedback (já existe)
│   ├── chat_log.py             # NOVO: ChatLog (ex-PocLog)
│   └── chat_scroll.py          # NOVO: ChatScroll (ex-PocVerticalScroll)
│
├── workers/                    # Workers assíncronos
│   ├── __init__.py
│   ├── base.py                 # BaseWorker
│   ├── claude.py               # ClaudeWorker
│   ├── rag.py                  # RAGWorker
│   ├── memory.py               # MemorySaveWorker
│   ├── queue.py                # WorkerQueue
│   ├── metrics.py              # WorkerMetrics
│   └── errors.py               # WorkerErrors
│
├── commands.py                 # Comandos (/new, /help, /sair, etc.)
└── styles/                     # Arquivos CSS (se houver)
```

### Diagrama de Componentes

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                              TextualChatApp                                │
├─────────────────────────────────────────────────────────────────────────────┤
│  CSS_PATH = "assets/sky_chat.css"                                          │
│  BINDINGS = [("^q", "quit", "Quit"), ("^d", "toggle_dark", "Toggle dark")]   │
│                                                                             │
│  on_mount() → WelcomeScreen                                                  │
└─────────────────────────────────────────────────────────────────────────────┘
                                       │
                                       ▼
┌───────────────────────────────────────────────────────────────────────────────────────┐
│                             WelcomeScreen                                             │
├───────────────────────────────────────────────────────────────────────────────────────┤
│  BINDINGS = [("q", "quit", "Quit")]                                                   │
│                                                                                       │
│  compose():                                                                           │
│  ├─ Vertical(id="welcome-container") [align: center middle]                           │
│  │   ├─ Static(id="banner") [class="splash-banner"] ← ASCII ART                       │
│  │   │   └─ "███████╗██╗  ██╗██╗   ██╗██████╗ ██████╗ ██╗██████╗  ██████╗ ███████╗"   │
│  │   │      "██╔════╝██║ ██╔╝╚██╗ ██╔╝██╔══██╗██╔══██╗██║██╔══██╗██╔════╝ ██╔════╝"   │
│  │   │      "███████╗█████╔╝  ╚████╔╝ ██████╔╝██████╔╝██║██║  ██║██║  ███╗█████╗"     │
│  │   │      "╚════██║██╔═██╗   ╚██╔╝  ██╔══██╗██╔══██╗██║██║  ██║██║   ██║██╔══╝"     │
│  │   │      "███████║██║  ██╗   ██║   ██████╔╝██║  ██║██║██████╔╝╚██████╔╝███████╗"   │
│  │   │      "╚══════╝╚═╝  ╚═╝   ╚═╝   ╚═════╝ ╚═╝  ╚═╝╚═╝╚═════╝  ╚═════╝ ╚══════╝"   │
│  │   │                                                                                │
│  │   │           ═══════════════════════════════════════════════                      │
│  │   │             Chat Interface by Sky 🚀                                           │
│  │   │                                                                                │
│  │   │           Bem-vindo ao SkyBridge!                                              │
│  │   ├─ ChatTextArea(id="first-input") ← NOVO                                         │
│  │   └─ Static(id="footer-hint") [dim] comandos                                       │
│  │                                                                                    │
│  on_chat_text_area_submitted() → ChatScreen(msg)                                      │
└───────────────────────────────────────────────────────────────────────────────────────┘
                                       │
                                       ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                              ChatScreen                                     │
├─────────────────────────────────────────────────────────────────────────────┤
│  BINDINGS = [("ctrl+l", "toggle_log", "Toggle Log"),                         │
│              ("ctrl+v", "ciclar_verbo", "Test Verbo")]                        │
│                                                                             │
│  compose():                                                                   │
│  ├─ ChatHeader(max_context=20) ← MODIFICAR                                   │
│  │   ├─ AnimatedTitle("Sky", verbo, predicado) ← MODIFICAR                  │
│  │   │   ├─ Static("[bold]Sky[/] ")                                        │
│  │   │   ├─ AnimatedVerb(verbo) ← NOVO                                      │
│  │   │   └─ Static(" predicado")                                           │
│  │   └─ Static("🔥 X msgs | RAG: on | GLM-4.7")                             │
│  │                                                                          │
│  ├─ ChatScroll(id="messages-scroll") ← NOVO                                │
│  │   └─ [UserBubble, SkyBubble, Separator, ...]                             │
│  │                                                                          │
│  ├─ ChatTextArea(id="chat-input") ← NOVO                                    │
│  ├─ ChatLog(id="debug-log") ← NOVO                                           │
│  └─ Footer()                                                                  │
│                                                                             │
│  on_chat_text_area_submitted():                                              │
│    → process_message() → async workers → update UI                            │
│                                                                             │
│  on_animated_verb_inspecionado():                                            │
│    → EstadoModal(estado) ← NOVO                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Decisões Técnicas

### Decisão 1: AnimatedVerb como Widget Independente

**Escolha:** Criar `widgets/animated_verb.py` com `AnimatedVerb(Static)` como widget independente.

**Por que:**
- Encapsula toda a lógica de animação (timers, reativos, render)
- Pode ser reutilizado em outros contextos
- Testável isoladamente
- Segue princípio de responsabilidade única

**Alternativas rejeitadas:**
- ❌ Integrar diretamente em `AnimatedTitle` → violaria SRP, difícil testar
- ❌ Usar apenas CSS animation → não implementa color sweep real

**Estrutura do AnimatedVerb:**
```python
class AnimatedVerb(Static):
    _offset: reactive = reactive(0.0)    # posição do sweep
    _pulso: reactive = reactive(0.0)     # fase da oscilação
    _estado: reactive = reactive(None)   # EstadoLLM atual

    def on_mount(self):
        self._timer_sweep = self.set_interval(self._intervalo_sweep(), self._tick_sweep)
        self._timer_oscila = self.set_interval(0.05, self._tick_oscila)

    def render(self) -> RenderResult:
        # Aplica cor letra-por-letra baseada em _offset e _pulso
        ...

    def update_verbo(self, novo_verbo: str) -> None:
        self.texto = novo_verbo

    def update_estado(self, estado: EstadoLLM) -> None:
        # Atualiza estado, reinicia timer com nova velocidade
        ...
```

### Decisão 2: EstadoLLM como Dataclass Central

**Escolha:** Criar `EstadoLLM` como dataclass central no módulo `animated_verb.py`.

**Por que:**
- Representa o estado emocional/cognitivo da LLM de forma estruturada
- Controla todas as dimensões da animação (certeza, esforço, emoção, direção)
- Pode ser expandido no futuro com mais dimensões

**Estrutura:**
```python
@dataclass
class EstadoLLM:
    verbo: str = "iniciando"
    certeza: float = 0.8    # 0.0=incerto → 1.0=certo
    esforco: float = 0.5    # 0.0=raso → 1.0=profundo
    emocao: str = "neutro"  # "urgente", "pensando", etc.
    direcao: int = 1        # +1=avançando, -1=revisando
```

### Decisão 3: ChatTextArea Customizado vs Input Padrão

**Escolha:** Criar `ChatTextArea(TextArea)` com comportamento customizado.

**Por que:**
- Enter envia mensagem (comportamento de chat)
- Shift+Enter insere nova linha (multi-line)
- Escape limpa texto
- Mensagem `Submitted` customizada para desacoplamento

**Alternativas rejeitadas:**
- ❌ Usar `Input` padrão do Textual → Enter não envia, precisa de workaround
- ❌ Usar `RichLog` como input → não é editável como TextArea

### Decisão 4: AnimatedTitle com compose() em vez de render()

**Escolha:** Refatorar `AnimatedTitle` para usar `compose()` com 3 widgets filhos.

**Por que:**
- `compose()` permite atualizar widgets filhos individualmente
- `render()` retorna string estática (não é atualizável)
- Segue padrão do Textual para layouts compostos

**ANTES (quebrado):**
```python
class AnimatedTitle(Widget):
    def render(self) -> str:
        return f"{self.sujeito} [@click=app.quit]{self.verbo}[/] {self.predicado}"
```

**DEPOIS (funcional):**
```python
class AnimatedTitle(Widget):
    def compose(self) -> ComposeResult:
        yield Static(f"[bold]{self._sujeito}[/] ")
        yield AnimatedVerb(self._verbo)
        yield Static(f" {self._predicado}")

    def update_title(self, verbo: str, predicado: str) -> None:
        self.query_one(AnimatedVerb).update_verbo(verbo)
        self.query_one("Static:last-of-type", Static).update(f" {predicado}")
```

### Decisão 5: ChatHeader Atualiza via query_one() em vez de mount()

**Escolha:** Modificar `ChatHeader._update_title()` para usar `query_one().update_title()`.

**Por que:**
- `mount()` **acumula** widgets a cada chamada (vazamento de memória)
- `query_one().update_title()` **atualiza** widget existente
- Mais eficiente e correto

**ANTES (quebrado):**
```python
def _update_title(self, verbo: str, predicado: str) -> None:
    title_container = self.query_one("#title-container", Static)
    title_container.mount(AnimatedTitle(verbo=verbo, predicado=predicado))  # ❌
```

**DEPOIS (funcional):**
```python
def update_title(self, verbo: str, predicado: str) -> None:
    self._verbo = verbo
    self._predicado = predicado
    self.query_one(AnimatedTitle).update_title(verbo, predicado)  # ✅
```

### Decisão 6: ChatScroll com Métodos Helpers

**Escolha:** Criar `ChatScroll(VerticalScroll)` com métodos `adicionar_mensagem()` e `limpar()`.

**Por que:**
- Abstrai a complexidade de montar widgets no ScrollView
- Fornece API semântica para o domínio de chat
- Simplifica o código de ChatScreen

**Estrutura:**
```python
class ChatScroll(VerticalScroll):
    def adicionar_mensagem(self, texto: str) -> None:
        bubble = Static(texto)
        self.mount(bubble)
        self.scroll_end()

    def limpar(self) -> None:
        self.remove_children()
```

### Decisão 7: Footer Padrão vs Input Customizado

**Escolha:** Usar `Footer()` padrão do Textual + `ChatTextArea` customizado separado (input NÃO fica no Footer).

**Por que:**
- `Footer()` padrão exibe atalhos de teclado (já implementado pelo Textual)
- `ChatTextArea` é um widget **separado** com comportamento customizado
- `Input` padrão do Footer tem comportamento diferente (Enter não envia)
- Separação de responsabilidades: Footer = atalhos, ChatTextArea = input

**PoC (funcional):**
```python
def compose(self) -> ComposeResult:
    yield PocHeader()
    yield PocVerticalScroll(id="container")
    yield ChatTextArea(id="chat_input")      # ← INPUT É SEPARADO
    yield PocLog()                         # ← LOG SEPARADO
    yield Footer()                          # ← FOOTER APENAS ATALHOS
```

**Change quebrada (INCORRETA):**
```python
def compose(self) -> ComposeResult:
    yield ChatHeader(max_context=20)
    yield Vertical(ScrollView(...))
    yield Footer()                          # ← INPUT IMPLÍCITO NO FOOTER? ❌
    # ❌ ChatTextArea não existe
```

**Correto (fix):**
```python
def compose(self) -> ComposeResult:
    yield ChatHeader(max_context=20)
    yield ChatScroll(id="messages-scroll")
    yield ChatTextArea(id="chat-input")   # ← INPUT SEPARADO
    yield ChatLog(id="debug-log")          # ← LOG SEPARADO
    yield Footer()                          # ← ATALHOS APENAS
```

**Importante:** O Footer do Textual **não contém input** quando usamos `ChatTextArea` separado. O Footer apenas exibe os bindings da aplicação.

---

### Decisão 8: ChatLog para Observabilidade

**Escolha:** Criar `ChatLog(RichLog)` com métodos estruturados (`debug()`, `info()`, `error()`, `evento()`), toggleável com `Ctrl+L`.

**Por que:**
- Permite debug e observabilidade da UI em produção
- Atalho `Ctrl+L` para toggle durante desenvolvimento
- Logs estruturados são mais fáceis de filtrar

**Estrutura:**
```python
class ChatLog(RichLog):
    markup = True

    def debug(self, message: str) -> None:
        self.write(f"[yellow][DEBUG][/] {message}")

    def info(self, message: str) -> None:
        self.write(f"[blue][INFO][/] {message}")

    def error(self, message: str) -> None:
        self.write(f"[red][ERROR][/] {message}")

    def evento(self, nome: str, dados: str = "") -> None:
        self.write(f"[green][EVENTO][/] {nome} {dados}")
```

---

### Decisão 9: WelcomeScreen com ASCII Art Banner

**Escolha:** Usar ASCII art estilo "box drawing" (com █, ╔, ═, ╝, ║, ╚, ╩, ╦, ╠, ╬, etc.) como título na WelcomeScreen, em vez de Label simples.

**Por que:**
- Textual não permite controle direto de tamanho de fonte
- Label comum fica pequeno e pouco impactante
- ASCII art box drawing é visível em qualquer terminal
- Cria identidade visual forte desde a primeira tela
- Estilo visualmente impactante com contornos e caracteres especiais

**Alternativas rejeitadas:**
- ❌ Label com markup `[bold]` → fica pequeno
- ❌ Markdown com `# Título` → depende de fonte do terminal
- ❌ ASCII art simples com █ apenas → menos visualmente interessante
- ❌ Imagem embutida → complexo e depende de terminal

**Banner ASCII Art (estilo box drawing com contorno):**
```
███████╗██╗  ██╗██╗   ██╗██████╗ ██████╗ ██╗██████╗  ██████╗ ███████╗
██╔════╝██║ ██╔╝╚██╗ ██╔╝██╔══██╗██╔══██╗██║██╔══██╗██╔════╝ ██╔════╝
███████╗█████╔╝  ╚████╔╝ ██████╔╝██████╔╝██║██║  ██║██║  ███╗█████╗
╚════██║██╔═██╗   ╚██╔╝  ██╔══██╗██╔══██╗██║██║  ██║██║   ██║██╔══╝
███████║██║  ██╗   ██║   ██████╔╝██║  ██║██║██████╔╝╚██████╔╝███████╗
╚══════╝╚═╝  ╚═╝   ╚═╝   ╚═════╝ ╚═╝  ╚═╝╚═╝╚═════╝  ╚═════╝ ╚══════╝

                      ═══════════════════════════════════════════════
                        Chat Interface by Sky 🚀
```

**Estrutura da WelcomeScreen:**
```python
class WelcomeScreen(Screen):
    """Tela de apresentação com banner ASCII art."""

    BINDINGS = [
        ("q", "app.quit", "Quit"),
    ]

    def compose(self) -> ComposeResult:
        # Banner ASCII art centralizado (estilo box drawing com contorno)
        banner = Static(
            """\
███████╗██╗  ██╗██╗   ██╗██████╗ ██████╗ ██╗██████╗  ██████╗ ███████╗
██╔════╝██║ ██╔╝╚██╗ ██╔╝██╔══██╗██╔══██╗██║██╔══██╗██╔════╝ ██╔════╝
███████╗█████╔╝  ╚████╔╝ ██████╔╝██████╔╝██║██║  ██║██║  ███╗█████╗
╚════██║██╔═██╗   ╚██╔╝  ██╔══██╗██╔══██╗██║██║  ██║██║   ██║██╔══╝
███████║██║  ██╗   ██║   ██████╔╝██║  ██║██║██████╔╝╚██████╔╝███████╗
╚══════╝╚═╝  ╚═╝   ╚═╝   ╚═════╝ ╚═╝  ╚═╝╚═╝╚═════╝  ╚═════╝ ╚══════╝

                      ═══════════════════════════════════════════════
                        Chat Interface by Sky 🚀

Bem-vindo ao SkyBridge! Digite sua mensagem para começar.
""",
            id="banner"
        )
        banner.add_class("splash-banner")

        with Vertical(id="welcome-container"):
            yield banner
            yield ChatTextArea(
                id="first-input",
                placeholder="Digite sua mensagem para começar..."
            )
            yield Static(
                "[dim]Comandos: [/dim][bold]/new[/bold] [dim]•[/dim] [bold]/help[/bold] [dim]•[/dim] [bold]/sair[/bold]",
                id="footer-hint"
            )

    def on_chat_text_area_submitted(self, event: ChatTextArea.Submitted) -> None:
        """Usuário enviou primeira mensagem → transitar para ChatScreen."""
        if event.value.strip():
            self.app.push_screen(ChatScreen(initial_message=event.value))
```

**CSS para o banner:**
```css
#welcome-container {
    align: center middle;
    height: 1fr;
}

.splash-banner {
    text-align: center;
    text-style: bold;
    margin: 1 0;
    padding: 1 0;
}

#first-input {
    min-height: 3;
    width: 60;
    margin: 1 0;
}

#footer-hint {
    text-align: center;
    margin: 1 0;
    color: $text-muted;
}
```

---

## Paletas de Cores por Emoção

### Sistema de Cores Dinâmicas

Cada emoção tem uma paleta de 2 cores (`de` e `ate`) que define o gradiente usado no color sweep.

```python
_PALETAS: dict[str, _TemplateCores] = {
    # 🔥 Quentes (ação intensa)
    "urgente":   _TemplateCores(de="#ff1c1c", ate="#ff9c8f"),
    "debugando": _TemplateCores(de="#ff1c1c", ate="#ffaa00"),
    "empolgado": _TemplateCores(de="#ff1c1c", ate="#ffd93d"),

    # 🌊 Frios (introspecção, incerteza)
    "em_duvida": _TemplateCores(de="#006aff", ate="#a3e2ff"),
    "pensando":  _TemplateCores(de="#006aff", ate="#c77dff"),
    "cuidadoso": _TemplateCores(de="#006aff", ate="#97f8a4"),

    # 🌿 Neutros (idle, concluindo)
    "concluindo": _TemplateCores(de="#007510", ate="#97f8a4"),
    "neutro":     _TemplateCores(de="#007510", ate="#a3e2ff"),
    "curioso":    _TemplateCores(de="#007510", ate="#ffd93d"),
}
```

### Interpolação de Cores

```python
def _lerp_cor(cor_a: str, cor_b: str, t: float) -> str:
    """Interpola linearmente entre duas cores hex. t=0.0→cor_a, t=1.0→cor_b."""
    t = max(0.0, min(1.0, t))
    ra, ga, ba = _hex_para_rgb(cor_a)
    rb, gb, bb = _hex_para_rgb(cor_b)
    return _rgb_para_hex(
        int(ra + (rb - ra) * t),
        int(ga + (gb - ga) * t),
        int(ba + (bb - ba) * t),
    )
```

---

## CSS Completo (da PoC)

### `assets/sky_chat.css`

```css
/* =============================================================================
   Sky Chat Textual UI - Tema Escuro (Baseado na PoC)
   ============================================================================= */

/* === Bubbles === */
SkyBubble {
    background: $panel;
    color: $text;
    margin: 1 2;
    padding: 1;
    border: thick $primary;
    border-subtitle: off;
}

UserBubble {
    background: $primary;
    color: $text;
    margin: 1 2;
    padding: 1;
    border: thick $accent;
    border-subtitle: off;
    text-align: right;
}

/* === AnimatedTitle === */
AnimatedTitle {
    layout: horizontal;
    height: 1;
    width: auto;
}
AnimatedTitle > Static { width: auto; }
AnimatedTitle > AnimatedVerb { width: auto; }

/* === ChatHeader === */
ChatHeader {
    dock: top;
    height: 2;
    background: $panel;
    text-style: bold;
}
ChatHeader > AnimatedTitle {
    text-align: left;
}
ChatHeader #components {
    text-style: dim;
    text-align: left;
}

/* === ChatScroll === */
ChatScroll {
    height: 1fr;
    overflow-y: auto;
}

/* === ChatTextArea === */
ChatTextArea {
    min-height: 3;
}
ChatTextArea:focus {
    border: thick $accent;
}

/* === ChatLog === */
ChatLog {
    height: 1fr;
    dock: bottom;
    display: none;
}
ChatLog.visible {
    display: block;
    height: 10;
}

/* === Separador === */
.turn-separator {
    margin: 1 0;
    text-align: center;
    color: $text-muted;
}

/* === Modal === */
EstadoModal {
    align: center middle;
}
EstadoModal > Vertical {
    width: 44;
    height: auto;
    border: round $accent;
    background: $surface;
    padding: 1 2;
}
```

---

## Implementação por Módulo

### 1. `widgets/animated_verb.py` (NOVO)

**Responsabilidades:**
- `EstadoLLM`: dataclass com estado emocional/cognitivo
- `AnimatedVerb`: widget com animação color sweep programática
- `EstadoModal`: modal para inspeção de estado
- Funções auxiliares: `_lerp_cor()`, `_hex_para_rgb()`, `_rgb_para_hex()`

**Dependencies:**
- `textual.widget.Widget`
- `textual.widgets.Static`
- `textual.reactive`
- `dataclasses`, `math`

### 2. `widgets/chat_text_area.py` (NOVO)

**Responsabilidades:**
- `ChatTextArea`: TextArea customizado com Enter envia, Shift+Enter nova linha
- Mensagem `Submitted`: customizada para desacoplamento

**Dependencies:**
- `textual.widgets.TextArea`
- `textual.events`
- `textual.keys`

### 3. `widgets/title.py` (MODIFICAR)

**Responsabilidades:**
- `AnimatedTitle`: container com 3 widgets filhos (Static + AnimatedVerb + Static)
- Métodos `update_title()`, `update_estado()`

**Mudanças:**
- De `render()` → `compose()`
- Adicionar métodos de atualização

**Dependencies:**
- `widgets.animated_verb.AnimatedVerb`

### 4. `widgets/header.py` (MODIFICAR)

**Responsabilidades:**
- `ChatHeader`: header com 2 linhas (título + métricas)
- Métodos `update_title()`, `update_estado()`, `update_context()`, `update_metrics()`

**Mudanças:**
- Remover `_update_title()` que usa `mount()`
- Modificar `update_title()` para usar `query_one().update_title()`

### 5. `widgets/chat_log.py` (NOVO)

**Responsabilidades:**
- `ChatLog`: RichLog com métodos estruturados

**Dependencies:**
- `textual.widgets.RichLog`

### 6. `widgets/chat_scroll.py` (NOVO)

**Responsabilidades:**
- `ChatScroll`: VerticalScroll com métodos helpers
- `adicionar_mensagem()`, `limpar()`

**Dependencies:**
- `textual.containers.VerticalScroll`

### 7. `screens/chat.py` (MODIFICAR)

**Responsabilidades:**
- `ChatScreen`: tela principal do chat
- Integração com workers assíncronos
- Handlers para mensagens e comandos

**Mudanças:**
- Trocar `Input` por `ChatTextArea`
- Trocar `ScrollView` por `ChatScroll`
- Adicionar `ChatLog`
- Adicionar handler `on_chat_text_area_submitted()`
- Adicionar handler `on_animated_verb_inspecionado()`

### 8. `screens/welcome.py` (MODIFICAR)

**Responsabilidades:**
- `WelcomeScreen`: tela de apresentação com banner ASCII art

**Mudanças:**
- Trocar `Input` por `ChatTextArea`
- Remover `Input.Submitted`, usar `ChatTextArea.Submitted`
- Adicionar banner ASCII art "SkyBridge" em vez de Label simples
- Usar estilo box drawing com caracteres especiais (█, ╔, ═, ╝, ║, ╚, ╩, ╦, ╠, ╬, etc.)
- Centralizar verticalmente com layout `Vertical` [align: center middle]

**Layout com ASCII Art (estilo box drawing):**
```python
class WelcomeScreen(Screen):
    """Tela de apresentação com banner ASCII art."""

    BINDINGS = [("q", "app.quit", "Quit")]

    def compose(self) -> ComposeResult:
        # Banner ASCII art com nome SkyBridge (estilo box drawing)
        banner = Static(
            """\
███████╗██╗  ██╗██╗   ██╗██████╗ ██████╗ ██╗██████╗  ██████╗ ███████╗
██╔════╝██║ ██╔╝╚██╗ ██╔╝██╔══██╗██╔══██╗██║██╔══██╗██╔════╝ ██╔════╝
███████╗█████╔╝  ╚████╔╝ ██████╔╝██████╔╝██║██║  ██║██║  ███╗█████╗
╚════██║██╔═██╗   ╚██╔╝  ██╔══██╗██╔══██╗██║██║  ██║██║   ██║██╔══╝
███████║██║  ██╗   ██║   ██████╔╝██║  ██║██║██████╔╝╚██████╔╝███████╗
╚══════╝╚═╝  ╚═╝   ╚═╝   ╚═════╝ ╚═╝  ╚═╝╚═╝╚═════╝  ╚═════╝ ╚══════╝

                      ═══════════════════════════════════════════════
                        Chat Interface by Sky 🚀

Bem-vindo ao SkyBridge! Digite sua mensagem para começar.
""",
            id="banner"
        )
        banner.add_class("splash-banner")

        with Vertical(id="welcome-container"):
            yield banner
            yield ChatTextArea(
                id="first-input",
                placeholder="Digite sua mensagem para começar..."
            )
            yield Static(
                "[dim]Comandos: [/dim][bold]/new[/bold] [dim]•[/dim] [bold]/help[/bold] [dim]•[/dim] [bold]/sair[/bold]",
                id="footer-hint"
            )

    def on_chat_text_area_submitted(self, event: ChatTextArea.Submitted) -> None:
        """Usuário enviou primeira mensagem → transitar para ChatScreen."""
        if event.value.strip():
            self.app.push_screen(ChatScreen(initial_message=event.value))
```

**CSS específico:**
```css
#welcome-container {
    align: center middle;
    height: 1fr;
}

.splash-banner {
    text-align: center;
    text-style: bold;
    margin: 1 0;
    padding: 1 0;
    font-family: monospace;  /* Importante para ASCII art */
}

#first-input {
    min-height: 3;
    width: 60;
    margin: 1 0;
}

#footer-hint {
    text-align: center;
    margin: 1 0;
    color: $text-muted;
}
```

### 9. Layout Completo da ChatScreen (DELTA CRÍTICO)

**ANTES (quebrado - Layout incorreto):**
```python
# ❌ Layout errado - depende de Input do Footer
def compose(self) -> ComposeResult:
    yield ChatHeader(max_context=20)
    yield Vertical(ScrollView(id="messages-scroll"), id="content-area")
    yield Footer()  # ← Input está implícito aqui, comportamento errado
```

**DEPOIS (funcional - Layout correto):**
```python
# ✅ Layout correto - ChatTextArea separado
def compose(self) -> ComposeResult:
    yield ChatHeader(max_context=20)
    yield ChatScroll(id="messages-scroll")  # ← Container com helpers
    yield ChatTextArea(id="chat-input", placeholder="Digite sua mensagem...")  # ← INPUT SEPARADO
    yield ChatLog(id="debug-log")           # ← LOG PARA DEBUG
    yield Footer()                            # ← APENAS ATALHOS

# Handler correto - não usa on_input_submitted
def on_chat_text_area_submitted(self, event: ChatTextArea.Submitted):
    message = event.value.strip()
    if not message:
        return
    self.process_message(message)
```

**IMPORTANTE:** O Footer do Textual **não contém input** quando usamos `ChatTextArea` separado. O Footer apenas exibe os bindings da aplicação (atalhos de teclado).

---

## Sequência de Eventos

### Fluxo de Mensagem

```
1. Usuário digita no ChatTextArea e pressiona Enter
   ↓
2. ChatTextArea posta ChatTextArea.Submitted(valor)
   ↓
3. ChatScreen.on_chat_text_area_submitted() recebe
   ↓
4. ChatScreen.process_message() é chamado
   ↓
5. UserBubble é montado no ChatScroll
   ↓
6. ThinkingIndicator é montado
   ↓
7. Workers assíncronos são executados (RAG → Claude)
   ↓
8. SkyBubble é montado com resposta
   ↓
9. ThinkingIndicator é removido
   ↓
10. ChatHeader é atualizado (métricas, título)
```

### Fluxo de Atualização de Título

```
1. ChatScreen detecta necessidade de atualizar título
   ↓
2. EstadoLLM é inferido ou definido
   ↓
3. ChatHeader.update_estado(estado, predicado) é chamado
   ↓
4. ChatHeader.query_one(AnimatedTitle).update_estado(estado, predicado)
   ↓
5. AnimatedTitle.query_one(AnimatedVerb).update_estado(estado)
   ↓
6. AnimatedVerb atualiza:
   - self._estado = estado
   - self.texto = estado.verbo
   - Reinicia timer com nova velocidade
   - Se direção mudou, inverte _offset
   ↓
7. watch__estado() atualiza tooltip
   ↓
8. render() é chamado automaticamente
   ↓
9. Novas cores são aplicadas letra-por-letra
```

---

## Riscos / Trade-offs

### [Risco] Performance da Animação

**Risco:** Animação com `render()` chamado frequentemente pode impactar performance.

**Mitigação:**
- `render()` é leve (apenas geração de string com markup)
- Timers usam `set_interval()` do Textual (non-blocking)
- Callbacks são extremamente leves (apenas aritmética)
- Apenas 1-2 AnimatedVerb por app (overhead mínimo)

### [Risco] Acúmulo de Timers

**Risco:** Cada atualização de estado reinicia o timer, pode haver acúmulo se não limpar o anterior.

**Mitigação:**
- `update_estado()` chama `self._timer_sweep.stop()` antes de criar novo
- Garante que apenas 1 timer ativo por dimensão

### [Trade-off] Complexidade vs Flexibilidade

**Trade-off:** `EstadoLLM` adiciona complexidade mas permite comunicação visual rica.

**Decisão:** Vale a pena — a UI fica muito mais expressiva e informativa.

---

## Plano de Implementação (Resumo)

1. **Portar AnimatedVerb + EstadoLLM** (maior complexidade)
2. **Criar ChatTextArea** (menor complexidade)
3. **Refatorar AnimatedTitle** (média complexidade)
4. **Corrigir ChatHeader** (baixa complexidade)
5. **Criar ChatLog e ChatScroll** (baixa complexidade)
6. **Integrar em ChatScreen e WelcomeScreen** (média complexidade)
7. **Testes TDD** (Red → Green → Refactor)

---

> "Design é a arte de fazer as escolhas certas antes de escrever código" – made by Sky 🚀
