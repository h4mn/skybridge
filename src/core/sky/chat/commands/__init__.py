# coding: utf-8
"""
Comandos do Chat Sky.

Este pacote contém os handlers para comandos especiais do chat:
- voice: Comandos de voz (/stt, /tts, /voice)
"""

from core.sky.chat.commands.voice_commands import (
    VoiceCommandHandler,
    get_voice_handler,
    execute_stt_command,
    execute_tts_command,
    execute_tts_toggle_command,
    execute_voice_command,
)

__all__ = [
    "VoiceCommandHandler",
    "get_voice_handler",
    "execute_stt_command",
    "execute_tts_command",
    "execute_tts_toggle_command",
    "execute_voice_command",
]
