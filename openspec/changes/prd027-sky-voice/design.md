# Design: Sky Voice - Arquitetura de Voz para a Sky

## Context

### Estado Atual
A Sky atualmente comunica apenas por texto via:
- **Chat CLI**: Interface textual com Rich/Textual
- **Textual TUI**: Interface moderna com header/footer, bubbles
- **RAG**: Busca semântica na memória permanente

### Motivação
Adicionar capacidades de voz para:
- **Acessibilidade**: Usuários com dificuldades visuais/motoras
- **Hands-free**: Comandos enquanto executa outras tarefas
- **Humanização**: Interface mais natural e conversacional

### Aprendizado PRD028 (YouTube)
O vídeo sobre MOSS-TTS mostrou:
- Modelos open source rodam localmente (sem custos)
- Interface web simples (Hugging Face)
- Qualidade comparável a serviços pagos
- Clonagem de voz é tecnicamente viável

### Restrições
- **Dependências**: MOSS-TTS requer Hugging Face, Whisper requer PyTorch
- **Performance**: Geração de áudio e transcrição têm latência
- **Storage**: Cache de áudio ocupa espaço em disco
- **Latency**: STT em tempo real requer processamento rápido

---

## Goals / Non-Goals

**Goals:**
1. Sky pode falar suas respostas (TTS)
2. Sky pode ouvir e transcrever (STT)
3. Modo conversacional completo (push-to-talk / always-on)
4. Integração transparente com chat existente
5. Suporte a múltiplos modelos (MOSS-TTS, ElevenLabs, Whisper)

**Non-Goals:**
- Reconhecimento de comandos complexos por voz (neste PRD)
- Síntese de voz em tempo real durante digitação
- Suporte a múltiplos idiomas simultâneos (PT-BR prioridade)
- Interface Web para voice chat (apenas CLI/TUI)

---

## Decisões

### D1: Escolha de Framework de Áudio
**Decisão:** sounddevice como framework de áudio para captura e reprodução.

**Justificativa:**
- **Manutenção ativa:** Ativamente desenvolvido (vs pyaudio parado desde 2017)
- **API Pythonica:** Simples e idiomática
- **Melhor streaming:** Suporte nativo a streams com callback
- **Callbacks simples:** Permite detectar silêncio em tempo real
- **Instalação:** `pip install sounddevice` funciona na maioria dos casos

**Alternativas consideradas:**
- pyaudio: ❌ Parado desde 2017, API verbosa, instalação problemática
- python-soundfile: ❌ Apenas leitura/escrita de arquivos, sem streaming

```python
import sounddevice as sd

# Exemplo: Callback para detecção de silêncio
def audio_callback(indata, frames, time, status):
    volume = np.max(np.abs(indata))
    if volume < SILENCE_THRESHOLD:
        silence_frames += 1
        if silence_frames > MAX_SILENCE_FRAMES:
            stop_recording()
    # Processa áudio...

stream = sd.InputStream(callback=audio_callback, samplerate=16000)
stream.start()
```

### D2: Estrutura de Módulos
**Decisão:** Criar novo módulo `src/core/sky/voice/` separado do chat.

**Justificativa:**
- **Separação de concerns**: Voz é um canal distinto de texto
- **Testabilidade:** Isolamento facilita testes unitários
- **Reuso:** Serviços de voz podem ser usados por outros componentes

**Alternativas consideradas:**
- Integrar diretamente em `chat/`: ❌ Acoplamento alto, difícil testar
- Módulo independente fora de Sky: ❌ Perderia contexto da Sky

```
src/core/sky/voice/
├── __init__.py
├── tts_service.py          # Text-to-Speech
├── stt_service.py          # Speech-to-Text
├── voice_chat.py           # Orquestrador
├── audio_capture.py        # sounddevice wrapper
└── audio_cache.py          # Cache de áudio
```

### D2: Escolha de Modelos TTS
**Decisão:** MOSS-TTS como padrão, com pluggable adapters para ElevenLabs.

**Justificativa:**
- **Open source**: Sem custos de API
- **Local**: Privacidade, baixa latência
- **Qualidade**: Comparável a serviços pagos

**Alternativas consideradas:**
- ElevenLabs apenas: ❌ Custoso, dependência de internet
- Coqui TTS: ❌ Menos maduro, menos vozes em PT-BR
- gTTS (Google): ❌ Qualidade inferior, requer internet

```python
class TTSService(ABC):
    @abstractmethod
    async def synthesize(self, text: str, voice: str) -> AudioData:
        pass

class MOSSTTSAdapter(TTSService):
    async def synthesize(self, text: str, voice: str) -> AudioData:
        # Chama MOSS-TTS via Hugging Face
        ...

class ElevenLabsAdapter(TTSService):
    async def synthesize(self, text: str, voice: str) -> AudioData:
        # Chama API ElevenLabs
        ...
```

### D3: Escolha de Modelos STT
**Decisão:** Whisper local (faster-whisper) como padrão.

**Justificativa:**
- **Open source**: Sem custos de API
- **Precisão**: SOTA em transcrição
- **Multi-idioma**: Suporta PT-BR nativamente

**Alternativas consideradas:**
- Whisper API (OpenAI): ❌ Custoso, latência de rede
- Google Speech-to-Text: ❌ Requer internet, menos preciso
- Vosk: ❌ Menos preciso em PT-BR

```python
class STTService(ABC):
    @abstractmethod
    async def transcribe(self, audio: AudioData) -> str:
        pass

class WhisperAdapter(STTService):
    def __init__(self):
        import faster_whisper
        self.model = faster_whisper.WhisperModel(
            "base",  # 74MB, bom tradeoff
            device="cpu",
            compute_type="int8"
        )
```

### D4: Modo de Operação
**Decisão:** Push-to-talk como padrão, always-on opcional.

**Justificativa:**
- **Privacidade**: Microfone só ativo quando usuário deseja
- **Controle**: Usuário sabe exatamente quando está sendo gravado
- **Performance**: Não processa silêncio desnecessário

**Alternativas consideradas:**
- Always-on apenas: ❌ Invasivo, processa silêncio
- Detecção de palavra-chave: ❌ Complexo, falsos positivos

### D5: Cache de Áudio
**Decisão:** Cache LRU em disco com TTL de 24h.

**Justificativa:**
- **Performance**: Textos repetidos não são reprocessados
- **Storage**: Disco é barato, CPU não
- **Simplicidade**: Python `functools.lru_cache` com `shelve` para persistência

```python
@lru_cache(maxsize=100)
def get_cached_audio(text_hash: str) -> Optional[AudioData]:
    # Verifica cache em disco
    ...

async def synthesize_with_cache(text: str) -> AudioData:
    text_hash = hashlib.md5(text.encode()).hexdigest()
    if cached := get_cached_audio(text_hash):
        return cached

    audio = await tts_service.synthesize(text)
    cache_audio(text_hash, audio)
    return audio
```

### D6: Integração com Chat
**Decisão:** Command pattern para `/voice`, `/tts` e `/stt`.

**Justificativa:**
- **Extensibilidade**: Fácil adicionar novos comandos de voz
- **Separação**: Chat não precisa saber detalhes de voz

**Implementação:**
```python
# src/core/sky/chat/commands/voice_commands.py
class VoiceCommandHandler:
    """Handler para comandos de voz no chat.

    Usa VoiceService singleton com lazy load.
    Implementa push-to-talk com ESPAÇO e toggle com /voice.
    """

    def __init__(self):
        self.voice_mode_active = False
        self.tts_responses = True  # TTS progressivo nas respostas
        self._voice_service = get_voice_service()

    async def handle_voice_toggle(self) -> bool:
        """Alterna modo conversacional."""
        self.voice_mode_active = not self.voice_mode_active
        return self.voice_mode_active

    async def handle_tts_toggle(self, state: bool | None = None) -> bool:
        """Alterna TTS progressivo nas respostas."""
        if state is None:
            self.tts_responses = not self.tts_responses
        else:
            self.tts_responses = state
        return self.tts_responses
```

---

## Arquitetura

### Fluxo de Dados

```
┌─────────────────────────────────────────────────────────────────────┐
│                         Voice Chat Flow                            │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  Usuário                                                       Sky  │
│    │                                                           ▲   │
│    │ fala───────────────┐                                       │   │
│    ▼                    │                                       │   │
│ ┌─────────┐          ┌─────────┐         ┌─────────┐         ┌───┴───┐│
│ │Microfone│─────────→│  STT    │─────────→│  Chat   │─────────→│  TTS  ││
│ │(sounddevice)│ áudio │ Whisper │  texto   │ClaudeSDK│  texto  │ MOSS  ││
│ └─────────┘          └─────────┘         └─────────┘         └───┬───┘│
│                                                           ▲           │   │   │
│                                                           │           │   │   │
│                                                    ┌──────────┘       │   │
│                                                    │ Cache        │   │
│                                                 ┌────┴──────┐        │   │
│                                                 │ Áudio .wav│◄───────┘   │
│                                                 └───────────┘             │
│                                                                            │
└────────────────────────────────────────────────────────────────────┘
```

### Componentes

**1. TTSService** (`tts_service.py`)
```python
class TTSService:
    """Serviço de Text-to-Speech com cache."""

    def __init__(self, adapter: TTSService):
        self.adapter = adapter  # MOSS-TTS ou ElevenLabs
        self.cache = AudioCache()

    async def speak(self, text: str, voice: str = "sky-female") -> None:
        """Gera e reproduz áudio do texto."""
        if audio := self.cache.get(text, voice):
            return self._play(audio)

        audio = await self.adapter.synthesize(text, voice)
        self.cache.put(text, voice, audio)
        return self._play(audio)
```

**2. STTService** (`stt_service.py`)
```python
class STTService:
    """Serviço de Speech-to-Text."""

    def __init__(self, model: str = "base"):
        self.model = faster_whisper.WhisperModel(model, device="cpu")

    async def listen(
        self,
        duration: float = 30.0,
        on_partial: Callable[[str], None] = None
    ) -> str:
        """Escuta e transcreve áudio."""
        audio_chunk = await self._record_audio(duration)
        result = self.model.transcribe(audio_chunk, language="pt")
        return result.text
```

**3. VoiceService** (`voice_service.py`)
```python
class VoiceService:
    """Orquestrador do chat por voz.

    Implementa singleton com lazy load para modelos.
    Integra TTS e STT com interface unificada.

    NOTA: Implementado como VoiceService ao invés de VoiceChat
    para refletir melhor o papel como serviço de infraestrutura.
    """

    def __init__(self, tts: TTSService, stt: STTService):
        self.tts = tts
        self.stt = stt
        self.voice_mode_active = False
        self.tts_responses = True  # TTS progressivo nas respostas

    async def speak(self, text: str) -> None:
        """Sintetiza e reproduz áudio do texto."""
        await self.tts.synthesize(text)

    async def record_and_transcribe(self, duration: float, language: str) -> str:
        """Grava áudio e retorna transcrição."""
        audio = await self._record_audio(duration)
        return await self.stt.transcribe(audio, language)

    def toggle_voice_mode(self) -> bool:
        """Alterna modo conversacional."""
        self.voice_mode_active = not self.voice_mode_active
        return self.voice_mode_active
```

---

## Risks / Trade-offs

### R1: Latência de STT
**Risco:** Transcrição em tempo real pode ter delay perceptível.

**Mitigação:**
- Usar `faster-whisper` (10x mais rápido que whisper original)
- Configurar timeout de silêncio agressivo (2-3 segundos)
- Mostrar indicador de "escutando..." para dar feedback visual

### R2: Qualidade de Voz
**Risco:** MOSS-TTS pode não soar natural em PT-BR.

**Mitigação:**
- Permitir configurar ElevenLabs como fallback
- Adicionar parâmetros de velocidade/pitch para ajustar
- Cache de vozes favoritas do usuário

### R3: Uso de CPU/Memória
**Risco:** Modelos de ML consomem muitos recursos.

**Mitigação:**
- Whisper "base" (74MB) ao invés de "large" (3GB)
- Quantização int8 para reduzir memória
- Unload de modelo após inatividade de 5 minutos

### R4: Privacidade
**Risco:** Gravação contínua de áudio pode ser invasiva.

**Mitigação:**
- Push-to-talk como padrão (microfone só ativo com tecla)
- Indicador visual claro (LED vermelho quando gravando)
- Áudio nunca é armazenado permanentemente
- Política de privacidade explícita no `/voice`

### R5: Dependências
**Risco:** Whisper e PyTorch são pacotes grandes.

**Mitigação:**
- Documentar requisitos claramente
- Oferecer versão "lite" sem STT (apenas TTS)
- Fornecer script de instalação automatizado

---

## Plano de Migração

### Fase 1: Infraestrutura (Sprint 1)
1. Instalar dependências (`pip install sounddevice faster-whisper torch numpy`)
2. Criar estrutura de diretórios `src/core/sky/voice/`
3. Implementar wrapper `audio_capture.py` com sounddevice
4. Implementar interfaces abstratas (TTSService, STTService)
5. Implementar MOSS-TTS adapter

### Fase 2: STT Básico (Sprint 2)
1. Implementar Whisper adapter
2. Integração com sounddevice (captura de microfone)
3. Callback para detecção de silêncio
4. Teste de transcrição standalone
5. Comando `/stt` para transcrição única

### Fase 3: TTS Básico (Sprint 3)
1. Implementar reprodução de áudio
2. Cache de áudio em disco
3. Comando `/tts <texto>` para teste
4. Integração com chat (`/voice`)

### Fase 4: Voice Chat Completo (Sprint 4)
1. Modo push-to-talk
2. Modo always-on (opcional)
3. Feedback visual (equalizador)
4. Indicadores sonoros

### Fase 5: Refinamento (Sprint 5)
1. Interrupção de fala
2. Comandos de voz nativos
3. Configuração de vozes
4. Histórico de conversas por voz

---

## Decisões Resolvidas

### D7: Nuvem vs Local
**Decisão:** Modelos locais apenas (MOSS-TTS, Whisper).

**Justificativa:**
- **Privacidade:** Áudio nunca sai da máquina
- **Custo zero:** Sem gastos com API
- **Latência:** Processamento local é mais rápido
- **Offline:** Funciona sem internet

**Escopo futuro:** Adicionar adapters para ElevenLabs/Whisper API como opcionais.

### D8: Multi-idioma
**Decisão:** Suporte a múltiplos idiomas desde o início, com PT-BR como padrão.

**Justificativa:**
- **Aprendizado:** Usuário quer usar Sky para aprender outros idiomas (ex: coreano)
- **Sky como tutor:** Sky pode ensinar/praticar outros idiomas
- **Detecção automática:** Whisper detecta idioma automaticamente

**Implementação:**
```python
# PT-BR como padrão, mas permite especificar
await stt_service.listen(language="pt")  # ou "auto" para detecção
await tts_service.speak("...", language="ko")  # coreano
```

### D9: Interface Web
**Decisão:** Deixar gancho arquitetural, mas fora do escopo inicial.

**Justificativa:**
- **sky.chat web:** Sky TUI será migrada para Web em breve
- **Web Speech API:** Navegadores modernos têm suporte nativo
- **Arquitetura preparada:** Interfaces abstratas permitem swap de implementação

**Gancho arquitetural:**
```python
# Interface abstrata permite swap de implementação
class AudioCapture(ABC):
    @abstractmethod
    def start_recording(self): pass

    @abstractmethod
    def stop_recording(self): pass

# Implementação CLI (atual)
class SoundDeviceCapture(AudioCapture):
    def start_recording(self):
        import sounddevice as sd
        ...

# Implementação Web (futura)
class WebSpeechCapture(AudioCapture):
    def start_recording(self):
        # Usa Web Speech API
        ...
```

---

## Open Questions

*Não há open questions pendentes.*

---

> "A arquitetura é a espinha dorsal da implementação" – made by Sky 🚀
