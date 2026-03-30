# -*- coding: utf-8 -*-
"""
Domain Services - Serviços de domínio Discord.
"""

from .access_service import AccessService, AccessResult
from .message_chunker import MessageChunker, ChunkResult

__all__ = [
    "AccessService",
    "AccessResult",
    "MessageChunker",
    "ChunkResult",
]
