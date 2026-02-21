# coding: utf-8
"""
Embedding Client - Geração de embeddings locais.

Exporta interface e implementação para embeddings com sentence-transformers.
"""

from .embedding import (
    EmbeddingClient,
    SentenceTransformerEmbedding,
    get_embedding_client,
    EMBEDDING_DIM,
    DEFAULT_MODEL,
)

__all__ = [
    "EmbeddingClient",
    "SentenceTransformerEmbedding",
    "get_embedding_client",
    "EMBEDDING_DIM",
    "DEFAULT_MODEL",
]
