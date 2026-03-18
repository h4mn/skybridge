# Spec: Voice Modes

Modos de voz Normal e Thinking com hesitações.

## ADDED Requirements

### Requirement: Enum VoiceMode
O sistema DEVE fornecer `VoiceMode` enum com valores `NORMAL` e `THINKING`.

#### Scenario: Modo normal
- **WHEN** `VoiceMode.NORMAL` é usado
- **THEN** velocidade é 1.0 e sem hesitações

#### Scenario: Modo thinking
- **WHEN** `VoiceMode.THINKING` é usado
- **THEN** velocidade é 0.85 e hesitações são adicionadas

### Requirement: Dicionário de hesitações
O sistema DEVE fornecer `HESITATIONS` com categorias de hesitações Kokoro-friendly.

#### Scenario: Hesitações starters
- **WHEN** `HESITATIONS["starters"]` é acessado
- **THEN** retorna lista de hesitações de início (ex: "deixa eu pensar...", "bom...")

#### Scenario: Hesitações pós-tool
- **WHEN** `HESITATIONS["post_tool"]["positive"]` é acessado
- **THEN** retorna lista de reações positivas (ex: "legal...", "ótimo...")

### Requirement: Função get_reaction
O sistema DEVE fornecer `get_reaction(context, tool_result_type, intensity)` que retorna hesitação contextual.

#### Scenario: Intensidade zero
- **WHEN** `intensity=0.0`
- **THEN** retorna string vazia

#### Scenario: Contexto start
- **WHEN** `context="start"` e `intensity=1.0`
- **THEN** retorna hesitação de `starters`

#### Scenario: Contexto post_tool
- **WHEN** `context="post_tool"` e `tool_result_type="surprise"`
- **THEN** retorna hesitação de `post_tool["surprise"]`
