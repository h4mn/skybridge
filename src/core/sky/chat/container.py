# coding: utf-8
"""
ChatContainer - Container DI com Lifecycle.

DOC: openspec/changes/refactor-chat-event-driven/design.md

Container que gerencia EventBus, TTSService e ChatOrchestrator
com Dependency Injection e lifecycle explícito (start/stop).

Uso:
    async with ChatContainer.create() as container:
        orchestrator = container.orchestrator
        async for chunk in orchestrator.process_turn("Oi", "turn-1"):
            print(chunk.content)
    # Cleanup automático na saída do context manager
"""

from dataclasses import dataclass
from typing import AsyncIterator

from core.sky.chat.claude_chat import ClaudeChatAdapter
from core.sky.chat.orchestrator import ChatOrchestrator
from core.sky.events import InMemoryEventBus
from core.sky.voice.streaming_tts_service import StreamingTTSService
from core.sky.voice import get_tts_adapter


@dataclass
class ChatContainerContext:
    """
    Contexto gerenciado pelo ChatContainer.

    Attributes:
        event_bus: EventBus para comunicação entre componentes
        tts_service: Serviço TTS com worker assíncrono
        orchestrator: Orquestrador que coordena chat + TTS
    """
    event_bus: InMemoryEventBus
    tts_service: StreamingTTSService
    orchestrator: ChatOrchestrator


class ChatContainer:
    """
    Container DI com lifecycle para componentes do Chat.

    Responsabilidades:
    - Criar EventBus, TTSService e ChatOrchestrator
    - Gerenciar lifecycle em ordem correta (start/stop reverso)
    - Fornecer context manager para cleanup automático

    Ordem de startup:
    1. EventBus (sem dependências)
    2. TTSService (depende de EventBus)
    3. ChatOrchestrator (depende de EventBus, TTSService)

    Ordem de shutdown (reversa):
    1. ChatOrchestrator (nada para limpar)
    2. TTSService (para worker)
    3. EventBus (notifica subscribers)
    """

    def __init__(
        self,
        event_bus: InMemoryEventBus,
        tts_service: StreamingTTSService,
        orchestrator: ChatOrchestrator,
    ):
        """
        Inicializa o ChatContainer com instâncias existentes.

        Args:
            event_bus: EventBus configurado
            tts_service: TTSService configurado
            orchestrator: ChatOrchestrator configurado

        NOTA: Prefira usar o factory method create() ao invés do __init__ direto.
        """
        self._event_bus = event_bus
        self._tts_service = tts_service
        self._orchestrator = orchestrator

    @property
    def orchestrator(self) -> ChatOrchestrator:
        """Retorna o ChatOrchestrator."""
        return self._orchestrator

    @property
    def event_bus(self) -> InMemoryEventBus:
        """Retorna o EventBus."""
        return self._event_bus

    @property
    def tts_service(self) -> StreamingTTSService:
        """Retorna o TTSService."""
        return self._tts_service

    @classmethod
    async def create(cls, chat: ClaudeChatAdapter | None = None) -> "ChatContainer":
        """
        Factory method que cria e inicializa todos componentes.

        Args:
            chat: ClaudeChatAdapter opcional (cria novo se None)

        Returns:
            ChatContainerContext com todos componentes inicializados

        Example:
            >>> container = await ChatContainer.create()
            >>> # ... usar container.orchestrator ...
            >>> await container.shutdown()
        """
        # Cria EventBus
        event_bus = InMemoryEventBus()

        # Cria TTSService com adapter TTS
        tts_adapter = get_tts_adapter()
        tts_service = StreamingTTSService(event_bus=event_bus, tts_adapter=tts_adapter)

        # Cria ChatOrchestrator
        orchestrator = ChatOrchestrator(
            chat=chat or ClaudeChatAdapter(),
            tts_service=tts_service,
            event_bus=event_bus
        )

        # Inicializa componentes em ordem
        await tts_service.start()

        # Retorna contexto gerenciado
        return cls(
            event_bus=event_bus,
            tts_service=tts_service,
            orchestrator=orchestrator
        )

    async def shutdown(self) -> None:
        """
        Encerra todos componentes em ordem reversa.

        Ordem:
        1. Para TTSService (worker para graciosamente)
        2. Para EventBus (notifica subscribers)
        """
        # Ordem reversa do startup
        await self._tts_service.stop()
        await self._event_bus.shutdown()

    async def __aenter__(self) -> "ChatContainer":
        """Context manager entry."""
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        """Context manager exit - garante cleanup."""
        await self.shutdown()
