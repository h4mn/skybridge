# Voice API Client Specification

Capability: `voice-api-client` - Cliente HTTP assíncrono integrado ao SkyChat para consumir a Voice API

## ADDED Requirements

### Requirement: Cliente STT assíncrono
O sistema SHALL fornecer cliente assíncrono para transcrição de áudio via Voice API.

#### Scenario: Cliente envia áudio para transcrição
- **WHEN** código SkyChat chama `await voice_client.stt(audio_bytes)`
- **THEN** cliente faz POST `/voice/stt` com multipart/form-data
- **AND** retorna texto transcrito como string
- **AND** levanta exceção se API retornar erro 4xx/5xx

#### Scenario: Cliente faz retry em erro transitório
- **WHEN** API retorna 503 Service Unavailable
- **THEN** cliente aguarda 1s e retenta até 3 vezes
- **AND** após 3 tentativas falhas, levanta exceção

#### Scenario: Cliente respeita timeout
- **WHEN** API não responde em 30 segundos
- **THEN** cliente cancela request e levanta `TimeoutError`

### Requirement: Cliente TTS com streaming
O sistema SHALL fornecer cliente assíncrono para síntese de voz com consumo de stream SSE.

#### Scenario: Cliente consome stream de áudio
- **WHEN** código SkyChat chama `voice_client.tts_stream(text)`
- **THEN** cliente faz POST `/voice/tts` e retorna async generator de chunks
- **AND** cada chunk pode ser processado imediatamente (streaming)
- **AND** generator fecha automaticamente ao fim do stream

#### Scenario: Cliente pode cancelar stream mid-way
- **WHEN** código SkyChat interrompe consumo do generator
- **THEN** cliente fecha conexão HTTP
- **AND** Voice API para de gerar áudio

#### Scenario: Cliente lida com erro de fila cheia
- **WHEN** API retorna 503 (fila cheia)
- **THEN** cliente aguarda tempo indicado em header `Retry-After`
- **AND** retenta request automaticamente

### Requirement: Configuração de endpoint base
O cliente SHALL ser configurável com URL base da Voice API.

#### Scenario: Cliente usa URL padrão localhost
- **WHEN** cliente é instanciado sem parâmetros
- **THEN** usa `http://localhost:8765` como base URL

#### Scenario: Cliente usa URL customizada
- **WHEN** cliente é instanciado com `base_url="http://localhost:9999"`
- **THEN** usa URL customizada para todos os requests

### Requirement: Health check assíncrono
O cliente SHALL fornecer método para verificar se Voice API está ready.

#### Scenario: Cliente faz health check
- **WHEN** código SkyChat chama `await voice_client.health()`
- **THEN** cliente faz GET `/health`
- **AND** retorna objeto com status, progress, message, stage
- **AND** levanta exceção se API não responde

#### Scenario: Cliente aguarda API ficar ready
- **WHEN** código SkyChat chama `await voice_client.wait_until_ready()`
- **THEN** cliente poll `/health` a cada 100ms
- **AND** retorna quando status é "ready"
- **AND** levanta exceção após timeout de 60 segundos

### Requirement: Error handling estruturado
O cliente SHALL fornecer exceções específicas para diferentes falhas.

#### Scenario: Exceção para timeout
- **WHEN** request excede timeout configurado
- **THEN** cliente levanta `VoiceAPITimeoutError`

#### Scenario: Exceção para API unavailable
- **WHEN** health check retorna "error" ou conexão falha
- **THEN** cliente levanta `VoiceAPIUnavailableError`

#### Scenario: Exceção para request inválido
- **WHEN** API retorna 400 Bad Request
- **THEN** cliente levanta `VoiceAPIRequestError` com mensagem da API

### Requirement: Integração com existente TTSService
O cliente SHALL ser drop-in replacement para TTSService existente onde aplicável.

#### Scenario: Cliente tem interface similar ao TTSService
- **WHEN** código legado usa TTSService
- **THEN** VoiceAPIClient pode ser usado com mudanças mínimas
- **AND** métodos têm assinaturas compatíveis onde possível

> "Cliente bem-feito esconde a complexidade HTTP, não expõe" – made by Sky 🔌
