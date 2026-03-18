# coding: utf-8
"""
TTSService - Serviço TTS isolado com lifecycle próprio.

DOC: openspec/changes/refactor-chat-event-driven/specs/tts-service/spec.md

Serviço TTS que gerencia próprio worker e fila, desacoplado da UI.
Consome eventos via EventBus e publica TTSStartedEvent/TTSCompletedEvent.

## Características

- Lifecycle explícito com métodos start() e stop()
- Worker assíncrono com buffer/fala inteligente
- Publica eventos para notificar UI (waveform, indicators)
- Tratamento silencioso de CancelledError
- Isolamento completo de UI Textual

## Exemplo

```python
from core.sy.voice import TTSService
from core.sy.events import InMemoryEventBus

bus = InMemoryEventBus()
tts = TTSService(event_bus=bus)

await tts.start()  # Inicia worker

# Enfileira eventos de fala
await tts.enqueue(StreamChunkEvent(
    turn_id="turn-1",
    content="Olá, mundo!",
    event_type="TEXT"
))

await tts.stop()  # Para worker graciosamente
```
"""

import asyncio
from dataclasses import dataclass, field
from typing import Literal

from core.sy.chat.events import (
    StreamChunkEvent,
    TTSCompletedEvent,
    TTSStartedEvent,
    TurnStartedEvent,
    TurnCompletedEvent,
)
from core.sy.events import InMemoryEventBus
from core.sky.voice.tts_adapter import VoiceMode, get_tts_adapter


class TTSService:
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

    def __init__(self, event_bus: InMemoryEventBus):
        """
        Inicializa o TTSService.

        Args:
            event_bus: EventBus para publicar eventos TTS
        """
        self._event_bus = event_bus
        self._queue: asyncio.Queue[StreamChunkEvent | None] | None = None
        self._worker_task: asyncio.Task | None = None
        self._running = False
        self._tts = get_tts_adapter()

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
            raise RuntimeError("TTSService já está rodando")

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
            raise RuntimeError("TTSService não está rodando. Chame start() primeiro.")

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
                            mode=VoiceMode.NORMAL
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
                            mode=VoiceMode.NORMAL
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
                            mode=VoiceMode.NORMAL
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
                            mode=VoiceMode.NORMAL
                        )
                        buffer = ""

                last_event_type = event_type

                # Fala quando buffer pronto (50+ chars E pontuação final)
                stripped = buffer.rstrip()
                if len(stripped) >= 50 and stripped[-1] in ".!?":
                    await self._speak_and_wait(
                        buffer.strip(),
                        current_turn_id,
                        mode=VoiceMode.NORMAL
                    )
                    buffer = ""

        except asyncio.CancelledError:
            # CancelledError silencioso - não propaga
            # Worker será limpo no stop()
            pass

    async def _speak_and_wait(self, text: str, turn_id: str, mode: VoiceMode) -> None:
        """
        Fala texto e publica eventos para UI.

        Args:
            text: Texto para falar
            turn_id: ID do turno atual
            mode: Modo de voz (NORMAL/THINKING)
        """
        if not text.strip():
            return

        # Publica evento de início
        await self._event_bus.publish(TTSStartedEvent(
            turn_id=turn_id,
            text=text,
            mode=mode.value
        ))

        try:
            # Fala o texto
            await self._tts.speak(text, mode=mode)
        finally:
            # Publica evento de conclusão
            await self._event_bus.publish(TTSCompletedEvent(
                turn_id=turn_id,
                text=text,
                duration_ms=0,  # TODO: capturar duração real
                metadata={"interrupted": False}
            ))
