"""
Voice Chat - Orquestrador do chat por voz para a Sky.

Este módulo coordena TTS e STT para proporcionar uma experiência
conversacional completa com a Sky.
"""

from dataclasses import dataclass
from enum import Enum
from typing import Optional, Callable

from core.sky.voice.tts_service import TTSService, VoiceConfig
from core.sky.voice.stt_service import STTService, TranscriptionResult


class VoiceMode(Enum):
    """Modos de operação do voice chat."""

    PUSH_TO_TALK = "push-to-talk"
    ALWAYS_ON = "always-on"


class VoiceState(Enum):
    """Estados do voice chat."""

    INACTIVE = "inactive"
    LISTENING = "listening"
    PROCESSING = "processing"
    SPEAKING = "speaking"


@dataclass
class VoiceChatConfig:
    """Configuração do Voice Chat.

    Attributes:
        mode: Modo de operação (push-to-talk ou always-on)
        voice_config: Configuração de voz para TTS
        silence_timeout: Segundos de silêncio antes de parar (always-on)
        interrupt_on_speech: Interromper fala da Sky quando usuário falar
    """

    mode: VoiceMode = VoiceMode.PUSH_TO_TALK
    voice_config: VoiceConfig = None
    silence_timeout: float = 60.0
    interrupt_on_speech: bool = True

    def __post_init__(self):
        if self.voice_config is None:
            self.voice_config = VoiceConfig()


class VoiceChat:
    """Orquestrador do chat por voz.

    Coordena TTS e STT para proporcionar uma experiência
    conversacional completa com a Sky.
    """

    def __init__(
        self,
        tts: TTSService,
        stt: STTService,
        chat_handler: Optional[Callable[[str], str]] = None,
        config: Optional[VoiceChatConfig] = None,
    ):
        """Inicializa Voice Chat.

        Args:
            tts: Serviço de Text-to-Speech
            stt: Serviço de Speech-to-Text
            chat_handler: Função para processar mensagens (texto → texto)
            config: Configuração do voice chat
        """
        self.tts = tts
        self.stt = stt
        self.chat_handler = chat_handler
        self.config = config or VoiceChatConfig()
        self.state = VoiceState.INACTIVE
        self._is_active = False

    @property
    def is_active(self) -> bool:
        """Verifica se o voice chat está ativo."""
        return self._is_active

    async def activate(self) -> None:
        """Ativa o modo conversacional."""
        self._is_active = True
        self.state = VoiceState.LISTENING

        if self.config.mode == VoiceMode.ALWAYS_ON:
            await self._always_on_loop()
        # PUSH_TO_TALK é controlado por eventos externos (teclado)

    async def deactivate(self) -> None:
        """Desativa o modo conversacional."""
        self._is_active = False
        self.state = VoiceState.INACTIVE

    async def toggle(self) -> None:
        """Alterna modo conversacional."""
        if self._is_active:
            await self.deactivate()
        else:
            await self.activate()

    async def push_and_talk(self) -> None:
        """Executa um ciclo de conversação (push-to-talk)."""
        if not self._is_active:
            return

        self.state = VoiceState.LISTENING

        # Escuta usuário
        result = await self.stt.listen(
            duration=30.0,
            on_partial=self._on_partial_transcription,
        )

        if not result.text:
            return

        # Processa mensagem
        self.state = VoiceState.PROCESSING
        response = await self._process_message(result.text)

        if not response:
            return

        # Fala resposta
        self.state = VoiceState.SPEAKING
        await self.tts.speak(response, self.config.voice_config)

        # Volta a escutar
        if self._is_active and self.config.mode == VoiceMode.ALWAYS_ON:
            self.state = VoiceState.LISTENING

    async def _always_on_loop(self) -> None:
        """Loop do modo always-on."""
        import asyncio

        while self._is_active:
            await self.push_and_talk()
            await asyncio.sleep(0.1)  # Pequena pausa entre ciclos

    async def _process_message(self, user_message: str) -> Optional[str]:
        """Processa mensagem do usuário.

        Args:
            user_message: Mensagem transcrita do usuário

        Returns:
            Resposta da Sky (ou None se não houver resposta)
        """
        if self.chat_handler is None:
            return None

        # Detecta comandos nativos
        if self._is_native_command(user_message):
            return await self._handle_native_command(user_message)

        # Processa via chat handler
        return self.chat_handler(user_message)

    def _is_native_command(self, text: str) -> bool:
        """Verifica se texto é um comando nativo."""
        text_lower = text.lower().strip()
        return text_lower in [
            "parar",
            "sky para",
            "ajuda",
            "o que você pode fazer",
        ]

    async def _handle_native_command(self, command: str) -> Optional[str]:
        """Lida com comandos nativos de voz."""
        command_lower = command.lower().strip()

        if command_lower in ["parar", "sky para"]:
            await self.deactivate()
            return "Microfone desativado."

        if command_lower in ["ajuda", "o que você pode fazer"]:
            return "Você pode dizer: Parar para desativar o microfone, ou apenas conversar normalmente."

        return None

    def _on_partial_transcription(self, partial_text: str) -> None:
        """Callback para transcrições parciais (streaming).

        Args:
            partial_text: Texto parcial transcrito
        """
        # TODO: Enviar para UI para exibir em tempo real
        pass

    def interrupt_speech(self) -> None:
        """Interrompe fala atual da Sky."""
        # TODO: Implementar interrupção de áudio
        pass


# TODO: Integrar com ChatService da Sky
# from src.core.sky.chat import ChatService
#
# class SkyVoiceChat(VoiceChat):
#     """Voice Chat integrado com ChatService da Sky."""
#
#     def __init__(self, chat_service: ChatService, ...):
#         super().__init__(
#             chat_handler=chat_service.respond,
#             ...
#         )
#         self.chat_service = chat_service
