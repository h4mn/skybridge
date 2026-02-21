# coding: utf-8
"""
Memória persistente da Sky.

Sky nunca esquece. Aprendizados são salvos em disco
e recuperados a cada vez que ela acorda.

Agora com suporte a busca semântica RAG!
"""

import json
import os
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any, Optional


# Feature flag para usar RAG
USE_RAG_MEMORY = os.getenv("USE_RAG_MEMORY", "false").lower() in ("true", "1", "yes")


class PersistentMemory:
    """
    Memória persistente da Sky.

    Salva aprendizados em disco e recupera ao iniciar.
    Agora com suporte opcional a busca semântica RAG.
    """

    def __init__(self, data_dir: str | None = None, use_rag: Optional[bool] = None):
        """
        Inicializa memória persistente.

        Args:
            data_dir: Diretório para salvar dados. Padrão: ~/.skybridge
            use_rag: Se True, usa busca semântica RAG. Padrão: USE_RAG_MEMORY env var.
        """
        if data_dir is None:
            data_dir = Path.home() / ".skybridge"

        self._data_dir = Path(data_dir)
        self._data_dir.mkdir(parents=True, exist_ok=True)

        # Arquivo de memória (legacy JSON)
        self._memory_file = self._data_dir / "sky_memory.json"

        # Determinar se deve usar RAG
        if use_rag is None:
            use_rag = USE_RAG_MEMORY
        self._use_rag = use_rag

        # Lazy load do CognitiveMemory (só se usar RAG)
        self._cognitive_memory: Optional[Any] = None

        # Carrega memória existente (sempre carrega JSON para compatibilidade)
        self._learnings: List[Dict[str, Any]] = self._load()

    def _get_cognitive_memory(self):
        """Lazy load do CognitiveMemory."""
        if self._cognitive_memory is None and self._use_rag:
            from .cognitive_layer import get_cognitive_memory
            self._cognitive_memory = get_cognitive_memory()
        return self._cognitive_memory

    def _load(self) -> List[Dict[str, Any]]:
        """
        Carrega memória do disco (legacy JSON).

        Returns:
            Lista de aprendizados carregados.
        """
        if not self._memory_file.exists():
            return []

        try:
            with open(self._memory_file, "r", encoding="utf-8") as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError):
            return []

    def _save(self) -> None:
        """Salva memória no disco (legacy JSON)."""
        with open(self._memory_file, "w", encoding="utf-8") as f:
            json.dump(self._learnings, f, ensure_ascii=False, indent=2)

    def _infer_collection(self, content: str) -> str:
        """
        Infere a coleção apropriada baseado no conteúdo.

        Args:
            content: Conteúdo da memória.

        Returns:
            Nome da coleção.
        """
        content_lower = content.lower()

        # Palavras-chave para cada coleção
        if any(kw in content_lower for kw in ["eu sou", "eu sou sky", "minha identidade"]):
            return "identity"
        if any(kw in content_lower for kw in ["juntos", "compartilhamos", "momento", "vez que"]):
            return "shared-moments"
        if any(kw in content_lower for kw in ["papai ensinou", "ensinamento", "lição"]):
            return "teachings"
        if any(kw in content_lower for kw in ["deploy", "status", "agora", "hoje"]):
            return "operational"

        # Padrão: operational (vida curta)
        return "operational"

    def learn(self, content: str, collection: Optional[str] = None) -> None:
        """
        Registra um novo aprendizado e salva em disco.

        Args:
            content: O que foi aprendido.
            collection: Coleção específica (só usado com RAG).
        """
        # Salvar no JSON (legacy)
        learning = {
            "content": content,
            "timestamp": datetime.now().isoformat(),
            "type": "learning",
        }
        self._learnings.append(learning)
        self._save()

        # Se usando RAG, também salvar no CognitiveMemory
        if self._use_rag:
            cognitive = self._get_cognitive_memory()
            if cognitive:
                # Inferir coleção se não especificada
                if collection is None:
                    collection = self._infer_collection(content)

                cognitive.learn(
                    content=content,
                    collection=collection,
                    metadata={"source_type": "learn"},
                )

    def get_all_learnings(self) -> List[Dict[str, Any]]:
        """
        Retorna todos os aprendizados.

        Returns:
            Lista de todos os aprendizados.
        """
        return self._learnings.copy()

    def get_today_learnings(self) -> List[str]:
        """
        Retorna o que aprendeu hoje.

        Returns:
            Lista de conteúdos aprendidos hoje.
        """
        today = datetime.now().date()
        today_learnings = []

        for learning in self._learnings:
            learning_date = datetime.fromisoformat(learning["timestamp"]).date()
            if learning_date == today:
                today_learnings.append(learning["content"])

        return today_learnings

    def search(self, query: str, top_k: int = 5) -> List[Dict[str, Any]]:
        """
        Busca aprendizados por conteúdo.

        Com RAG: busca semântica com roteamento automático.
        Sem RAG: busca por substring (legacy).

        Args:
            query: Termo de busca.
            top_k: Número máximo de resultados (só com RAG).

        Returns:
            Lista de aprendizados encontrados.
        """
        # Se usando RAG, busca semântica
        if self._use_rag:
            cognitive = self._get_cognitive_memory()
            if cognitive:
                results = cognitive.search(query, top_k=top_k)
                # Converter para formato compatível
                return [
                    {
                        "content": r.content,
                        "timestamp": r.created_at or datetime.now().isoformat(),
                        "similarity": r.similarity,
                        "collection": r.collection,
                    }
                    for r in results
                ]

        # Legacy: busca por substring
        query_lower = query.lower()
        return [
            learning
            for learning in self._learnings
            if query_lower in learning["content"].lower()
        ][:top_k]

    def is_rag_enabled(self) -> bool:
        """
        Retorna se RAG está habilitado.

        Returns:
            True se busca semântica está ativa.
        """
        return self._use_rag

    def enable_rag(self) -> None:
        """Habilita busca semântica RAG."""
        self._use_rag = True

    def disable_rag(self) -> None:
        """Desabilita busca semântica RAG."""
        self._use_rag = False


# Instância global
_persistent_memory: PersistentMemory | None = None


def get_memory() -> PersistentMemory:
    """
    Retorna a memória persistente da Sky.

    Returns:
        Memória persistente.
    """
    global _persistent_memory
    if _persistent_memory is None:
        _persistent_memory = PersistentMemory()
    return _persistent_memory


__all__ = [
    "PersistentMemory",
    "get_memory",
    "USE_RAG_MEMORY",
    # Novos exports RAG
    "CognitiveMemory",
    "IntentRouter",
    "MemoryResult",
    "VectorStore",
    "CollectionConfig",
    "CollectionManager",
    "SourceType",
    "get_cognitive_memory",
    "get_vector_store",
    "get_collection_manager",
    "get_embedding_client",
]

# Re-exports para facilitar importações
from .cognitive_layer import CognitiveMemory, IntentRouter, MemoryResult, get_cognitive_memory
from .vector_store import VectorStore, get_vector_store
from .collections import CollectionConfig, CollectionManager, SourceType, get_collection_manager
from .embedding import get_embedding_client
