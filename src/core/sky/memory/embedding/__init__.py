# coding: utf-8
"""
Embedding Client - Geração de embeddings locais.

Exporta interface e implementação para embeddings com sentence-transformers.
"""

from .embedding import (
    EmbeddingClient,
    SentenceTransformerEmbedding,
    get_embedding_client,
    set_progress_callback,
    get_progress_callback,
    EMBEDDING_DIM,
    DEFAULT_MODEL,
)

__all__ = [
    "EmbeddingClient",
    "SentenceTransformerEmbedding",
    "get_embedding_client",
    "set_progress_callback",
    "get_progress_callback",
    "EMBEDDING_DIM",
    "DEFAULT_MODEL",
]
