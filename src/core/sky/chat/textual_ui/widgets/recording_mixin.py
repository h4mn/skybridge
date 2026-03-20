# coding: utf-8
"""
Mixin para funcionalidade de gravação toggle (PRD027).

Fornece lógica compartilhada para gravação de áudio com toggle:
- Primeira vez: Inicia gravação contínua
- Segunda vez: Para gravação e transcreve

Integração Voice API (voice-api-isolation):
- Quando SKYBRIDGE_VOICE_API_ENABLED=1: Usa VoiceAPIClient (HTTP)
- Quando desabilitado: Usa VoiceService legado (direto)

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
    - _use_voice_api: Se deve usar Voice API (feature flag)
    - _voice_api_client: Cliente HTTP VoiceAPIClient (quando ativo)
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._is_recording: bool = False
        self._recording_capture: Optional["SoundDeviceCapture"] = None
        self._use_voice_api: bool = False
        self._voice_api_client: Optional["VoiceAPIClient"] = None
        self._voice_service = None

    def _initialize_voice_backend(self) -> None:
        """
        Inicializa backend de voz (legado ou Voice API).

        Verifica feature flag SKYBRIDGE_VOICE_API_ENABLED e configura
        o backend apropriado.
        """
        try:
            from core.sky.voice.feature_toggle import is_voice_api_enabled
            from core.sky.voice.client import VoiceAPIClient
            from core.sky.voice import get_voice_service

            if is_voice_api_enabled():
                # Usa Voice API (HTTP) - backend isolado
                self._use_voice_api = True
                self._voice_api_client = VoiceAPIClient()
            else:
                # Usa legado (direto) - VoiceService local
                self._use_voice_api = False
                self._voice_service = get_voice_service()

        except ImportError as e:
            # Fallback para legado se Voice API não disponível
            from core.sky.voice import get_voice_service
            self._use_voice_api = False
            self._voice_service = get_voice_service()

    def action_toggle_recording(self) -> None:
        """
        Action para toggle de gravação (Ctrl+S).

        Comportamento:
        - Primeira chamada: Inicia gravação contínua
        - Segunda chamada: Para gravação e transcreve
        """
        # Inicializa backend na primeira vez
        if self._voice_service is None and self._voice_api_client is None:
            self._initialize_voice_backend()

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

            # Inicia captura
            self._recording_capture = SoundDeviceCapture(sample_rate=16000, channels=1)
            await self._recording_capture.start_recording()

            # Aguarda até que a flag seja desativada
            while self._is_recording:
                await asyncio.sleep(0.1)

            # Para gravação
            audio = await self._recording_capture.stop_recording()
            self._recording_capture = None

            # Transcreve usando backend configurado (Voice API ou legado)
            if self._use_voice_api and self._voice_api_client:
                # Voice API - backend isolado via HTTP
                from core.sky.voice.audio_capture import AudioData
                from core.sky.voice.client import VoiceAPIUnavailableError

                # Converte AudioData para bytes WAV
                if isinstance(audio, AudioData):
                    audio_bytes = audio.to_wav_bytes()
                else:
                    # Se já for bytes, usa diretamente
                    audio_bytes = audio

                try:
                    transcribed_text = await self._voice_api_client.stt(audio_bytes)
                except VoiceAPIUnavailableError as e:
                    # Fallback para legado se Voice API indisponível
                    self._log_event("Voice API", f"Indisponível, usando legado: {e}")
                    voice = self._get_voice_service_fallback()
                    transcribed_text = await voice.transcribe(audio, language="pt")

            else:
                # Legado - VoiceService local (faster-whisper direto)
                voice = self._voice_service or self._get_voice_service_fallback()
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

    def _get_voice_service_fallback(self):
        """
        Retorna VoiceService legado como fallback.

        Usado quando Voice API não está disponível ou falhou.
        """
        from core.sky.voice import get_voice_service
        return get_voice_service()

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
