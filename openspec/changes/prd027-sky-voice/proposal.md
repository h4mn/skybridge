# Proposal: Sky Voice - TTS/STT para a Sky

## Why

A Sky atualmente comunica apenas por texto. Adicionar voz permitirá:
- **Acessibilidade**: Interação por voz para usuários com dificuldades visuais ou motoras
- **Hands-free**: Comandos e conversação enquanto o usuário faz outras tarefas
- **Humanização**: Interface mais natural e conversacional
- **Projetos de referência**: Kokoro-82M e Whisper são open source e rodam localmente (sem custos de API)

## What Changes

Adicionar capacidades de voz à Sky:

- **TTS (Text-to-Speech)**: Sky fala suas respostas em voz sintética
- **STT (Speech-to-Text)**: Sky ouve e transcreve o áudio do usuário
- **Clonagem de voz** (opcional): Sky pode adotar vozes personalizadas
- **Integração Chat**: Comando `/voice` para ativar modo conversacional

**BREAKING**: Nenhuma - é uma adição, não substituição

## Capabilities

### New Capabilities

- `sky-tts`: Geração de fala a partir de texto
  - **Padrão**: Kokoro-82M (Hexgrad) - voz feminina natural em pt-BR
  - Alternativas: MOSS-TTS, Pyttsx3 (offline), ElevenLabs (premium)
  - Configuração: voz, velocidade, pitch
  - Cache de áudio gerado

- `sky-stt`: Transcrição de áudio para texto
  - Whisper (OpenAI) local ou via API
  - Detecção de idioma (PT-BR prioridade)
  - Streaming vs batch

- `sky-voice-chat`: Interface conversacional
  - Modo push-to-talk ou always-on
  - Interrupção de fala
  - Feedback visual (onda sonora, equalizador)

### Modified Capabilities

Nenhuma - as capacidades existentes (chat, RAG, etc.) permanecem iguais

## Impact

### Código Afetado

- **Novo**: `src/core/sky/voice/`
  - `tts_service.py` - Serviço Text-to-Speech
  - `stt_service.py` - Serviço Speech-to-Text
  - `voice_chat.py` - Orquestrador do chat por voz

- **Modificar**: `src/core/sky/chat/`
  - Integração com serviços de voz
  - Comando `/voice` para alternar modo

### Dependências

- **TTS**: Kokoro-82M (biblioteca standalone), MOSS-TTS (alternativa), ElevenLabs SDK (premium)
- **STT**: Whisper OpenAI (faster-whisper local)
- **Áudio**: sounddevice, soundfile, numpy

### APIs Externas

- Hexgrad/Kokoro-82M (Hugging Face - download automático)
- OpenAI Whisper (opcional, para STT em nuvem)

---

**Baseado em**: Aprendizado do vídeo MOSS-TTS (PRD028 - YouTube Integration)

> "A voz é a interface mais natural da inteligência" – made by Sky 🚀
