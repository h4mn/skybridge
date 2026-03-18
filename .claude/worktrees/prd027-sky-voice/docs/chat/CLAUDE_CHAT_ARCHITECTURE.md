# Arquitetura do Chat Claude

Documentação técnica da arquitetura do chat com Claude SDK.

## Visão Geral

```
┌─────────────────────────────────────────────────────────────┐
│                    sky_rag.py / sky_claude.bat              │
│  - Feature flag USE_CLAUDE_CHAT                             │
│  - Inicializa ClaudeChatAdapter ou SkyChat                  │
└──────────────────────┬──────────────────────────────────────┘
                       │
         ┌─────────────┼─────────────┐
         ▼             ▼             ▼
   ┌──────────┐  ┌──────────┐  ┌──────────┐
   │ Claude   │  │  SkyChat │  │ ChatUI   │
   │ Adapter  │  │ (Legacy) │  │ (Rich)   │
   └──────────┘  └──────────┘  └──────────┘
         │
    ┌────┴────┐
    ▼         ▼
┌────────┐ ┌─────────┐
│MemoryRAG│ │ClaudeSDK│
└────────┘ └─────────┘
```

## Componentes

### 1. ClaudeChatAdapter (`claude_chat.py`)

Adapter principal que implementa a interface de chat com inferência via Claude.

**Responsabilidades:**
- Gerenciar histórico de mensagens (limite: 20)
- Recuperar memórias relevantes via RAG
- Construir system prompt com personalidade + contexto
- Chamar Claude SDK para gerar respostas
- Fallback para SkyChat em caso de erro

**Métodos principais:**
```python
adapter = ClaudeChatAdapter(memory=memory)
adapter.receive(message)  # Armazena no histórico
response = adapter.respond(message)  # Gera resposta
adapter.clear_history()  # Limpa sessão
```

### 2. Personality Module (`personality.py`)

Define a personalidade da Sky via system prompt.

**Responsabilidades:**
- Template de system prompt com slots dinâmicos
- Injeção de contexto de memória RAG
- Regras comportamentais (não alucinar, ser honesto)
- Assinatura "made by Sky 🚀"

**Uso:**
```python
from src.core.sky.chat.personality import build_system_prompt, format_memory_context

memories = memory.search("query", top_k=5)
memory_context = format_memory_context([m["content"] for m in memories])
system_prompt = build_system_prompt(memory_context)
```

### 3. ChatUI (`ui.py`)

Interface visual usando Rich para renderização rica.

**Responsabilidades:**
- Renderizar header com status (RAG, memórias)
- Renderizar thinking ("🤔 Pensando...")
- Renderizar tools executadas
- Renderizar memórias usadas
- Renderizar mensagens em Markdown
- Renderizar footer com comandos
- Renderizar resumo da sessão

**Uso:**
```python
from src.core.sky.chat.ui import ChatUI, ChatMetrics

ui = ChatUI(verbose=True)
ui.render_header(rag_enabled=True, memory_count=5)
ui.render_thinking()
ui.render_message("sky", "Olá!", metrics=metrics)
ui.render_session_summary(session_metrics)
```

## Fluxo de Mensagens

### 1. Usuário envia mensagem

```
Usuário → sky_rag.py → ChatUI → input()
                ↓
        ChatMessage(role="user", content="...")
                ↓
        ClaudeChatAdapter.receive(message)
                ↓
        Adiciona ao histórico (self._history)
```

### 2. Adapter gera resposta

```
ClaudeChatAdapter.respond(message)
                ↓
        1. Recupera memórias RAG (_retrieve_memory)
                ↓
        2. Constrói system prompt (build_system_prompt)
                ↓
        3. Chama Claude SDK (_call_claude_sdk)
                ↓
        4. Armazena resposta no histórico
                ↓
        Retorna texto da resposta
```

### 3. Fallback em caso de erro

```
_call_claude_sdk() levanta Exception
                ↓
        except Exception → _fallback_to_legacy()
                ↓
        Usa SkyChat (respostas fixas)
```

## Limites e Configurações

| Configuração | Padrão | Descrição |
|--------------|--------|-----------|
| `MAX_HISTORY_LENGTH` | 20 | Limite de mensagens no contexto |
| `TOP_K_MEMORIES` | 5 | Memórias RAG recuperadas |
| `MAX_TOKENS` | 500 | Limite de tokens por resposta |
| `DEFAULT_MODEL` | claude-3-5-haiku-20241022 | Modelo Claude padrão |

## Observabilidade

### Métricas Coletadas

```python
@dataclass
class ChatMetrics:
    latency_ms: float      # Tempo de resposta
    tokens_in: int         # Tokens de entrada
    tokens_out: int        # Tokens de saída
    memory_hits: int       # Memórias RAG usadas
    model: str             # Modelo usado
```

### Logs Estruturados

O sistema registra eventos estruturados:

```python
logger.info("[Claude SDK] Resposta gerada", extra={
    "model": model,
    "latency_ms": latency_ms,
    "tokens_in": tokens_in,
    "tokens_out": tokens_out,
})
```

## Testes

### Testes Unitários

- `test_personality.py`: Testa system prompt e formatação
- `test_claude_chat.py`: Testa adapter, RAG, fallback
- `test_ui.py`: Testa renderização da UI

### Executar Testes

```bash
pytest tests/unit/core/sky/chat/ -v
```

## Extensões Futuras

### Persistência de Sessão (Fora do escopo inicial)

- Salvar sessão em `.sky_session.json`
- Retomar sessão com flag `--resume`
- Histórico entre múltiplas sessões

### Multi-Modalidade

- Imagens: usar Vision API
- Arquivos: upload e processamento
- Áudio: transcrição via Whisper

### Custom Tools

- Tools específicas para o chat
- Function calling via Claude SDK
- Integração com APIs externas

## Referências

- Spec: `openspec/changes/chat-claude-sdk/specs/`
- Design: `openspec/changes/chat-claude-sdk/design.md`
- Quickstart: `docs/chat/CLAUDE_CHAT_QUICKSTART.md`

---

> "Design é fazer as escolhas certas antes que elas se tornem caras" – made by Sky 🚀
