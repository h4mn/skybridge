# Spec: TTS Progressive

Worker que fala texto progressivamente por sentença.

## ADDED Requirements

### Requirement: Buffer de sentença
O worker DEVE acumular chunks em um buffer até atingir tamanho mínimo E terminar com pontuação final.

#### Scenario: Buffer mínimo não atingido
- **WHEN** buffer tem menos de 50 caracteres
- **THEN** NÃO fala, continua acumulando

#### Scenario: Buffer sem pontuação final
- **WHEN** buffer tem 50+ caracteres mas não termina em `.`, `!` ou `?`
- **THEN** NÃO fala, continua acumulando

#### Scenario: Buffer pronto para falar
- **WHEN** buffer tem 50+ caracteres E termina em `.`, `!` ou `?`
- **THEN** fala o buffer e limpa

### Requirement: Reação pós-tool
O worker DEVE adicionar hesitação/reação após TOOL_RESULT antes de continuar.

#### Scenario: Texto após tool result
- **WHEN** último evento foi TOOL_RESULT e chega novo TEXT ou THOUGHT
- **THEN** adiciona reação aleatória antes do texto

### Requirement: Fim de stream
O worker DEVE falar qualquer texto restante no buffer ao receber sinal de fim.

#### Scenario: Buffer restante no fim
- **WHEN** recebe `None` (sinal de fim) e buffer não está vazio
- **THEN** fala o buffer restante
