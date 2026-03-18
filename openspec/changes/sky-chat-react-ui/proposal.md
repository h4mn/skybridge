# Proposal: Sky Chat ReAct UI

## Why

O SkyChat atual trata o ciclo de interação com o modelo como um fluxo linear — mensagem entra, resposta sai. Mas o **claude-agent-sdk** que já utilizamos emite um protocolo muito mais rico: o modelo **pensa, age e observa** em ciclos antes de responder. A UI atual não reflete esse ciclo, mostrando pensamento e ação em painéis separados e misturando texto de razão com a resposta final.

## What Changes

- **Novo componente `AgenticLoopPanel`**: substitui `ThinkingPanel`, agrupando **Steps** completos (Thought + Action + Observation) ao invés de listar tools isoladas
- **Novo componente `StepWidget`**: representa uma iteração do loop ReAct com ThoughtLine (intenção) + ActionLine (execução e resultado)
- **Roteador de eventos**: differentiate `text_delta` entre **Thought** (intenção antes de tool) e **Final Answer** (resposta final ao usuário)
- **`SkyBubble` limpo**: exibe somente o Final Answer, sem texto de raciocínio misturado
- **Novo estado `TurnState.CANCELLED`**: permite interromper um turno em andamento
- **ActionBar** com botões **Copy** e **Retry**: ações pós-resposta para melhorar UX

## Capabilities

### New Capabilities
- `agentic-loop-ui`: Interface que espelha o ciclo ReAct (Reasoning + Acting) do claude-agent-sdk, agrupando Steps de Thought → Action → Observation
- `event-router`: Roteador de eventos que diferencia texto de intenção (Thought) de resposta final (Final Answer) baseado em `AssistantMessage`
- `turn-actions`: Ações pós-resposta (Copy, Retry) para melhorar experiência do usuário
- `turn-cancellation`: Capacidade de interromper um turno em andamento

### Modified Capabilities
- *(nenhuma - esta é uma nova funcionalidade)*

## Impact

**Arquitetura de componentes:**
- `src/core/sky/chat/textual_ui/widgets/turn.py` - atualizar para usar novos componentes
- `src/core/sky/chat/textual_ui/widgets/thinking.py` - substituir `ThinkingPanel` por `AgenticLoopPanel`, adicionar `StepWidget`
- `src/core/sky/chat/textual_ui/widgets/bubbles.py` - adicionar `ActionBar` no `SkyBubble`

**Core:**
- `src/core/sky/chat/claude_chat.py` - implementar roteador de eventos (yield `StreamEvent.THOUGHT` vs `StreamEvent.TEXT`)
- `src/core/sky/chat/turn_state.py` - adicionar estado `CANCELLED`

**Dependências:**
- `pyperclip` (novo) - para funcionalidade Copy
- `anthropic-agent-sdk` (já existe) - aproveitar eventos `content_block_delta`, `AssistantMessage`, `ToolResultMessage`

**Compatibilidade:**
- **BREAKING**: `Turn.add_thinking_entry()` muda assinatura para criar `StepWidget` ao invés de `ToolCallWidget`
- **BREAKING**: `SkyBubble` não recebe mais texto de raciocínio misturado

---

> "Testes são a especificação que não mente" – made by Sky [emoji]
