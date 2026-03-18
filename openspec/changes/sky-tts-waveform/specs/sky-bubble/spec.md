# Spec: Sky Bubble (Modified)

Delta spec para adicionar WaveformTopBar ao SkyBubble.

## MODIFIED Requirements

### Requirement: Composição do SkyBubble
O SkyBubble DEVE conter WaveformTopBar como primeiro filho, antes do Markdown.

#### Scenario: Composição padrão
- **WHEN** SkyBubble é montado sem agentic_panel
- **THEN** composição é: WaveformTopBar → Markdown

#### Scenario: Composição com agentic_panel
- **WHEN** SkyBubble é montado com agentic_panel
- **THEN** composição é: WaveformTopBar → AgenticLoopPanel → Markdown

## ADDED Requirements

### Requirement: API de waveform
O SkyBubble DEVE expor métodos `start_speaking()`, `start_thinking()` e `stop_waveform()` que delegam para WaveformTopBar.

#### Scenario: Iniciar fala
- **WHEN** `sky_bubble.start_speaking()` é chamado
- **THEN** WaveformTopBar interno recebe `start_speaking()`

#### Scenario: Iniciar pensamento
- **WHEN** `sky_bubble.start_thinking()` é chamado
- **THEN** WaveformTopBar interno recebe `start_thinking()`

#### Scenario: Parar waveform
- **WHEN** `sky_bubble.stop_waveform()` é chamado
- **THEN** WaveformTopBar interno recebe `stop()`

### Requirement: WaveformTopBar oculto por padrão
O WaveformTopBar dentro do SkyBubble DEVE iniciar com `height: 0` (invisível).

#### Scenario: Montagem inicial
- **WHEN** SkyBubble é montado
- **THEN** WaveformTopBar está invisível até `start_speaking()` ou `start_thinking()` ser chamado
