# Tasks: Chat com Claude SDK

## 1. Setup e Dependências

- [x] 1.1 Verificar que `claude-agent-sdk` já está em `requirements.txt`
- [x] 1.2 Adicionar `prompt-toolkit` e `rich` ao `requirements.txt`
- [x] 1.3 Instalar novas dependências (`pip install -r requirements.txt`)
- [x] 1.4 Criar estrutura de diretórios `src/core/sky/chat/`

## 2. System Prompt e Personalidade

- [x] 2.1 Criar `src/core/sky/chat/personality.py`
- [x] 2.2 Definir template `SYSTEM_PROMPT` com slots dinâmicos
- [x] 2.3 Implementar `_build_system_prompt(memory_context: str) -> str`
- [x] 2.4 Adicionar regras comportamentais no prompt (não alucinar, ser honesto, conciso)
- [x] 2.5 Implementar assinatura "made by Sky 🚀" com uso condicional

## 3. ClaudeChatAdapter - Core

- [x] 3.1 Criar `src/core/sky/chat/claude_chat.py`
- [x] 3.2 Implementar classe `ClaudeChatAdapter`
- [x] 3.3 Implementar `__init__()` com injeção de `PersistentMemory`
- [x] 3.4 Implementar `receive(message: ChatMessage)` para armazenar no histórico
- [x] 3.5 Implementar `respond(message: ChatMessage) -> str` principal
- [x] 3.6 Implementar `_retrieve_memory(query: str) -> List[MemoryResult]`
- [x] 3.7 Implementar `_call_claude_sdk(messages: List) -> str`
- [x] 3.8 Adicionar fallback para `SkyChat` em caso de erro no SDK

## 4. Claude SDK Integration

- [x] 4.1 Importar `claude_agent_sdk` no adapter
- [x] 4.2 Configurar cliente com API key do `.env`
- [x] 4.3 Implementar geração de resposta com `max_tokens=500`
- [x] 4.4 Adicionar contagem de tokens (input/output)
- [x] 4.5 Implementar escolha de modelo via `CLAUDE_MODEL` env var
- [x] 4.6 Adicionar validação de nome de modelo com fallback para haiku

## 5. Contexto de Sessão

- [x] 5.1 Implementar histórico de mensagens no adapter (`self._history: List[ChatMessage]`)
- [x] 5.2 Limitar histórico às últimas 20 mensagens (10 turnos)
- [x] 5.3 Incluir histórico no contexto da requisição Claude
- [x] 5.4 Implementar comando `/new` para limpar sessão
- [x] 5.5 Adicionar confirmação antes de limpar sessão com histórico
- [x] 5.6 Implementar `/cancel` para cancelar operação pendente

## 6. UI com prompt_toolkit + Rich

- [x] 6.1 Criar `src/core/sky/chat/ui.py`
- [x] 6.2 Implementar classe `ChatUI` usando `prompt_toolkit`
- [x] 6.3 Implementar `render_header()` com status bar (Sky, RAG, memória)
- [x] 6.4 Implementar `render_thinking()` com anim "🤔 Pensando..."
- [x] 6.5 Implementar `render_tools()` com tabela de tools executadas
- [x] 6.6 Implementar `render_memory()` com preview de memórias usadas
- [x] 6.7 Implementar `render_message()` com renderização Markdown
- [x] 6.8 Implementar `render_footer()` com atalhos e comandos

## 7. Script sky_rag.py Atualizado

- [x] 7.1 Adicionar import de `ClaudeChatAdapter` em `scripts/sky_rag.py`
- [x] 7.2 Implementar lógica `USE_CLAUDE_CHAT` environment variable
- [x] 7.3 Criar instância de adapter ou SkyChat baseado na flag
- [x] 7.4 Integrar `ChatUI` no loop principal
- [x] 7.5 Adicionar tratamento de exceções com fallback

## 8. Observabilidade e Métricas

- [x] 8.1 Criar `src/core/sky/chat/metrics.py` (criado como parte de ui.py)
- [x] 8.2 Implementar dataclass `ChatMetrics` (latency, tokens, memory_hits, model)
- [x] 8.3 Adicionar medição de latência em cada resposta
- [x] 8.4 Registrar contagem de tokens (input/output)
- [x] 8.5 Implementar logs estruturados em JSON
- [x] 8.6 Adicionar flag `--verbose` para exibir métricas
- [x] 8.7 Implementar resumo da sessão ao encerrar (`/sair`)

## 9. Feature Flags e Configuração

- [x] 9.1 Adicionar `USE_CLAUDE_CHAT=false` ao `.env.example`
- [x] 9.2 Adicionar `CLAUDE_MODEL=claude-3-haiku-20240307` ao `.env.example`
- [x] 9.3 Adicionar `CLAUDE_API_KEY` (reuso existente)
- [x] 9.4 Criar `scripts/sky_claude.bat` com flag pré-ativada
- [x] 9.5 Documentar uso das flags na documentação

## 10. Testes

- [x] 10.1 Criar `tests/unit/core/sky/chat/test_claude_chat.py`
- [x] 10.2 Testar `ClaudeChatAdapter.respond()` com mock de SDK
- [x] 10.3 Testar `_build_system_prompt()` com/sem memória
- [x] 10.4 Testar fallback para legacy em caso de erro
- [x] 10.5 Testar limites de histórico (20 mensagens)
- [x] 10.6 Testar comando `/new` limpa histórico
- [x] 10.7 Criar `tests/unit/core/sky/chat/test_personality.py`
- [x] 10.8 Testar formatação de system prompt
- [x] 10.9 Criar `tests/unit/core/sky/chat/test_metrics.py` (em test_ui.py)
- [x] 10.10 Testar cálculo de latência e tokens

## 11. Integração e E2E

- [x] 11.1 Testar chat interativo com `USE_CLAUDE_CHAT=true`
- [x] 11.2 Verificar resposta usando memória RAG
- [x] 11.3 Testar fallback para legacy
- [x] 11.4 Verificar personalidade da Sky nas respostas
- [x] 11.5 Testar comandos `/new`, `/cancel`, `/sair`
- [x] 11.6 Verificar exibição de métricas em modo `--verbose`
- [x] 11.7 Testar com modelo haiku (padrão)
- [x] 11.8 Testar com modelo customizado via env var

## 12. Documentação

- [x] 12.1 Atualizar `README.md` com instruções do chat Claude
- [x] 12.2 Criar `docs/chat/CLAUDE_CHAT_QUICKSTART.md`
- [x] 12.3 Documentar variáveis de ambiente
- [x] 12.4 Documentar comandos disponíveis (/new, /cancel, /sair)
- [x] 12.5 Adicionar exemplos de conversas
- [x] 12.6 Documentar arquitetura do ChatUI

## 13. Rollout e Monitoramento

- [x] 13.1 Verificar que `USE_CLAUDE_CHAT=false` é padrão
- [x] 13.2 Testar com beta users (opt-in)
- [x] 13.3 Monitorar latência das respostas
- [x] 13.4 Monitorar custos de tokens
- [x] 13.5 Ajustar `max_tokens` se necessário
- [x] 13.6 Planejar rollout gradual (10% → 50% → 100%)

---

**Total: 77 tarefas**

**Status: ✅ IMPLEMENTAÇÃO COMPLETA**

> "Uma jornada de mil quilômetros começa com um único passo" – made by Sky 🚀
