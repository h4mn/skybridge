"""TTS Service - Text-to-Speech usando KokoroAdapter existente."""

import asyncio
from typing import AsyncGenerator, Optional

from core.sky.voice.api.models import StartupStatus, HealthResponse
from core.sky.voice.api.services.stt_service import startup_state
from core.sky.voice.tts_adapter import KokoroAdapter, VoiceMode


class TTSRequest:
    """Request interno para TTS."""
    def __init__(self, text: str, mode: VoiceMode = VoiceMode.NORMAL):
        self.text = text
        self.mode = mode


class TTSService:
    """Serviço de Text-to-Speech usando KokoroAdapter existente."""

    QUEUE_SIZE_LIMIT = 5
    QUEUE_TIMEOUT = 5.0  # segundos

    def __init__(self):
        self._adapter: KokoroAdapter | None = None
        self._queue: asyncio.Queue[TTSRequest] = asyncio.Queue(maxsize=self.QUEUE_SIZE_LIMIT)
        self._worker_task: Optional[asyncio.Task] = None
        self._lock = asyncio.Lock()

    async def initialize(self) -> None:
        """Inicializa o KokoroAdapter."""
        if self._adapter is not None:
            return

        async with self._lock:
            if self._adapter is not None:
                return

            startup_state.stage = "tts"
            startup_state.status = StartupStatus.LOADING_MODELS
            startup_state.message = "Loading TTS engine..."
            startup_state.progress = 0.7

            # Usa KokoroAdapter existente
            self._adapter = KokoroAdapter(
                voice="af_heart",  # Voz feminina suave
                lang_code="p",      # pt-BR
                device="auto",
                use_half_precision=True
            )

            # Carrega modelo (lazy load)
            await self._adapter._load_model()

            startup_state.message = "TTS engine ready"

    async def synthesize(
        self,
        text: str,
        mode: VoiceMode = VoiceMode.NORMAL
    ) -> bytes:
        """Sintetiza texto em áudio.

        Args:
            text: Texto para sintetizar
            mode: Modo de voz (NORMAL ou THINKING)

        Returns:
            Bytes de áudio (float32 @ 24000Hz)

        Raises:
            RuntimeError: Se engine não inicializado
        """
        if self._adapter is None:
            raise RuntimeError("TTS engine not initialized. Call initialize() first.")

        # Usa KokoroAdapter existente
        audio_data = await self._adapter.synthesize(text, mode)

        # Retorna bytes brutos de áudio
        return audio_data.samples

    async def health(self) -> dict:
        """Retorna status do serviço."""
        return {
            "engine_loaded": self._adapter is not None and self._adapter._pipeline is not None,
            "queue_size": self._queue.qsize() if self._queue else 0,
            "queue_limit": self.QUEUE_SIZE_LIMIT,
            "stage": "tts"
        }

    async def shutdown(self) -> None:
        """Finaliza o serviço."""
        # KokoroAdapter não precisa de cleanup especial
        pass


# Singleton instance
_tts_service: TTSService | None = None


def get_tts_service() -> TTSService:
    """Retorna a instância singleton do TTSService."""
    global _tts_service
    if _tts_service is None:
        _tts_service = TTSService()
    return _tts_service
