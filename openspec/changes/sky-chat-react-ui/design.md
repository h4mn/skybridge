# Design: Sky Chat ReAct UI

## Context

O SkyChat atual usa uma arquitetura linear de UI onde `ThinkingPanel` lista tools isoladas e `SkyBubble` recebe todo o texto misturado (raciocínio + resposta). O claude-agent-sdk emite eventos ricos (`content_block_delta`, `AssistantMessage`, `ToolResultMessage`) que espelham o padrão ReAct, mas a UI não aproveita essa estrutura.

**Arquitetura atual:**
- `Turn` compõe `UserBubble`, `ThinkingPanel`, `SkyBubble`
- `ThinkingPanel` contém `ToolCallWidget`s isolados
- `SkyBubble` recebe todos os `text_delta` sem distinção

**Stakeholders:**
- Usuários finais do SkyChat (desenvolvedores)
- Mantenedores do código Textual UI

**Restrições:**
- Compatibilidade com Textual 0.80+
- Uso obrigatório de claude-agent-sdk (ADR021)
- Manter testes existentes passando

---

## Goals / Non-Goals

**Goals:**
1. UI espelha o ciclo ReAct (Thought → Action → Observation)
2. Separação clara entre intenção (Thought) e resposta final (Final Answer)
3. Capacidade de interromper turnos em andamento
4. Ações pós-resposta (Copy, Retry)

**Non-Goals:**
- Modificar o protocolo do claude-agent-sdk
- Suportar múltiplos modelos simultâneos
- Alterar a estrutura de `UserBubble`
- Implementar histórico persistente (fora do escopo)

---

## Decisions

### D1: StreamEvent.THOUGHT para diferenciar Thought de Final Answer

**Decisão:** Adicionar `StreamEvent.THOUGHT` ao enum `StreamEvent`, emitido quando `tool_start` confirma que texto anterior era Thought.

**Racional:**
- Eventos tipados são mais seguros que strings mágicas
- Permite que `Turn` reaja diferentemente a cada tipo
- Segue padrão existente (`StreamEvent.TEXT`, `StreamEvent.TOOL_START`)

**Alternativas consideradas:**
- ✗ Usar `StreamEvent.TEXT` com flag `is_thought` → menos type-safe
- ✗ Não emitir evento, modificar `Turn.add_thinking_entry()` → quebra princípio de responsabilidade única

### D2: pending_thought buffer no estado do stream

**Decisão:** Manter `pending_thought: str` no estado do stream em `claude_chat.py`, acumulando até `tool_start` confirmar.

**Racional:**
- Simples e determinístico
- Não depende de parse complexo de `AssistantMessage`
- Funciona mesmo quando `AssistantMessage` chega após os eventos

**Alternativas consideradas:**
- ✗ Tentar prever com base em conteúdo heurístico → frágil
- ✗ Exibir texto imediatamente e mover depois → UX ruim (flicker)

### D3: StepWidget composto por ThoughtLine + ActionLine

**Decisão:** `StepWidget` é um container com dois componentes filhos: `ThoughtLine` (estático) e `ActionLine` (reativo, muda estado).

**Racional:**
- Separação de responsabilidades (conteúdo vs estado)
- `ActionLine` pode ser reutilizável em outros contextos
- Facilita testes unitários isolados

**Alternativas consideradas:**
- ✗ Widget único com render condicional → mais complexo para testar
- ✗Thought e Action em widgets separados sem parent → quebra semântica de Step

### D4: AgenticLoopPanel substitui ThinkingPanel (não herda)

**Decisão:** `AgenticLoopPanel` é um novo componente, não herda de `ThinkingPanel`.

**Racional:**
- `ThinkingPanel` lista tools isoladas, `AgenticLoopPanel` agrupa Steps
- Semântica completamente diferente (herança forçaria adaptações)
- Permite manter ambos durante migração gradual

**Alternativas consideradas:**
- ✗ Herdar e sobrescrever métodos → risco de comportamento residual
- ✗ Modificar `ThinkingPanel` in-place → quebra compatibilidade

### D5: TurnState.CANCELLED como estado final

**Decisão:** `CANCELLED` é um estado terminal (como `DONE`), não transitório.

**Racional:**
- Turno cancelado não deve voltar a processar
- Simplifica lógica de transição (PENDING → THINKING → DONE/CANCELLED)
- Histórico preserva estado para auditoria

**Alternativas consideradas:**
- ✗ Estado transitório que volta para PENDING → complexifica lógica
- ✗ Usar flag separado `is_cancelled` → menos explícito

### D6: pyperclip para Copy (não clipboard do sistema)

**Decisão:** Usar biblioteca `pyperclip` para funcionalidade Copy.

**Racional:**
- Cross-platform (Windows, macOS, Linux)
- API simples (`pyperclip.copy()`)
- Não depende de frameworks específicos

**Alternativas consideradas:**
- ✗ `clipboard` do Textual → menos controle sobre formatação markdown
- ✗ Chamadas nativas por plataforma → mais código de manutenção

### D7: Timeout de 500ms para Step sem ToolResult

**Decisão:** Implementar timeout de 500ms para resolver `StepWidget` quando `ToolResultMessage` não chega.

**Racional:**
- Models glm-4.7 podem não emitir `ToolResultMessage` (fallback)
- 500ms é suficiente para distinguir "sem resultado" de "lento"
- Feedback visual claro ao usuário

**Alternativas consideradas:**
- ✗ Esperar indefinidamente → StepWidget nunca completa
- ✗ Timeout menor (100ms) → risco de falso positivo
- ✗ Timeout maior (2s) → UX ruim

### D8: Retry cria novo Turn (não reusa)

**Decisão:** Botão [Retry] cria um novo `Turn` com a mesma mensagem do usuário, não reusa o existente.

**Racional:**
- Preserva histórico (turno anterior permanece visível)
- Evita complexidade de "resetar" estado interno
- Segue padrão de chat (cada mensagem é um turno)

**Alternativas consideradas:**
- ✗ Reusar mesmo `Turn` → complexidade de reset de estado
- ✗ Editar mensagem in-place → quebra imutabilidade do histórico

---

## Risks / Trade-offs

### R1: AssistantMessage pode chegar após text_deltas
[Risco] Roteamento pode falhar se `AssistantMessage` não chegar antes dos eventos finais.

→ **Mitigação:** Heurística de fallback: após último `ToolResult`, próximo `text` = Final Answer. Testar com claude-3.5-sonnet e glm-4.7.

### R2: glm-4.7 não emite ToolResultMessage consistentemente
[Risco] Steps podem ficar pendentes indefinidamente.

→ **Mitigação:** Timeout de 500ms + indicador "(sem resultado)". Monitorar logs em produção.

### R3: Streaming visual perdido durante Thoughts
[Risco] Usuário vê "travamento" enquanto `pending_thought` acumula.

→ **Mitigação:** Exibir preview com delay de 150ms (opcional, implementar se UX for degradada).

### R4: Breaking change em Turn.add_thinking_entry()
[Risco] Código que depende da assinatura antiga quebra.

→ **Mitigação:** Manter compatibilidade durante migração com sobrecarga de método. Deprecar assinatura antiga.

### R5: ActionBar pode poluir UI em turnos curtos
[Risco] Botões Copy/Retry sempre visíveis podem ser desnecessários em respostas simples.

→ **Mitigação:** UX aceitável; botões pequenos e não intrusivos. Considerar colapsar em turnos < 100 caracteres (futuro).

---

## Migration Plan

### Fase 1: Roteador de eventos (claude_chat.py)
- Adicionar `StreamEvent.THOUGHT`
- Implementar buffer `pending_thought`
- Emitir evento THOUGHT quando `tool_start` confirmar

### Fase 2: Componentes Textual (thinking.py, bubbles.py, turn.py)
- Criar `ThoughtLine`, `ActionLine`, `StepWidget`
- Criar `AgenticLoopPanel` (manter `ThinkingPanel` para deprecate)
- Adicionar `ActionBar` no `SkyBubble`
- Atualizar `Turn` para consumir `StreamEvent.THOUGHT`

### Fase 3: TurnState (turn_state.py)
- Adicionar `CANCELLED`
- Implementar lógica de cancelamento em `Turn`

### Fase 4: Testes
- Testes unitários para roteador
- Testes de integração para `AgenticLoopPanel`
- Testes E2E para Cancel e Retry

**Rollback:** Reverter commits; branches curtos facilitam rollback se necessário.

---

## Open Questions

1. **Q:** Deve exibir preview de `pending_thought` com delay?
   - **A:** Decidir após UX testing com Fase 1 implementada.

2. **Q:** Timeout de 500ms é adequado para glm-4.7?
   - **A:** Validar em testes; ajustar via configuração se necessário.

3. **Q:** Deve persistir TurnState.CANCELLED em histórico?
   - **A:** Sim, para auditoria e debug.

---

> "Design é a inteligência tornada visível" – made by Sky 🎨
