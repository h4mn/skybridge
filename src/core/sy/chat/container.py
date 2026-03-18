# coding: utf-8
"""
ChatContainer - Container DI com Lifecycle para Chat.

DOC: openspec/changes/refactor-chat-event-driven/design.md

Gerencia lifecycle de todas as dependências do chat (EventBus, TTSService,
ChatOrchestrator) com AsyncContextManager para garantir resource safety.

## Responsabilidades

- Criar todas as dependências na ordem correta
- Gerenciar lifecycle com async with (cleanup garantido)
- Fazer shutdown em ordem reversa (TTS → Chat → EventBus)
- Expor serviços prontos para uso

## Exemplo

```python
from core.sy.chat import ChatContainer

async with ChatContainer.create() as container:
    orchestrator = container.orchestrator
    async for chunk in orchestrator.process_turn("Oi Sky", turn_id="turn-1"):
        print(f"Chunk: {chunk.content}")
# Cleanup automático: TTS → Chat → EventBus
```
"""

from types import TracebackType
from typing import AsyncIterator, Self

from core.sky.chat.claude_chat import ClaudeChatAdapter
from core.sy.chat.orchestrator import ChatOrchestrator
from core.sy.events import InMemoryEventBus
from core.sy.voice import TTSService


class ChatContainerContext:
    """
    AsyncContextManager para criar e gerenciar ChatContainer.

    Permite uso direto com async with:

    ```python
    async with ChatContainerContext() as container:
        # use container
    ```

    Internamente chama ChatContainer.create() e garante cleanup.
    """

    def __init__(self, chat: ClaudeChatAdapter | None = None) -> None:
        self._chat = chat
        self._container: ChatContainer | None = None

    async def __aenter__(self) -> "ChatContainer":
        self._container = await ChatContainer.create(chat=self._chat)
        return self._container

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: TracebackType | None,
    ) -> None:
        if self._container:
            await self._container.shutdown()


class ChatContainer:
    """
    Container DI com Lifecycle para componentes do Chat.

    Responsável por criar e gerenciar o lifecycle de todas as dependências:
    - InMemoryEventBus: Barramento de eventos
    - TTSService: Serviço TTS isolado
    - ChatOrchestrator: Coordenador de chat + TTS

    Implementa AsyncContextManager para garantir cleanup em caso de exceção.
    """

    def __init__(
        self,
        event_bus: InMemoryEventBus,
        tts_service: TTSService,
        orchestrator: ChatOrchestrator,
    ) -> None:
        """
        Inicializa o ChatContainer com dependências já criadas.

        Args:
            event_bus: EventBus para comunicação entre componentes
            tts_service: Serviço TTS isolado
            orchestrator: Coordenador de chat + TTS
        """
        self._event_bus = event_bus
        self._tts_service = tts_service
        self._orchestrator = orchestrator

    @property
    def event_bus(self) -> InMemoryEventBus:
        """Retorna o EventBus."""
        return self._event_bus

    @property
    def tts_service(self) -> TTSService:
        """Retorna o TTSService."""
        return self._tts_service

    @property
    def orchestrator(self) -> ChatOrchestrator:
        """Retorna o ChatOrchestrator."""
        return self._orchestrator

    @classmethod
    async def create(cls, chat: ClaudeChatAdapter | None = None) -> Self:
        """
        Factory method que cria e inicializa o container.

        Cria dependências na ordem:
        1. InMemoryEventBus
        2. TTSService (já startado)
        3. ChatOrchestrator

        Args:
            chat: ClaudeChatAdapter opcional. Se None, cria instância padrão.

        Returns:
            ChatContainer inicializado e pronto para uso
        """
        # 1. Cria EventBus
        event_bus = InMemoryEventBus()

        # 2. Cria e inicia TTSService
        tts_service = TTSService(event_bus=event_bus)
        await tts_service.start()

        # 3. Cria ClaudeChatAdapter se não fornecido
        if chat is None:
            chat = ClaudeChatAdapter()

        # 4. Cria ChatOrchestrator
        orchestrator = ChatOrchestrator(
            chat=chat,
            tts_service=tts_service,
            event_bus=event_bus,
        )

        return cls(
            event_bus=event_bus,
            tts_service=tts_service,
            orchestrator=orchestrator,
        )

    async def shutdown(self) -> None:
        """
        Faz shutdown dos recursos em ordem reversa.

        Ordem de shutdown:
        1. TTSService.stop()
        2. (EventBus não precisa de cleanup)
        3. (ChatOrchestrator não tem estado interno)

        Não levanta exceção se chamado múltiplas vezes.
        """
        # Para TTSService
        if self._tts_service.is_running:
            await self._tts_service.stop()

    async def __aenter__(self) -> Self:
        """
        Entry point do AsyncContextManager.

        Returns:
            Self para uso em async with
        """
        return self

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: TracebackType | None,
    ) -> None:
        """
        Exit point do AsyncContextManager.

        Garante cleanup mesmo em caso de exceção.

        Args:
            exc_type: Tipo da exceção (se houver)
            exc_val: Valor da exceção (se houver)
            exc_tb: Traceback da exceção (se houver)
        """
        await self.shutdown()
