# coding: utf-8
"""
Mixin para funcionalidade de gravação toggle (PRD027).

Fornece lógica compartilhada para gravação de áudio com toggle:
- Primeira vez: Inicia gravação contínua
- Segunda vez: Para gravação e transcreve

Uso em Screens:
    class MyScreen(RecordingToggleMixin, Screen):
        BINDINGS = [
            ("ctrl+space", "toggle_recording", "Gravar"),
        ]
"""

import asyncio
from typing import Optional, TYPE_CHECKING
from textual import work

if TYPE_CHECKING:
    from core.sky.voice.audio_capture import SoundDeviceCapture


class RecordingToggleMixin:
    """
    Mixin para gravação toggle de áudio.

    Estados:
    - _is_recording: Se está gravando
    - _recording_capture: Instância de SoundDeviceCapture ativa
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._is_recording: bool = False
        self._recording_capture: Optional["SoundDeviceCapture"] = None

    def action_toggle_recording(self) -> None:
        """
        Action para toggle de gravação (Ctrl+S).

        Comportamento:
        - Primeira chamada: Inicia gravação contínua
        - Segunda chamada: Para gravação e transcreve
        """
        if self._is_recording:
            # Para gravação e transcreve
            self._stop_recording_and_transcribe()
        else:
            # Inicia gravação
            self._start_recording()

    def _start_recording(self) -> None:
        """Inicia gravação contínua."""
        self._is_recording = True
        self._update_placeholder("🎙️ Gravando... (Ctrl+S para parar)")
        self._log_event("Gravação", "Iniciada (Ctrl+S para parar)")
        self._start_recording_worker()

    def _stop_recording_and_transcribe(self) -> None:
        """Sinaliza para parar gravação e transcrever."""
        self._is_recording = False
        self._update_placeholder("🎙️ Transcrevendo...")
        self._log_event("Gravação", "Parada. Transcrevendo...")

        # O worker detecta a mudança da flag e para a gravação

    @work(exclusive=True)
    async def _start_recording_worker(self) -> None:
        """Worker para gravar áudio continuamente até toggle."""
        try:
            # Importa aqui para evitar import circular
            from core.sky.voice.audio_capture import SoundDeviceCapture
            from core.sky.voice import get_voice_service

            # Inicia captura
            self._recording_capture = SoundDeviceCapture(sample_rate=16000, channels=1)
            await self._recording_capture.start_recording()

            # Aguarda até que a flag seja desativada
            while self._is_recording:
                await asyncio.sleep(0.1)

            # Para gravação
            audio = await self._recording_capture.stop_recording()
            self._recording_capture = None

            # Transcreve
            voice = get_voice_service()
            transcribed_text = await voice.transcribe(audio, language="pt")

            # Callback com resultado
            await self._on_recording_complete(transcribed_text)

        except asyncio.CancelledError:
            # Gravação cancelada
            self._cleanup_recording()
            self._update_placeholder("Digite algo...")

        except Exception as e:
            self._cleanup_recording()
            self._log_error(f"Gravação erro: {e}")
            self._update_placeholder("Digite algo...")

    def _cleanup_recording(self) -> None:
        """Limpa recursos de gravação."""
        self._is_recording = False
        if self._recording_capture:
            try:
                import asyncio
                # Tenta parar a gravação se ainda estiver ativa
                loop = asyncio.get_event_loop()
                loop.create_task(self._recording_capture.stop_recording())
            except Exception:
                pass
            self._recording_capture = None

    # Métodos abstratos que devem ser implementados pela Screen

    def _update_placeholder(self, text: str) -> None:
        """Atualiza placeholder do TextArea. Deve ser implementado pela Screen."""
        raise NotImplementedError("_update_placeholder deve ser implementado")

    def _log_event(self, title: str, message: str) -> None:
        """Loga evento. Deve ser implementado pela Screen."""
        raise NotImplementedError("_log_event deve ser implementado")

    def _log_error(self, message: str) -> None:
        """Loga erro. Deve ser implementado pela Screen."""
        raise NotImplementedError("_log_error deve ser implementado")

    async def _on_recording_complete(self, transcribed_text: str) -> None:
        """
        Callback chamado quando a gravação é completa e transcrita.

        Args:
            transcribed_text: Texto transcrito
        """
        raise NotImplementedError("_on_recording_complete deve ser implementado")


__all__ = ["RecordingToggleMixin"]
