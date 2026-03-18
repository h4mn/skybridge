# coding: utf-8
"""
Vector Store - Wrapper sqlite-vec para busca vetorial.

Exporta classes para busca semântica usando embeddings.
"""

from .vector_store import (
    VectorStore,
    SearchResult,
    get_vector_store,
    EMBEDDING_DIM,
)

__all__ = [
    "VectorStore",
    "SearchResult",
    "get_vector_store",
    "EMBEDDING_DIM",
]
