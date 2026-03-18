# Tasks: Sky Chat ReAct UI

## 0. Bug Fixes (descobertos durante implementação)

- [x] 0.1 Corrigir "Can't mount widget(s) before StepWidget() is mounted" - usar `on_children_updated()` hook
- [x] 0.2 Adicionar tratamento de `asyncio.CancelledError` em `_stream_claude_sdk()`
- [x] 0.3 Adicionar `finally` block com `aclose()` do query generator SDK
- [x] 0.4 Corrigir AgenticLoopPanel não aparecendo no SkyBubble - montar painel antes de usar, remover antes de mover
- [x] 0.5 Corrigir TypeError no botão Retry - criar classe ChatRetry ao invés de usar Message genérico
- [x] 0.6 Remover prints que estragam UX do chat - substituir por logger estruturado (embedding.py, collections.py, tracer.py, watcher.py)
- [x] 0.7 Corrigir espaçamento do AgenticLoopPanel - adicionar margin-top no SkyBubble, remover padding-bottom excessivo
- [x] 0.8 **CRÍTICO**: Corrigir vazamento de logs para UI do chat - mudar logger de stdout para stderr
- [x] 0.9 Corrigir import circular em snapshot.py - mover import de SkyTextualDOM para dentro da função (lazy import)
- [x] 0.10 Corrigir ThoughtLine invisível - mudar cor de `$text-muted` para `$text` para visibilidade

### Problemas Conhecidos
- **Windows + asyncio**: "ValueError: I/O operation on closed pipe" no shutdown do app
  - Causa: Bug do asyncio no Windows quando subprocessos não são limpos antes do event loop fechar
  - Impacto: Apenas visual (Exception ignored), não afeta funcionalidade
  - Origem: claude-agent-sdk usa subprocessos internamente que não são fechados graciosamente

## 1. Setup e Dependências

- [x] 1.1 Adicionar `pyperclip` ao `requirements.txt`
- [x] 1.2 Adicionar `StreamEvent.THOUGHT` ao enum `StreamEvent` em `claude_chat.py` (já existia)

## 2. Event Router (claude_chat.py)

- [x] 2.1 Implementar buffer `pending_thought: str` no estado do stream
- [x] 2.2 Implementar lógica de acumulação de `text_delta` em `pending_thought`
- [x] 2.3 Emitir `StreamEvent.THOUGHT` quando `tool_start` confirmar que texto anterior era Thought
- [x] 2.4 Implementar heurística de fallback: após último `ToolResult`, próximo `text` = Final Answer
- [x] 2.5 Implementar fallback usando `AssistantMessage` como mapa semântico (já existe linha 720)
- [x] 2.6 Adicionar timeout de 500ms para Steps sem `ToolResultMessage` (glm-4.7) (ActionLine.set_timeout implementado)

## 3. Componentes Textual - Step (thinking.py)

- [x] 3.1 Criar `ThoughtLine` widget (estático, itálico muted)
- [x] 3.2 Criar `ActionLine` widget (reativo, ciclos: ⚙ → ✓)
- [x] 3.3 Implementar estado pendente (⚙ Tool: param) em azul
- [x] 3.4 Implementar estado resolvido (✓ Tool: param └ N linhas) em muted
- [x] 3.5 Implementar indicador "(sem resultado)" para timeout
- [x] 3.6 Criar `StepWidget` que agrupa `ThoughtLine` + `ActionLine`
- [x] 3.7 Implementar montagem sob demanda: nasce com Thought, completa com Action

## 4. Componentes Textual - AgenticLoopPanel (thinking.py)

- [x] 4.1 Criar `AgenticLoopPanel` (collapsible, substituto do `ThinkingPanel`)
- [x] 4.2 Implementar lista de `StepWidget`s com scroll automático
- [x] 4.3 Implementar título dinâmico "⟳ N steps • Xs"
- [x] 4.4 Implementar colapso automático ao receber Final Answer
- [x] 4.5 Adicionar suporte a atalho de teclado para colapsar/expadir
- [x] 4.6 Implementar freeze ao cancelar (Steps parciais ficam visíveis)

## 5. Componentes Textual - ActionBar (bubbles.py)

- [x] 5.1 Criar `ActionBar` widget com botões [Copy] [Retry]
- [x] 5.2 Implementar funcionalidade Copy usando `pyperclip`
- [x] 5.3 Adicionar feedback visual "✓ Copiado!" (2s)
- [x] 5.4 Implementar tratamento de erro ao copiar
- [x] 5.5 Implementar funcionalidade Retry (cria novo Turn)
- [x] 5.6 Adicionar verificação: desabilitar Retry se não há mensagem anterior
- [x] 5.7 Integrar `ActionBar` no `SkyBubble` (SkyBubble.show_actions implementado)

## 6. TurnState Cancellation (turn_state.py)

- [x] 6.1 Adicionar estado `CANCELLED` ao enum `TurnState`
- [x] 6.2 Implementar lógica de transição PENDING/THINKING → CANCELLED
- [x] 6.3 Implementar encerramento gracioso do stream (`asyncio.CancelledError`)
- [x] 6.4 Implementar limpeza de recursos (conexões, tasks)
- [x] 6.5 Adicionar indicador visual "(interrompido)" no `StepWidget` pendente

## 7. Turn Integration (turn.py)

- [x] 7.1 Atualizar `Turn` para consumir `StreamEvent.THOUGHT` (métodos add_thought/add_action criados)
- [x] 7.2 Modificar `add_thinking_entry()` para criar `StepWidget` ao invés de `ToolCallWidget` (nova API add_action)
- [x] 7.3 Implementar tratamento de Ctrl+C para cancelamento (Ctrl+C handler adicionado)
- [x] 7.4 Implementar remoção de `ThinkingIndicator` ao cancelar (feito em set_cancelled)
- [x] 7.5 Implementar preservação de `UserBubble` ao cancelar (comportamento padrão)
- [x] 7.6 Implementar foco automático para novo Turn ao Retry (handler on_chat_retry adicionado)
- [x] 7.7 Substituir `ThinkingPanel` por `AgenticLoopPanel` no `Turn` (ChatScreen integrado)

## 8. Testes Unitários

- [ ] 8.1 Testar roteador de eventos (Thought vs Final Answer)
- [ ] 8.2 Testar acúmulo de `pending_thought`
- [ ] 8.3 Testar emissão de `StreamEvent.THOUGHT`
- [ ] 8.4 Testar heurística de fallback
- [ ] 8.5 Testar timeout de 500ms para Steps sem resultado
- [ ] 8.6 Testar `ThoughtLine` renderização
- [ ] 8.7 Testar `ActionLine` transições de estado
- [ ] 8.8 Testar `StepWidget` montagem e conclusão
- [ ] 8.9 Testar `AgenticLoopPanel` colapso automático
- [ ] 8.10 Testar `ActionBar` Copy (sucesso e erro)
- [ ] 8.11 Testar `ActionBar` Retry
- [ ] 8.12 Testar `TurnState.CANCELLED` transições
- [ ] 8.13 Testar cancelamento de stream gracioso

## 9. Testes de Integração

- [ ] 9.1 Testar ciclo completo: UserBubble → AgenticLoopPanel → SkyBubble
- [ ] 9.2 Testar múltiplos Steps em sequência
- [ ] 9.3 Testar cancelamento durante processamento
- [ ] 9.4 Testar Retry após cancelamento
- [ ] 9.5 Testar colapso/expadir de `AgenticLoopPanel`
- [ ] 9.6 Testar scroll automático para Step mais recente

## 10. Testes E2E

- [ ] 10.1 Testar fluxo completo com modelo real (claude-3.5-sonnet)
- [ ] 10.2 Testar fluxo com glm-4.7 (validar timeout)
- [ ] 10.3 Testar Copy de resposta com markdown
- [ ] 10.4 Testar Retry de mensagem complexa
- [ ] 10.5 Testar cancelamento com Ctrl+C
- [ ] 10.6 Testar cancelamento com botão [Parar]

## 11. Documentação

- [ ] 11.1 Atualizar `CLAUDE_CHAT_QUICKSTART.md` com nova UI
- [ ] 11.2 Adicionar exemplos de `AgenticLoopPanel` na documentação
- [ ] 11.3 Documentar atalhos de teclado (colapsar, cancelar)
- [ ] 11.4 Adicionar CHANGELOG entry para PRD-REACT-001

## 12. Cleanup e Deprecação

- [ ] 12.1 Manter `ThinkingPanel` durante migração (deprecate)
- [ ] 12.2 Manter `ToolCallWidget` durante migração (deprecate)
- [ ] 12.3 Adicionar warnings de deprecation nos componentes antigos
- [ ] 12.4 Remover código morto após validação completa

---

**Total:** 68 tarefas distribuídas em 12 fases.

> "Cada tarefa é um degrau para o topo" – made by Sky 🪜
