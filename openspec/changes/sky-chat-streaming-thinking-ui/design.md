# Design: Sky Chat Streaming & Thinking UI

## Context

### Estado Atual

A implementação atual do Sky Chat usa a API Anthropic diretamente com `client.messages.create()`, que retorna a resposta completa de uma vez:

```python
# Implementação atual (claude.py)
response = await client.messages.create(
    model=self.model,
    max_tokens=max_tokens,
    system=system_prompt,
    messages=[{"role": "user", "content": user_message}],
)
content = response.content[0].text  # ← Tudo de uma vez
```

**Problemas identificados:**
- **Latência percebida alta**: Usuário espera 5-10s sem nenhum feedback
- **Experiência pobre**: Sem indicativo de progresso durante a geração
- **Ferramentas invisíveis**: Quando Sky usa Read/Grep/Bash, usuário não vê

### Restrições

- **Compatibilidade**: UI legada (`legacy_ui.py`) deve continuar funcionando
- **Feature flag**: `USE_TEXTUAL_UI=true/false` controla qual versão está ativa
- **Dependências**: `claude-agent-sdk` já é dependência, nenhuma nova lib externa
- **Terminal mínimo**: 80x24 caracteres para TUI

---

## Goals / Non-Goals

### Goals

1. **Streaming de resposta**: Primeiro conteúdo aparece em < 500ms, texto é atualizado incrementalmente
2. **Thinking UI**: Painel colapsável mostrando processo de pensamento da Sky
3. **Tool feedback visual**: Indicação clara quando ferramentas estão sendo executadas
4. **Interruptibilidade**: Usuário pode cancelar resposta em andamento (Ctrl+C ou botão)

### Non-Goals

1. **Persistência de thinking**: ThinkingPanel não é salvo entre sessões (futuro)
2. **Edição de pensamento**: Usuário não pode editar entradas do thinking (futuro)
3. **Multi-usuário**: Sistema é single-user, sincronização entre sessões não está no escopo
4. **Web UI**: Esta change foca apenas em TUI (Textual)

---

## Decisões

### DECISÃO 1: Claude Agent SDK com include_partial_messages

**Escolha:** Usar `ClaudeAgentSDK` com `include_partial_messages=True` ao invés da API Anthropic direta.

**Por que:**
- Agent SDK gerencia automaticamente o loop de ferramentas
- Streaming de resposta é nativo via `query()` + `receive_response()`
- Sessão persistente é mantida automaticamente

**Alternativas consideradas:**
- **API Anthropic direta com streaming**: Requer implementação manual do loop de ferramentas
- **WebSocket custom**: Overkill para este caso, adiciona complexidade

**Implementação:**
```python
from claude_agent_sdk import query, ClaudeAgentOptions

async def stream_response(user_message: str):
    options = ClaudeAgentOptions(
        include_partial_messages=True,  # ← CHAVE
        allowed_tools=["Read", "Grep", "Glob"],
    )
    async for message in query(prompt=user_message, options=options):
        yield message
```

---

### DECISÃO 2: Async Generator para Streaming

**Escolha:** `ClaudeWorker.stream_response()` retorna `AsyncIterator[str]` ao invés de uma string completa.

**Por que:**
- Permite que `ChatScreen` faça loop sobre chunks
- SkyBubble é atualizado incrementalmente
- Cancelável via `asyncio.CancelledError`

**Alternativas consideradas:**
- **Callback-based**: Mais complexo, não nativo do Python async
- **Queue-based**: Overhead adicional, sem benefício

**Fluxo:**
```python
class ClaudeWorker:
    async def stream_response(self, user_message: str) -> AsyncIterator[str]:
        async for message in query(prompt=user_message, options=options):
            if isinstance(message, StreamEvent):
                event = message.event
                if event.get("type") == "content_block_delta":
                    delta = event.get("delta", {})
                    if delta.get("type") == "text_delta":
                        yield delta.get("text", "")
```

---

### DECISÃO 3: Turn com ThinkingPanel Integrado

**Escolha:** `Turn` contém `ThinkingPanel` como componente filho, criado no início do turno.

**Por que:**
- ThinkingPanel é parte do turno (não global)
- Estado colapsado/expandido é preservado no turno
- Facilita limpeza quando turno completa

**Alternativas consideradas:**
- **ThinkingPanel global no ChatScreen**: Mais complexo gerenciar múltiplos turnos
- **Modal separado**: Quebra fluxo visual, menos integrado

**Estrutura do Turn:**
```
Turn
├── TurnSeparator (se não for o primeiro)
├── UserBubble
├── ThinkingPanel (colapsável)
│   ├── Header (título + botões)
│   └── Content (lista de ThinkingEntry)
└── SkyBubble (criado após stream completo)
```

---

### DECISÃO 4: ThinkingPanel com CSS para Estados

**Escolha:** `ThinkingPanel` usa classes CSS para alternar entre colapsado/expandido.

**Por que:**
- Textual lida com animações de CSS nativamente
- Performance melhor que re-render completo
- Estado é preservado via classe CSS

**CSS:**
```css
ThinkingPanel {
    height: auto;
    max-height: 20;  /* Limita altura */
    overflow-y: auto;
}

ThinkingPanel.--collapsed {
    height: 3;
    overflow: hidden;
}
```

---

### DECISÃO 5: SkyFragment para Update Incremental

**Escolha:** `SkyBubble` já suporta update via `watch_content`, vamos usar isso para streaming.

**Por que:**
- Componente `Markdown` do Textual atualiza automaticamente
- `watch_content` é padrão do Textual para reactive attributes
- Sem necessidade de otimizações extras

**Alternativas consideradas:**
- **Textual app.call_from_thread()**: Mais complexo, não necessário
- **SSE/WebSocket**: Overkill para TUI local

**Implementação:**
```python
class Turn(Widget):
    def append_response(self, text: str) -> None:
        if not hasattr(self, '_sky_bubble'):
            self._sky_bubble = SkyBubble("")
            self.mount(self._sky_bubble)

        # watch_content é chamado automaticamente
        self._sky_bubble.content += text
```

---

## Estrutura de Componentes

```
src/core/sky/chat/textual_ui/
├── workers/
│   └── claude.py              # ClaudeWorker.stream_response() [NOVO]
├── widgets/
│   ├── turn.py                # Turn.append_response() [MODIFICADO]
│   ├── bubbles.py             # SkyBubble com Markdown (JÁ FEITO)
│   ├── thinking_panel.py      # ThinkingPanel [NOVO]
│   ├── thinking_entry.py      # ThinkingEntryWidget [NOVO]
│   └── thinking.py            # ThinkingIndicator (JÁ EXISTE)
└── screens/
    └── chat.py                # ChatScreen loop de streaming [MODIFICADO]
```

---

## Fluxo de Dados

### Diagrama de Streaming

```
┌─────────────┐    query(prompt,      ┌─────────────┐
│ ChatScreen │    include_partial)   │ Agent SDK   │
│             │───────────────────────>│             │
│             │                        │             │
│             │    receive_response()  │             │
│             │<───────────────────────│             │
└─────────────┘    async for message  └─────────────┘
      │                    │
      │                    │ StreamEvent
      ▼                    ▼
┌─────────────┐      ┌──────────┐
│   Turn      │      │ Claude   │
│             │      │ Worker   │
┌─────────────┤      └──────────┘
│ Thinking    │             │
│ Panel       │<────────────┘
│ [EXPANDIDO] │      yield text
│             │             │
│ SkyBubble   │<────────────┘
│ [VAZIO→...] │      append
└─────────────┘
```

### Sequência de Eventos

1. **Usuário envia mensagem**
   - `ChatScreen.on_input_submitted()`
   - Cria `Turn` com `UserBubble`
   - Cria `ThinkingPanel` vazio

2. **Streaming começa**
   - `ChatScreen` chama `ClaudeWorker.stream_response()`
   - Loop `async for chunk in stream`:

3. **Chunk de texto chega**
   - `Turn.append_response(chunk)` é chamado
   - `SkyBubble.content += chunk`
   - Textual repinta o Markdown

4. **Ferramenta é chamada**
   - StreamEvent com `content_block_start` (type: `tool_use`)
   - `Turn.add_thinking_entry(tool_name, input)`
   - `ThinkingEntryWidget` é adicionado ao `ThinkingPanel`

5. **Resultado de ferramenta chega**
   - `Turn.add_thinking_entry(result)`
   - Entrada com ✓ e resultado

6. **Streaming completa**
   - Generator é esgotado
   - `ThinkingPanel` é colapsado automaticamente
   - Métricas são exibidas no header

---

## CSS e Estilos

### ThinkingPanel

```css
ThinkingPanel {
    height: auto;
    max-height: 20;
    overflow-y: auto;
    background: $panel;
    border: round $primary;
    padding: 1;
    margin: 1 2;
}

ThinkingPanel.--collapsed {
    height: 3;
    overflow: hidden;
}

ThinkingPanel Header {
    height: 3;
    dock: top;
    content-align: center;
}

ThinkingPanel Content {
    height: 1fr;
}
```

### ThinkingEntryWidget

```css
ThinkingEntryWidget {
    padding: 0 1;
    margin: 0 0 1 0;
    height: auto;
}

ThinkingEntryWidget.--thought {
    text-style: italic;
    color: $text-muted;
}

ThinkingEntryWidget.--tool {
    color: $accent;
    text-style: bold;
}

ThinkingEntryWidget.--result {
    color: $success;
}

ThinkingEntryWidget.--error {
    color: $error;
    background: $error-panel;
}
```

---

## Riscos / Trade-offs

### [RISCO] Textual pode não suportar update muito frequente

**Mitigação:**
- SkyBubble usa `watch_content` que é otimizado pelo Textual
- Testar com chunks grandes (100+ chars) em vez de char-a-char
- Usar `batch` de chunks se performance for problema

### [RISCO] ThinkingPanel pode crescer demais

**Mitigação:**
- `max-height: 20` no CSS limita tamanho
- Entradas muito antigas podem ser removidas
- Auto-scroll mantém entrada mais recente visível

### [RISCO] Cancelamento pode deixar estado inconsistente

**Mitigação:**
- Usar `try/finally` para garantir cleanup
- `asyncio.CancelledError` é capturado e tratado
- Turn é marcado como ERROR se cancelado

### [RISCO] Streaming aumenta uso de CPU

**Mitigação:**
- Textual já é eficiente com repaint
- `max-height` no ThinkingPanel limita área de repaint
- Métricas de CPU serão monitoradas

### [Trade-off] Complexidade vs Benefício

**Decisão:** Adicionar streaming aumenta complexidade mas melhora UX significativamente
**Mitigação:** Manter UI legada como fallback, feature flag permite migração gradual

---

## Plano de Implementação

### Fase 1: Streaming Básico (Sprint 1)

**Objetivo:** Texto aparece incrementalmente

- [ ] Modificar `ClaudeWorker.stream_response()` com `include_partial_messages=True`
- [ ] Adicionar `Turn.append_response()`
- [ ] Modificar `ChatScreen` para loop de streaming
- [ ] Testar latência < 500ms

### Fase 2: Thinking UI (Sprint 2)

**Objetivo:** Painel de pensamento funcional

- [ ] Criar `ThinkingPanel` widget
- [ ] Criar `ThinkingEntryWidget`
- [ ] Adicionar `Turn.add_thinking_entry()`
- [ ] Integrar com stream de ferramentas

### Fase 3: Tool Feedback Visual (Sprint 3)

**Objetivo:** Feedback claro de ferramentas

- [ ] Capturar eventos `tool_use` e `tool_result` do stream
- [ ] Exibir status visual (pending → running → complete)
- [ ] Mostrar resultado abreviado

### Fase 4: Polimento (Sprint 4)

**Objetivo:** Experiência refinada

- [ ] Animações de collapse/expand
- [ ] Cancelamento de resposta (Ctrl+C)
- [ ] Testes E2E completos
- [ ] Documentação

---

## Rollback Strategy

Se bugs críticos forem encontrados:

1. **Feature flag**: `USE_TEXTUAL_UI=false` volta para UI legada
2. **Reverter commit**: `git revert <commit>` da change
3. **Código legado**: `legacy_ui.py` permanece intocado

---

## Open Questions

1. **Tamanho máximo do ThinkingPanel**
   - Pergunta: Quantas entradas máximas? (20? 50? ilimitado?)
   - Decisão pendente: Testar em uso, definir limite se necessário

2. **Compressão de histórico thinking**
   - Pergunta: Manter todas as entradas ou remover as mais antigas?
   - Decisão pendente: Manter todas por enquanto, avaliar performance

3. **Persistência de estado colapsado**
   - Pergunta: Salvar preferência do usuário (colapsado vs expandido)?
   - Decisão pendente: Não implementar na Fase 1, considerar futuro

---

## Referências

- [Claude Agent SDK - Streaming Guide](https://docs.claude.com/en/docs/agent-sdk/streaming-vs-single-mode)
- [Open Claude - GitHub](https://github.com/Damienchakma/Open-claude) (referência de Thinking UI)
- [AI-Agent-Desktop - GitHub](https://github.com/unfish/AI-Agent-Desktop) (exemplo de implementação)
- [Docs de pesquisa](../../../docs/research/ai-chat-tools-state-of-art.md) - pesquisa completa de referências

---

> "Design é não apenas o que parece, mas como funciona" – Steve Jobs 🚀
