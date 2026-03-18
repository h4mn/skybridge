"""
Sky Voice - Sistema de TTS/STT para a Sky.

Este módulo fornece capacidades de voz para a Sky:
- TTS (Text-to-Speech): Geração de fala a partir de texto com Kokoro
- STT (Speech-to-Text): Transcrição de áudio para texto com Whisper
- VoiceService: Serviço singleton com lazy load e cache
- Voice Chat: Interface conversacional completa

Tecnologias:
- TTS: Kokoro-82M (Hexgrad) - voz feminina suave em pt-BR
- STT: Whisper base (faster-whisper) - transcrição rápida

Performance:
- RTF TTS: ~0.35x (síntese mais rápida que tempo real)
- RTF STT: ~0.06x (transcrição 16x mais rápido que tempo real)
- Lazy load: Modelos carregados sob demanda e mantidos em cache

Uso recomendado (singleton):
    >>> from core.sky.voice import get_voice_service
    >>> voice = get_voice_service()
    >>> await voice.speak("Olá mundo!")  # TTS
    >>> text = await voice.record_and_transcribe(5.0)  # STT

Uso avançado (adapters diretos):
    >>> from core.sky.voice import KokoroAdapter, VoiceConfig
    >>> tts = KokoroAdapter(voice="af_heart", lang_code="p")
    >>> audio = await tts.synthesize("Texto", VoiceConfig())
"""

# VoiceService (serviço singleton principal)
from core.sky.voice.voice_service import (
    VoiceService,
    VoiceStats,
    get_voice_service,
)

# Serviços principais (interfaces e adapters)
from core.sky.voice.tts_service import (
    TTSService,
    MOSSTTSAdapter,
    KokoroAdapter,
    Pyttsx3Adapter,
    ElevenLabsAdapter,
    TTSModel,
    VoiceConfig,
)
from core.sky.voice.stt_service import (
    STTService,
    WhisperAdapter,
    WhisperAPIAdapter,
    STTModel,
    TranscriptionConfig,
    TranscriptionResult,
)
from core.sky.voice.voice_chat import (
    VoiceChat,
    VoiceMode,
    VoiceState,
    VoiceChatConfig,
)

# Captura de áudio
from core.sky.voice.audio_capture import (
    AudioCapture,
    SoundDeviceCapture,
    AudioData,
    AudioState,
)

# Cache de áudio
from core.sky.voice.audio_cache import (
    AudioCache,
    CacheEntry,
)

__all__ = [
    # VoiceService (singleton principal)
    "VoiceService",
    "VoiceStats",
    "get_voice_service",
    # TTS
    "TTSService",
    "MOSSTTSAdapter",
    "KokoroAdapter",
    "Pyttsx3Adapter",
    "ElevenLabsAdapter",
    "TTSModel",
    "VoiceConfig",
    # STT
    "STTService",
    "WhisperAdapter",
    "WhisperAPIAdapter",
    "STTModel",
    "TranscriptionConfig",
    "TranscriptionResult",
    # Voice Chat
    "VoiceChat",
    "VoiceMode",
    "VoiceState",
    "VoiceChatConfig",
    # Audio Capture
    "AudioCapture",
    "SoundDeviceCapture",
    "AudioData",
    "AudioState",
    # Cache
    "AudioCache",
    "CacheEntry",
]

__version__ = "0.1.0"
