# Proposal: Sky Chat Streaming & Thinking UI

## Why

A implementação atual do Sky Chat usa `client.messages.create()` que retorna a resposta completa de uma vez, causando **latência percebida alta** (usuário espera 5-10s sem nenhum feedback) e **experiência ruim**.

Pesquisa com projetos de referência (Open Claude, Lobe Chat, Claude Code) mostra que **streaming de resposta é obrigatório** para chat tools modernos - todos os projetos sérios usam esse padrão para dar feedback imediato ao usuário.

## What Changes

- **Streaming de texto em tempo real**: Resposta da Sky aparece incrementalmente (efeito "datilografia") em vez de tudo de uma vez
- **Thinking UI colapsável**: Painel mostrando o processo de pensamento da Sky ("pesquisando...", "usando ferramenta X", "encontrei!") com toggle para mostrar/esconder
- **Tool feedback visual**: Indicação clara quando ferramentas estão sendo executadas (Read, Grep, Bash, etc.) com status e resultado
- **Latência primeira resposta < 500ms**: Primeiro conteúdo aparece quase instantaneamente mesmo que a resposta completa demore segundos

## Capabilities

### New Capabilities

- **`streaming-response`**: Streaming de texto em tempo real da resposta da Sky usando Claude Agent SDK com `include_partial_messages=True`
- **`thinking-ui`**: Painel colapsável (`ThinkingPanel`) mostrando processo de pensamento da Sky durante a geração da resposta
- **``tool-feedback-visual`**: Feedback visual de ferramentas sendo executadas com status (pending → running → complete) e exibição de resultado

### Modified Capabilities

Nenhuma - são funcionalidades inteiramente novas sem alteração de especificações existentes.

## Impact

**Código Afetado:**
- `src/core/sky/chat/textual_ui/workers/claude.py` - `ClaudeWorker` para usar `query()` + `receive_response()` com streaming
- `src/core/sky/chat/textual_ui/widgets/turn.py` - `Turn` para suportar atualizações incrementais e `ThinkingPanel`
- `src/core/sky/chat/textual_ui/widgets/bubbles.py` - `SkyBubble` para update incremental de conteúdo (já suporta via `watch_content`)
- `src/core/sky/chat/textual_ui/widgets/thinking_panel.py` - **NOVO** Widget de painel de thinking
- `src/core/sky/chat/textual_ui/widgets/thinking_entry.py` - **NOVO** Widget de entrada de pensamento
- `src/core/sky/chat/textual_ui/screens/chat.py` - `ChatScreen` para loop de streaming ao invés de `await respond()` completo

**Dependências:**
- `claude-agent-sdk` - já é dependência do projeto
- Nenhuma nova dependência externa necessária

**APIs:**
- `ClaudeWorker.stream_response()` - **NOVO** método que retorna async generator de chunks
- `Turn.append_response()` - **NOVO** método para atualização incremental
- `Turn.add_thinking_entry()` - **NOVO** método para adicionar entradas de pensamento

**Compatibilidade:**
- **BACKWARD COMPATIBLE**: UI legada (`legacy_ui.py`) permanece inalterada
- Feature flag `USE_TEXTUAL_UI` controla qual versão está ativa

> "A melhor interface é a que aparece instantaneamente" – principle of perceived performance 🚀
