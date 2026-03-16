# Sky Voice - Arquitetura

**Data:** 2026-03-14
**Status:** 🟢 Ativo
**Versão:** 0.1.0

## Visão Geral

O **Sky Voice** é o sistema de TTS/STT (Text-to-Speech / Speech-to-Text) da Sky, permitindo interação conversacional por voz.

### Tecnologias

| Componente | Tecnologia | Modelo | Performance |
|------------|-----------|--------|-------------|
| **TTS** | Kokoro-82M (Hexgrad) | 82M params | RTF 0.35x |
| **STT** | faster-whisper | base (74MB) | RTF 0.06x |

### Vozes

- **Kokoro af_heart**: Feminina, suave e natural (padrão)
- **Idiomas**: pt-BR (português brasileiro), en, es, fr, hi, it, ja

## Arquitetura

```
┌─────────────────────────────────────────────────────────────┐
│                       VoiceService                          │
│                   (Singleton + Lazy Load)                   │
│                                                              │
│  ┌─────────────────┐         ┌─────────────────┐           │
│  │  TTS (Kokoro)   │         │  STT (Whisper)  │           │
│  │  - af_voice     │         │  - base model   │           │
│  │  - lang_code='p'│         │  - device='cpu' │           │
│  │  - pt-BR        │         │  - auto-detect  │           │
│  └─────────────────┘         └─────────────────┘           │
└─────────────────────────────────────────────────────────────┘
         ↓                                  ↓
    AudioData                        TranscriptionResult
```

## Componentes

### VoiceService (Singleton)

Serviço centralizado com lazy load e cache.

**Métodos principais:**
```python
from core.sky.voice import get_voice_service

voice = get_voice_service()

# TTS - Texto para fala
await voice.speak("Olá mundo!")
audio = await voice.synthesize("Texto")

# STT - Fala para texto
text = await voice.transcribe(audio_data)
text = await voice.record_and_transcribe(5.0)  # 5s gravação

# Pré-carregamento (opcional)
await voice.preload_tts()
await voice.preload_stt()
await voice.preload_all()
```

**Propriedades:**
```python
voice.is_tts_ready  # bool
voice.is_stt_ready  # bool
voice.stats         # VoiceStats
```

### Adapters (Uso Avançado)

Para controle mais detalhado:

```python
from core.sky.voice import KokoroAdapter, VoiceConfig

tts = KokoroAdapter(voice="af_heart", lang_code="p")
config = VoiceConfig(speed=1.0, pitch=0, language="pt-BR")
audio = await tts.synthesize("Texto", config)
```

### Comandos do Chat

Integrados ao chat Sky:

- `/tts <texto>` - Falar texto
- `/stt` - Transcrever 5s de áudio
- `/voice` - Modo conversacional (futuro)

## Performance

### Lazy Load

Modelos são carregados apenas na primeira chamada:

```
Cold start (primeira vez):  ~3s carregamento + síntese
Warm start (modelo carregado):  ~2-5s síntese
Ganho: 8-10x mais rápido
```

### RTF (Real-Time Factor)

- **TTS**: RTF 0.35x (síntese mais rápida que tempo real)
- **STT**: RTF 0.06x (transcrição 16x mais rápido que tempo real)

### Exemplo

```
Texto: "Olá! Eu sou a Sky."
Duração áudio: 2.5s
Tempo síntese: 0.9s
RTF: 0.9 / 2.5 = 0.36x
```

## Configuração

### Variáveis de Ambiente

```bash
# .env
VOICE_TTS_ENGINE=kokoro
VOICE_TTS_VOICE=af_heart
VOICE_TTS_LANG=p
VOICE_STT_ENGINE=whisper
VOICE_STT_MODEL=base
```

### Config Code

```python
from core.sky.voice import VoiceConfig

config = VoiceConfig(
    speed=1.0,        # 0.5 a 2.0
    pitch=0,          # -10 a 10
    language="pt-BR"
)
```

## Guia de Uso

### Básico

```python
from core.sky.voice import get_voice_service

voice = get_voice_service()

# Falar texto
await voice.speak("Olá mundo!")

# Gravar e transcrever
text = await voice.record_and_transcribe(5.0)
```

### Com Callback

```python
# Sintetizar sem reproduzir
audio = await voice.synthesize("Texto")

# Salvar em arquivo
with open("output.wav", "wb") as f:
    f.write(audio.samples)
```

### Multi-idioma

```python
from core.sky.voice import KokoroAdapter

# Inglês
tts_en = KokoroAdapter(voice="af_heart", lang_code="a")

# Português
tts_pt = KokoroAdapter(voice="af_heart", lang_code="p")
```

## Bootstrap

O VoiceService não é carregado automaticamente no bootstrap. Use lazy load ou pré-carregue explicitamente:

```python
# Opcional: pré-carregar no startup
from core.sky.voice import get_voice_service

async def startup():
    voice = get_voice_service()
    await voice.preload_all()
```

## Referências

- [Kokoro GitHub](https://github.com/hexgrad/kokoro)
- [faster-whisper](https://github.com/SYSTRAN/faster-whisper)
- [PRD027 - Sky Voice](../prd/PRD027-sky-voice.md)

> "Voz natural, resposta rápida" – made by Sky 🎤🚀
