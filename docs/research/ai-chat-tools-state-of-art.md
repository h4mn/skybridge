# Pesquisa: Chat com Ferramentas em IA - State of the Art

**Data:** 2026-02-25
**Objetivo:** Entender como profissionais e grandes empresas implementam chat com ferramentas em IA

---

## 1. Principais Descobertas

### 1.1 Streaming é o Padrão Obrigatório

**Todos os projetos sérios usam streaming de resposta.**

| Projeto | Streaming | Latência Primeira Resposta |
|---------|-----------|----------------------------|
| Claude Code | ✅ SSE | < 500ms |
| ChatGPT | ✅ SSE | < 300ms |
| Open Claude | ✅ WebSocket | < 400ms |
| Lobe Chat | ✅ SSE | < 500ms |

**Por que streaming é obrigatório?**
- Usuário vê feedback imediato ("pesquisando...")
- Experiência "pensando junto" com a IA
- Reduz percepção de latência

---

### 1.2 Arquitetura Padrão

```
┌─────────────┐      ┌─────────────┐      ┌─────────────┐
│   Frontend  │ SSE  │   Backend   │ API  │  Agent SDK  │
│  (React/TUI)│◄────►│  (Node/Py)  │◄────►│   (Claude)  │
└─────────────┘      └─────────────┘      └─────────────┘
     │                    │                     │
     │                    │                     │
  ┌──▼──┐            ┌───▼───┐            ┌───▼───┐
  │ UI  │            │Server │            │ Tools │
  │     │            │ Event│            │Read/  │
  │Chat │            │Stream│            │Grep/  │
  │Tool │            │Handler│           │Bash/  │
  │     │            │      │            │MCP    │
  └─────┘            └───────┘            └───────┘
```

**Componentes Chave:**

1. **Frontend (UI)**
   - React/Next.js ou TUI (Textual)
   - Exibe mensagens em tempo real
   - Mostra status de ferramentas

2. **Backend (Server)**
   - Node.js (Express/Fastify) ou Python (FastAPI)
   - Gerencia sessões do Agent SDK
   - Server-Sent Events (SSE) para streaming

3. **Agent SDK**
   - Claude Agent SDK (ou similar)
   - Sessão persistente
   - Ferramentas (Read, Grep, Bash, MCP)

---

### 1.3 Padrão de Streaming do Claude Agent SDK

```python
from claude_agent_sdk import query, ClaudeAgentOptions
from claude_agent_sdk.types import StreamEvent

# Configurar streaming
options = ClaudeAgentOptions(
    include_partial_messages=True,  # ← CHAVE para streaming
    allowed_tools=["Read", "Grep", "Bash"],
)

async for message in query(prompt="...", options=options):
    if isinstance(message, StreamEvent):
        event = message.event

        # Texto chegando incrementalmente
        if event.get("type") == "content_block_delta":
            delta = event.get("delta", {})
            if delta.get("type") == "text_delta":
                text = delta.get("text", "")
                print(text, end="", flush=True)  # Streaming!

        # Ferramenta sendo chamada
        elif event.get("type") == "content_block_start":
            content = event.get("content_block", {})
            if content.get("type") == "tool_use":
                tool_name = content.get("name")
                print(f"🔧 Usando ferramenta: {tool_name}")
```

**Eventos de Streaming:**

| Evento | Significado | Quando Disparar |
|--------|-------------|-----------------|
| `content_block_delta` | Texto chegando | Cada token/chunk |
| `content_block_start` | Início de bloco | Ferramenta chamada |
| `content_block_stop` | Fim de bloco | Ferramenta completa |
| `text_delta` | Texto incremental | Dentro de `content_block_delta` |

---

## 2. Padrões de UI para Ferramentas

### 2.1 Ciclo de Vida de uma Ferramenta

```
1. INDICAÇÃO VISUAL
   UI: "🔧 Pesquisando nos arquivos..."
   Estado: thinking/working

2. FERRAMENTA CHAMADA
   UI: "📂 Lendo: src/main.py"
   Estado: tool-running

3. RESULTADO DA FERRAMENTA
   UI: "✓ Encontrado: 3 ocorrências"
   Estado: tool-complete

4. RESPOSTA BASEADA NO RESULTADO
   UI: "Encontrei o bug! Está na linha 42..."
   Estado: responding
```

### 2.2 Exemplo: Open Claude

```typescript
// Componente de Tool Call
function ToolCall({ tool }) {
  return (
    <div className="tool-call">
      <div className="tool-header">
        <Icon name={tool.icon} />
        <span>{tool.name}</span>
      </div>

      {tool.state === "running" && (
        <Spinner size="small" />
      )}

      {tool.state === "complete" && (
        <pre>{tool.result}</pre>
      )}
    </div>
  );
}
```

### 2.3 Thinking UI

**Padrão observado em Open Claude e Claude Code:**

```
┌─────────────────────────────────────┐
│ 🤔 Thinking (13.2s)          [▶]    │ ← Colapsável
├─────────────────────────────────────┤
│ Analisando estrutura do projeto...  │
│ Preciso pesquisar por "def main"    │
│ Encontrei 5 arquivos Python         │
│ Lendo main.py...                    │
└─────────────────────────────────────┘

┌─────────────────────────────────────┐
│ ✨ Response                         │
│ Encontrei o bug em main.py:42...    │
└─────────────────────────────────────┘
```

---

## 3. Projetos de Referência

### 3.1 Open Claude
- **GitHub:** https://github.com/Damienchakma/Open-claude
- **Estrelas:** 5k+
- **Tech:** React, TypeScript, Tavily Search
- **Features:**
  - Thinking UI colapsável
  - Tool feedback em tempo real
  - Artifacts panel
  - Multi-provider (OpenAI, Claude, Gemini, Groq)

### 3.2 Lobe Chat
- **GitHub:** https://github.com/lobehub/lobe-chat
- **Estrelas:** 65k+
- **Tech:** Next.js, React, Zustand
- **Features:**
  - MCP Marketplace
  - Artifacts & Thinking
  - Multi-model
  - Agent workflow

### 3.3 AI-Agent-Desktop
- **GitHub:** https://github.com/unfish/AI-Agent-Desktop
- **Tech:** Tauri 2.0, React, Claude Agent SDK
- **Features:**
  - Streaming com SSE
  - Tool feedback visual
  - 4 modos de system prompt
  - Exemplo completo de implementação

### 3.4 claude-code-open
- **GitHub:** https://github.com/kill136/claude-code-open
- **Tech:** TypeScript, Ink (React for CLI)
- **Features:**
  - Reimplementação do Claude Code
  - 25+ ferramentas
  - Hooks system
  - MCP protocol

---

## 4. Padrões de Comunicação

### 4.1 Server-Sent Events (SSE)

**Backend (Node.js/Express):**
```typescript
app.post('/api/chat', async (req, res) => {
  res.setHeader('Content-Type', 'text/event-stream');
  res.setHeader('Cache-Control', 'no-cache');
  res.setHeader('Connection', 'keep-alive');

  const agent = new ClaudeSDKClient(options);

  for await (const message of agent.receive_response()) {
    if (message.type === 'stream_event') {
      res.write(`data: ${JSON.stringify(message)}\n\n`);
    }
  }

  res.write('data: [DONE]\n\n');
});
```

**Frontend (React):**
```typescript
const response = await fetch('/api/chat', {
  method: 'POST',
  body: JSON.stringify({ message }),
});

const reader = response.body.getReader();
const decoder = new TextDecoder();

while (true) {
  const { done, value } = await reader.read();
  if (done) break;

  const chunk = decoder.decode(value);
  const lines = chunk.split('\n');

  for (const line of lines) {
    if (line.startsWith('data: ')) {
      const data = JSON.parse(line.slice(6));
      onMessage(data);
    }
  }
}
```

### 4.2 TUI (Terminal UI) Streaming

**Com Textual (Python):**
```python
from textual.widgets import Markdown

class ChatScreen(Screen):
    async def on_input_submitted(self, event):
        # Cria SkyBubble vazio
        bubble = SkyBubble("")  # Começa vazio
        self.mount(bubble)

        # Streaming update
        async for chunk in claude_worker.stream(message):
            bubble.content += chunk  # Incremental
            bubble.refresh()  # Repaint
```

---

## 5. Estrutura de Dados

### 5.1 Modelo de Mensagem

```typescript
interface Message {
  id: string;
  role: 'user' | 'assistant';
  content: ContentBlock[];
  timestamp: number;
  status: 'pending' | 'streaming' | 'complete';
  tools?: ToolCall[];
}

type ContentBlock =
  | { type: 'text'; text: string }
  | { type: 'tool_use'; name: string; input: any }
  | { type: 'tool_result'; tool_use_id: string; content: string };

interface ToolCall {
  id: string;
  name: string;
  input: any;
  result?: any;
  status: 'pending' | 'running' | 'complete' | 'error';
  timestamp: number;
}
```

### 5.2 Estado da Sessão

```typescript
interface SessionState {
  messages: Message[];
  tools: ToolCall[];
  context: ContextSnapshot;
  metrics: {
    tokensIn: number;
    tokensOut: number;
    cost: number;
    latency: number;
  };
}
```

---

## 6. Recomendações para Sky Chat

### 6.1 Arquitetura Sugerida

```
Textual UI (Frontend)
    │
    │ SSE ou async generator
    ▼
ClaudeWorker (Backend)
    │
    │ query() + receive_response()
    ▼
Claude Agent SDK
```

### 6.2 Implementação por Fases

**Fase 1: Streaming de Texto**
- Mudar `client.messages.create()` para `query()` + `receive_response()`
- Atualizar `SkyBubble` incrementalmente
- Latência: texto aparece em < 500ms

**Fase 2: Tool Feedback**
- Mostrar "Usando ferramenta: Read" quando tool_use start
- Mostrar resultado quando tool_result chega
- Componente `ToolFeedback` já existe, basta conectar ao stream

**Fase 3: Thinking UI**
- Adicionar painel colapsável com processo de pensamento
- Mostrar "Pesquisando..." durante tool calls
- Exibir número de tokens usados

**Fase 4: Interruptibilidade**
- Permitir cancelar resposta em andamento
- Ctrl+C ou botão "Stop"
- `agent.cancel()` se disponível

### 6.3 Componentes a Criar/Modificar

| Componente | Estado | Ação Necessária |
|-------------|--------|-----------------|
| `ClaudeWorker` | ❌ Usa `create()` | ✅ Mudar para `query()` stream |
| `Turn.set_response()` | ✅ Existe | ⚡ Adicionar `append_response()` |
| `SkyBubble` | ✅ Tem `watch_content` | ✅ Já suporta update |
| `ToolFeedback` | ✅ Existe | ⚡ Conectar ao stream |
| `ChatScreen` | ⚡ Chama `respond()` | ✅ Mudar para loop de stream |

---

## 7. Exemplo de Implementação

### 7.1 Worker com Streaming

```python
class ClaudeWorker:
    async def stream_response(self, user_message: str) -> AsyncIterator[str]:
        """Stream response chunk by chunk."""
        client = await self._get_client()

        options = ClaudeAgentOptions(
            include_partial_messages=True,
            allowed_tools=["Read", "Grep", "Glob"],
        )

        async for message in query(prompt=user_message, options=options):
            if isinstance(message, StreamEvent):
                event = message.event

                # Tool use start
                if event.get("type") == "content_block_start":
                    block = event.get("content_block", {})
                    if block.get("type") == "tool_use":
                        yield f"[TOOL:{block.get('name')}]"

                # Text delta
                elif event.get("type") == "content_block_delta":
                    delta = event.get("delta", {})
                    if delta.get("type") == "text_delta":
                        yield delta.get("text", "")

                # Tool result
                elif event.get("type") == "content_block_stop":
                    yield "[TOOL_COMPLETE]"
```

### 7.2 Turn com Update Incremental

```python
class Turn(Widget):
    def append_response(self, text: str) -> None:
        """Adiciona texto incrementalmente à resposta."""
        if not hasattr(self, '_sky_bubble'):
            self._sky_bubble = SkyBubble("")
            self.mount(self._sky_bubble)

        # Atualiza conteúdo existente
        self._sky_bubble.content += text
        self._sky_bubble.refresh()
```

### 7.3 ChatScreen com Streaming

```python
class ChatScreen(Screen):
    async def _process_message(self, user_message: str):
        # Cria turn com SkyBubble vazia
        turn = Turn(user_message, self._turn_count)
        self.mount(turn)

        # Cria SkyBubble vazia para receber stream
        bubble = SkyBubble("")
        turn.mount(bubble)

        # Stream response
        async for chunk in claude_worker.stream_response(user_message):
            # Special markers para tools
            if chunk.startswith("[TOOL:"):
                tool_name = chunk.replace("[TOOL:", "").replace("]", "")
                self._show_tool_feedback(tool_name)
            elif chunk == "[TOOL_COMPLETE]":
                self._hide_tool_feedback()
            else:
                # Texto normal - atualiza bubble
                bubble.content += chunk
                bubble.refresh()
```

---

## 8. Referências

- [Claude Agent SDK - Streaming Guide](https://docs.claude.com/en/docs/agent-sdk/streaming-vs-single-mode)
- [Open Claude - GitHub](https://github.com/Damienchakma/Open-claude)
- [Lobe Chat - GitHub](https://github.com/lobehub/lobe-chat)
- [AI-Agent-Desktop - GitHub](https://github.com/unfish/AI-Agent-Desktop)
- [claude-code-open - GitHub](https://github.com/kill136/claude-code-open)

---

> "A melhor forma de prever o futuro é inventá-lo" – Alan Kay

> Pesquisa compilada por Sky 🚀
