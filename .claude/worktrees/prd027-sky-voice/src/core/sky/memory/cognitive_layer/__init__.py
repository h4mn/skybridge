# coding: utf-8
"""
Cognitive Layer - Orquestrador RAG (roteamento + busca híbrida).

Exporta classes para busca semântica e roteamento de intenção.
"""

from .cognitive_layer import (
    CognitiveMemory,
    IntentRouter,
    MemoryResult,
    get_cognitive_memory,
)

__all__ = [
    "CognitiveMemory",
    "IntentRouter",
    "MemoryResult",
    "get_cognitive_memory",
]
