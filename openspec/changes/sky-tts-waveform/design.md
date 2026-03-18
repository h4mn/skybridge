# Design: Sky TTS + Waveform

## Context

O PRD027 já implementou infraestrutura de voz (Kokoro TTS + Whisper STT), mas:
- TTS fala tudo no final (não é progressivo)
- Sem feedback visual de áudio no SkyBubble
- Sem distinção entre modo normal e thinking

### Estado Atual
- `VoiceService` singleton com KokoroAdapter
- `_tts_worker` em `main.py` acumula tudo e fala no fim
- `SkyBubble` sem indicador de áudio

## Goals / Non-Goals

**Goals:**
- TTS progressivo (fala por sentença, não espera tudo)
- Interface abstrata para trocar backend TTS
- Modos de voz Normal e Thinking
- TopBar com waveform animada (só visível durante áudio)

**Non-Goals:**
- Substituir Kokoro por MOSS (só preparar gancho)
- Streaming TTS chunk-by-chunk (overkill)
- Novos modelos de voz

## Decisions

### D1: Interface Abstrata TTSAdapter

**Decisão:** Criar interface `TTSAdapter` com métodos `speak()` e `synthesize()`.

**Racional:** Permite trocar Kokoro por MOSS ou outro backend sem mudar código consumidor.

**Alternativas:**
- ❌ Manter KokoroAdapter direto: acoplamento forte
- ✅ Interface abstrata: flexibilidade futura

```python
class TTSAdapter(ABC):
    @abstractmethod
    async def speak(self, text: str, mode: VoiceMode) -> None: ...

    @abstractmethod
    async def synthesize(self, text: str, mode: VoiceMode) -> AudioData: ...
```

### D2: TTS Progressivo por Sentença

**Decisão:** Buffer de ~50 chars + detecção de pontuação final (`.!?`).

**Racional:** Balanceia latência inicial com naturalidade. Evita cortar palavras.

**Alternativas:**
- ❌ Chunk-by-chunk: overkill, sincronização complexa
- ❌ Falar tudo no final (atual): UX ruim, espera muda
- ✅ Por sentença: sweet spot entre simplicidade e UX

### D3: Hesitações no Texto (não no modelo)

**Decisão:** Modo Thinking adiciona hesitações via pré-processamento de texto.

**Racional:** Kokoro fala bem português real, mas soletra "hmm". Usar palavras reais ("hum", "deixa eu pensar").

**Alternativas:**
- ❌ Usar MOSS para thinking: dois modelos, inconsistência
- ❌ Pós-processamento de áudio: complexo
- ✅ Hesitações no texto: simples, funciona com Kokoro

### D4: WaveformTopBar com Height Reativo

**Decisão:** TopBar com `height: 0` por padrão, `height: 3` quando `.active`.

**Racional:** Não atrapalha leitura, só aparece durante áudio.

**Alternativas:**
- ❌ Sempre visível: polui UI
- ❌ Waveform em widget separado: não integra com SkyBubble
- ✅ Height reativo: melhor UX

### D5: Unicode para Waveform

**Decisão:** Usar caracteres Unicode `▀█` para animação.

**Racional:** Textual não suporta CSS keyframes. Unicode + timer funciona bem.

**Alternativas:**
- ❌ CSS animations: Textual não suporta
- ❌ Canvas/SVG: não aplicável em TUI
- ✅ Unicode bars: compatível, visual interessante

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                         MainScreen                              │
│  ┌───────────────────────────────────────────────────────────┐  │
│  │ _tts_worker                                               │  │
│  │   ├─ buffer: str                                          │  │
│  │   ├─ last_event_type: str                                 │  │
│  │   │                                                       │  │
│  │   └─ loop:                                                │  │
│  │       1. chunk = await queue.get()                        │  │
│  │       2. buffer += chunk                                  │  │
│  │       3. if len >= 50 && ends_in_punctuation:             │  │
│  │          - sky_bubble.start_speaking()                    │  │
│  │          - await tts.speak(buffer, mode)                  │  │
│  │          - sky_bubble.stop_waveform()                     │  │
│  └───────────────────────────────────────────────────────────┘  │
│                              │                                   │
│                              ▼                                   │
│  ┌───────────────────────────────────────────────────────────┐  │
│  │ Turn → SkyBubble                                          │  │
│  │   ├─ WaveformTopBar (height: 0/3)                         │  │
│  │   ├─ AgenticLoopPanel                                     │  │
│  │   └─ Markdown                                             │  │
│  └───────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
```

## Componentes

### VoiceModes
```python
class VoiceMode(Enum):
    NORMAL = "normal"      # speed=1.0, sem hesitações
    THINKING = "thinking"  # speed=0.85, hesitações

HESITATIONS = {
    "starters": ["deixa eu pensar...", "bom...", "hum...", ...],
    "post_tool_positive": ["legal...", "ótimo...", ...],
    "post_tool_surprise": ["nossa...", "olha só...", ...],
    ...
}
```

### WaveformTopBar
```python
class WaveformTopBar(Static):
    DEFAULT_CSS = """
    WaveformTopBar {
        height: 0;  /* oculto por padrão */
        transition: height 0.3s;
    }
    WaveformTopBar.active {
        height: 3;  /* visível quando falando */
    }
    """

    def start_speaking(self) -> None: ...
    def start_thinking(self) -> None: ...
    def stop(self) -> None: ...
```

## Risks / Trade-offs

| Risco | Mitigação |
|-------|-----------|
| Latência TTS em frases longas | Buffer máx 200 chars + split por pontuação |
| Hesitações soando artificiais | Lista curada de palavras Kokoro-friendly |
| Waveform não sincroniza com áudio | Timer independente, não precisa de sync |
| Troca de backend quebra API | Interface abstrata com testes |

## Migration Plan

1. **Fase 1**: Criar interface TTSAdapter + refatorar KokoroAdapter
2. **Fase 2**: Implementar VoiceModes + hesitações
3. **Fase 3**: Criar WaveformTopBar + integrar no SkyBubble
4. **Fase 4**: Refatorar _tts_worker para progressivo
5. **Fase 5**: Testes + documentação

**Rollback:** Cada fase é independente. Se problema, reverter commit específico.

> "Design é sobre decisões, não sobre detalhes" – made by Sky 🎨
