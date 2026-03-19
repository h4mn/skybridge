# coding: utf-8
"""
POC - Prova de Conceito: Arquitetura Event-Driven Chat

DOC: openspec/changes/refactor-chat-event-driven

Ponto de entrada para demonstrar a nova arquitetura com:
- EventBus para comunicação loose-coupled
- TTSService com worker assíncrono
- ChatOrchestrator coordenando chat + TTS
- ChatContainer com lifecycle automático

Uso:
    python -m core.sky.events.poc           # Demo completa
    python -m core.sky.events.poc tts      # Demo TTS isolado
    python -m core.sky.events.poc eventbus # Demo EventBus isolado
"""

import asyncio
import time
from typing import AsyncIterator

from core.sky.chat import ClaudeChatAdapter
from core.sky.chat.container import ChatContainer
from core.sky.chat.events import (
    StreamChunkEvent,
    TTSCompletedEvent,
    TTSStartedEvent,
    TurnCompletedEvent,
    TurnStartedEvent,
)
from core.sky.events import InMemoryEventBus


async def demo_event_driven_chat() -> None:
    """
    Demonstração completa da arquitetura event-driven.

    Fluxo:
    1. Cria ChatContainer com todos componentes
    2. Inicia listeners de eventos em background
    3. Processa uma mensagem de exemplo
    4. Mostra eventos sendo publicados/consumidos
    5. Cleanup automático ao sair
    """
    print("=" * 60)
    print("POC: Arquitetura Event-Driven Chat")
    print("=" * 60)

    # Cria container com todos componentes
    container = await ChatContainer.create()

    async with container:
        event_bus = container.event_bus
        tts_service = container.tts_service
        orchestrator = container.orchestrator

        print("\n[OK] Componentes inicializados:")
        print(f"  - EventBus: {type(event_bus).__name__}")
        print(f"  - TTSService: {type(tts_service).__name__}")
        print(f"  - ChatOrchestrator: {type(orchestrator).__name__}")

        # Inicia listeners de eventos em background
        listener_task = asyncio.create_task(
            _event_listener_task(event_bus)
        )

        # Processa um turno de chat
        print("\n" + "=" * 60)
        print("Processando mensagem: \"Olá Sky, quem e voce?\"")
        print("=" * 60 + "\n")

        turn_id = f"turn-{int(time.time())}"

        try:
            async for chunk in orchestrator.process_turn(
                user_message="Olá Sky, quem e voce?",
                turn_id=turn_id
            ):
                # Mostra chunks chegando
                print(f"[STREAM] {chunk.event_type:12} | {chunk.content[:50]}")

        except Exception as e:
            print(f"\n[ERRO] Erro durante processamento: {e}")
            raise
        finally:
            # Para listener task
            listener_task.cancel()
            try:
                await listener_task
            except asyncio.CancelledError:
                pass

        print("\n" + "=" * 60)
        print("[OK] Turno completado")
        print("=" * 60)

    # Cleanup automatico pelo context manager
    print("\n[OK] Container encerrado (cleanup automatico)")


async def _event_listener_task(event_bus: InMemoryEventBus) -> None:
    """
    Task que escuta todos os eventos e os imprime.

    Usa o padrão AsyncIterator do subscribe().
    """
    print("\n[OK] Event listeners ativos (mostrando eventos):\n")

    # Cria tasks para cada tipo de evento
    async def listen_turn_started():
        async for event in event_bus.subscribe(TurnStartedEvent):
            print(f"[EVENT] TurnStartedEvent")
            print(f"       turn_id: {event.turn_id}")
            print(f"       user_message: {event.user_message}\n")

    async def listen_tts_started():
        async for event in event_bus.subscribe(TTSStartedEvent):
            print(f"[AUDIO] TTS START modo={event.mode}")
            print(f"    texto: \"{event.text[:50]}...\"\n")

    async def listen_tts_completed():
        async for event in event_bus.subscribe(TTSCompletedEvent):
            print(f"    [OK] TTS COMPLETE {event.duration_ms:.0f}ms\n")

    async def listen_turn_completed():
        async for event in event_bus.subscribe(TurnCompletedEvent):
            print(f"[EVENT] TurnCompletedEvent")
            print(f"       turn_id: {event.turn_id}")
            print(f"       duration_ms: {event.duration_ms:.0f}ms\n")

    # Executa todos os listeners em paralelo
    await asyncio.gather(
        listen_turn_started(),
        listen_tts_started(),
        listen_tts_completed(),
        listen_turn_completed(),
    )


async def demo_tts_only() -> None:
    """
    Demonstração isolada do TTSService.

    Útil para testar buffer/fala sem depender do chat.
    """
    from core.sky.chat.events import StreamChunkEvent
    from core.sky.voice import get_tts_adapter
    from core.sky.voice.streaming_tts_service import StreamingTTSService

    print("=" * 60)
    print("POC: TTSService Isolado")
    print("=" * 60)

    event_bus = InMemoryEventBus()
    tts_adapter = get_tts_adapter()
    tts_service = StreamingTTSService(event_bus=event_bus, tts_adapter=tts_adapter)

    # Listener de eventos TTS
    async def listen_tts_start():
        async for event in event_bus.subscribe(TTSStartedEvent):
            print(f"\n[AUDIO] TTS START modo={event.mode}")
            print(f"    texto: \"{event.text[:50]}...\"")

    async def listen_tts_complete():
        async for event in event_bus.subscribe(TTSCompletedEvent):
            print(f"    [OK] TTS COMPLETE {event.duration_ms:.0f}ms")

    listener_task = asyncio.create_task(listen_tts_start())
    listener_task2 = asyncio.create_task(listen_tts_complete())

    # Inicia serviço
    await tts_service.start()
    print("\n[OK] TTSService iniciado")

    # Teste 1: Texto curto (não deve falar imediatamente)
    print("\n--- Teste 1: Texto curto (< 50 chars) ---")
    await tts_service.enqueue(StreamChunkEvent(
        turn_id="test-1",
        content="Este é um texto curto.",
        event_type="TEXT"
    ))
    await asyncio.sleep(0.5)
    print("    (buffer acumulando, texto curto ainda não falado)")

    # Teste 2: Texto longo com pontuação (deve falar)
    print("\n--- Teste 2: Texto longo com pontuação (> 50 chars + .) ---")
    await tts_service.enqueue(StreamChunkEvent(
        turn_id="test-1",
        content="Este é um texto bem mais longo que tem cinquenta caracteres."
    ))
    await asyncio.sleep(3)  # Aguarda fala completar

    # Teste 3: Múltiplos chunks (buffer deve acumular)
    print("\n--- Teste 3: Múltiplos chunks (buffer) ---")
    await tts_service.enqueue(StreamChunkEvent(
        turn_id="test-2",
        content="Primeira parte do texto. ",
        event_type="TEXT"
    ))
    await tts_service.enqueue(StreamChunkEvent(
        turn_id="test-2",
        content="Segunda parte que completa.",
        event_type="TEXT"
    ))
    await asyncio.sleep(3)  # Aguarda fala completar

    # Para serviço
    await tts_service.stop()
    listener_task.cancel()
    listener_task2.cancel()

    print("\n[OK] TTSService encerrado")


async def demo_event_bus_only() -> None:
    """
    Demonstração isolada do EventBus.

    Mostra publish/subscribe e type-safety.
    """
    from core.sky.chat.events import StreamChunkEvent, TurnStartedEvent

    print("=" * 60)
    print("POC: EventBus Isolado")
    print("=" * 60)

    event_bus = InMemoryEventBus()

    # Listener de eventos
    async def listen_turn_started():
        async for event in event_bus.subscribe(TurnStartedEvent):
            print(f"  [Listener] TurnStarted: {event.user_message}")

    async def listen_stream_chunk():
        async for event in event_bus.subscribe(StreamChunkEvent):
            print(f"  [Listener] StreamChunk: {event.event_type} | {event.content[:30]}")

    # Cria tasks para cada listener
    listener_task = asyncio.create_task(listen_turn_started())
    listener_task2 = asyncio.create_task(listen_stream_chunk())

    print("\n[OK] Subscriber ativo")

    # Aguarda listeners iniciarem
    await asyncio.sleep(0.05)

    # Publica eventos
    print("\n--- Publicando TurnStartedEvent ---")
    await event_bus.publish(TurnStartedEvent(
        turn_id="demo-1",
        user_message="Teste de evento"
    ))
    await asyncio.sleep(0.1)  # Aguarda delivery

    print("\n--- Publicando StreamChunkEvent ---")
    await event_bus.publish(StreamChunkEvent(
        turn_id="demo-1",
        content="Conteúdo do chunk",
        event_type="TEXT"
    ))
    await asyncio.sleep(0.1)

    print("\n--- Publicando múltiplos chunks ---")
    for i in range(3):
        await event_bus.publish(StreamChunkEvent(
            turn_id="demo-1",
            content=f"Chunk {i+1}",
            event_type="TEXT"
        ))
    await asyncio.sleep(0.2)

    # Cleanup
    listener_task.cancel()
    listener_task2.cancel()
    await event_bus.shutdown()

    print("\n[OK] EventBus encerrado")


async def main() -> None:
    """
    Entry point para executar as demonstrações.
    """
    import sys

    # Escolhe qual demo executar
    demo = sys.argv[1] if len(sys.argv) > 1 else "full"

    if demo == "tts":
        await demo_tts_only()
    elif demo == "eventbus":
        await demo_event_bus_only()
    else:
        await demo_event_driven_chat()


if __name__ == "__main__":
    asyncio.run(main())
