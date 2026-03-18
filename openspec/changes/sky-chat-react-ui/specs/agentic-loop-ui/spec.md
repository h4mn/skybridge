# Agentic Loop UI

Interface que espelha o ciclo ReAct (Reasoning + Acting) do claude-agent-sdk, agrupando Steps de Thought → Action → Observation.

## ADDED Requirements

### Requirement: Exibir AgenticLoopPanel com Steps completos
O sistema SHALL exibir um painel colapsável (`AgenticLoopPanel`) que agrupa Steps completos do loop agentic, cada Step contendo Thought (intenção), Action (execução) e Observation (resultado).

#### Scenario: AgenticLoopPanel exibe Steps durante processamento
- **WHEN** o modelo emite eventos de pensamento, ação e resultado
- **THEN** o AgenticLoopPanel exibe cada Step com ThoughtLine, ActionLine e Observation completas
- **AND** o título do painel mostra "⟳ N steps • Xs" (quantidade e duração total)

#### Scenario: AgenticLoopPanel é colapsável
- **WHEN** o usuário clica no painel ou pressiona atalho
- **THEN** o painel colapsa/expande, mostrando/escondendo os Steps

### Requirement: StepWidget representa iteração ReAct
O sistema SHALL criar um `StepWidget` para cada iteração do loop ReAct, contendo ThoughtLine (texto de intenção) e ActionLine (execução com estado pendente ou resolvido).

#### Scenario: StepWidget nasce com Thought
- **WHEN** chega `text_delta` antes de `tool_start`
- **THEN** StepWidget é criado com ThoughtLine exibindo o texto em itálico muted

#### Scenario: StepWidget transita para estado de ação
- **WHEN** chega `content_block_stop` (tool)
- **THEN** ActionLine mostra '⚙ ToolName: param' em azul (estado pendente)

#### Scenario: StepWidget completa com Observation
- **WHEN** chega `ToolResultMessage`
- **THEN** ActionLine mostra '✓ ToolName: param  └ N linhas' em muted (estado resolvido)

### Requirement: AgenticLoopPanel fecha ao receber Final Answer
O sistema SHALL colapsar automaticamente o AgenticLoopPanel quando o modelo envia a resposta final (sem mais tools após).

#### Scenario: Painel colapsa ao finalizar loop
- **WHEN** o último `text_delta` chega sem `tool_start` subsequente
- **THEN** AgenticLoopPanel colapsa automaticamente
- **AND** o foco move para o SkyBubble com a resposta final

### Requirement: Ordenação de Steps no AgenticLoopPanel
O sistema SHALL exibir Steps em ordem cronológica, com o Step mais recente sempre visível (scroll automático).

#### Scenario: Scroll automático para Step mais recente
- **WHEN** um novo Step é adicionado ou atualizado
- **THEN** a lista de Steps scrolla automaticamente para tornar o Step mais recente visível

---

> "A interface espelha o pensamento" – made by Sky 🔄
