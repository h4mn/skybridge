# coding: utf-8
"""
Collections - Configuração e gerenciamento de coleções vetoriais.

Exporta configurações e gerenciador para coleções de memória.
"""

from .collections import (
    CollectionConfig,
    CollectionManager,
    SourceType,
    get_collection_manager,
    DEFAULT_COLLECTIONS,
)

__all__ = [
    "CollectionConfig",
    "CollectionManager",
    "SourceType",
    "get_collection_manager",
    "DEFAULT_COLLECTIONS",
]
