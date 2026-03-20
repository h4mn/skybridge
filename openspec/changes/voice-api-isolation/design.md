## Context

**Estado Atual:**
O SkyChat usa Claude Agent SDK que depende de anyio task groups. Task groups anyio exigem cleanup na mesma task onde foram criados. O Textual `@work` decorator cria tasks separadas, causando `RuntimeError: Attempted to exit cancel scope in a different task`.

**Tentativa Anterior:**
A refatoração `refactor-chat-event-driven` implementou arquitetura event-driven, mas o @work precisou ser removido para evitar o erro. Resultado: processamento síncrono (UI bloqueada durante chat).

**Restrições:**
- Chat SDK DEVE rodar na main task (restrição anyio)
- Voice API NÃO pode compartilhar task groups com o SDK
- Streaming TTS precisa ser fluido (não block everything)
- Modelos de STT/TTS são pesados (demoram no startup)

## Goals / Non-Goals

**Goals:**
- Isolar STT/TTS em processo separado via API HTTP
- Permitir concorrência real: Chat SDK processa enquanto TTS fala
- Streaming TTS: áudio começa antes de terminar geração
- Bootstrap integrado: mostrar progresso de carregamento de modelos
- Fila TTS: evitar overlap de streams (só um fala por vez)

**Non-Goals:**
- Mover Chat SDK para fora da main task (fora do escopo)
- Suporte a múltiplos usuários simultâneos (single-user)
- Microserviço distribuído (local-only, mesma máquina)
- Persistência de audio (stream-only, sem storage)

## Decisions

### 1. Protocolo: HTTP + multipart/form-data

**Decisão:** Usar HTTP REST com `multipart/form-data` para transferência de áudio binário.

**Racional:**
| Opção | Vantagens | Desvantagens |
|-------|-----------|--------------|
| HTTP + JSON base64 | Simples | 33% overhead + encode/decode lento |
| **HTTP + multipart** | Zero encoding overhead | Parsing um pouco mais complexo |
| WebSocket | Streaming natural | Handshake overhead, mais complexo |
| gRPC | Ultra eficiente | Code generation, overkill |

**Alternativas rejeitadas:**
- JSON base64: 33% overhead em 1MB de áudio = inaceitável
- WebSocket: Handshake de 50ms compensa só para streaming contínuo
- gRPC: Overkill para API local, complexidade desnecessária

### 2. Framework: Starlette (não FastAPI)

**Decisão:** Usar **Starlette** puro, não FastAPI.

**Racional:**
- FastAPI adiciona OpenAPI, validation, docs – desnecessário para API local
- Starlette é o core do FastAPI, mesmas capacidades de routing/middleware
- Menos dependências, startup mais rápido
- Voice API é interna, não precisa de auto-documentação

### 3. Modelo STT: faster-whisper (já instalado)

**Decisão:** Manter **faster-whisper** (já usado em `stt_service.py`).

**Racional:**
- Já instalado e configurado no projeto
- Modelo "base" é bom suficiente (750MB, ~5-10s load)
- API simples: `transcribe(audio_bytes)` → texto
- Multi-idioma com suporte a pt-BR

### 4. Modelo TTS: Kokoro (já implementado)

**Decisão:** Usar **KokoroAdapter** existente em `core.sky.voice.tts_adapter`.

**Racional:**
- Já implementado e testado no projeto
- Voz feminina suave ("af_heart")
- Modelo compacto de 82M
- Multi-idioma com suporte a pt-BR
- API limpa: `synthesize()` retorna AudioData
- Suporte a VoiceMode (NORMAL, THINKING)

**Implementação existente:**
```python
from core.sky.voice import KokoroAdapter

tts = KokoroAdapter(voice="af_heart", lang_code="p")
audio_data = await tts.synthesize("Olá mundo")
# audio_data.samples = bytes de áudio
# audio_data.sample_rate = 24000
# audio_data.duration = segundos
```

### 3. Process Isolation: multiprocessing (não threading)

**Decisão:** Usar `multiprocessing.Process` para isolar completamente.

**Racional:**
```
multiprocessing                          threading
─────────────────                        ─────────────────
✅ Isolamento total de memória          ❌ Shared memory (lock issues)
✅ Crash na API não derruba UI          ❌ Exception propaga
✅ True parallelism (multi-core)        ❌ GIL limita
❌ Startup mais lento                   ✅ Startup rápido
❌ IPC overhead (HTTP já resolve)       ✅ Shared memory
```

**Trade-off:** Startup time vs isolamento. Escolhemos isolamento.

### 4. Modelo TTS: Kokoro (já implementado)

**Decisão:** Usar **KokoroAdapter** existente em `core.sky.voice.tts_adapter`.

**Racional:**
- Já implementado e testado no projeto
- Voz feminina suave ("af_heart")
- Modelo compacto de 82M
- Multi-idioma com suporte a pt-BR
- API limpa: `synthesize()` retorna AudioData
- Suporte a VoiceMode (NORMAL, THINKING)

**Implementação existente:**
```python
from core.sky.voice import KokoroAdapter

tts = KokoroAdapter(voice="af_heart", lang_code="p")
audio_data = await tts.synthesize("Olá mundo")
# audio_data.samples = bytes de áudio
# audio_data.sample_rate = 24000
# audio_data.duration = segundos
```

### 5. Streaming TTS: HTTP Response (não SSE)

**Decisão:** TTS endpoint usa HTTP response direto com bytes de áudio.

**Racional:**
- Kokoro gera áudio completo (não streaming)
- SSE desnecessário para resposta completa
- Cliente pode tocar progressivamente se quiser
- Mais simples que SSE

**Fluxo:**
```python
POST /voice/tts
Request: {"text": "Olá mundo", "mode": "normal"}
Response: Content-Type: audio/raw
          [bytes de áudio Kokoro - float32 @ 24000Hz]
```

### 6. Health Endpoint: Polling

**Decisão:** Bootstrap do SkyChat faz polling de `/health` a cada 100ms.

**Racional:**
- SSE/WebSocket é overkill para startup (one-time)
- Polling é simples e funciona
- 100ms = 10 checks/segundo, latência imperceptível

**Payload:**
```json
{
  "status": "starting" | "loading_models" | "ready" | "error",
  "progress": 0.5,
  "message": "Loading STT model...",
  "stage": "stt" | "tts"
}
```

### 7. Cliente HTTP: httpx (não aiohttp)

**Decisão:** Usar **httpx** para cliente assíncrono.

**Racional:**
- httpx: HTTP/1.1 + HTTP/2 support, async/sync same API
- aiohttp: HTTP/1.1 only, API diferente para sync
- httpx tem melhor ergonomia para retries/timeouts

## Arquitetura

```
┌─────────────────────────────────────────────────────────────────────────┐
│                    PROCESSO 1: SkyChat (Main)                           │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  ┌───────────────────────────────────────────────────────────────────┐  │
│  │  Bootstrap (polls /health até ready)                              │  │
│  │  ┌─────────────────────────────────────────────────────────────┐  │  │
│  │  │ VoiceAPIStage: aguarda models carregarem, mostra progresso   │  │  │
│  │  └─────────────────────────────────────────────────────────────┘  │  │
│  └───────────────────────────────────────────────────────────────────┘  │
│                              │                                          │
│                              ▼                                          │
│  ┌───────────────────────────────────────────────────────────────────┐  │
│  │  MainScreen (Textual UI)                                          │  │
│  │  ┌─────────────────────────────────────────────────────────────┐  │  │
│  │  │ ChatOrchestrator (anyio task groups OK!)                    │  │  │
│  │  │   - Processa chat na main task                              │  │  │
│  │  │   - Publica StreamChunkEvent                                │  │  │
│  │  └─────────────────────────────────────────────────────────────┘  │  │
│  │                              │                                     │  │
│  │  ┌─────────────────────────────────────────────────────────────┐  │  │
│  │  │ VoiceAPIClient (httpx async)                                │  │  │
│  │  │   POST /voice/stt (audio wav) → text                        │  │  │
│  │  │   POST /voice/tts (text) → SSE audio stream                 │  │  │
│  │  └─────────────────────────────────────────────────────────────┘  │  │
│  └───────────────────────────────────────────────────────────────────┘  │
│                                   │                                     │
└───────────────────────────────────┼─────────────────────────────────────┘
                                    │ HTTP (localhost:8765)
                                    │ multipart + SSE
┌───────────────────────────────────┼─────────────────────────────────────┐
│              PROCESSO 2: Voice API (Separado)                            │
│                         core/sky/voice/api/                              │
│                                   │                                     │
│  ┌───────────────────────────────┴────────────────────────────────────┐  │
│  │  Starlette App (port 8765)                                        │  │
│  │  ┌──────────────────────────────────────────────────────────────┐  │  │
│  │  │ POST /voice/stt                                              │  │  │
│  │  │   - Recebe audio (multipart)                                 │  │  │
│  │  │   - Transcreve com faster-whisper                            │  │  │
│  │  │   - Retorna {"text": "..."}                                  │  │  │
│  │  └──────────────────────────────────────────────────────────────┘  │  │
│  │  ┌──────────────────────────────────────────────────────────────┐  │  │
│  │  │ POST /voice/tts                                              │  │  │
│  │  │   - Recebe {"text": "...", "voice": "..."}                  │  │  │
│  │  │   - Enfileira na TTSQueue                                   │  │  │
│  │  │   - Retorna SSE stream de audio chunks                       │  │  │
│  │  └──────────────────────────────────────────────────────────────┘  │  │
│  │  ┌──────────────────────────────────────────────────────────────┐  │  │
│  │  │ GET /health                                                  │  │  │
│  │  │   - Retorna status, progress, stage                          │  │  │
│  │  └──────────────────────────────────────────────────────────────┘  │  │
│  └────────────────────────────────────────────────────────────────────┘  │
│                                         │                                 │
│  ┌──────────────────────────────────────┴─────────────────────────────┐  │
│  │  Startup (lifespan)                                                │  │
│  │  1. Carregar faster-whisper model (~500MB, ~5-10s)                  │  │
│  │  2. Inicializar edge-tts engine (~1s)                               │  │
│  │  3. Atualizar /health status durante loading                        │  │
│  └────────────────────────────────────────────────────────────────────┘  │
│                                         │                                 │
│  ┌──────────────────────────────────────┴─────────────────────────────┐  │
│  │  Background Workers                                                 │  │
│  │  ┌──────────────────────────────────────────────────────────────┐  │  │
│  │  │ TTSWorker                                                     │  │  │
│  │  │   - Consome TTSQueue                                          │  │  │
│  │  │   - Gera audio com edge-tts                                    │  │  │
│  │  │   - Faz streaming via SSE                                     │  │  │
│  │  └──────────────────────────────────────────────────────────────┘  │  │
│  └────────────────────────────────────────────────────────────────────┘  │
│                                                                         │
│  ┌─────────────────────────────────────────────────────────────────────┐  │
│  │  POC Entry Point: core/sky/voice/poc.py                           │  │
│  │  - Inicia API em subprocess                                        │  │
│  │  - Menu interativo para testar STT/TTS                             │  │
│  │  - Mostra logs e métricas                                          │  │
│  └─────────────────────────────────────────────────────────────────────┘  │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

## Risks / Trade-offs

### Risk 1: Startup time de modelos

**Risk:** faster-whisper model (~500MB) demora 5-10s para carregar. Usuario espera.

**Mitigation:**
- Health endpoint mostra progresso em tempo real
- Bootstrap exibe barra de progresso detalhada
- Modelos carregados apenas uma vez no startup (não a cada request)

### Risk 2: Latência HTTP

**Risk:** Overhead de HTTP pode degradar experiência de voz.

**Mitigation:**
- Multipart = zero encoding overhead
- Localhost = <1ms network latency
- Streaming TTS compensa: primeiro chunk sai rápido

### Risk 3: Voice API crash silencioso

**Risk:** Processo morre, SkyChat não percebe, TTS para de funcionar.

**Mitigation:**
- Health check contínuo a cada 30s após startup
- Se API crasha, mostrar erro visual ao usuario
- Restart automático do processo (opcional)

### Risk 4: Fila TTS enche

**Risk:** Muitos requests TTS enchem a fila, usuarios recebem 503.

**Mitigation:**
- Limite de 5 items na fila
- Timeout de 5s para sair da fila
- Cliente faz retry com backoff

## Estrutura de Módulos

### Localização: `core/sky/voice/`

Todo código da Voice API deve estar isolado dentro de `core/sky/voice/`:

```
core/sky/voice/
├── __init__.py           # Exports públicos
├── poc.py                # Ponto de entrada POC para experimentação
├── api/                  # Voice API (servidor HTTP)
│   ├── __init__.py
│   ├── app.py            # Starlette app setup
│   ├── main.py           # Entry point do processo
│   ├── endpoints/        # HTTP endpoints
│   │   ├── __init__.py
│   │   ├── stt.py        # POST /voice/stt
│   │   ├── tts.py        # POST /voice/tts
│   │   └── health.py     # GET /health
│   ├── services/         # Lógica de negócio
│   │   ├── __init__.py
│   │   ├── stt_service.py
│   │   └── tts_service.py
│   └── models.py         # DTOs (Request/Response)
├── client.py             # VoiceAPIClient (consumidor HTTP)
└── tests/                # Testes da Voice API
    ├── __init__.py
    ├── test_stt_service.py
    ├── test_tts_service.py
    └── test_endpoints.py
```

### Ponto de Entrada POC: `core/sky/voice/poc.py`

Antes de integrar com o SkyChat, o `poc.py` permite experimentar a Voice API isoladamente:

```python
# Uso direto para experimentação
python -m core.sky.voice.poc

# Funcionalidades do POC:
# 1. Inicia Voice API em subprocesso
# 2. Aguarda health status "ready"
# 3. Oferece menu interativo para testar:
#    - STT: gravar áudio e transcrever
#    - TTS: digitar texto e ouvir síntese
#    - Health: verificar status da API
#    - Stats: ver latência de requests
# 4. Mostra logs detalhados para debug
# 5. Permite testar cenários de erro (timeout, fila cheia, etc.)
```

**Benefícios do POC:**
- Valida arquitetura antes de integrar
- Permite ajustar latências/timeouts empiricamente
- Testa modelo STT e vozes TTS em isolamento
- Facilita debugging de problemas de voice sem UI Textual

## Migration Plan

### Fase 0: Proof of Concept (POC)
1. Criar estrutura `core/sky/voice/` com `poc.py`
2. Implementar endpoints STT/TTS/health básicos
3. Testar via POC interativo (sem SkyChat)
4. Validar latências, modelo STT e vozes TTS
5. Ajustar timeouts/config baseado em experimentação

### Fase 1: Implementação (feature flag OFF)
1. Implementar endpoints completos com fila TTS
2. Criar `VoiceAPIClient` em `core/sky/voice/client.py`
3. Adicionar `VoiceAPIStage` no bootstrap (desabilitado via flag)
4. Testes unitários e integração

### Fase 2: Enable e Validação
1. Feature flag `SKYBRIDGE_VOICE_API_ENABLED=1`
2. Testar chat + TTS simultâneos
3. Verificar que SDK não tem mais "cancel scope" error
4. Medir latência end-to-end

### Fase 3: Rollout
1. Default: flag OFF (código legado)
2. Usuários opt-in via flag
3. Monitorar bugs por 1 semana
4. Se estável, default: flag ON

### Fase 4: Remoção Legado
1. Manter flag por 2 semanas (rollback safety)
2. Remover código legado de STT/TTS do MainScreen
3. Remover feature flag
4. Cleanup: `core.sky.voice` modules obsoletos

### Rollback Strategy
- Se problemas: `SKYBRIDGE_VOICE_API_ENABLED=0`
- Volta instantâneo para código legado
- Nenhum dado é migrado (sem "breaking" data)

## Open Questions

1. **Modelo STT específico:** faster-whisper "base" ou "medium"? (trade-off: qualidade vs speed/memory)
2. **Porta fixa:** 8765 ou dinâmica? (se dinâmica, precisa descobrir no bootstrap)
3. **Restart automático:** Se Voice API crasha, SkyChat reinicia o processo ou mostra erro?
4. **Timeout TTS stream:** Quanto tempo esperar antes de cancelar stream travado?
5. **Audio device:** API toca áudio ou retorna bytes? (se toca, precisa access ao device)

> "Desenhamos a arquitetura para respeitar as restrições, não para lutar contra elas" – made by Sky 🏗️
