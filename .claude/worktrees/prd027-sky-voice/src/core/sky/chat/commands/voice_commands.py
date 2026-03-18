"""
Comandos de Voz para o Chat Sky (PRD027).

Este módulo implementa os comandos de voz:
- /stt: Transcreve áudio do microfone
- /tts <texto>: Fala o texto especificado
- /voice: Ativa modo conversacional

O handler usa VoiceService singleton com lazy load.
Modelos são carregados sob demanda e mantidos em memória.
"""

import asyncio
import sys
from typing import Optional

# Adiciona src ao path para imports
sys.path.insert(0, "src")

from core.sky.voice import get_voice_service


class VoiceCommandHandler:
    """Handler para comandos de voz no chat.

    Usa VoiceService singleton com lazy load.
    Após primeira inicialização, modelos permanecem em memória.

    Performance:
    - Cold start TTS: ~3s (primeira vez)
    - Warm start TTS: ~0.3s (RTF 0.35x)
    - Warm start STT: ~0.1s (RTF 0.06x)
    """

    def __init__(self):
        """Inicializa handler de comandos de voz."""
        self.voice_mode_active: bool = False
        self.tts_responses: bool = True  # Flag para TTS progressivo nas respostas (padrão: ativo)
        self._voice_service = get_voice_service()

    async def handle_stt(self, duration: float = 5.0) -> str:
        """
        Manipula comando /stt.

        Grava áudio do microfone e transcreve usando VoiceService.

        Args:
            duration: Duração da gravação em segundos

        Returns:
            Texto transcrito
        """
        return await self._voice_service.record_and_transcribe(
            duration=duration,
            language="pt"
        )

    async def handle_tts(self, text: str) -> None:
        """
        Manipula comando /tts <texto>.

        Fala o texto especificado usando VoiceService.

        Args:
            text: Texto para falar
        """
        await self._voice_service.speak(text)

    async def handle_voice_toggle(self) -> bool:
        """
        Manipula comando /voice.

        Alterna modo conversacional.

        Returns:
            Novo estado do modo voz (True=ativo)
        """
        self.voice_mode_active = not self.voice_mode_active
        return self.voice_mode_active

    async def handle_tts_toggle(self, state: bool | None = None) -> bool:
        """
        Alterna TTS progressivo nas respostas.

        Args:
            state: True para ativar, False para desativar, None para toggle

        Returns:
            Novo estado do TTS progressivo (True=ativo)
        """
        if state is None:
            self.tts_responses = not self.tts_responses
        else:
            self.tts_responses = state
        return self.tts_responses

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


async def execute_tts_toggle_command(arg: str = "") -> str:
    """
    Executa comando /tts on|off.

    Ativa ou desativa TTS progressivo nas respostas do chat.

    Args:
        arg: Argumento do comando ("on", "off" ou vazio para toggle)

    Returns:
        Mensagem de resultado para exibir no chat
    """
    handler = get_voice_handler()

    # Determina estado desejado
    state: bool | None = None
    if arg.lower() == "on":
        state = True
    elif arg.lower() == "off":
        state = False
    # Se vazio ou outro valor, é toggle (state=None)

    is_active = await handler.handle_tts_toggle(state)

    if is_active:
        return "🔊 **TTS Progressivo Ativado**\n\nA Sky falará as respostas em tempo real conforme forem geradas."
    else:
        return "🔇 TTS progressivo desativado."


__all__ = [
    "VoiceCommandHandler",
    "get_voice_handler",
    "execute_stt_command",
    "execute_tts_command",
    "execute_tts_toggle_command",
    "execute_voice_command",
]
