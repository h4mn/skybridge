# Design: Sky Chat Textual UI

## Context

### Estado Atual
A UI do chat Sky é implementada com:
- **Rich Console** para renderização de markdown, tabelas e painéis
- **Prompt Toolkit** para input do usuário (via `scripts/sky_rag.py`)
- **Output linear** via stdout/stderr (mensagens são impressas sequencialmente)
- **ASCII art** para tela de apresentação

### Limitações Atuais
- Sem layout estruturado (header/footer não são fixos)
- Mensagens se misturam visualmente (não há separação clara entre turnos)
- Sem possibilidade de componentes interativos (buttons, modais, etc.)
- CSS não é suportado (cores são hardcoded via Rich tags)
- Workers assíncronos não existem (chamadas bloqueiam a UI)

### Restrições
- **Compatibilidade**: Modo legado deve continuar funcionando via `USE_TEXTUAL_UI=false`
- **Performance**: Workers não devem travar a UI durante operações pesadas
- **Acessibilidade**: Terminal mínimo de 80x24 caracteres
- **Dependências**: `textual` e `textual-dev` serão adicionadas ao projeto

---

## Goals / Non-Goals

### Goals
1. **UI moderna** com header/footer fixos e container scrollável
2. **Título dinâmico** com verbo animado (color sweep)
3. **Barra de contexto** visual com cores indicando uso
4. **Message bubbles** estilizados via CSS
5. **Workers assíncronos** para operações pesadas (Claude SDK, RAG)
6. **Screen management** com push/pop para navegação
7. **Modal/Toast** para confirmações e notificações
8. **Tela de apresentação** centralizada e animada

### Non-Goals
1. **Persistência de sessão** (fora do escopo inicial)
2. **Multi-usuário** ou chat em tempo real
3. **API HTTP** para chat (escopo separado)
4. **Upload/download** de arquivos
5. **Integração com webhooks** durante chat (futuro)

---

## Decisions

### DECISÃO 1: Framework Textual TUI

**Escolha:** [Textual](https://github.com/Textualize/textual) para UI

**Por que Textual?**
| Critério | Textual | Rich (atual) | Urwid | Curses |
|----------|---------|--------------|-------|--------|
| Layout estruturado | ✅ | ❌ | ✅ | ❌ |
| CSS suportado | ✅ | ❌ | ❌ | ❌ |
| Assíncrono nativo | ✅ | ❌ | Parcial | ❌ |
| Screen management | ✅ | ❌ | Manual | Manual |
| Componentes ricos | ✅ | Parcial | ❌ | ❌ |
| Ativo e mantido | ✅ | ✅ | ❌ | ❌ |

**Alternativas consideradas:**
- **Rich**: Já em uso, mas não oferece layout estruturado ou screen management
- **Urwid**: Obsoleto, curva de aprendizado íngreme
- **Curses**: Muito baixo nível, sem abstração moderna

**Racional:** Textual é a escolha natural para TUIs modernas em Python, criado pelo mesmo autor do Rich.

---

### DECISÃO 2: Arquitetura de Screens

**Escolha:** Sistema de screens com pilha (stack) para navegação

```
┌─────────────────────────────────────┐
│  Screen Stack (pilha de screens)    │
│  ┌─────────────────────────────────┐ │
│  │ WelcomeScreen (splash)          │ │
│  └─────────────────────────────────┘ │
│  ┌─────────────────────────────────┐ │
│  │ ChatScreen (principal)          │ │ ← Sempre no fundo
│  └─────────────────────────────────┘ │
│  ┌─────────────────────────────────┐ │
│  │ ConfigScreen (opcional)         │ │ ← Empilhada sob demanda
│  └─────────────────────────────────┘ │
└─────────────────────────────────────┘
```

**Por que pilha de screens?**
- Permite navegação simples (push/pop)
- Estado de cada screen é preservado
- Modais são apenas screens especiais (com overlay)

**Alternativas:**
- **Single screen com visibility toggles**: Mais complexo, estado misturado
- **Múltiplas instâncias de App**: Pesado, compartilhamento de estado difícil

**Racional:** Padrão bem estabelecido em UI frameworks (navigation stack).

---

### DECISÃO 3: Layout com Vertical + Horizontal

**Escolha:** `Vertical` layout principal com `Horizontal` para componentes lado a lado

```python
Vertical(
    Header(height=2),           # Fixo no topo
    ScrollView(id="messages"),  # Expande no meio
    Footer(height=3),           # Fixo na base
)
```

**Por que:**
- `Vertical` organiza header/conteúdo/footer naturalmente
- `Horizontal` organiza métricas no header lado a lado
- Textual lida com redimensionamento automaticamente

**Alternativa:** `Grid` layout
- Mais complexo para layout simples
- Overkill para organização linear

---

### DECISÃO 4: Workers Assíncronos com asyncio

**Escolha:** Workers implementados como `asyncio.Task` rodando em background

```python
async def call_claude_worker(message: str) -> ChatResponse:
    """Worker assíncrono para chamada Claude SDK."""
    return await claude_client.messages.create(...)

# Na UI
task = asyncio.create_task(call_claude_worker(msg))
# UI continua responsiva
```

**Por que asyncio:**
- Textual já é assíncrono (usa asyncio internally)
- `Claude Agent SDK` tem suporte async
- Sem threads necessárias (evita GIL issues)

**Alternativas:**
- **ThreadPoolExecutor**: Adiciona complexidade, GIL ainda é problema
- **ProcessPoolExecutor**: Overhead de IPC, excessivo para I/O bound

---

### DECISÃO 5: CSS em arquivo separado

**Escolha:** `assets/sky_chat.css` com temas (dark/light)

**Por que:**
- Customizável sem mudar código
- Suporta múltiplos temas
- Textual recarrega CSS ao detectar mudanças (dev mode)

**Estrutura de CSS:**
```css
/* Tema escuro padrão */
SkyBubble {
    background: $primary;
    color: $text;
}
UserBubble {
    background: $accent;
    color: $text;
}
```

---

### DECISÃO 6: Título Dinâmico gerado por LLM

**Escolha:** Sky gera título chamando Claude com prompt específico

```python
async def generate_session_title(conversation: List[ChatMessage]) -> str:
    prompt = "Gere um título curto (3-5 palavras) para esta conversa no formato: 'Sujeito | verbo no gerúndio | predicado'"
    return await claude_client.messages.create(...)
```

**Por que:**
- Mais inteligente que heurísticas baseadas em keywords
- Se adapta a qualquer tópico
- Usa infraestrutura Claude já existente

**Alternativa:** Heurística regex-based
- Menos flexível, não entende contexto
- Maior manutenção

**Trade-off:** Custo de 1 chamada extra a cada 2-3 turnos (aceitável).

---

### DECISÃO 7: Feature Flag para Migração Gradual

**Escolha:** `USE_TEXTUAL_UI=true/false` para alternar entre UIs

**Por que:**
- Permite teste gradual da nova UI
- Fallback fácil se bugs forem encontrados
- Usuários podem escolher qual preferem

**Implementação:**
```python
if os.getenv("USE_TEXTUAL_UI", "false").lower() == "true":
    from sky.chat.textual_ui import TextualChatApp
    TextualChatApp().run()
else:
    from sky.chat.legacy_ui import LegacyChatApp
    LegacyChatApp().run()
```

---

## Estrutura de Módulos

```
src/core/sky/chat/
├── __init__.py           # Fábrica que escolhe UI baseado em feature flag
├── textual_ui.py         # Nova implementação Textual
│   ├── screens/          # Definição de screens
│   │   ├── welcome.py    # WelcomeScreen (tela de apresentação)
│   │   ├── chat.py       # ChatScreen (principal)
│   │   ├── config.py     # ConfigScreen
│   │   └── help.py       # HelpScreen
│   ├── widgets/          # Widgets customizados
│   │   ├── bubbles.py    # SkyBubble, UserBubble
│   │   ├── title.py      # AnimatedTitle com verbo animado
│   │   ├── context_bar.py # ProgressBar com cores
│   │   └── thinking.py   # ThinkingIndicator
│   ├── workers/          # Workers assíncronos
│   │   ├── claude.py     # Worker para chamadas Claude
│   │   └── rag.py        # Worker para buscas RAG
│   └── styles/           # CSS
│       └── default.css   # Tema padrão
├── ui.py                 # Implementação atual (Rich) - será renomeada
└── legacy_ui.py          # Alias para ui.py (compatibilidade)
```

---

## Componentes Principais

### ChatScreen (Principal)

```python
class ChatScreen(Screen):
    """Screen principal do chat."""

    def compose(self) -> ComposeResult:
        yield Header()  # 2 linhas fixas
        yield ScrollView(MessageList)  # Bubbles scrolláveis
        yield Footer(InputField)  # Input + comandos

    async def on_input_submitted(self, event: Input.Submitted) -> None:
        """Usuário enviou mensagem."""
        # Cria worker assíncrono
        task = asyncio.create_task(self._process_message(event.value))
        # Exibe thinking indicator
        self.thinking.show()
```

### AnimatedTitle Widget

```python
class AnimatedTitle(Widget):
    """Título com verbo animado (color sweep)."""

    def __init__(self, sujeito: str, verbo: str, predicado: str):
        super().__init__()
        self.sujeito = sujeito
        self.verbo = verbo
        self.predicado = predicado

    def render(self) -> RenderResult:
        # Aplica classe CSS 'verbo-animado' ao verbo
        return Text.assemble(
            self.sujeito, " ",
            (self.verbo, "verbo-animado"), " ",
            self.predicado
        )
```

**CSS:**
```css
.verbo-animado {
    animation: color-sweep 2s linear infinite;
}

@keyframes color-sweep {
    0% { color: $primary; }
    50% { color: $accent; text-style: bold underline; }
    100% { color: $primary; }
}
```

---

## Fluxo de Dados

```
┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│   Usuário   │────▶│   Footer    │────▶│  ChatScreen │
│  (digita)   │     │  (Input)    │     │  (evento)   │
└─────────────┘     └─────────────┘     └──────┬──────┘
                                                │
                                                ▼
                                         ┌──────────────┐
                                         │ Worker Async │
                                         │ (Claude SDK) │
                                         └──────┬───────┘
                                                │
                    ┌─────────────────────────────┼─────────────────────┐
                    ▼                             ▼                     ▼
             ┌─────────────┐              ┌─────────────┐       ┌─────────────┐
             │  Worker RAG │              │Thinking UI  │       │  Response  │
             │  (optional) │              │  (animado)  │       │  (bubble)   │
             └─────────────┘              └─────────────┘       └─────────────┘
```

---

## CSS e Temas

### Arquivo: `assets/sky_chat.css`

```css
/* === Bubbles === */
SkyBubble {
    background: $panel;
    color: $text;
    margin: 1 2;
    padding: 1;
    border: thick $primary;
}

UserBubble {
    background: $primary;
    color: $text;
    margin: 1 2;
    padding: 1;
    border: thick $accent;
    text-align: right;
}

/* === Título Animado === */
.verbo-animado {
    animation: color-sweep 2s linear infinite;
}

@keyframes color-sweep {
    0% { color: $primary; }
    50% { color: $accent; text-style: bold; }
    100% { color: $primary; }
}

/* === Barra de Contexto === */
ProgressBar.--green { progress-bar-background: $success; }
ProgressBar.--yellow { progress-bar-background: $warning; }
ProgressBar.--orange { progress-bar-background: $error; }
ProgressBar.--red { progress-bar-background: red; }

/* === Markdown === */
MarkdownText {
    background: transparent;
}
```

---

## Protocolos e Interfaces

### ChatAdapter (interface compartilhada)

```python
class ChatAdapter(Protocol):
    """Interface para adapters de chat."""

    async def respond(self, message: ChatMessage) -> ChatResponse:
        """Gera resposta para mensagem do usuário."""
        ...

    def get_ui(self) -> Any:
        """Retorna UI apropriada (Rich ou Textual)."""
        ...
```

Isso permite que `ClaudeChatAdapter` funcione com ambas as UIs.

---

## Riscos / Trade-offs

### [RISCO] Textual pode não estar disponível em todos os ambientes
**Mitigação:**
- Feature flag `USE_TEXTUAL_UI=false` permite fallback para UI Rich
- Dependência `textual` é marcada como optional em requirements.txt

### [RISCO] Workers assíncronos podem causar condições de corrida
**Mitigação:**
- Usar `asyncio.Queue` para comunicação thread-safe
- Cada worker atualiza UI via `app.call_from_thread()`

### [RISCO] CSS pode não funcionar em terminais sem cores
**Mitigação:**
- Textual detecta capabilities do terminal automaticamente
- Fallback para estilos monócro máticos se necessário

### [RISCO] Tamanho do código pode aumentar significativamente
**Mitigação:**
- Módulos bem organizados (screens/, widgets/, workers/)
- Reutilização de componentes (bubbles, title, etc.)

### [Trade-off] Geração de título por LLM adiciona latência e custo
**Decisão:** Aceitável, pois ocorre apenas 2-3 vezes por sessão
**Mitigação:** Cache de título se contexto não mudar significativamente

---

## Plano de Migração

### Fase 1: Implementação Paralela (Semana 1)
- [ ] Adicionar `textual` ao requirements.txt
- [ ] Criar estrutura de módulos `textual_ui/`
- [ ] Implementar ChatScreen básico (sem workers)
- [ ] Feature flag `USE_TEXTUAL_UI=false` (padrão)

### Fase 2: Componentes e Workers (Semana 2)
- [ ] Implementar widgets customizados (bubbles, title, context_bar)
- [ ] Implementar workers assíncronos (Claude, RAG)
- [ ] Implementar WelcomeScreen
- [ ] Testar com `USE_TEXTUAL_UI=true`

### Fase 3: Screens Navegação (Semana 3)
- [ ] Implementar ConfigScreen
- [ ] Implementar HelpScreen
- [ ] Sistema de modais (confirmação /new)
- [ ] Toast notifications

### Fase 4: Polimento e Testes (Semana 4)
- [ ] Refinar CSS e temas
- [ ] Testes E2E do fluxo completo
- [ ] Testes de performance (latência, memória)
- [ ] Documentação (README, Quickstart)

### Fase 5: Lançamento (Semana 5)
- [ ] Atualizar `USE_TEXTUAL_UI=true` como padrão
- [ ] Anunciar nova UI
- [ ] Monitorar feedback e bugs

### Rollback Strategy
- Se bugs críticos forem encontrados, reverter `USE_TEXTUAL_UI=false`
- Código legado (`legacy_ui.py`) permanece intacto

---

## Open Questions

1. **Tamanho mínimo de terminal**
   - Pergunta: Qual o mínimo suportado? (80x24? 100x30?)
   - Decisão pendente: Testar em terminais pequenos

2. **Compatibilidade com Windows Terminal**
   - Pergunta: Textual funciona bem no Windows?
   - Decisão pendente: Testar em Windows

3. **Persistência de título entre sessões**
   - Pergunta: Salvar título gerado para retomar sessão?
   - Decisão pendente: Fora do escopo inicial, pode ser futuro

4. **Sintaxe de comandos**
   - Pergunta: Usar `/comando` ou `:comando`?
   - Decisão pendente: `/comando` já é usado em specs, manter

---

## Referências

- [Textual Documentation](https://textual.textual.io/)
- [Textual CSS Guide](https://textual.textual.io/guide/css.html)
- [Spec: Textual Chat UI](specs/textual-chat-ui/spec.md)
- [Spec: Claude Chat Integration](specs/claude-chat-integration/spec.md)

---

> "O design é a inteligência tornada visível" – made by Sky 🚀
