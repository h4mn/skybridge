"""
Comandos de Voz para o Chat Sky (PRD027).

Este módulo implementa os comandos de voz:
- /stt: Transcreve áudio do microfone
- /tts <texto>: Fala o texto especificado
- /voice: Ativa modo conversacional

O handler usa lazy load para manter modelos em memória após primeira inicialização.
"""

import asyncio
import sys
from typing import Optional

# Adiciona src ao path para imports
sys.path.insert(0, "src")

from core.sky.voice.audio_capture import SoundDeviceCapture
from core.sky.voice.stt_service import WhisperAdapter, TranscriptionConfig
from core.sky.voice.tts_service import KokoroAdapter, VoiceConfig


class VoiceCommandHandler:
    """Handler para comandos de voz no chat.

    Usa lazy load para inicializar modelos apenas na primeira use.
    Após inicialização, modelos permanecem em memória para respostas rápidas.
    """

    def __init__(self):
        """Inicializa handler de comandos de voz."""
        self.stt: Optional[WhisperAdapter] = None
        self.tts: Optional[KokoroAdapter] = None
        self.voice_mode_active: bool = False

    def _ensure_stt(self) -> WhisperAdapter:
        """Garante que STT está inicializado (lazy load)."""
        if self.stt is None:
            self.stt = WhisperAdapter(model_size="base", device="cpu")
        return self.stt

    def _ensure_tts(self) -> KokoroAdapter:
        """Garante que TTS está inicializado (lazy load - Kokoro pt-BR)."""
        if self.tts is None:
            # Kokoro com voz feminina suave e português brasileiro
            self.tts = KokoroAdapter(voice="af_heart", lang_code="p")
        return self.tts

    async def handle_stt(self, duration: float = 5.0) -> str:
        """
        Manipula comando /stt.

        Grava áudio do microfone e transcreve.

        Args:
            duration: Duração da gravação em segundos

        Returns:
            Texto transcrito
        """
        stt = self._ensure_stt()

        # Inicia captura
        capture = SoundDeviceCapture(sample_rate=16000, channels=1)
        await capture.start_recording()

        # Aguarda duração
        await asyncio.sleep(duration)

        # Para e transcreve
        audio = await capture.stop_recording()
        result = await stt.transcribe(
            audio,
            config=TranscriptionConfig(language="pt", detect_language=False),
        )

        return result.text

    async def handle_tts(self, text: str) -> None:
        """
        Manipula comando /tts <texto>.

        Fala o texto especificado.

        Args:
            text: Texto para falar
        """
        tts = self._ensure_tts()
        await tts.speak(text, VoiceConfig())

    async def handle_voice_toggle(self) -> bool:
        """
        Manipula comando /voice.

        Alterna modo conversacional.

        Returns:
            Novo estado do modo voz (True=ativo)
        """
        self.voice_mode_active = not self.voice_mode_active
        return self.voice_mode_active

    @property
    def is_voice_active(self) -> bool:
        """Verifica se modo voz está ativo."""
        return self.voice_mode_active


# Singleton global para o handler
_voice_handler: Optional[VoiceCommandHandler] = None


def get_voice_handler() -> VoiceCommandHandler:
    """Retorna o singleton do handler de voz."""
    global _voice_handler
    if _voice_handler is None:
        _voice_handler = VoiceCommandHandler()
    return _voice_handler


async def execute_stt_command(duration: float = 5.0) -> str:
    """
    Executa comando /stt.

    Args:
        duration: Duração da gravação em segundos

    Returns:
        Mensagem de resultado para exibir no chat
    """
    handler = get_voice_handler()

    try:
        text = await handler.handle_stt(duration)
        if text:
            return f"🎤 Transcrição: \"{text}\""
        else:
            return "🎤 Nenhum áudio detectado."
    except ImportError as e:
        return f"❌ Erro: {e}\n💡 Instale: pip install faster-whisper sounddevice"
    except Exception as e:
        return f"❌ Erro na transcrição: {e}"


async def execute_tts_command(text: str) -> str:
    """
    Executa comando /tts <texto>.

    Usa Kokoro TTS com voz feminina suave em português brasileiro.
    Após primeira chamada, modelo permanece em memória para respostas rápidas.

    Args:
        text: Texto para falar

    Returns:
        Mensagem de resultado para exibir no chat
    """
    if not text:
        return "💡 Uso: /tts <texto para falar>"

    handler = get_voice_handler()

    try:
        import time
        start = time.perf_counter()

        await handler.handle_tts(text)

        elapsed = time.perf_counter() - start
        return f"🔊 Kokoro: \"{text}\"\n⏱️ {elapsed*1000:.0f}ms"
    except ImportError as e:
        return f"❌ Erro: {e}\n💡 Instale: pip install kokoro sounddevice"
    except Exception as e:
        return f"❌ Erro na síntese: {e}"


async def execute_voice_command() -> str:
    """
    Executa comando /voice.

    Returns:
        Mensagem de resultado para exibir no chat
    """
    handler = get_voice_handler()
    is_active = await handler.handle_voice_toggle()

    if is_active:
        return (
            "🎙️ **Modo Voz Ativado**\n\n"
            "Pressione ESPAÇO para falar (push-to-talk)\n"
            "Pressione ESC ou /voice para desativar"
        )
    else:
        return "🎙️ Modo voz desativado."


__all__ = [
    "VoiceCommandHandler",
    "get_voice_handler",
    "execute_stt_command",
    "execute_tts_command",
    "execute_voice_command",
]
