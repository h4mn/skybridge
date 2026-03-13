"""
Audio Capture - Interface abstrata para captura de áudio.

Este módulo define a interface para captura de áudio, permitindo
swap de implementação entre diferentes backends (sounddevice, Web Speech API, etc).
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import Enum
from typing import Callable, Optional


class AudioState(Enum):
    """Estados da captura de áudio."""

    IDLE = "idle"
    RECORDING = "recording"
    PROCESSING = "processing"
    STOPPED = "stopped"


@dataclass
class AudioData:
    """Dados de áudio capturado ou gerado.

    Attributes:
        samples: Array de amostras de áudio (numpy array ou bytes)
        sample_rate: Taxa de amostragem em Hz (ex: 16000 para 16kHz)
        channels: Número de canais (1=mono, 2=estéreo)
        duration: Duração em segundos
    """

    samples: bytes
    sample_rate: int
    channels: int = 1
    duration: float = 0.0

    def __post_init__(self):
        """Calcula duração se não fornecida."""
        if self.duration == 0.0 and self.sample_rate > 0:
            # Duração = bytes / (sample_rate * channels * bytes_per_sample)
            # Assumindo 16-bit (2 bytes por sample)
            bytes_per_second = self.sample_rate * self.channels * 2
            self.duration = len(self.samples) / bytes_per_second


class AudioCapture(ABC):
    """Interface abstrata para captura de áudio.

    Esta interface permite swap de implementação entre diferentes backends:
    - SoundDeviceCapture: Implementação local com sounddevice
    - WebSpeechCapture: Implementação Web futura (Web Speech API)
    - FileCapture: Implementação para testes (arquivos de áudio)
    """

    def __init__(self, sample_rate: int = 16000, channels: int = 1):
        """Inicializa captura de áudio.

        Args:
            sample_rate: Taxa de amostragem em Hz (padrão: 16000 para Whisper)
            channels: Número de canais (1=mono, 2=estéreo)
        """
        self.sample_rate = sample_rate
        self.channels = channels
        self.state = AudioState.IDLE

    @abstractmethod
    async def start_recording(
        self,
        on_audio_callback: Optional[Callable[[bytes], None]] = None,
        silence_threshold: float = 0.01,
        silence_timeout: float = 2.0,
    ) -> None:
        """Inicia gravação de áudio.

        Args:
            on_audio_callback: Callback chamado com chunks de áudio
            silence_threshold: Volume mínimo para detectar fala (0.0 a 1.0)
            silence_timeout: Segundos de silêncio antes de parar automaticamente
        """
        pass

    @abstractmethod
    async def stop_recording(self) -> AudioData:
        """Para gravação e retorna os dados capturados.

        Returns:
            AudioData com as amostras capturadas
        """
        pass

    @abstractmethod
    def is_recording(self) -> bool:
        """Verifica se está gravando.

        Returns:
            True se estiver gravando
        """
        pass

    @abstractmethod
    async def get_volume(self) -> float:
        """Retorna volume atual do microfone (0.0 a 1.0).

        Returns:
            Volume atual (0.0=silêncio, 1.0=máximo)
        """
        pass


class SoundDeviceCapture(AudioCapture):
    """Implementação de captura de áudio usando sounddevice.

    Esta é a implementação padrão para ambientes desktop/CLI.
    Para ambientes web, use WebSpeechCapture (futuro).
    """

    def __init__(self, sample_rate: int = 16000, channels: int = 1, device: Optional[int] = None):
        """Inicializa captura com sounddevice.

        Args:
            sample_rate: Taxa de amostragem em Hz
            channels: Número de canais
            device: Índice do dispositivo de áudio (None=padrão)
        """
        super().__init__(sample_rate, channels)
        self.device = device
        self._stream = None
        self._recorded_frames = []
        self._audio_callback = None
        self._silence_threshold = 0.01
        self._silence_timeout = 2.0
        self._silence_frames = 0
        self._import_sd()

    def _import_sd(self):
        """Importa sounddevice lazy (só quando necessário)."""
        try:
            import sounddevice as sd
            self._sd = sd
        except ImportError as e:
            raise ImportError(
                "sounddevice não está instalado. "
                "Execute: pip install sounddevice"
            ) from e

    async def start_recording(
        self,
        on_audio_callback: Optional[Callable[[bytes], None]] = None,
        silence_threshold: float = 0.01,
        silence_timeout: float = 2.0,
    ) -> None:
        """Inicia gravação de áudio."""
        import numpy as np

        self._audio_callback = on_audio_callback
        self._silence_threshold = silence_threshold
        self._silence_timeout = silence_timeout
        self._recorded_frames = []
        self._silence_frames = 0
        self.state = AudioState.RECORDING

        def callback(indata, frames, time, status):
            """Callback interno do sounddevice."""
            if status:
                print(f"Audio callback status: {status}", file=__import__("sys").stderr)

            # Calcula volume
            volume = float(np.max(np.abs(indata)))

            # Detecta silêncio
            if volume < self._silence_threshold:
                self._silence_frames += frames
            else:
                self._silence_frames = 0

            # Armazena frame
            audio_bytes = indata.tobytes()
            self._recorded_frames.append(audio_bytes)

            # Callback externo
            if self._audio_callback:
                self._audio_callback(audio_bytes)

        # Inicia stream
        self._stream = self._sd.InputStream(
            samplerate=self.sample_rate,
            channels=self.channels,
            dtype="float32",
            callback=callback,
            device=self.device,
        )
        self._stream.start()

    async def stop_recording(self) -> AudioData:
        """Para gravação e retorna dados capturados."""
        if self._stream is None:
            raise RuntimeError("Nenhuma gravação ativa")

        self._stream.stop()
        self._stream.close()
        self._stream = None
        self.state = AudioState.STOPPED

        # Combina todos os frames
        import numpy as np

        all_bytes = b"".join(self._recorded_frames)

        return AudioData(
            samples=all_bytes,
            sample_rate=self.sample_rate,
            channels=self.channels,
        )

    def is_recording(self) -> bool:
        """Verifica se está gravando."""
        return self.state == AudioState.RECORDING and self._stream is not None

    async def get_volume(self) -> float:
        """Retorna volume atual do microfone."""
        # Nota: sounddevice não tem API direta para volume
        # Este é um placeholder para implementação futura
        return 0.0


# TODO (futuro): WebSpeechCapture para integração Web
# class WebSpeechCapture(AudioCapture):
#     """Implementação usando Web Speech API (navegador)."""
#     pass
