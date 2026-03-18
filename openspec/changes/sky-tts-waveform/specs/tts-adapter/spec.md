# Spec: TTS Adapter

Interface abstrata para backends de Text-to-Speech.

## ADDED Requirements

### Requirement: Interface TTSAdapter
O sistema DEVE fornecer uma interface abstrata `TTSAdapter` que define o contrato para backends TTS.

#### Scenario: Implementação de adapter
- **WHEN** um novo backend TTS é implementado
- **THEN** ele DEVE herdar de `TTSAdapter` e implementar `speak()` e `synthesize()`

### Requirement: Fábrica de adapters
O sistema DEVE fornecer uma fábrica `get_tts_adapter()` que retorna o adapter configurado.

#### Scenario: Adapter padrão
- **WHEN** `get_tts_adapter()` é chamado sem configuração
- **THEN** retorna `KokoroAdapter` como padrão

#### Scenario: Adapter via configuração
- **WHEN** variável de ambiente `TTS_BACKEND=moss` está definida
- **THEN** `get_tts_adapter()` retorna `MOSSAdapter`

### Requirement: Suporte a modos de voz
O adapter DEVE aceitar `VoiceMode` como parâmetro em `speak()` e `synthesize()`.

#### Scenario: Modo normal
- **WHEN** `speak(text, mode=VoiceMode.NORMAL)` é chamado
- **THEN** o áudio é gerado com speed=1.0 e sem hesitações

#### Scenario: Modo thinking
- **WHEN** `speak(text, mode=VoiceMode.THINKING)` é chamado
- **THEN** o áudio é gerado com speed=0.85 e hesitações adicionadas
