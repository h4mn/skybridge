"""STT Service - Speech-to-Text usando faster-whisper."""

import asyncio
from typing import Optional
from dataclasses import dataclass

from core.sky.voice.api.models import StartupStatus


# Estado global de startup (compartilhado entre serviços)
@dataclass
class StartupState:
    """Estado global do startup da Voice API."""
    status: StartupStatus = StartupStatus.STARTING
    progress: float = 0.0
    message: str = "Initializing..."
    stage: Optional[str] = None
    error: Optional[str] = None


startup_state = StartupState()


# Exceções customizadas para STT
class STTError(Exception):
    """Erro base do STT Service."""
    pass


class InvalidAudioFormatError(STTError):
    """Formato de áudio inválido."""
    pass


class AudioTooShortError(STTError):
    """Áudio muito curto para transcrição."""
    pass


class AudioEmptyError(STTError):
    """Áudio vazio."""
    pass


class STTModelNotReadyError(STTError):
    """Modelo STT não está carregado."""
    pass


class STTService:
    """Serviço de Speech-to-Text usando faster-whisper."""

    def __init__(self):
        self._model = None
        self._lock = asyncio.Lock()

    async def load_model(self) -> None:
        """Carrega o modelo faster-whisper (lazy load)."""
        if self._model is not None:
            return

        async with self._lock:
            # Double-check
            if self._model is not None:
                return

            startup_state.stage = "stt"
            startup_state.status = StartupStatus.LOADING_MODELS
            startup_state.message = "Loading STT model..."
            startup_state.progress = 0.3

            # Import aqui para lazy loading
            from faster_whisper import WhisperModel

            # Carrega modelo base (menor, mais rápido)
            self._model = WhisperModel(
                "base",
                device="cpu",
                compute_type="int8"
            )

            startup_state.progress = 0.5
            startup_state.message = "STT model loaded"

    async def transcribe(self, audio_bytes: bytes) -> str:
        """Transcreve áudio para texto.

        Args:
            audio_bytes: Áudio em float32 bytes (16kHz mono)

        Returns:
            Texto transcrito

        Raises:
            AudioEmptyError: Se áudio estiver vazio
            AudioTooShortError: Se áudio for muito curto (< 0.3s)
            InvalidAudioFormatError: Se formato for inválido
            STTError: Se erro ocorrer durante transcrição
        """
        # Validações de entrada
        if not audio_bytes:
            raise AudioEmptyError("Áudio vazio fornecido para transcrição")

        if len(audio_bytes) < 100:  # Menos de 100 bytes é inválido
            raise InvalidAudioFormatError(
                f"Áudio muito pequeno ({len(audio_bytes)} bytes): formato inválido"
            )

        # Carrega modelo se necessário
        if self._model is None:
            await self.load_model()

        import numpy as np

        try:
            # Converte bytes para numpy array float32
            audio_array = np.frombuffer(audio_bytes, dtype=np.float32)
        except (ValueError, TypeError) as e:
            raise InvalidAudioFormatError(
                f"Não foi possível decodificar áudio como float32: {e}"
            ) from e

        # Verifica se há áudio suficiente (mínimo 0.3 segundos @ 16kHz)
        min_samples = 4800  # 0.3s @ 16kHz
        if len(audio_array) < min_samples:
            raise AudioTooShortError(
                f"Áudio muito curto: {len(audio_array)/16000:.2f}s (mínimo: 0.3s)"
            )

        # Usa faster-whisper para transcrever
        # Executa em thread separada para não bloquear o event loop
        def transcribe_sync():
            try:
                segments, info = self._model.transcribe(
                    audio_array,
                    language="pt",  # pt-BR
                    beam_size=5,
                    vad_filter=True,
                    vad_parameters={
                        "min_silence_duration_ms": 100,
                        "speech_pad_ms": 30
                    }
                )

                # Concatena todos os segmentos de texto
                text_parts = []
                for segment in segments:
                    if segment.text.strip():
                        text_parts.append(segment.text.strip())

                return " ".join(text_parts)

            except Exception as e:
                raise STTError(f"Erro durante transcrição: {e}") from e

        # Executa transcrição em thread separada (CPU-intensive)
        try:
            result = await asyncio.to_thread(transcribe_sync)
        except STTError:
            raise  # Re-leva STTError
        except Exception as e:
            raise STTError(f"Erro ao executar transcrição: {e}") from e

        if not result:
            return ""  # Retorna vazio se nenhuma fala detectada

        return result

    async def health(self) -> dict:
        """Retorna status do serviço."""
        return {
            "model_loaded": self._model is not None,
            "stage": "stt"
        }


# Singleton instance
_stt_service: STTService | None = None


def get_stt_service() -> STTService:
    """Retorna a instância singleton do STTService."""
    global _stt_service
    if _stt_service is None:
        _stt_service = STTService()
    return _stt_service
