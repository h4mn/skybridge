## 1. Testes FIRST (Pré-requisito Crítico)

- [x] 1.1 Escrever teste E2E do fluxo atual (STT + TTS sem API)
- [ ] 1.2 Capturar baseline de performance (tempo médio de transcrição/síntese)
- [ ] 1.3 Documentar edge cases que funcionam hoje (para garantir regressão)
- [x] 1.4 Criar feature toggle `SKYBRIDGE_VOICE_API_ENABLED` (default: 0)

## 2. Setup - Estrutura de Módulos (Core)

- [x] 2.1 Criar `core/sky/voice/api/__init__.py`
- [x] 2.2 Criar `core/sky/voice/api/main.py` (entry point do processo)
- [x] 2.3 Criar `core/sky/voice/api/app.py` (Starlette app setup)
- [x] 2.4 Criar `core/sky/voice/api/endpoints/` (stt.py, tts.py, health.py)
- [x] 2.5 Criar `core/sky/voice/api/services/` (stt_service.py, tts_service.py)
- [x] 2.6 Criar `core/sky/voice/api/models.py` (DTOs para requests/responses)
- [x] 2.7 Criar `core/sky/voice/client.py` (VoiceAPIClient)
- [x] 2.8 Adicionar dependências: `starlette`, `httpx`, `uvicorn`, `python-multipart` (já instaladas?)
- [x] 2.9 Adicionar `core.sky.voice.api.main` em `pyproject.toml` como console script

## 3. Voice API - Health Endpoint

- [x] 2.1 Criar `core/sky/voice/api/__init__.py`
- [x] 2.2 Criar `core/sky/voice/api/main.py` (entry point do processo)
- [x] 2.3 Criar `core/sky/voice/api/app.py` (Starlette app setup)
- [x] 2.4 Criar `core/sky/voice/api/endpoints/` (stt.py, tts.py, health.py)
- [x] 2.5 Criar `core/sky/voice/api/services/` (stt_service.py, tts_service.py)
- [x] 2.6 Criar `core/sky/voice/api/models.py` (DTOs para requests/responses)
- [x] 2.7 Criar `core/sky/voice/client.py` (VoiceAPIClient)
- [x] 2.8 Adicionar dependências: `starlette`, `httpx`, `uvicorn`, `python-multipart` (já instaladas?)
- [x] 2.9 Adicionar `core.sky.voice.api.main` em `pyproject.toml` como console script

## 3. Voice API - Health Endpoint

- [x] 3.1 Criar `StartupStatus` enum (STARTING, LOADING_MODELS, READY, ERROR)
- [x] 3.2 Criar `HealthResponse` dataclass (status, progress, message, stage)
- [x] 3.3 Implementar `GET /health` retornando `HealthResponse`
- [x] 3.4 Criar `startup_state` global para rastrear progresso
- [ ] 3.5 Adicionar testes unitários do health endpoint
- [ ] 3.6 Testar health response durante cada estágio de startup

## 4. Voice API - STT Service (faster-whisper)

- [x] 4.1 Criar `STTService` em `core/sky/voice/api/services/stt_service.py`
- [x] 4.2 Implementar `load_model()` carregando faster-whisper base
- [x] 4.3 Implementar `transcribe(audio_bytes)` retornando texto (placeholder na POC)
- [x] 4.4 Adicionar tratamento de erros (formato inválido, áudio vazio)
- [x] 4.5 Atualizar `startup_state` durante carregamento do modelo
- [x] 4.6 Adicionar testes unitários do STTService (mock do modelo)
- [ ] 4.7 Adicionar teste de integração com modelo real (opcional, lento)

## 5. Voice API - STT Endpoint

- [x] 5.1 Criar `POST /voice/stt` endpoint em `core/sky/voice/api/endpoints/stt.py`
- [x] 5.2 Implementar parsing de multipart/form-data com áudio (POC usa base64)
- [x] 5.3 Chamar `STTService.transcribe()`
- [x] 5.4 Retornar `{"text": "..."}` como JSON
- [x] 5.5 Adicionar validação: arquivo vazio → 400, formato inválido → 400
- [x] 5.6 Adicionar testes do endpoint (usando TestClient Starlette)
- [x] 5.7 Testar com diferentes formatos de áudio (WAV, MP3, OGG)

## 6. Voice API - TTS Service (Kokoro)

- [x] 6.1 Criar `TTSService` em `core/sky/voice/api/services/tts_service.py`
- [x] 6.2 Implementar `initialize()` carregando KokoroAdapter (não edge-tts)
- [ ] 6.3 Implementar `TTSQueue` com `asyncio.Queue` (limite: 5 itens) - REMOVIDO do design
- [ ] 6.4 Implementar `_worker()` que consome a fila e gera áudio - REMOVIDO do design
- [x] 6.5 Implementar `synthesize(text, mode)` retornando bytes (não streaming)
- [ ] 6.6 Implementar `StreamingResponse` com SSE para chunks de áudio - REMOVIDO do design
- [ ] 6.7 Adicionar timeout de 5s para sair da fila (503 se expirar) - REMOVIDO do design
- [x] 6.8 Adicionar testes unitários do TTSService (mock do engine)
- [ ] 6.9 Adicionar teste de fila cheia (5+ requests → 503) - REMOVIDO do design

## 7. Voice API - TTS Endpoint

- [x] 7.1 Criar `POST /voice/tts` endpoint em `core/sky/voice/api/endpoints/tts.py`
- [x] 7.2 Implementar parsing de JSON request (`{"text": "...", "mode": "..."}`)
- [x] 7.3 Chamar `TTSService.synthesize()` e retornar bytes de áudio (não SSE)
- [x] 7.4 Adicionar header `Content-Type: audio/raw` com metadados
- [x] 7.5 Adicionar validação: texto vazio → 400, mode inválido → 400
- [x] 7.6 Retornar lista de vozes disponíveis em erro de voz inválida
- [x] 7.7 Adicionar testes do endpoint com resposta de áudio
- [x] 7.8 Testar cancelamento mid-stream (cliente fecha conexão)

## 8. Voice API - Startup Lifecycle

- [x] 8.1 Implementar `lifespan()` handler em `core/sky/voice/api/app.py`
- [x] 8.2 Carregar modelo STT no startup (atualiza health progress)
- [x] 8.3 Inicializar engine TTS (Kokoro) no startup (atualiza health progress)
- [ ] 8.4 Iniciar TTS worker background no startup - REMOVIDO do design
- [x] 8.5 Adicionar tratamento de erros no startup (marca status como ERROR)
- [x] 8.6 Adicionar testes do lifecycle (startup/shutdown)
- [x] 8.7 Testar tempo de startup (deve ser <30s em máquina típica)

## 9. Cliente HTTP - VoiceAPIClient

- [x] 9.1 Criar `core/sky/voice/client.py` com classe `VoiceAPIClient`
- [x] 9.2 Implementar `__init__(base_url)` com default `localhost:8765`
- [x] 9.3 Implementar `async stt(audio_bytes) -> str`
- [x] 9.4 Implementar `async tts(text, mode) -> bytes` (não streaming)
- [x] 9.5 Implementar `async health() -> HealthResponse`
- [x] 9.6 Implementar `async wait_until_ready(timeout=60)`
- [x] 9.7 Adicionar retry automático (3 tentativas para erros 5xx)
- [x] 9.8 Adicionar timeout configurável (default: 30s)
- [x] 9.9 Criar exceções customizadas: `VoiceAPITimeoutError`, `VoiceAPIUnavailableError`, `VoiceAPIRequestError`
- [ ] 9.10 Adicionar testes unitários do cliente (mock httpx)

## 10. Proof of Concept (POC) - Experimentação Integrada

> **Nota:** POC movido para cá pois depende de toda a estrutura API estar pronta.

- [x] 10.1 Criar estrutura de diretórios `core/sky/voice/`
- [x] 10.2 Criar `core/sky/voice/__init__.py` com exports públicos
- [x] 10.3 Criar `core/sky/voice/poc.py` (entry point interativo)
- [x] 10.4 Criar `core/sky/voice/api/` com estrutura básica
- [x] 10.5 Implementar health endpoint básico (`GET /health`)
- [x] 10.6 Implementar STT endpoint básico (`POST /voice/stt`)
- [x] 10.7 Implementar TTS endpoint básico (`POST /voice/tts`)
- [x] 10.8 Adicionar menu interativo no POC (testar STT, TTS, health, stats)
- [x] 10.9 Adicionar UTF-8 fix para Windows (emojis e acentos)
- [x] 10.10 Corrigir imports e singletons (get_stt_service, get_tts_service)
- [ ] 10.11 Testar POC manualmente: `python -m src.core.sky.voice.poc`
- [ ] 10.12 Ajustar timeouts/config baseado em experimentação
- [ ] 10.13 Validar latências, modelo STT e vozes TTS

## 11. Voice API - Main Entry Point

- [x] 11.1 Criar `core/sky/voice/api/main.py` com `main()` function
- [x] 11.2 Implementar parsing de argumentos (`--port`, `--host`, `--reload`, `--log-level`)
- [x] 11.3 Configurar Uvicorn para servir Starlette app
- [x] 11.4 Adicionar logging configurável
- [x] 11.5 Adicionar signal handlers para shutdown graciosos
- [ ] 11.6 Testar iniciar processo manualmente: `python -m src.core.sky.voice.api.main`

## 12. Bootstrap - VoiceAPIStage

- [x] 12.1 Criar `core/sky/bootstrap/stages/voice_api.py`
- [x] 12.2 Implementar `VoiceAPIStage(BootstrapStage)` herdando de `BootstrapStage`
- [x] 12.3 Implementar `execute()` iniciando subprocess da Voice API
- [x] 12.4 Implementar polling de `/health` a cada 100ms
- [x] 12.5 Atualizar `progress` e `message` visualmente
- [x] 12.6 Adicionar timeout de 120s para API ficar ready
- [x] 12.7 Adicionar retry (2 tentativas) se crashar no startup
- [ ] 12.8 Adicionar teste de integração do stage
- [ ] 12.9 Testar cenário de crash no startup

## 13. Bootstrap - Integração com Sistema

- [x] 13.1 Registrar `VoiceAPIStage` no bootstrap pipeline
- [x] 13.2 Adicionar condicional: só executa se feature flag enabled
- [x] 13.3 Passar URL da API para dependências via BootstrapContext
- [x] 13.4 Implementar cleanup no shutdown: SIGTERM → wait 5s → SIGKILL
- [x] 13.5 Adicionar logging de startup (pid, porta, status)
- [ ] 13.6 Testar bootstrap com feature flag ON e OFF
- [ ] 13.7 Testar shutdown graciosos e forçados

## 14. Integração - MainScreen

- [x] 14.1 Modificar `MainScreen` para usar `VoiceAPIClient` se feature flag ON
- [x] 14.2 Remover chamadas diretas a STT/TTS legado quando flag ON
- [x] 14.3 Implementar fallback: se API unavailable, mostra erro ao usuário
- [ ] 14.4 Adicionar teste A/B comparando old vs new implementation
- [ ] 14.5 Verificar que Chat SDK continua na main task (sem @work)

## 15. Testes Abrangentes

- [ ] 15.1 Testes E2E: Usuário fala → STT → Chat → TTS → Áudio
- [ ] 15.2 Teste de concorrência: Chat processa enquanto TTS fala
- [ ] 15.3 Teste de fila TTS: 3 requests simultâneos → sequencial
- [ ] 15.4 Teste de cancelamento: Usuário interrompe TTS mid-stream
- [ ] 15.5 Teste de crash recovery: Voice API crasha → SkyChat detecta
- [ ] 15.6 Teste de latência: medir overhead HTTP (deve ser <10ms)
- [ ] 15.7 Teste de stress: 100 requests STT/TTS sequenciais (sem leaks)
- [ ] 15.8 Verificar覆盖率 > 80% para novos componentes

## 16. Documentação

- [ ] 16.1 Atualizar `README.md` com instruções da Voice API
- [ ] 16.2 Criar `docs/architecture/voice-api.md` com diagramas
- [ ] 16.3 Documentar variáveis de ambiente (`SKYBRIDGE_VOICE_API_ENABLED`, `VOICE_API_PORT`)
- [ ] 16.4 Adicionar exemplos de uso do `VoiceAPIClient`
- [ ] 16.5 Documentar formato de requests/responses dos endpoints

## 17. Validação Final e Rollout

- [ ] 17.1 Executar testes: `pytest tests/unit/core/sky/voice/api/ tests/integration/core/sky/voice/api/`
- [ ] 17.2 Testar manualmente: Chat + TTS funcionando
- [ ] 17.3 Verificar que não há "cancel scope" error (objetivo principal!)
- [ ] 17.4 Medir performance: novo deve ter <5% de overhead vs baseline
- [ ] 17.5 Testar rollback: desabilitar feature flag → voltar ao legado
- [ ] 17.6 Testar crash: matar Voice API → SkyChat continua rodando
- [ ] 17.7 Documentar decisão final: (a) manter como opt-in, (b) default ON, ou (c) remover legado

## 18. Remoção de Código Legado (Opcional - Após Validação)

- [ ] 18.1 Remover `core/sy/voice/` (TTSService antigo)
- [ ] 18.2 Remover chamadas diretas a faster-whisper do MainScreen
- [ ] 18.3 Remover feature toggle (se decidido default ON)
- [ ] 18.4 Cleanup imports não utilizados
- [ ] 18.5 Atualizar documentação removendo referências ao legado
