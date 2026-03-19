# coding: utf-8
"""
StreamingTTSService - Serviço TTS com worker assíncrono para streaming.

DOC: openspec/changes/refactor-chat-event-driven/specs/tts-service/spec.md

Serviço TTS que gerencia próprio worker e fila, desacoplado da UI.
Consome eventos via EventBus e publica TTSStartedEvent/TTSCompletedEvent.

NOTA: Nome diferente de TTSService legado para evitar conflitos.
O TTSService legado (core.sky.voice.tts_service) é a interface para backends TTS.
Este StreamingTTSService é o wrapper com worker/fila para processamento de stream.
"""

import asyncio
from dataclasses import dataclass, field
from typing import Literal

from core.sky.chat.events import (
    StreamChunkEvent,
    TTSCompletedEvent,
    TTSStartedEvent,
)
from core.sky.events import InMemoryEventBus
from core.sky.voice import get_tts_adapter, TTSAdapter
from core.sky.voice.voice_modes import VoiceMode


class StreamingTTSService:
    """
    Serviço TTS isolado com lifecycle próprio.

    Responsabilidades:
    - Gerenciar fila de eventos de fala
    - Implementar lógica de buffer/fala (transferida de MainScreen)
    - Publicar eventos TTSStartedEvent/TTSCompletedEvent
    - Tratar CancelledError silenciosamente

    NÃO faz:
    - Conhecer UI ou Screen
    - Gerenciar waveform (isso é feito via EventBus por UI)
    """

    def __init__(self, event_bus: InMemoryEventBus, tts_adapter: TTSAdapter | None = None):
        """
        Inicializa o StreamingTTSService.

        Args:
            event_bus: EventBus para publicar eventos TTS
            tts_adapter: Adapter TTS (opcional, usa get_tts_adapter() se None)
        """
        self._event_bus = event_bus
        self._queue: asyncio.Queue[StreamChunkEvent | None] | None = None
        self._worker_task: asyncio.Task | None = None
        self._running = False
        self._tts = tts_adapter or get_tts_adapter()

    @property
    def is_running(self) -> bool:
        """Retorna True se o serviço está rodando."""
        return self._running

    async def start(self) -> None:
        """
        Inicia o worker TTS.

        Cria fila e inicia task assíncrona. Deve ser chamado
        antes de enfileirar qualquer evento.

        Raises:
            RuntimeError: Se já estiver rodando
        """
        if self._running:
            raise RuntimeError("StreamingTTSService já está rodando")

        self._queue = asyncio.Queue()
        self._worker_task = asyncio.create_task(self._worker())
        self._running = True

    async def stop(self) -> None:
        """
        Para o worker TTS graciosamente.

        Envia sentinel None para fila e aguarda worker terminar.
        Não levanta exceção se não estiver rodando.
        """
        if not self._running:
            return

        # Envia sinal de fim
        if self._queue:
            await self._queue.put(None)

        # Aguarda worker terminar (com tratamento de CancelledError)
        if self._worker_task:
            try:
                await self._worker_task
            except asyncio.CancelledError:
                # Worker foi cancelado externamente - OK
                pass

        self._running = False
        self._worker_task = None
        self._queue = None

    async def enqueue(self, event: StreamChunkEvent) -> None:
        """
        Enfileira evento para processamento pelo worker.

        Non-blocking - retorna imediatamente após put na fila.

        Args:
            event: Evento de stream para processar

        Raises:
            RuntimeError: Se serviço não estiver rodando
        """
        if not self._running or not self._queue:
            raise RuntimeError("StreamingTTSService não está rodando. Chame start() primeiro.")

        await self._queue.put(event)

    async def _worker(self) -> None:
        """
        Worker TTS com lógica de buffer/fala.

        Transferido de MainScreen._tts_worker() (~100 linhas).

        Lógica:
        1. Acumula texto até 50+ chars com pontuação final
        2. Detecta transições de evento (TOOL_RESULT → THOUGHT/TEXT)
        3. Publica TTSStartedEvent/TTSCompletedEvent
        4. Trata CancelledError silenciosamente
        """
        if not self._queue:
            return

        buffer = ""
        last_event_type = None
        current_turn_id = None

        try:
            while True:
                event = await self._queue.get()

                if event is None:  # Sinal de fim (EOF)
                    # Fala buffer restante
                    if buffer.strip() and current_turn_id:
                        await self._speak_and_wait(
                            buffer.strip(),
                            current_turn_id,
                            mode="normal"
                        )
                    break

                # Atualiza turno atual
                if current_turn_id != event.turn_id:
                    current_turn_id = event.turn_id

                event_type = event.event_type
                content = event.content

                # NOVO CICLO DE PENSAMENTO (TOOL_RESULT → THOUGHT)
                if last_event_type == "TOOL_RESULT" and event_type == "THOUGHT":
                    if buffer.strip():
                        await self._speak_and_wait(
                            buffer.strip(),
                            current_turn_id,
                            mode="normal"
                        )
                        buffer = ""
                    # Reação de início de novo ciclo
                    buffer = "hum... "

                # TRANSIÇÃO PARA TEXTO FINAL (TOOL_RESULT → TEXT)
                if last_event_type == "TOOL_RESULT" and event_type == "TEXT":
                    if buffer.strip():
                        await self._speak_and_wait(
                            buffer.strip(),
                            current_turn_id,
                            mode="normal"
                        )
                        buffer = ""

                # Processa por tipo de evento
                if event_type == "TEXT":
                    buffer += content

                elif event_type == "THOUGHT":
                    if not buffer:
                        buffer = f"hum... {content}"
                    else:
                        buffer += content

                elif event_type in ("TOOL_START", "TOOL_RESULT", "ERROR"):
                    # Antes de tool/error: fala buffer acumulado
                    if buffer.strip():
                        await self._speak_and_wait(
                            buffer.strip(),
                            current_turn_id,
                            mode="normal"
                        )
                        buffer = ""

                last_event_type = event_type

                # Fala quando buffer pronto (50+ chars E pontuação final)
                stripped = buffer.rstrip()
                if len(stripped) >= 50 and stripped[-1] in ".!?":
                    await self._speak_and_wait(
                        buffer.strip(),
                        current_turn_id,
                        mode="normal"
                    )
                    buffer = ""

        except asyncio.CancelledError:
            # CancelledError silencioso - não propaga
            # Worker será limpo no stop()
            pass

    async def _speak_and_wait(self, text: str, turn_id: str, mode: str) -> None:
        """
        Fala texto e publica eventos para UI.

        Args:
            text: Texto para falar
            turn_id: ID do turno atual
            mode: Modo de voz como string ("normal" ou "thinking")
        """
        if not text.strip():
            return

        # Converte string para VoiceMode enum
        voice_mode = VoiceMode(mode)

        # Publica evento de início
        await self._event_bus.publish(TTSStartedEvent(
            turn_id=turn_id,
            text=text,
            mode=mode
        ))

        try:
            # Fala o texto
            await self._tts.speak(text, mode=voice_mode)
        finally:
            # Publica evento de conclusão
            await self._event_bus.publish(TTSCompletedEvent(
                turn_id=turn_id,
                text=text,
                duration_ms=0,  # TODO: capturar duração real
                metadata={"interrupted": False}
            ))
