# Event Router

Roteador de eventos que diferencia texto de intenção (Thought) de resposta final (Final Answer) baseado em `AssistantMessage`.

## ADDED Requirements

### Requirement: Rotear text_delta para Thought ou Final Answer
O sistema SHALL rotear cada `text_delta` (`content_block_delta`) para **Thought** (se vier antes de `tool_start`) ou **Final Answer** (se vier após último `ToolResult`).

#### Scenario: Texto antes de tool é Thought
- **WHEN** `text_delta` chega e depois vem `tool_start`
- **THEN** o texto é acumulado como Thought e associado ao StepWidget da tool

#### Scenario: Texto após ToolResult é Final Answer
- **WHEN** `text_delta` chega após o último `ToolResultMessage`
- **THEN** o texto é enviado para `SkyBubble` como resposta final

### Requirement: Acumular texto pendente até confirmação de tool
O sistema SHALL acumular `text_delta` em buffer (`pending_thought`) até receber `tool_start` ou confirmar que não virão mais tools.

#### Scenario: Acumulação de texto pendente
- **WHEN** múltiplos `text_delta` chegam antes de `tool_start`
- **THEN** todos são acumulados em `pending_thought`
- **AND** exibidos juntos como ThoughtLine quando `tool_start` confirma

### Requirement: Usar AssistantMessage como mapa semântico
O sistema SHALL usar `AssistantMessage` como mapa de fallback para diferenciar Thoughts de Final Answer quando streaming não for conclusivo.

#### Scenario: Fallback para AssistantMessage
- **WHEN** streaming é ambíguo (não está claro se virão mais tools)
- **THEN** `AssistantMessage` é consultada para identificar `TextBlock` vs `ToolUseBlock`
- **AND** TextBlock antes de ToolUseBlock = Thought, TextBlock final = Final Answer

### Requirement: Emitir StreamEvent.THOUGHT para Thought confirmado
O sistema SHALL emitir evento `StreamEvent.THOUGHT` quando `tool_start` confirma que texto anterior era Thought.

#### Scenario: Evento THOUGHT emitido
- **WHEN** `tool_start` chega após `text_delta`
- **THEN** evento `StreamEvent.THOUGHT` é emitido com o texto acumulado
- **AND** o Turn consome o evento para criar StepWidget

### Requirement: Heurística de timeout para Step sem resultado
O sistema SHALL resolver StepWidget por timeout (500ms sem eventos) quando `ToolResultMessage` não chega (fallback para modelos glm-4.7).

#### Scenario: Timeout resolve Step pendente
- **WHEN** StepWidget está em estado pendente há 500ms sem novos eventos
- **THEN** ActionLine é marcada como resolvida sem Observation
- **AND** texto indicativo mostra "(sem resultado)"

---

> "O texto encontra seu destino" – made by Sky 🚦
