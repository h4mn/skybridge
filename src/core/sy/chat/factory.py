# coding: utf-8
"""
Factory functions para componentes do Chat.

DOC: openspec/changes/refactor-chat-event-driven/design.md

Funções factory opcionais para customização de dependências.
Útil para testes e variações de configuração.
"""

from core.sky.chat.claude_chat import ClaudeChatAdapter
from core.sy.chat.orchestrator import ChatOrchestrator
from core.sy.events import InMemoryEventBus
from core.sy.voice import TTSService


async def create_chat_container(
    chat: ClaudeChatAdapter | None = None,
    event_bus: InMemoryEventBus | None = None,
    auto_start_tts: bool = True,
) -> "ChatContainer":
    """
    Factory function para criar ChatContainer com customizações.

    Args:
        chat: ClaudeChatAdapter opcional. Se None, cria instância padrão.
        event_bus: EventBus opcional. Se None, cria InMemoryEventBus.
        auto_start_tts: Se True, inicia TTSService automaticamente.

    Returns:
        ChatContainer configurado

    Example:
        ```python
        from core.sy.chat.factory import create_chat_container

        # Usando defaults
        container = await create_chat_container()

        # Com chat customizado
        custom_chat = ClaudeChatAdapter(system_prompt="...")
        container = await create_chat_container(chat=custom_chat)

        # Sem iniciar TTS automaticamente
        container = await create_chat_container(auto_start_tts=False)
        ```
    """
    # Import aqui para evitar circular import
    from core.sy.chat.container import ChatContainer

    # Cria EventBus se não fornecido
    if event_bus is None:
        event_bus = InMemoryEventBus()

    # Cria TTSService
    tts_service = TTSService(event_bus=event_bus)

    # Inicia TTS se solicitado
    if auto_start_tts:
        await tts_service.start()

    # Cria ClaudeChatAdapter se não fornecido
    if chat is None:
        chat = ClaudeChatAdapter()

    # Cria ChatOrchestrator
    orchestrator = ChatOrchestrator(
        chat=chat,
        tts_service=tts_service,
        event_bus=event_bus,
    )

    return ChatContainer(
        event_bus=event_bus,
        tts_service=tts_service,
        orchestrator=orchestrator,
    )


async def create_orchestrator_only() -> ChatOrchestrator:
    """
    Factory function para criar apenas ChatOrchestrator sem container.

    Útil para casos onde não se precisa do lifecycle management do container.

    Returns:
        ChatOrchestrator configurado com TTSService não iniciado

    Example:
        ```python
        from core.sy.chat.factory import create_orchestrator_only

        orchestrator = await create_orchestrator_only()
        # TTSService não está rodando - você precisa iniciar manualmente
        await orchestrator._tts.start()
        ```
    """
    event_bus = InMemoryEventBus()
    tts_service = TTSService(event_bus=event_bus)
    chat = ClaudeChatAdapter()

    return ChatOrchestrator(
        chat=chat,
        tts_service=tts_service,
        event_bus=event_bus,
    )


def create_event_bus() -> InMemoryEventBus:
    """
    Factory function para criar EventBus isolado.

    Útil para testes ou quando se precisa de um EventBus separado.

    Returns:
        InMemoryEventBus novo
    """
    return InMemoryEventBus()
