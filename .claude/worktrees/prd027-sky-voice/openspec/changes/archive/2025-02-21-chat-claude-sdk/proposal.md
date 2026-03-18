# Proposal: Chat com Claude SDK

## Why

O chat atual da Sky usa respostas pré-programadas baseadas em padrões fixos (`if/else`), o que limita a naturalidade e profundidade das conversas. A Sky não consegue:
- Gerar respostas contextualizadas e nuances
- Processar linguagem natural de forma mais sofisticada
- Adaptar o tom e estilo conforme a conversa

A oportunidade é usar o **Claude Agent SDK** (já aprovado na ADR021/PRD019 para webhooks) para trazer inferência de LLM para o chat da Sky, mantendo sua personalidade e memória.

## What Changes

- **Novo `ClaudeChatAdapter`**: Implementação de chat usando Claude Agent SDK para geração de respostas
- **Feature flag `USE_CLAUDE_CHAT`**: Para migração gradual entre chat atual (respostas fixas) e chat com inferência
- **System prompt da Sky**: Definir personalidade, tom e limites da Sky
- **Session continuity**: Manter contexto da conversa via SDK
- **Integração com memória**: RAG continua funcionando como fonte de conhecimento
- **Fallback mode**: Se SDK falhar, voltar para respostas fixas

## Capabilities

### New Capabilities

- `claude-chat-integration`: Integração do Claude Agent SDK no chat da Sky para geração de respostas com inferência
- `sky-personality`: Definição de personalidade, tom e comportamento da Sky via system prompt
- `chat-session-context`: Manutenção de contexto conversacional ao longo da sessão
- `chat-observability`: Hooks de observabilidade para geração de respostas (latência, tokens, etc.)

### Modified Capabilities

- Nenhuma - as capacidades existentes de memória (RAG) são mantidas sem alteração de requisitos

## Impact

### Código Afetado

| Arquivo | Alteração |
|---------|-----------|
| `scripts/sky_rag.py` | Adicionar opção de usar Claude Chat |
| `src/core/sky/chat/__init__.py` | Novo `ClaudeChatAdapter` |
| `.env.example` | Nova variável `USE_CLAUDE_CHAT` |
| `requirements.txt` | Adicionar `claude-agent-sdk` (já está no projeto) |

### APIs

- **Nova API interna**: `ClaudeChatAdapter` implementando interface similar a `SkyChat`
- **Compatibilidade**: `SkyChat` atual mantido como fallback

### Dependências

- `claude-agent-sdk` (já em uso no projeto para webhooks)
- `anthropic` (já em uso no projeto)

### Sistemas

- Chat interativo via `sky.bat`
- Futuramente: API endpoints de chat (outro escopo)

---

> "A verdadeira inteligência não é saber respostas, é gerar as perguntas certas" – made by Sky 🚀
