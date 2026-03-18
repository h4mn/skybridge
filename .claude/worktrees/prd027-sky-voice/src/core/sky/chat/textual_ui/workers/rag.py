# coding: utf-8
"""
RAGWorker - Worker assíncrono para busca RAG.

Executa busca semântica em memória em background
sem bloquear a UI Textual.
"""

import asyncio
from dataclasses import dataclass
from typing import List

from core.sky.chat.textual_ui.workers.base import BaseWorker


@dataclass
class MemoryResult:
    """Resultado de busca de memória."""

    content: str
    similarity: float


@dataclass
class RAGResponse:
    """Resposta da busca RAG."""

    memories: List[MemoryResult]
    count: int


class RAGWorker(BaseWorker):
    """
    Worker assíncrono para busca RAG.

    Executa busca semântica no banco de memória
    em background, permitindo que a UI continue responsiva.
    """

    def __init__(self, memory_adapter):
        """
        Inicializa RAGWorker.

        Args:
            memory_adapter: Adaptador de memória (PersistentMemory).
        """
        super().__init__(memory_adapter)
        self.memory_adapter = memory_adapter

    async def search(
        self,
        query: str,
        top_k: int = 5,
        threshold: float = 0.6,
    ) -> RAGResponse:
        """
        Busca memórias relevantes via RAG.

        Args:
            query: Query de busca.
            top_k: Quantidade de resultados (padrão: 5).
            threshold: Score mínimo de similaridade (padrão: 0.6).

        Returns:
            RAGResponse com memórias encontradas.
        """
        # Yield para event loop (não bloquear UI)
        await self._yield_to_event_loop()

        results = self.memory_adapter.search_memory(
            query=query,
            top_k=top_k,
        )

        # Filtra por threshold e converte para MemoryResult
        memories = []
        for content, score in results:
            if score >= threshold:
                memories.append(MemoryResult(content=content, similarity=score))

        return RAGResponse(
            memories=memories,
            count=len(memories),
        )


__all__ = ["RAGWorker", "RAGResponse", "MemoryResult"]
