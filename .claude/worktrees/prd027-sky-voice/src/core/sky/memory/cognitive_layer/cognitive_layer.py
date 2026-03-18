# coding: utf-8
"""
Cognitive Layer - Orquestrador RAG para memória semântica.

Implementa roteamento de intenção, busca híbrida e re-ranking.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Optional

from ..vector_store import VectorStore, SearchResult, get_vector_store
from ..embedding import SentenceTransformerEmbedding, get_embedding_client
from ..collections import CollectionConfig, CollectionManager, get_collection_manager


@dataclass
class MemoryResult:
    """Resultado de busca de memória com score."""

    id: int
    content: str
    collection: str
    similarity: float  # 0-1, maior = mais similar
    distance: float
    created_at: Optional[str] = None
    metadata: dict = field(default_factory=dict)


class IntentRouter:
    """
    Roteador de intenção para queries de memória.

    Detecta o tipo de pergunta e roteia para a coleção apropriada.
    """

    # Padrões de roteamento para cada coleção
    PATTERNS = {
        "identity": [
            r"quem (é|você é|são vocês)",
            r"o que (você|sky) (é|sabe|pode)",
            r"descreva(-se)?\s*$",
            r"suas (características|capacidades)",
        ],
        "shared-moments": [
            r"lembra?(?!te)|recorda",
            r"momento|vez que|juntos",
            r"nossa (memória|experiência|história)",
        ],
        "teachings": [
            r"(o que )?papai (me )?ensinou",
            r"ensinamento|lição|aprendi",
            r"papai (me )?disse|falou",
        ],
        "operational": [
            r"o que (aconteceu|está (acontecendo|ocorrendo))",
            r"(hoje|agora|recentemente)",
            r"status|estado (atual|atualmente)",
        ],
    }

    def __init__(self):
        """Inicializa IntentRouter."""
        # Compilar regexes para performance
        self._compiled_patterns = {
            collection: [re.compile(pattern, re.IGNORECASE) for pattern in patterns]
            for collection, patterns in self.PATTERNS.items()
        }

    def route_query(self, query: str) -> list[str]:
        """
        Roteia query para coleções apropriadas.

        Args:
            query: Query do usuário.

        Returns:
            Lista de coleções para buscar (pode ser múltipla ou todas).
        """
        query_lower = query.lower()

        # Verificar cada coleção
        matched = []
        for collection, patterns in self._compiled_patterns.items():
            if any(pattern.search(query) for pattern in patterns):
                matched.append(collection)

        # Se nenhuma correspondeu, buscar todas
        if not matched:
            return list(self.PATTERNS.keys())

        return matched

    def detect_intent(self, query: str) -> str:
        """
        Detecta a intenção principal da query.

        Args:
            query: Query do usuário.

        Returns:
            Nome da intenção/coleção principal.
        """
        collections = self.route_query(query)
        return collections[0] if collections else "operational"


class CognitiveMemory:
    """
    Camada cognitiva de memória.

    Orquestra:
    - Ingestão de memórias com embedding
    - Busca semântica com roteamento
    - Re-ranking por relevância + recência
    - Deduplicação de resultados similares
    """

    def __init__(
        self,
        embedding_client: Optional[SentenceTransformerEmbedding] = None,
        vector_store: Optional[VectorStore] = None,
        collection_manager: Optional[CollectionManager] = None,
    ):
        """
        Inicializa CognitiveMemory.

        Args:
            embedding_client: Cliente de embeddings (singleton se None).
            vector_store: Vector store (singleton se None).
            collection_manager: Gerenciador de coleções (singleton se None).
        """
        self._embedding = embedding_client or get_embedding_client()
        self._vector_store = vector_store or get_vector_store()
        self._collection_manager = collection_manager or get_collection_manager()
        self._router = IntentRouter()

    def learn(
        self,
        content: str,
        collection: str,
        metadata: Optional[dict] = None,
    ) -> int:
        """
        Registra uma nova memória.

        Args:
            content: Conteúdo da memória.
            collection: Nome da coleção.
            metadata: Metadados adicionais.

        Returns:
            ID da memória inserida.
        """
        # Validar coleção
        config = self._collection_manager.get_collection(collection)
        if config is None:
            raise ValueError(f"Coleção inválida: {collection}")

        # Gerar embedding
        embedding = self._embedding.encode(content)

        # Inserir no vector store
        memory_id = self._vector_store.insert_vector(
            collection=collection,
            embedding=embedding,
            content=content,
            metadata=metadata or {},
        )

        return memory_id

    def search(
        self,
        query: str,
        top_k: int = 5,
        collection: Optional[str] = None,
        threshold: float = 0.0,
        hybrid_keywords: bool = True,
    ) -> list[MemoryResult]:
        """
        Busca memórias por similaridade semântica.

        Args:
            query: Query de busca.
            top_k: Número máximo de resultados por coleção.
            collection: Coleção específica ou None (rota automaticamente).
            threshold: Score mínimo de similaridade (0-1).
            hybrid_keywords: Se True, filtra por keywords também.

        Returns:
            Lista de MemoryResult ordenados por relevância.
        """
        # Rotear query se coleção não especificada
        if collection is None:
            collections = self._router.route_query(query)
        else:
            collections = [collection]

        # Gerar embedding da query
        query_embedding = self._embedding.encode(query)

        # Buscar em cada coleção
        all_results = []
        for coll in collections:
            results = self._vector_store.search_vectors(
                collection=coll,
                query_vector=query_embedding,
                k=top_k,
            )
            all_results.extend(results)

        # Converter para MemoryResult e aplicar filtro de keywords
        memory_results = self._to_memory_results(all_results, query, hybrid_keywords)

        # Aplicar threshold
        if threshold > 0:
            memory_results = [r for r in memory_results if r.similarity >= threshold]

        # Re-rank por relevância + recência
        memory_results = self._rerank(memory_results)

        # Deduplicar resultados muito similares
        memory_results = self._deduplicate(memory_results)

        return memory_results[:top_k]

    def _to_memory_results(
        self,
        search_results: list[SearchResult],
        query: str,
        filter_keywords: bool,
    ) -> list[MemoryResult]:
        """
        Converte SearchResult para MemoryResult.

        Args:
            search_results: Resultados do VectorStore.
            query: Query original (para filtro de keywords).
            filter_keywords: Se deve filtrar por keywords.

        Returns:
            Lista de MemoryResult.
        """
        results = []
        query_lower = query.lower()

        # Extrair keywords da query (remover stop words)
        keywords = self._extract_keywords(query_lower)

        for sr in search_results:
            # Converter distância para similaridade (0-1)
            similarity = 1.0 / (1.0 + sr.distance)

            # Filtro de keywords (opcional)
            if filter_keywords and keywords:
                content_lower = sr.content.lower()
                # Pelo menos uma keyword deve estar presente
                if not any(kw in content_lower for kw in keywords):
                    continue

            results.append(MemoryResult(
                id=sr.id,
                content=sr.content,
                collection="",  # Será preenchido depois
                similarity=similarity,
                distance=sr.distance,
                metadata=sr.metadata,
            ))

        return results

    def _extract_keywords(self, query: str) -> list[str]:
        """
        Extrai keywords relevantes da query.

        Args:
            query: Query em minúsculas.

        Returns:
            Lista de keywords (sem stop words).
        """
        # Stop words simples em português
        stop_words = {
            "o", "a", "os", "as", "um", "uma", "uns", "umas",
            "de", "do", "da", "dos", "das", "em", "para", "por",
            "com", "sem", "que", "quem", "como", "onde", "quando",
            "é", "foi", "está", "estou", "sou", "são", "me", "te",
            "lhe", "seu", "sua", "seus", "suas", "nosso", "nossa",
        }

        # Tokenizar e filtrar
        words = re.findall(r"\b\w+\b", query)
        keywords = [w for w in words if w not in stop_words and len(w) > 2]

        return keywords

    def _rerank(self, results: list[MemoryResult]) -> list[MemoryResult]:
        """
        Re-ranca resultados por relevância + recência.

        Args:
            results: Lista de MemoryResult.

        Returns:
            Lista re-ordenada.
        """
        # Score combinado: 70% similaridade + 30% recência
        # Recência é calculada baseado na data de criação

        now = datetime.now()

        def score_with_recency(result: MemoryResult) -> float:
            base_score = result.similarity * 0.7

            # Recency bonus (mais recente = maior bonus)
            if result.created_at:
                try:
                    created = datetime.fromisoformat(result.created_at)
                    days_old = (now - created).days
                    # Decay: 1.0 para hoje, 0.5 para 30 dias
                    recency_bonus = max(0.0, 1.0 - (days_old / 60))
                    base_score += recency_bonus * 0.3
                except (ValueError, TypeError):
                    pass

            return base_score

        return sorted(results, key=score_with_recency, reverse=True)

    def _deduplicate(self, results: list[MemoryResult]) -> list[MemoryResult]:
        """
        Remove resultados muito similares (>0.95 de similaridade).

        Args:
            results: Lista de MemoryResult.

        Returns:
            Lista sem duplicatas.
        """
        if not results:
            return []

        deduped = [results[0]]

        for result in results[1:]:
            # Comparar com todos já adicionados
            is_duplicate = False
            for existing in deduped:
                if result.similarity > 0.95 and existing.similarity > 0.95:
                    # Similaridade muito alta, comparar conteúdo
                    if self._content_similarity(result.content, existing.content) > 0.95:
                        is_duplicate = True
                        break

            if not is_duplicate:
                deduped.append(result)

        return deduped

    def _content_similarity(self, text1: str, text2: str) -> float:
        """
        Calcula similaridade simples entre dois textos.

        Args:
            text1: Primeiro texto.
            text2: Segundo texto.

        Returns:
            Similaridade (0-1).
        """
        # Similaridade de Jaccard simples baseada em palavras
        words1 = set(re.findall(r"\b\w+\b", text1.lower()))
        words2 = set(re.findall(r"\b\w+\b", text2.lower()))

        if not words1 or not words2:
            return 0.0

        intersection = len(words1 & words2)
        union = len(words1 | words2)

        return intersection / union if union > 0 else 0.0


# Singleton global
_cognitive_memory: Optional[CognitiveMemory] = None


def get_cognitive_memory() -> CognitiveMemory:
    """
    Retorna instância singleton do CognitiveMemory.

    Returns:
        Instância do CognitiveMemory.
    """
    global _cognitive_memory
    if _cognitive_memory is None:
        _cognitive_memory = CognitiveMemory()
    return _cognitive_memory
