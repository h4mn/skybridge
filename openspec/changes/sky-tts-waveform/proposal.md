# Sky TTS + Waveform

## Why

A Sky precisa de feedback de áudio natural durante conversas, com indicação visual de quando está falando ou pensando. Atualmente o TTS fala tudo no final (alta latência) e não há indicação visual de áudio ativo.

## What Changes

- **TTS Progressivo**: Falar por sentença/frase ao invés de acumular tudo
- **Modos de Voz**: Normal (fluido) e Thinking (com hesitações naturais)
- **Interface Abstrata**: TTSAdapter para permitir troca de backend (Kokoro → MOSS)
- **TopBar Waveform**: Barra animada de 3 linhas no topo do SkyBubble
- **Waveform Reativa**: Aparece apenas durante áudio ativo (não atrapalha leitura)

## Capabilities

### New Capabilities

- `tts-adapter`: Interface abstrata para backends TTS (KokoroAdapter, MOSSAdapter)
- `tts-progressive`: Worker que fala por sentença com buffer e detecção de pontuação
- `voice-modes`: Modos Normal (speed=1.0) e Thinking (speed=0.85 + hesitações)
- `waveform-topbar`: TopBar animada de 3 linhas com height reativo (0 → 3)

### Modified Capabilities

- `sky-bubble`: Adicionar WaveformTopBar integrado com API start_speaking/stop
- `main-screen`: Modificar _tts_worker para TTS progressivo com controle de waveform

## Impact

### Arquivos Modificados
- `src/core/sky/voice/tts_service.py` - Adicionar TTSAdapter interface
- `src/core/sky/voice/voice_service.py` - Suporte a VoiceMode
- `src/core/sky/chat/textual_ui/widgets/bubbles/sky_bubble.py` - WaveformTopBar
- `src/core/sky/chat/textual_ui/screens/main.py` - _tts_worker progressivo

### Novos Arquivos
- `src/core/sky/voice/tts_adapter.py` - Interface abstrata + KokoroAdapter
- `src/core/sky/voice/voice_modes.py` - VoiceMode enum + hesitações
- `src/core/sky/chat/textual_ui/widgets/bubbles/waveform_topbar.py` - Widget de waveform

### Dependências
- Nenhuma dependência nova (Kokoro já instalado via PRD027)

> "A voz é a alma da IA, o visual é sua expressão" – made by Sky 🎙️
