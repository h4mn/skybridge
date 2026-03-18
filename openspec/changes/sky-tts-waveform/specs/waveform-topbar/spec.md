# Spec: Waveform TopBar

TopBar animada de 3 linhas com height reativo.

## ADDED Requirements

### Requirement: Widget WaveformTopBar
O sistema DEVE fornecer widget `WaveformTopBar` que exibe animação de waveform.

#### Scenario: Composição
- **WHEN** `WaveformTopBar` é montado
- **THEN** exibe 3 linhas de barras Unicode (`▀█`)

### Requirement: Height reativo
O widget DEVE ter `height: 0` por padrão e `height: 3` quando ativo.

#### Scenario: Estado idle
- **WHEN** widget está inativo
- **THEN** `height: 0` (invisível)

#### Scenario: Estado speaking
- **WHEN** `start_speaking()` é chamado
- **THEN** adiciona classe `active` e `height: 3`

#### Scenario: Estado thinking
- **WHEN** `start_thinking()` é chamado
- **THEN** adiciona classe `active`, `thinking` e `height: 3`

### Requirement: Animação por timer
O widget DEVE atualizar visual a cada 100ms via timer.

#### Scenario: Timer ativo
- **WHEN** widget tem classe `active`
- **THEN** timer atualiza alturas das barras a cada 100ms

#### Scenario: Timer parado
- **WHEN** `stop()` é chamado
- **THEN** timer continua mas não atualiza visual

### Requirement: Estilos por modo
O widget DEVE ter cores diferentes para speaking e thinking.

#### Scenario: Cor speaking
- **WHEN** classe `speaking` está presente
- **THEN** cor é `$primary`

#### Scenario: Cor thinking
- **WHEN** classe `thinking` está presente
- **THEN** cor é `$warning`
