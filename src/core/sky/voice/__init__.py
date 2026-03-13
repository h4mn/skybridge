"""
Sky Voice - Sistema de TTS/STT para a Sky.

Este módulo fornece capacidades de voz para a Sky:
- TTS (Text-to-Speech): Geração de fala a partir de texto
- STT (Speech-to-Text): Transcrição de áudio para texto
- Voice Chat: Interface conversacional completa

Example:
    >>> from src.core.sky.voice import TTSService, STTService, VoiceChat
    >>> tts = TTSService(adapter="moss-tts")
    >>> stt = STTService(model="whisper-base")
    >>> voice_chat = VoiceChat(tts=tts, stt=stt)
    >>> await voice_chat.activate()
"""

# Serviços principais (interfaces e adapters)
from src.core.sky.voice.tts_service import (
    TTSService,
    MOSSTTSAdapter,
    ElevenLabsAdapter,
    TTSModel,
    VoiceConfig,
)
from src.core.sky.voice.stt_service import (
    STTService,
    WhisperAdapter,
    WhisperAPIAdapter,
    STTModel,
    TranscriptionConfig,
    TranscriptionResult,
)
from src.core.sky.voice.voice_chat import (
    VoiceChat,
    VoiceMode,
    VoiceState,
    VoiceChatConfig,
)

# Captura de áudio
from src.core.sky.voice.audio_capture import (
    AudioCapture,
    SoundDeviceCapture,
    AudioData,
    AudioState,
)

# Cache de áudio
from src.core.sky.voice.audio_cache import (
    AudioCache,
    CacheEntry,
)

__all__ = [
    # TTS
    "TTSService",
    "MOSSTTSAdapter",
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
