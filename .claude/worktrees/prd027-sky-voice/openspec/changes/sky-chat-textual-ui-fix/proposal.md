# Proposal: Sky Chat Textual UI Fix

## Why

A change `sky-chat-textual-ui` implementou UI Textual para o chat Sky, mas o componente principal de título animado está **quebrado**: a animação de "color sweep" especificada não funciona. A spec `textual-chat-ui` define claramente que o verbo deve exibir "onda de cor percorrendo letras da esquerda para direita com animação contínua", mas a implementação atual usa apenas markup estático com CSS fade simples.

Uma PoC funcional em `src/core/sky/chat/poc/app.py` demonstra a implementação correta e prova que a animação é possível sem bloquear a UI (usa `set_interval()` do Textual que roda no event loop assíncrono, não threads separados).

## What Changes

### Correções Críticas

- **BREAKING**: `AnimatedTitle` será refatorado de `render()` → `compose()` para decompor em widgets filhos atualizáveis
- **ADICIONAR**: `AnimatedVerb` widget com animação programática (timers, reativos, render letra-por-letra)
- **CORRIGIR**: `ChatHeader._update_title()` para atualizar widgets existentes em vez de acumular com `mount()`
- **ADICIONAR**: `EstadoLLM` dataclass com dimensões de estado (certeza, esforço, emoção, direção)
- **ADICIONAR**: Sistema de paletas de cores baseado em emoção (urgente, pensando, neutro, etc.)
- **ADICIONAR**: `ChatTextArea` customizado com Enter envia, Shift+Enter nova linha (substitui Input padrão)
- **REMOVER**: CSS `@keyframes color-sweep` que não implementa color sweep real (será substituído por animação Python)

### Mudanças de Comportamento

- Animação do verbo será **verdadeira** (gradiente percorrendo letras) em vez de fade CSS simples
- Atualizações de título serão **incrementais** (update_* methods) em vez de recriar widgets
- Timers de animação usarão `set_interval()` do Textual (non-blocking, event loop) em vez de CSS animation

## Capabilities

### New Capabilities
- `animated-verb`: Widget `AnimatedVerb` com animação de color sweep programática em Python, timers independentes para sweep e oscilação, sistema de cores dinâmicas baseado em `EstadoLLM`
- `textual-title-composition`: `AnimatedTitle` como container que compõe Static + AnimatedVerb + Static, atualizável via métodos `update_verbo()` e `update_estado()`
- `chat-text-area`: Widget `ChatTextArea` (TextArea customizado) com Enter envia mensagem, Shift+Enter nova linha, Escape limpa texto

### Modified Capabilities
- `textual-chat-ui`: O requirement **"Título de sessão dinâmico com verbo animado"** será implementado corretamente. A animação de color sweep especificada ("onda de cor percorrendo letras da esquerda para direita") será realizada via animação Python programática em vez de CSS. A delta spec corrigirá a implementação para atender à especificação original.

## Impact

- **Código afetado**: `src/core/sky/chat/textual_ui/widgets/title.py`, `src/core/sky/chat/textual_ui/widgets/header.py`
- **Novos arquivos**: `src/core/sky/chat/textual_ui/widgets/animated_verb.py`, `src/core/sky/chat/textual_ui/widgets/chat_text_area.py`
- **CSS**: `assets/sky_chat.css` terá animação CSS removida/substituída (animação será Python)
- **Dependências**: Nenhuma nova dependência (usa apenas Textual existente)
- **Performance**: Timers do Textual são non-blocking por design (event loop asyncio), callbacks são leves (apenas aritmética), sem risco de bloquear UI
- **Compatibilidade**: API pública de `ChatHeader.update_title()` será mantida, mas implementação interna mudará

---

> "A animação é a diferença entre o que funciona e o que encanta" – made by Sky 🚀
