# Proposal: Sky Voice - TTS/STT para a Sky

## Why

A Sky atualmente comunica apenas por texto. Adicionar voz permitirá:
- **Acessibilidade**: Interação por voz para usuários com dificuldades visuais ou motoras
- **Hands-free**: Comandos e conversação enquanto o usuário faz outras tarefas
- **Humanização**: Interface mais natural e conversacional
- **Projetos de referência**: MOSS-TTS é open source e roda localmente (sem custos de API)

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
  - Modelos: MOSS-TTS (open source), ElevenLabs (premium), Coqui TTS
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

- **TTS**: MOSS-TTS (Hugging Face) ou ElevenLabs SDK
- **STT**: Whisper OpenAI (openai/whisper-local)
- **Áudio**: pyaudio, soundfile, numpy

### APIs Externas

- Hugging Face (MOSS-TTS)
- OpenAI Whisper (opcional, para STT em nuvem)

---

**Baseado em**: Aprendizado do vídeo MOSS-TTS (PRD028 - YouTube Integration)

> "A voz é a interface mais natural da inteligência" – made by Sky 🚀
