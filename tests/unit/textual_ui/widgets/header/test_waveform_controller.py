# coding: utf-8
"""
Testes do WaveformController.

DOC: openspec/changes/refactor-chat-event-driven/tasks.md

Testa consumo de eventos TTS e atualização do header.
"""

import asyncio

import pytest

from core.sky.chat.events import TTSCompletedEvent, TTSStartedEvent
from core.sky.events import InMemoryEventBus
from core.sky.chat.textual_ui.widgets.header.waveform_controller import WaveformControllerV2


class MockHeader:
    """Mock do ChatHeader."""

    def __init__(self):
        self.state = None  # "thinking", "speaking", None
        self.start_thinking_count = 0
        self.start_speaking_count = 0
        self.stop_count = 0

    def start_thinking(self):
        self.state = "thinking"
        self.start_thinking_count += 1

    def start_speaking(self):
        self.state = "speaking"
        self.start_speaking_count += 1

    def stop_waveform(self):
        self.state = None
        self.stop_count += 1


@pytest.mark.asyncio
async def test_waveform_controller_subscribes_to_events():
    """Teste: WaveformController se inscreve em eventos TTS."""
    bus = InMemoryEventBus()
    controller = WaveformControllerV2(event_bus=bus)

    # Simula on_mount
    controller._running = True
    controller._consumer_task = asyncio.create_task(controller._consume_tts_events())

    # Aguarda subscriber registrar
    await asyncio.sleep(0.01)

    # Publica evento
    await bus.publish(TTSStartedEvent(
        turn_id="turn-1",
        text="Teste",
        mode="NORMAL"
    ))

    # Aguarda processamento
    await asyncio.sleep(0.1)

    # Cleanup
    controller._running = False
    if controller._consumer_task:
        controller._consumer_task.cancel()
        try:
            await controller._consumer_task
        except asyncio.CancelledError:
            pass

    # Não levanta exceção = sucesso
    assert True


@pytest.mark.asyncio
async def test_waveform_controller_handles_speaking_event():
    """Teste: TTSStartedEvent com mode NORMAL inicia speaking."""
    bus = InMemoryEventBus()
    controller = WaveformControllerV2(event_bus=bus)

    # Mock header
    mock_header = MockHeader()

    # Simula app.query_one
    class MockApp:
        def query_one(self, _):
            return mock_header

    controller.app = MockApp()

    # Simula on_mount
    controller._running = True
    controller._consumer_task = asyncio.create_task(controller._consume_tts_events())
    await asyncio.sleep(0.01)

    # Publica evento speaking
    await bus.publish(TTSStartedEvent(
        turn_id="turn-1",
        text="Olá mundo",
        mode="NORMAL"
    ))

    # Aguarda processamento
    await asyncio.sleep(0.05)

    # Verifica que header foi atualizado
    assert mock_header.state == "speaking"
    assert mock_header.start_speaking_count == 1

    # Cleanup
    controller._running = False
    if controller._consumer_task:
        controller._consumer_task.cancel()


@pytest.mark.asyncio
async def test_waveform_controller_handles_thinking_event():
    """Teste: TTSStartedEvent com mode THINKING inicia thinking."""
    bus = InMemoryEventBus()
    controller = WaveformControllerV2(event_bus=bus)

    # Mock header
    mock_header = MockHeader()
    class MockApp:
        def query_one(self, _):
            return mock_header
    controller.app = MockApp()

    # Simula on_mount
    controller._running = True
    controller._consumer_task = asyncio.create_task(controller._consume_tts_events())
    await asyncio.sleep(0.01)

    # Publica evento thinking
    await bus.publish(TTSStartedEvent(
        turn_id="turn-1",
        text="Hum...",
        mode="THINKING"
    ))

    # Aguarda processamento
    await asyncio.sleep(0.05)

    # Verifica que header foi atualizado
    assert mock_header.state == "thinking"
    assert mock_header.start_thinking_count == 1

    # Cleanup
    controller._running = False
    if controller._consumer_task:
        controller._consumer_task.cancel()


@pytest.mark.asyncio
async def test_waveform_controller_stops_on_completed():
    """Teste: TTSCompletedEvent para waveform."""
    bus = InMemoryEventBus()
    controller = WaveformControllerV2(event_bus=bus)

    # Mock header
    mock_header = MockHeader()
    class MockApp:
        def query_one(self, _):
            return mock_header
    controller.app = MockApp()

    # Simula on_mount
    controller._running = True
    controller._consumer_task = asyncio.create_task(controller._consume_tts_events())
    await asyncio.sleep(0.01)

    # Publica started + completed
    await bus.publish(TTSStartedEvent(
        turn_id="turn-1",
        text="Texto",
        mode="NORMAL"
    ))
    await asyncio.sleep(0.02)

    await bus.publish(TTSCompletedEvent(
        turn_id="turn-1",
        text="Texto",
        duration_ms=1000,
        metadata={}
    ))
    await asyncio.sleep(0.05)

    # Verifica que waveform parou
    assert mock_header.state is None
    assert mock_header.stop_count >= 1

    # Cleanup
    controller._running = False
    if controller._consumer_task:
        controller._consumer_task.cancel()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
