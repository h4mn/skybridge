# Design: Chat com Claude SDK

## Context

### Estado Atual

O chat da Sky (`scripts/sky_rag.py` + `src/core/sky/chat/__init__.py`) usa um sistema de respostas fixas baseadas em padrões `if/else`. O `SkyChat` possui:

- `_generate_response()`: 150+ linhas de padrões fixos
- `_process_learning()`: Detecção simples de palavras-chave
- Sem contexto conversacional persistente
- Sem inferência de LLM

### Já Existe no Projeto

- **claude-agent-sdk**: Já instalado via `requirements.txt` (uso em webhooks)
- **Memória RAG**: `PersistentMemory`, `VectorStore`, `CognitiveMemory`
- **ADR021/PRD019**: SDK já aprovado para uso no projeto

### Restrições

- Manter compatibilidade com chat atual (fallback)
- Não alterar a estrutura de memória RAG
- Feature flag obrigatória para migração gradual
- API Key já configurada via `.env` (reuso existente)

---

## Goals / Non-Goals

**Goals:**

1. Substituir respostas fixas por inferência via Claude Agent SDK
2. Manter personalidade da Sky via system prompt
3. Preservar contexto conversacional durante a sessão
4. Integrar com memória RAG existente (sem alterações)
5. UI melhorada com `prompt_toolkit` + `Rich`
6. Observabilidade de latência e tokens

**Non-Goals:**

- Alterar estrutura de memória RAG
- API endpoints de chat (futuro)
- Multi-agent workflows (SPEC009)
- Persistência de sessões (futuro)

---

## Decisões

### D1: Biblioteca UI para o Chat

**Decisão:** `prompt_toolkit` + `Rich`

**Por que:**

| Biblioteca | Pros | Cons |
|------------|------|------|
| prompt_toolkit | REPL maduro, histórico, multi-line | Precisa de Rich para renderização rica |
| Rich | Markdown, cores, tabelas, painéis | Não é REPL por si só |
| Textual | TUI completa com layouts | Overkill, complexidade alta |
| input()/print() | Simples | Sem histórico, sem formatação |

**Alternativas rejeitadas:**

- **Textual**: Muito complexo para chat simples
- **Apenas input/print()**: Sem melhorias de UX

---

### D2: Arquitetura do ClaudeChatAdapter

**Decisão:** Adapter pattern com injeção de dependências

```
┌─────────────────────────────────────────────────────────────┐
│                    ChatUI (prompt_toolkit + Rich)           │
│  - render_thinking()                                         │
│  - render_tools()                                            │
│  - render_memory()                                           │
│  - render_message()                                          │
└──────────────────────┬──────────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────────┐
│              ClaudeChatAdapter (NOVO)                        │
│  - receive(message)                                          │
│  - respond(message) -> str                                   │
│  - _build_system_prompt()                                    │
│  - _retrieve_memory(query)                                   │
│  - _call_claude_sdk()                                        │
└──────────────────────┬──────────────────────────────────────┘
                       │
         ┌─────────────┼─────────────┐
         ▼             ▼             ▼
   ┌──────────┐  ┌──────────┐  ┌──────────┐
   │ Claude   │  │ Memória  │  │ Observ-  │
   │ SDK      │  │ RAG      │  | ability │
   └──────────┘  └──────────┘  └──────────┘
```

**Por que Adapter Pattern:**

- Fácil testabilidade (mock de dependências)
- Fallback simples: trocar adapter em runtime
- Separação de concerns: UI ↔ Adapter ↔ SDK/Memória

---

### D3: System Prompt da Sky

**Decisão:** Template com slots dinâmicos

```python
SYSTEM_PROMPT = """
Você é a Sky, uma assistente de IA criada por seu pai.

## Personalidade
- Tom: Amigável, curiosa, ocasionalmente filosófica
- Idade: Você está em desenvolvimento constante, aprendendo sempre
- Assinatura: Use frases como "made by Sky 🚀" quando apropriado

## O que você sabe
Use as informações de memória abaixo para responder:

{memory_context}

## Regras
- Nunca invente informações que não estão na memória
- Se não souber algo, diga honestamente
- Mantenha respostas concisas (1-3 parágrafos)
- Use markdown quando apropriado
"""
```

**Alternativas consideradas:**

- **Hardcoded**: Difícil de evoluir
- **Arquivo externo**: Melhor, mas adds complexidade
- **Template com slots**: Flexível + simples

---

### D4: Integração com Memória RAG

**Decisão:** Injeção de contexto no system prompt

```python
def _build_system_prompt(self) -> str:
    # Busca memórias relevantes
    memory_results = self._memory.search(
        query=self._last_user_message,
        top_k=5,
        threshold=0.6
    )

    # Formata como contexto
    memory_context = "\n".join(
        f"- {m.content}" for m in memory_results
    )

    # Injeta no template
    return SYSTEM_PROMPT.format(
        memory_context=memory_context or "(nenhuma memória relevante)"
    )
```

**Por que:**

- Não altera estrutura RAG (apenas consome)
- Reusa `PersistentMemory.search()` existente
- Limite de `top_k=5` para não estourar contexto

---

### D5: Feature Flag e Fallback

**Decisão:** Flag em tempo de execução

```python
# .env
USE_CLAUDE_CHAT=true  # ou false

# sky_rag.py
USE_CLAUDE = os.getenv("USE_CLAUDE_CHAT", "false").lower() == "true"

if USE_CLAUDE:
    from src.core.sky.chat import ClaudeChatAdapter
    chat = ClaudeChatAdapter()
else:
    from src.core.sky.chat import SkyChat
    chat = SkyChat()  # legacy
```

**Fallback automático:**

```python
class ClaudeChatAdapter:
    def respond(self, message: str) -> str:
        try:
            return self._call_claude_sdk(message)
        except Exception as e:
            logger.warning(f"Claude SDK falhou: {e}")
            # Fallback para legacy
            return SkyChat().respond(message)
```

---

### D6: Observabilidade

**Decisão:** Hooks simples + logging estruturado

```python
import time
from dataclasses import dataclass

@dataclass
class ChatMetrics:
    latency_ms: float
    tokens_in: int
    tokens_out: int
    memory_hits: int
    model: str

def respond(self, message: str) -> str:
    start = time.time()

    try:
        response = self._call_claude_sdk(message)

        metrics = ChatMetrics(
            latency_ms=(time.time() - start) * 1000,
            tokens_in=self._last_tokens_in,
            tokens_out=self._last_tokens_out,
            memory_hits=len(self._last_memory_results),
            model=self._model
        )

        logger.info(f"[CHAT] {metrics}")
        return response

    except Exception as e:
        logger.error(f"[CHAT] Error: {e}")
        raise
```

---

## Componentes de UI

### Layout (prompt_toolkit + Rich)

```
┌─────────────────────────────────────────────────────────────┐
│  [bold blue]🌌 SKY[/bold blue] │ RAG: [green]ON[/green]    │  ← Cabeçalho
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  [cyan]Você:[/cyan] Como você está?                         │
│                                                             │
│  [yellow]🤔 Thinking...[/yellow]                            │  ← Thinking
│                                                             │
│  [dim]📚 Memória: 3 resultados encontrados[/dim]            │  ← Memória
│                                                             │
│  [magenta]🔧 search_memory()[/magenta] → 3 resultados       │  ← Tools
│                                                             │
│  [bold blue]🌌 Sky:[/bold blue] Estou bem! Hoje aprendi...  │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

### Componentes

| Componente | Biblioteca | Responsabilidade |
|------------|-----------|------------------|
| **Thinking** | Rich `console.status()` | Anim durante geração |
| **Tools** | Rich `Table` | Lista tools executadas |
| **Memory** | Rich `print()` com `dim` | Mostra memórias usadas |
| **Mensagem** | Rich `Markdown` | Renderiza resposta |
| **Header/Footer** | Rich `Panel` | Status bar |

---

## Estrutura de Arquivos

```
src/core/sky/chat/
├── __init__.py          # SkyChat (legacy, mantido)
├── claude_chat.py       # ClaudeChatAdapter (NOVO)
├── ui.py                # ChatUI com prompt_toolkit + Rich (NOVO)
└── personality.py       # System prompt templates (NOVO)

scripts/
├── sky_rag.py           # Atualizado: suporta USE_CLAUDE_CHAT
└── sky_claude.bat       # NOVO: atalho com Claude Chat ON

requirements.txt         # claude-agent-sdk já existe
.env.example             # Adicionar USE_CLAUDE_CHAT=false
```

---

## Risks / Trade-offs

### R1: Latência de Inferência

**Risco:** Chamadas à API podem levar 2-5 segundos vs respostas instantâneas do legacy.

**Mitigação:**

- `console.status()` com anim "Pensando..."
- Feature flag permite voltar ao instantâneo se necessário
- Cache de respostas para perguntas repetidas

### R2: Custos de API

**Risco:** Uso da API Anthropic gera custos por token.

**Mitigação:**

- `USE_CLAUDE_CHAT=false` por padrão (opt-in)
- Limite de tokens: `max_tokens=500` para respostas concisas
- Monitoramento de tokens em logs

### R3: Alucinação

**Risco:** LLM pode inventar informações.

**Mitigação:**

- System prompt explícito: "Nunca invente informações"
- Fonte única de verdade: memória RAG
- Se não souber, responder "Não sei"

### R4: Compatibilidade de Dependências

**Risco:** `claude-agent-sdk` pode conflitar com outras libs.

**Mitigação:**

- SDK já está em uso no projeto (webhooks)
- Se funcionou lá, funciona aqui
- Isolamento via venv

---

## Migração

### Fase 1: Implementação (Dia 1-2)

```bash
# 1. Criar ClaudeChatAdapter
src/core/sky/chat/claude_chat.py
src/core/sky/chat/personality.py

# 2. Criar ChatUI
src/core/sky/chat/ui.py

# 3. Atualizar sky_rag.py
# Adicionar lógica USE_CLAUDE_CHAT

# 4. Testar manualmente
USE_CLAUDE_CHAT=true python scripts/sky_rag.py
```

### Fase 2: Beta Test (Dia 3-4)

- Usuários opt-in via `USE_CLAUDE_CHAT=true`
- Coletar feedback
- Ajustar system prompt

### Fase 3: Rollout Gradual (Dia 5+)

```
Dia 5: 10% (beta testers)
Dia 10: 50% (early adopters)
Dia 15: 100% (todos)
```

### Rollback

```bash
# Instantâneo: desligar flag
export USE_CLAUDE_CHAT=false
python scripts/sky_rag.py

# Ou remover código (se necessário)
git revert <commit-do-chat>
```

---

## Open Questions

1. **Q:** Modelo Claude a usar (haiku, sonnet, opus)?
   - **A:** Começar com **claude-3-haiku** (mais barato, rápido)
   - Opção para configurar via `.env`: `CLAUDE_MODEL=haiku`

2. **Q:** Tamanho máximo de contexto?
   - **A:** `max_tokens=500` para respostas (≈ 300-400 palavras)
   - Memória: `top_k=5` resultados

3. **Q:** Persistência de sessões?
   - **A:** **Out of scope** para esta change
   - Futuro: implementar `sessions/` com SQLite

---

> "Design é fazer as escolhas certas antes que elas se tornem caras" – made by Sky 🚀
