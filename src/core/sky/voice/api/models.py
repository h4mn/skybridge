"""DTOs para requests/responses da Voice API."""

from enum import Enum
from dataclasses import dataclass
from typing import Optional


class StartupStatus(str, Enum):
    """Status do startup da Voice API."""
    STARTING = "starting"
    LOADING_MODELS = "loading_models"
    READY = "ready"
    ERROR = "error"


@dataclass
class HealthResponse:
    """Response do health endpoint."""
    status: StartupStatus
    progress: float  # 0.0 a 1.0
    message: str
    stage: Optional[str] = None  # "stt" | "tts" | None


@dataclass
class STTRequest:
    """Request para STT."""
    audio: bytes  # áudio em formato WAV
    language: str = "pt"  # idioma para transcrição


@dataclass
class STTResponse:
    """Response do STT."""
    text: str
    language: str
    duration: float  # segundos


@dataclass
class TTSRequest:
    """Request para TTS."""
    text: str
    voice: str = "pt-BR-FranciscaNeural"
    rate: str = "+0%"  # ajuste de taxa
    pitch: str = "+0Hz"  # ajuste de pitch
