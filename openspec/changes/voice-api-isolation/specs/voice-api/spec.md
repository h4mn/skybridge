# Voice API Specification

Capability: `voice-api` - Serviço HTTP isolado para STT (Speech-to-Text) e TTS (Text-to-Speech)

## ADDED Requirements

### Requirement: Transcrição de áudio via endpoint STT
O sistema SHALL fornecer endpoint HTTP POST `/voice/stt` que recebe áudio e retorna texto transcrito.

#### Scenario: Transcrição bem-sucedida de áudio em português
- **WHEN** cliente envia POST `/voice/stt` com áudio WAV/portuguese via multipart/form-data
- **THEN** sistema retorna status 200 OK com JSON `{"text": "transcrição"}`
- **AND** tempo de resposta é menor que 10 segundos para áudio de 30 segundos

#### Scenario: Transcrição com formato de áudio inválido
- **WHEN** cliente envia POST `/voice/stt` com arquivo não-audio
- **THEN** sistema retorna status 400 Bad Request com erro descrevendo formato inválido

#### Scenario: Transcrição com áudio vazio
- **WHEN** cliente envia POST `/voice/stt` com áudio vazio ou silêncio
- **THEN** sistema retorna status 200 OK com `{"text": ""}`

### Requirement: Síntese de voz via endpoint TTS com streaming
O sistema SHALL fornecer endpoint HTTP POST `/voice/tts` que recebe texto e retorna stream de áudio via Server-Sent Events (SSE).

#### Scenario: Síntese bem-sucedida com streaming
- **WHEN** cliente envia POST `/voice/tts` com JSON `{"text": "Olá mundo", "voice": "pt-BR-FranciscaNeural"}`
- **THEN** sistema retorna status 200 OK com header `Content-Type: text/event-stream`
- **AND** primeiro chunk de áudio é enviado em menos de 500ms
- **AND** áudio é enviado em chunks sequenciais via SSE

#### Scenario: Síntese com texto vazio
- **WHEN** cliente envia POST `/voice/tts` com JSON `{"text": ""}`
- **THEN** sistema retorna status 400 Bad Request

#### Scenario: Síntese com voz não disponível
- **WHEN** cliente envia POST `/voice/tts` com JSON contendo voz inválida
- **THEN** sistema retorna status 400 Bad Request com lista de vozes disponíveis

### Requirement: Enfileiramento de TTS para evitar overlap
O sistema SHALL manter fila interna de requests TTS e processá-los sequencialmente.

#### Scenario: Múltiplos requests TTS são enfileirados
- **WHEN** três requests TTS são enviados simultaneamente
- **THEN** primeiro request é processado imediatamente
- **AND** segundo e terceiro aguardam na fila
- **AND** requests são processados em ordem FIFO

#### Scenario: Fila cheia retorna erro
- **WHEN** mais de 5 requests TTS aguardam na fila
- **THEN** novo request retorna status 503 Service Unavailable
- **AND** response inclui header `Retry-After: 5`

#### Scenario: Request cancelado antes de ser processado
- **WHEN** cliente cancela request (fecha conexão) enquanto aguarda na fila
- **THEN** sistema remove request da fila sem processar
- **AND** próximo request na fila avança

### Requirement: Health endpoint para status de startup
O sistema SHALL fornecer endpoint HTTP GET `/health` retornando status do serviço, progresso de carregamento e estágio atual.

#### Scenario: Health retorna status starting
- **WHEN** cliente faz GET `/health` durante inicialização
- **THEN** sistema retorna status 200 OK com JSON:
  ```json
  {
    "status": "starting",
    "progress": 0.0,
    "message": "Initializing...",
    "stage": null
  }
  ```

#### Scenario: Health retorna progresso durante carregamento de modelo STT
- **WHEN** cliente faz GET `/health` enquanto modelo STT carrega
- **THEN** sistema retorna status 200 OK com JSON:
  ```json
  {
    "status": "loading_models",
    "progress": 0.3,
    "message": "Loading STT model...",
    "stage": "stt"
  }
  ```

#### Scenario: Health retorna ready quando API está pronta
- **WHEN** cliente faz GET `/health` após conclusão do startup
- **THEN** sistema retorna status 200 OK com JSON:
  ```json
  {
    "status": "ready",
    "progress": 1.0,
    "message": "Voice API ready",
    "stage": null
  }
  ```

#### Scenario: Health retorna erro se startup falhar
- **WHEN** erro ocorre durante inicialização
- **THEN** sistema retorna status 503 Service Unavailable com JSON:
  ```json
  {
    "status": "error",
    "progress": 0.5,
    "message": "Failed to load STT model: out of memory",
    "stage": "stt"
  }
  ```

### Requirement: Carregamento de modelos no startup
O sistema SHALL carregar modelos STT e inicializar engine TTS durante startup, não sob demanda.

#### Scenario: Modelos são carregados na inicialização
- **WHEN** Voice API inicia
- **THEN** modelo faster-whisper é carregado em memória
- **AND** engine edge-tts é inicializada
- **AND** `/health` reflete progresso durante carregamento

#### Scenario: Requests após models loaded são rápidos
- **WHEN** cliente faz request após status `ready`
- **THEN** transcrição começa em menos de 100ms (modelo já carregado)
- **AND** síntese começa em menos de 50ms (engine já pronta)

### Requirement: Isolamento de processo
O sistema SHALL rodar em processo Python separado do processo principal SkyChat.

#### Scenario: Crash na Voice API não derruba SkyChat
- **WHEN** exceção não tratada ocorre na Voice API
- **THEN** processo Voice API termina
- **AND** SkyChat continua rodando
- **AND** SkyChat detecta crash via health check

#### Scenario: SkyChat pode reiniciar Voice API
- **WHEN** Voice API crasha e SkyChat detecta via health check
- **THEN** SkyChat pode reiniciar o processo da API
- **AND** novos requests funcionam após restart

### Requirement: Transferência de áudio sem overhead
O sistema SHALL usar multipart/form-data para transferência de áudio binário sem encoding overhead.

#### Scenario: Áudio é enviado sem base64 encoding
- **WHEN** cliente envia áudio WAV de 1MB via multipart/form-data
- **THEN** payload HTTP tem aproximadamente 1MB + headers (sem +33% de base64)
- **AND** tempo de processamento não inclui decode de base64

> "Specs são o contrato: o que prometemos que o sistema faz" – made by Sky 📋
