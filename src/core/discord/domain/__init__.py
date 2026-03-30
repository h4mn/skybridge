# -*- coding: utf-8 -*-
"""
Domain Layer - Camada de domínio do módulo Discord.

Esta camada contém:
- Entities: Message, Channel, Thread, Attachment
- Value Objects: IDs, MessageContent, AccessPolicy
- Domain Events: MessageReceived, MessageSent, ButtonClicked
- Domain Services: AccessService, MessageChunker
- Repository Interfaces: MessageRepository, ChannelRepository

Regras de dependência:
- Domain NÃO depende de Application, Infrastructure ou Presentation
- Domain é o núcleo independente do sistema
"""

from . import entities
from . import value_objects
from . import events
from . import services
from . import repositories

# Re-exports comuns
from .entities import (
    Message,
    Channel,
    ChannelType,
    Thread,
    Attachment,
    Reaction,
    MessageEditError,
)
from .value_objects import (
    ChannelId,
    MessageId,
    UserId,
    MessageContent,
    MessageTooLongError,
    AccessPolicy,
    DMPolicy,
    GroupPolicyType,
)
from .events import (
    DomainEvent,
    MessageReceivedEvent,
    MessageSentEvent,
    ButtonClickedEvent,
)
from .services import (
    AccessService,
    AccessResult,
    MessageChunker,
    ChunkResult,
)
from .repositories import (
    MessageRepository,
    ChannelRepository,
)

__all__ = [
    # Entities
    "entities",
    "Message",
    "Channel",
    "ChannelType",
    "Thread",
    "Attachment",
    "Reaction",
    "MessageEditError",
    # Value Objects
    "value_objects",
    "ChannelId",
    "MessageId",
    "UserId",
    "MessageContent",
    "MessageTooLongError",
    "AccessPolicy",
    "DMPolicy",
    "GroupPolicyType",
    # Events
    "events",
    "DomainEvent",
    "MessageReceivedEvent",
    "MessageSentEvent",
    "ButtonClickedEvent",
    # Services
    "services",
    "AccessService",
    "AccessResult",
    "MessageChunker",
    "ChunkResult",
    # Repositories
    "repositories",
    "MessageRepository",
    "ChannelRepository",
]
