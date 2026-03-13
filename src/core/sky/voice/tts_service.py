"""
TTS Service - Text-to-Speech para a Sky.

Este módulo define a interface abstrata para síntese de voz,
com suporte a múltiplos backends (MOSS-TTS, ElevenLabs, etc).
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import Enum
from typing import Optional

from src.core.sky.voice.audio_capture import AudioData


class TTSModel(Enum):
    """Modelos de TTS disponíveis."""

    MOSS_TTS = "moss-tts"
    ELEVENLABS = "elevenlabs"
    COQUI_TTS = "coqui-tts"


@dataclass
class VoiceConfig:
    """Configuração de voz para TTS.

    Attributes:
        voice_id: Identificador da voz (ex: "sky-female", "sky-male")
        speed: Velocidade da fala (0.5=lento, 1.0=normal, 2.0=rápido)
        pitch: Ajuste de pitch em semitons (-12=grave, 0=normal, +12=agudo)
        language: Código do idioma (ex: "pt-BR", "en")
    """

    voice_id: str = "sky-female"
    speed: float = 1.0
    pitch: int = 0
    language: str = "pt-BR"

    def validate(self) -> None:
        """Valida parâmetros de configuração."""
        if not 0.5 <= self.speed <= 2.0:
            raise ValueError(f"Speed deve estar entre 0.5 e 2.0, got {self.speed}")
        if not -12 <= self.pitch <= 12:
            raise ValueError(f"Pitch deve estar entre -12 e +12, got {self.pitch}")


class TTSService(ABC):
    """Interface abstrata para Text-to-Speech.

    Esta interface permite swap de implementação entre diferentes backends:
    - MOSSTTSAdapter: MOSS-TTS via Hugging Face (open source)
    - ElevenLabsAdapter: ElevenLabs API (premium)
    - CoquiTTSAdapter: Coqui TTS (alternativa open source)
    """

    def __init__(self, model: TTSModel = TTSModel.MOSS_TTS):
        """Inicializa serviço TTS.

        Args:
            model: Modelo de TTS a ser usado
        """
        self.model = model

    @abstractmethod
    async def synthesize(
        self,
        text: str,
        config: Optional[VoiceConfig] = None,
    ) -> AudioData:
        """Sintetiza áudio a partir do texto.

        Args:
            text: Texto para ser falado
            config: Configuração de voz (opcional)

        Returns:
            AudioData com o áudio gerado
        """
        pass

    @abstractmethod
    async def speak(
        self,
        text: str,
        config: Optional[VoiceConfig] = None,
    ) -> None:
        """Sintetiza e reproduz áudio.

        Args:
            text: Texto para ser falado
            config: Configuração de voz (opcional)
        """
        pass

    @abstractmethod
    def get_available_voices(self) -> list[str]:
        """Retorna lista de vozes disponíveis.

        Returns:
            Lista de voice_ids disponíveis
        """
        pass


class MOSSTTSAdapter(TTSService):
    """Adapter para MOSS-TTS via Hugging Face.

    MOSS-TTS é um modelo open source de alta qualidade
    para síntese de voz em múltiplos idiomas.
    """

    def __init__(self, voice: str = "sky-female"):
        """Inicializa adapter MOSS-TTS.

        Args:
            voice: Voz padrão a ser usada
        """
        super().__init__(model=TTSModel.MOSS_TTS)
        self.voice = voice
        self._model = None
        self._import_transformers()

    def _import_transformers(self):
        """Importa transformers lazy (só quando necessário)."""
        try:
            from transformers import AutoModelForTextToSpectrogram, AutoProcessor
            self._AutoModel = AutoModelForTextToSpectrogram
            self._AutoProcessor = AutoProcessor
        except ImportError as e:
            raise ImportError(
                "transformers não está instalado. "
                "Execute: pip install transformers"
            ) from e

    async def _load_model(self):
        """Carrega modelo MOSS-TTS."""
        if self._model is None:
            # TODO: Carregar modelo específico do MOSS-TTS
            # Por enquanto, placeholder
            pass

    async def synthesize(
        self,
        text: str,
        config: Optional[VoiceConfig] = None,
    ) -> AudioData:
        """Sintetiza áudio a partir do texto."""
        config = config or VoiceConfig()
        config.validate()

        await self._load_model()

        # TODO: Implementar síntese real com MOSS-TTS
        # Por enquanto, retorna placeholder
        raise NotImplementedError("MOSS-TTS síntese não implementada ainda")

    async def speak(
        self,
        text: str,
        config: Optional[VoiceConfig] = None,
    ) -> None:
        """Sintetiza e reproduz áudio."""
        audio = await self.synthesize(text, config)
        await self._play_audio(audio)

    async def _play_audio(self, audio: AudioData) -> None:
        """Reproduz áudio usando sounddevice."""
        try:
            import sounddevice as sd
            import numpy as np

            # Converte bytes para numpy array
            samples = np.frombuffer(audio.samples, dtype=np.float32)

            sd.play(samples, samplerate=audio.sample_rate)
            sd.wait()  # Aguarda fim da reprodução
        except ImportError:
            raise ImportError("sounddevice não está instalado")

    def get_available_voices(self) -> list[str]:
        """Retorna vozes disponíveis."""
        return ["sky-female", "sky-male"]


class ElevenLabsAdapter(TTSService):
    """Adapter para ElevenLabs API.

    ElevenLabs é um serviço premium de alta qualidade
    para síntese de voz.
    """

    def __init__(self, api_key: str, voice: str = "sky-female"):
        """Inicializa adapter ElevenLabs.

        Args:
            api_key: Chave de API da ElevenLabs
            voice: Voz padrão a ser usada
        """
        super().__init__(model=TTSModel.ELEVENLABS)
        self.api_key = api_key
        self.voice = voice

    async def synthesize(
        self,
        text: str,
        config: Optional[VoiceConfig] = None,
    ) -> AudioData:
        """Sintetiza áudio via ElevenLabs API."""
        # TODO: Implementar chamada à API ElevenLabs
        raise NotImplementedError("ElevenLabs API não implementada ainda")

    async def speak(
        self,
        text: str,
        config: Optional[VoiceConfig] = None,
    ) -> None:
        """Sintetiza e reproduz áudio."""
        audio = await self.synthesize(text, config)
        await self._play_audio(audio)

    async def _play_audio(self, audio: AudioData) -> None:
        """Reproduz áudio usando sounddevice."""
        try:
            import sounddevice as sd
            import numpy as np

            samples = np.frombuffer(audio.samples, dtype=np.float32)
            sd.play(samples, samplerate=audio.sample_rate)
            sd.wait()
        except ImportError:
            raise ImportError("sounddevice não está instalado")

    def get_available_voices(self) -> list[str]:
        """Retorna vozes disponíveis na ElevenLabs."""
        # TODO: Buscar vozes disponíveis via API
        return []
