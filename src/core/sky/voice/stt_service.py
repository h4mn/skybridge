"""
STT Service - Speech-to-Text para a Sky.

Este módulo define a interface abstrata para transcrição de áudio,
com suporte a múltiplos backends (Whisper, Whisper API, etc).
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import Enum
from typing import Optional, Callable

from core.sky.voice.audio_capture import AudioData


class STTModel(Enum):
    """Modelos de STT disponíveis."""

    WHISPER_LOCAL = "whisper-local"
    WHISPER_API = "whisper-api"
    VOSK = "vosk"


@dataclass
class TranscriptionConfig:
    """Configuração de transcrição.

    Attributes:
        language: Código do idioma (ex: "pt", "en", "auto" para detecção)
        model: Tamanho do modelo (tiny, base, small, medium, large)
        detect_language: Detectar idioma automaticamente
    """

    language: str = "pt"
    model: str = "base"
    detect_language: bool = False


@dataclass
class TranscriptionResult:
    """Resultado da transcrição.

    Attributes:
        text: Texto transcrito
        language: Idioma detectado
        confidence: Confiança da transcrição (0.0 a 1.0)
        duration: Duração do áudio transcrita
    """

    text: str
    language: str
    confidence: float = 0.0
    duration: float = 0.0


class STTService(ABC):
    """Interface abstrata para Speech-to-Text.

    Esta interface permite swap de implementação entre diferentes backends:
    - WhisperAdapter: Whisper local (open source)
    - WhisperAPIAdapter: Whisper API OpenAI (premium)
    - VoskAdapter: Vosk (alternativa leve)
    """

    def __init__(self, model: STTModel = STTModel.WHISPER_LOCAL):
        """Inicializa serviço STT.

        Args:
            model: Modelo de STT a ser usado
        """
        self.model = model

    @abstractmethod
    async def transcribe(
        self,
        audio: AudioData,
        config: Optional[TranscriptionConfig] = None,
    ) -> TranscriptionResult:
        """Transcreve áudio para texto.

        Args:
            audio: Dados de áudio para transcrever
            config: Configuração de transcrição (opcional)

        Returns:
            TranscriptionResult com texto transcrito
        """
        pass

    @abstractmethod
    async def listen(
        self,
        duration: float = 30.0,
        on_partial: Optional[Callable[[str], None]] = None,
        config: Optional[TranscriptionConfig] = None,
    ) -> TranscriptionResult:
        """Escuta microfone e transcreve.

        Args:
            duration: Duração máxima de gravação em segundos
            on_partial: Callback para transcrições parciais (streaming)
            config: Configuração de transcrição (opcional)

        Returns:
            TranscriptionResult com texto transcrito
        """
        pass


class WhisperAdapter(STTService):
    """Adapter para Whisper local (faster-whisper).

    Whisper é um modelo de transcrição da OpenAI
    com suporte a múltiplos idiomas, incluindo PT-BR.
    """

    def __init__(self, model_size: str = "base", device: str = "cpu"):
        """Inicializa adapter Whisper.

        Args:
            model_size: Tamanho do modelo (tiny, base, small, medium, large)
            device: Dispositivo de execução (cpu, cuda)
        """
        super().__init__(model=STTModel.WHISPER_LOCAL)
        self.model_size = model_size
        self.device = device
        self._model = None

    def _load_model(self):
        """Carrega modelo Whisper (lazy load)."""
        if self._model is None:
            try:
                from faster_whisper import WhisperModel

                self._model = WhisperModel(
                    self.model_size,
                    device=self.device,
                    compute_type="int8",  # Quantização para menor uso de memória
                )
            except ImportError as e:
                raise ImportError(
                    "faster-whisper não está instalado. "
                    "Execute: pip install faster-whisper"
                ) from e

    async def transcribe(
        self,
        audio: AudioData,
        config: Optional[TranscriptionConfig] = None,
    ) -> TranscriptionResult:
        """Transcreve áudio para texto."""
        config = config or TranscriptionConfig()
        self._load_model()

        # Prepara áudio para Whisper
        import numpy as np

        audio_array = np.frombuffer(audio.samples, dtype=np.float32)

        # Transcreve
        language = None if config.detect_language else config.language

        segments, info = self._model.transcribe(
            audio_array,
            language=language,
            beam_size=5,
        )

        # Combina todos os segmentos
        text_parts = []
        for segment in segments:
            text_parts.append(segment.text)

        full_text = "".join(text_parts).strip()

        return TranscriptionResult(
            text=full_text,
            language=info.language,
            confidence=info.language_probability,
            duration=audio.duration,
        )

    async def listen(
        self,
        duration: float = 30.0,
        on_partial: Optional[Callable[[str], None]] = None,
        config: Optional[TranscriptionConfig] = None,
    ) -> TranscriptionResult:
        """Escuta microfone e transcreve."""
        from core.sky.voice.audio_capture import SoundDeviceCapture

        capture = SoundDeviceCapture()

        # Captura áudio
        await capture.start_recording(
            on_audio_callback=lambda x: None,  # TODO: Implementar streaming
        )

        # Aguarda duração ou silêncio
        # TODO: Implementar detecção de silêncio
        import asyncio

        await asyncio.sleep(duration)

        audio = await capture.stop_recording()

        # Transcreve
        return await self.transcribe(audio, config)


class WhisperAPIAdapter(STTService):
    """Adapter para Whisper API da OpenAI.

    Usa a API OpenAI para transcrição em nuvem.
    """

    def __init__(self, api_key: str):
        """Inicializa adapter Whisper API.

        Args:
            api_key: Chave de API da OpenAI
        """
        super().__init__(model=STTModel.WHISPER_API)
        self.api_key = api_key

    async def transcribe(
        self,
        audio: AudioData,
        config: Optional[TranscriptionConfig] = None,
    ) -> TranscriptionResult:
        """Transcreve áudio via OpenAI API."""
        # TODO: Implementar chamada à API OpenAI
        raise NotImplementedError("Whisper API não implementada ainda")

    async def listen(
        self,
        duration: float = 30.0,
        on_partial: Optional[Callable[[str], None]] = None,
        config: Optional[TranscriptionConfig] = None,
    ) -> TranscriptionResult:
        """Escuta microfone e transcreve via API."""
        # TODO: Implementar captura + API call
        raise NotImplementedError("Não implementado ainda")
