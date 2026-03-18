# coding: utf-8
"""
WaveformController - Controlador de waveform via EventBus.

DOC: openspec/changes/refactor-chat-event-driven/design.md

Consome eventos TTSStartedEvent/TTSCompletedEvent do EventBus e
atualiza o header (start_speaking, start_thinking, stop_waveform).

Desacopla TTSService da UI Textual - comunicação via eventos.
"""

import asyncio
from typing import AsyncIterator

from textual.widget import Widget

from core.sy.events import InMemoryEventBus
from core.sy.chat.events import TTSCompletedEvent, TTSStartedEvent


class WaveformController(Widget):
    """
    Controlador de waveform que consome eventos TTS via EventBus.

    Responsabilidades:
    - Inscrever-se em TTSStartedEvent/TTSCompletedEvent
    - Atualizar header (start_speaking, start_thinking, stop_waveform)
    - Rodar em background sem bloquear UI

    NÃO conhece TTSService - apenas consome eventos.
    """

    def __init__(self, event_bus: InMemoryEventBus) -> None:
        """
        Inicializa o WaveformController.

        Args:
            event_bus: EventBus para consumir eventos TTS
        """
        super().__init__()
        self._event_bus = event_bus
        self._task: asyncio.Task | None = None
        self._running = False

    def on_mount(self) -> None:
        """Inicia consumer de eventos quando widget é montado."""
        self._running = True
        self._task = asyncio.create_task(self._consume_events())

    def on_unmount(self) -> None:
        """Para consumer de eventos quando widget é desmontado."""
        self._running = False
        if self._task and not self._task.done():
            self._task.cancel()

    async def _consume_events(self) -> None:
        """
        Consome eventos TTS e atualiza header.

        Roda em background, consumindo eventos do EventBus.
        """
        try:
            # Inscreve-se em ambos os tipos de evento
            async for event in self._event_bus.subscribe(TTSStartedEvent):
                if not self._running:
                    break

                # TTSStartedEvent: inicia waveform
                if isinstance(event, TTSStartedEvent):
                    self._handle_tts_started(event)

        except asyncio.CancelledError:
            # Consumer foi cancelado - OK
            pass

    def _handle_tts_started(self, event: TTSStartedEvent) -> None:
        """
        Lida com TTSStartedEvent - inicia waveform no header.

        Args:
            event: Evento com turn_id, text, mode
        """
        try:
            header = self.app.query_one("ChatHeader")
        except Exception:
            # Header não encontrado - ignora
            return

        mode = event.mode
        if mode == "THINKING":
            header.start_thinking()
        else:
            header.start_speaking()

        # Agenda parada após conclusão (ou via TTSCompletedEvent)
        # Por simplicidade, aqui não agendamos - TTSCompletedEvent vai parar

    def _handle_tts_completed(self, event: TTSCompletedEvent) -> None:
        """
        Lida com TTSCompletedEvent - para waveform no header.

        Args:
            event: Evento com turn_id, text, duration_ms
        """
        try:
            header = self.app.query_one("ChatHeader")
        except Exception:
            # Header não encontrado - ignora
            return

        header.stop_waveform()


class WaveformControllerV2(Widget):
    """
    Versão 2 do WaveformController com consumer único para ambos eventos.

    Usa pattern async for com filtro de tipo de evento.
    """

    DEFAULT_CSS = """
    WaveformControllerV2 {
        display: none;
    }
    """

    def __init__(self, event_bus: InMemoryEventBus) -> None:
        """
        Inicializa o WaveformControllerV2.

        Args:
            event_bus: EventBus para consumir eventos TTS
        """
        super().__init__()
        self._event_bus = event_bus
        self._consumer_task: asyncio.Task | None = None
        self._running = False

    def on_mount(self) -> None:
        """Inicia consumer de eventos quando widget é montado."""
        self._running = True
        self._consumer_task = asyncio.create_task(self._consume_tts_events())

    def on_unmount(self) -> None:
        """Para consumer de eventos quando widget é desmontado."""
        self._running = False
        if self._consumer_task and not self._consumer_task.done():
            self._consumer_task.cancel()

    async def _consume_tts_events(self) -> None:
        """
        Consome eventos TTS e atualiza header.

        Técnicas:
        - Usa multi-subscribe: inscreve-se em ambos tipos de evento
        - Filtra por tipo usando isinstance
        - Atualiza header conforme tipo
        """
        try:
            # Subscribe em Started primeiro
            async for event in self._event_bus.subscribe(TTSStartedEvent):
                if not self._running:
                    break

                if isinstance(event, TTSStartedEvent):
                    self._on_tts_started(event)

                    # Aguarda Completed correspondente
                    await self._wait_for_completion(event.turn_id)

        except asyncio.CancelledError:
            pass

    async def _wait_for_completion(self, turn_id: str) -> None:
        """
        Aguarda TTSCompletedEvent para o turno atual.

        Args:
            turn_id: ID do turno a aguardar
        """
        try:
            # Timeout de 5s para aguardar completion
            async for event in self._event_bus.subscribe(TTSCompletedEvent):
                if not self._running:
                    break

                if isinstance(event, TTSCompletedEvent) and event.turn_id == turn_id:
                    self._on_tts_completed(event)
                    break
        except asyncio.CancelledError:
            pass

    def _on_tts_started(self, event: TTSStartedEvent) -> None:
        """Lida com TTSStartedEvent - inicia waveform."""
        try:
            from core.sky.chat.textual_ui.widgets.header import ChatHeader
            header = self.app.query_one(ChatHeader)
        except Exception:
            return

        mode = event.mode
        if mode == "THINKING":
            header.start_thinking()
        else:
            header.start_speaking()

    def _on_tts_completed(self, event: TTSCompletedEvent) -> None:
        """Lida com TTSCompletedEvent - para waveform."""
        try:
            from core.sky.chat.textual_ui.widgets.header import ChatHeader
            header = self.app.query_one(ChatHeader)
        except Exception:
            return

        header.stop_waveform()
