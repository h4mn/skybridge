## Why

O Chat SDK (Claude Agent SDK) usa **anyio task groups** que exigem cleanup na mesma task onde foram criados, mas o **@work decorator** do Textual cria tasks separadas em background. Isso causa `RuntimeError: Attempted to exit cancel scope in a different task`, bloqueando funcionalidades críticas como **TTS em paralelo** com o chat. A refatoração event-drive anterior (refactor-chat-event-driven) resolveu parcialmente, mas ainda limita o chat a processamento síncrono (UI bloqueada). A solução é isolar STT/TTS em um **processo separado** com API HTTP, permitindo concorrência real sem conflitos com o SDK.

## What Changes

- **Criar Voice API**: Processo Python separado servindo STT e TTS via HTTP (FastAPI/Starlette)
- **Mover serviços de voice**: STT (faster-whisper) e TTS (edge-tts) saem do processo principal
- **HTTP endpoints**: `POST /voice/stt` (audio → texto), `POST /voice/tts` (texto → audio streaming)
- **Health endpoint**: `GET /health` retornando status de startup (progress, stage, message) para integração com bootstrap
- **Cliente HTTP integrado**: `VoiceAPIClient` no SkyChat para consumir os endpoints
- **Enfileiramento TTS**: Fila interna na API para evitar overlap de streams (só um TTS por vez)
- **Streaming TTS**: Áudio começa a ser enviado antes de terminar de gerar (mais fluido)
- **Bootstrap integration**: Nova etapa no bootstrap que aguarda Voice API ficar ready, mostrando progresso visualmente
- **Model loading no startup**: Modelos carregados na inicialização da API (não sob demanda)

## Capabilities

### New Capabilities

- `voice-api`: Serviço HTTP isolado para STT (Speech-to-Text) e TTS (Text-to-Speech). Expõe endpoints REST para transcrição de áudio e síntese de voz com streaming.
- `voice-api-client`: Cliente HTTP assíncrono integrado ao SkyChat para consumir a Voice API. Abstrai a comunicação HTTP com retry e error handling.
- `voice-api-bootstrap`: Integração da Voice API com o sistema de bootstrap do SkyChat. Inicia o processo, poll health endpoint e mostra progresso de carregamento de modelos.

## Impact

- **Código afetado**: `src/core/sky/chat/textual_ui/screens/main.py` (remove chamadas diretas a STT/TTS), `bootstrap/` (nova etapa)
- **Novos componentes**: `voice_api/` (novo módulo raiz), `core/sky/voice/client.py`
- **Novo processo**: Python subprocess rodando Voice API independente
- **Dependencies**: FastAPI ou Starlette, httpx ou aiohttp, uvicorn
- **Sistemas**: Chat, TTS, STT, Bootstrap
- **Migração**: Retrocompatível mantida durante transição via feature flag
- **Performance**: Overhead HTTP ~2-10ms por request, mas ganho de paralelismo real

> "A melhor arquitetura é a que respeita as restrições do seu ecossistema" – made by Sky 🏗️
