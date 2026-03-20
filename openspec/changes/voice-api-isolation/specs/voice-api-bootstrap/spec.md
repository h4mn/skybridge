# Voice API Bootstrap Integration Specification

Capability: `voice-api-bootstrap` - Integração da Voice API com o sistema de bootstrap do SkyChat

## ADDED Requirements

### Requirement: Inicialização de processo Voice API
O sistema SHALL iniciar Voice API como subprocess durante bootstrap.

#### Scenario: Voice API é iniciada no bootstrap
- **WHEN** SkyChat inicia e feature flag está enabled
- **THEN** bootstrap cria subprocess para Voice API
- **AND** subprocess usa mesmo Python interpreter do SkyChat
- **AND** subprocess é configurado com port 8765 (ou configurável)

#### Scenario: Crash na Voice API é detectado
- **WHEN** subprocess da Voice API termina inesperadamente
- **THEN** bootstrap detecta exit code != 0
- **AND** bootstrap marca Voice API como failed
- **AND** SkyChat inicia sem Voice API (degradação graceful)

### Requirement: Etapa de bootstrap para Voice API
O sistema SHALL fornecer etapa de bootstrap dedicada que aguarda Voice API ficar ready.

#### Scenario: Bootstrap aguarda Voice API ficar ready
- **WHEN** etapa `VoiceAPIStage` é executada
- **THEN** stage inicia processo Voice API
- **AND** stage poll `/health` a cada 100ms
- **AND** stage mostra progresso visual ao usuário
- **AND** stage só completa quando status é "ready"

#### Scenario: Bootstrap mostra progresso detalhado
- **WHEN** Voice API está carregando modelos
- **THEN** bootstrap exibe: "Carregando Voice API... [Loading STT model... 60%]"
- **AND** barra de progresso avança conforme `progress` do health endpoint

#### Scenario: Bootstrap timeout se API demora demais
- **WHEN** Voice API não fica ready em 120 segundos
- **THEN** etapa marca como failed
- **AND** usuário pode optar por continuar sem Voice API

### Requirement: Feature flag para habilitar Voice API
O sistema SHALL respeitar feature flag para habilitar/desabilitar Voice API.

#### Scenario: Feature flag OFF pula etapa Voice API
- **WHEN** `SKYBRIDGE_VOICE_API_ENABLED` não está definido ou é "0"
- **THEN** `VoiceAPIStage` é skipped
- **AND** SkyChat usa código legado de STT/TTS

#### Scenario: Feature flag ON ativa Voice API
- **WHEN** `SKYBRIDGE_VOICE_API_ENABLED="1"`
- **THEN** `VoiceAPIStage` é executada
- **AND** SkyChat usa VoiceAPIClient para STT/TTS

### Requirement: Retry em falha de inicialização
O sistema SHALL tentar reiniciar Voice API se falhar na primeira tentativa.

#### Scenario: Primeira tentativa falha, retry é feito
- **WHEN** Voice API crasha no startup (exit code != 0)
- **THEN** bootstrap aguarda 2 segundos
- **AND** tenta reiniciar processo até 2 vezes
- **AND** se todas tentativas falham, marca como failed

#### Scenario: Usuário pode optar por continuar sem Voice API
- **WHEN** todas tentativas de iniciar Voice API falham
- **THEN** bootstrap pergunta usuário: "Continuar sem Voice API? (STT/TTS não funcionarão)"
- **AND** se usuário confirmar, SkyChat inicia sem Voice API

### Requirement: Cleanup no shutdown
O sistema SHALL encerrar processo Voice API graciosamente no shutdown do SkyChat.

#### Scenario: SkyChat shutdown encerra Voice API
- **WHEN** SkyChat recebe sinal de shutdown (SIGTERM/SIGINT)
- **THEN** bootstrap envia SIGTERM para processo Voice API
- **AND** aguarda até 5 segundos para processo terminar
- **AND** se processo não terminar, envia SIGKILL

#### Scenario: Shutdown gracios permite completar requests
- **WHEN** Voice API está processando request durante shutdown
- **THEN** SIGTERM permite request completar
- **AND** novos requests são rejeitados durante shutdown

### Requirement: Logging de startup
O sistema SHALL registrar eventos importantes do startup de Voice API.

#### Scenario: Eventos de startup são logados
- **WHEN** Voice API é iniciada
- **THEN** bootstrap loga: "Starting Voice API process (pid: 12345)"
- **AND** quando health muda de status, loga: "Voice API status: loading_models (30%)"
- **AND** quando ready, loga: "Voice API ready at http://localhost:8765"

#### Scenario: Erros de startup são logados
- **WHEN** Voice API crasha no startup
- **THEN** bootstrap loga: "Voice API failed to start: <error details>"
- **AND** log inclui stdout/stderr do processo se disponível

### Requirement: Descoberta de porta dinâmica (opcional)
O sistema SHALL suportar porta dinâmica se configurado.

#### Scenario: Porta dinâmica é descoberta via stdout
- **WHEN** Voice API inicia com porta dinâmica (--port 0)
- **THEN** API imprime porta no stdout: "Voice API listening on port 12345"
- **AND** bootstrap captura porta e configura cliente com URL correta

> "Bootstrap é a primeira impressão: faça contar" – made by Sky 🚀
