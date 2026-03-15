# coding: utf-8
"""
ChatTextArea - TextArea customizado com comportamento de chat.

Enter envia mensagem, Shift+Enter nova linha, Escape limpa texto.

PRD027: Suporte a comandos de voz (/stt, /tts, /voice).
Comandos são processados antes de enviar mensagem.
"""

import asyncio
import re
import numpy as np
from textual import events, work
from textual.keys import Keys
from textual.widgets import TextArea
from textual.reactive import var
from textual.app import ComposeResult


class ChatTextArea(TextArea):
    """TextArea customizado para chat com Enter envia, Shift+Enter nova linha."""

    class Submitted(events.Message):
        """Postada quando o usuário pressiona Enter."""
        def __init__(self, value: str) -> None:
            super().__init__()
            self.value = value

    def __init__(self, id: str = "chat_input_textarea", placeholder: str = "🎙️ Digite algo...", **kwargs) -> None:
        super().__init__(id=id, placeholder=placeholder, **kwargs)

    def on_key(self, event: events.Key) -> None:
        """Handler de teclas - Enter envia, Shift+Enter nova linha."""
        # PRD027 F6.1: Toggle recording com Ctrl+Espaço é tratado pelo binding do Screen
        # Não interceptamos Ctrl+Espaço aqui - deixamos o binding processar

        if event.key == Keys.Enter:
            event.prevent_default()
            event.stop()

            # PRD027: Verifica se é comando /stt antes de enviar
            text = self.text.strip()
            if text.startswith("/stt"):
                self._process_stt_command(text)
            elif text.startswith("/tts"):
                # /tts: envia comando normalmente (Screen trata)
                self.post_message(self.Submitted(text))
                self.clear()
            elif text.startswith("/voice"):
                # /voice: envia comando normalmente (Screen trata)
                self.post_message(self.Submitted(text))
                self.clear()
            else:
                # Mensagem normal
                self.post_message(self.Submitted(text))
                self.clear()
        elif event.key == Keys.Escape:
            # Esc: limpa o texto
            self.text = ""
            event.stop()
        # Outras teclas - comportamento padrão do TextArea

    @work(exclusive=True)
    async def _process_stt_command(self, raw_command: str) -> None:
        """Processa comando /stt: ouve e transcreve áudio (PRD027)."""
        # Extrai duração do comando: "/stt 5" -> 5.0 segundos
        match = re.match(r"/stt\s+(\d+(?:\.\d+)?)", raw_command)
        duration = float(match.group(1)) if match else 5.0

        # UX: Limpa comando imediatamente (dá impressão de consumo)
        self.clear()

        # UX: Bip de início
        self._play_beep()

        # UX: Feedback visual
        self.placeholder = "🎙️ Transcrevendo..."

        try:
            # Importa VoiceService (tem record_and_transcribe)
            from core.sky.chat.textual_ui.voice_commands import get_voice_handler

            # Usa VoiceHandler para gravar e transcrever
            handler = get_voice_handler()
            transcribed_text = await handler.handle_stt(duration=duration)

            # Transcrição bem-sucedida
            if transcribed_text:
                # Atualiza o TextArea com texto transcrito
                self._set_text_and_submit(transcribed_text)
            else:
                # Nenhuma transcrição
                self.placeholder = "🎙️ Nenhuma fala detectada. Tente novamente."

        except Exception as e:
            # Erro na transcrição
            self.placeholder = f"Erro: {str(e)}"

    def _play_beep(self) -> None:
        """Toca bip sonoro de início de gravação (PRD027)."""
        try:
            import sounddevice as sd

            # Gera tom de 880Hz (A5) por 100ms
            sample_rate = 44100
            frequency = 880  # A5 - agudo e claro
            duration = 0.1  # 100ms

            t = np.linspace(0, duration, int(sample_rate * duration), False)
            # Onda senoidal com fade suave
            tone = np.sin(2 * np.pi * frequency * t)
            # Fade in/out para evitar clique
            fade_samples = int(sample_rate * 0.01)  # 10ms fade
            fade_in = np.linspace(0, 1, fade_samples)
            fade_out = np.linspace(1, 0, fade_samples)
            tone[:fade_samples] *= fade_in
            tone[-fade_samples:] *= fade_out
            # Normaliza para 30% do volume máximo
            tone = tone * 0.3

            sd.play(tone, sample_rate)
        except Exception:
            # Falha silenciosa - não trava o fluxo se som falhar
            pass

    def _set_text_and_submit(self, text: str) -> None:
        """Define texto e envia mensagem."""
        self.placeholder = ""  # Reseta feedback visual
        self.text = text
        self.focus()
        # Auto-envia a transcrição
        self.post_message(self.Submitted(text))
        # Limpa após o processamento
        self.clear()


__all__ = ["ChatTextArea"]
