# coding: utf-8
"""
Embedding Client - Geração de embeddings locais.

Interface e implementação para embeddings usando sentence-transformers.
"""

from __future__ import annotations

import hashlib
import sqlite3
from abc import ABC, abstractmethod
from pathlib import Path
from typing import List, Optional

try:
    from sentence_transformers import SentenceTransformer  # type: ignore
except ImportError:
    raise ImportError(
        "sentence-transformers é necessário. "
        "Instale com: pip install sentence-transformers"
    )

# Modelo padrão: multilingual, suporta PT-BR
DEFAULT_MODEL = "paraphrase-multilingual-MiniLM-L12-v2"
# Dimensão do embedding (modelo MiniLM)
EMBEDDING_DIM = 384


class EmbeddingClient(ABC):
    """Interface abstrata para clientes de embedding."""

    @abstractmethod
    def encode(self, text: str) -> List[float]:
        """
        Gera embedding para um texto.

        Args:
            text: Texto para codificar.

        Returns:
            Vetor de embedding.
        """

    @abstractmethod
    def encode_batch(self, texts: List[str]) -> List[List[float]]:
        """
        Gera embeddings para múltiplos textos.

        Args:
            texts: Lista de textos para codificar.

        Returns:
            Lista de vetores de embedding.
        """

    @abstractmethod
    def get_dimension(self) -> int:
        """
        Retorna dimensão dos embeddings.

        Returns:
            Dimensão do vetor.
        """


class SentenceTransformerEmbedding(EmbeddingClient):
    """
    Cliente de embedding usando sentence-transformers.

    Usa cache SQLite para evitar re-gerar embeddings do mesmo texto.
    """

    def __init__(
        self,
        model_name: str = DEFAULT_MODEL,
        db_path: Optional[Path] = None,
    ):
        """
        Inicializa cliente de embedding.

        Args:
            model_name: Nome do modelo HuggingFace.
            db_path: Caminho para banco de cache. Padrão: ~/.skybridge/sky_memory.db
        """
        self._model_name = model_name
        self._model: Optional[SentenceTransformer] = None

        # Configurar cache
        if db_path is None:
            data_dir = Path.home() / ".skybridge"
            data_dir.mkdir(parents=True, exist_ok=True)
            db_path = data_dir / "sky_memory.db"

        self._db_path = db_path
        self._init_cache()

    def _init_cache(self) -> None:
        """Inicializa tabela de cache de embeddings."""
        conn = sqlite3.connect(self._db_path)
        cursor = conn.cursor()

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS embeddings_cache (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                text_hash TEXT UNIQUE NOT NULL,
                text TEXT NOT NULL,
                embedding BLOB NOT NULL,
                model_name TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # Índice para busca rápida por hash
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_text_hash
            ON embeddings_cache(text_hash)
        """)

        conn.commit()
        conn.close()

    def _get_model(self) -> SentenceTransformer:
        """
        Lazy load do modelo (só carrega quando necessário).

        Returns:
            Instância do SentenceTransformer.
        """
        if self._model is None:
            print(f"📥 Carregando modelo {self._model_name}...")
            self._model = SentenceTransformer(self._model_name)
            print("✅ Modelo carregado!")
        return self._model

    def _hash_text(self, text: str) -> str:
        """
        Gera hash único do texto para cache.

        Args:
            text: Texto para hashear.

        Returns:
            Hash SHA256 do texto.
        """
        return hashlib.sha256(text.encode("utf-8")).hexdigest()

    def _serialize_embedding(self, embedding: List[float]) -> bytes:
        """
        Serializa embedding para bytes (armazenamento).

        Args:
            embedding: Lista de floats.

        Returns:
            Bytes representando o embedding.
        """
        import struct
        return struct.pack(f"{len(embedding)}f", *embedding)

    def _deserialize_embedding(self, data: bytes) -> List[float]:
        """
        Deserializa bytes para embedding.

        Args:
            data: Bytes do embedding.

        Returns:
            Lista de floats.
        """
        import struct
        # Descobrir dimensão
        dim = len(data) // 4  # 4 bytes por float
        return list(struct.unpack(f"{dim}f", data))

    def _get_from_cache(self, text_hash: str) -> Optional[List[float]]:
        """
        Busca embedding do cache.

        Args:
            text_hash: Hash do texto.

        Returns:
            Embedding se encontrado, None caso contrário.
        """
        conn = sqlite3.connect(self._db_path)
        cursor = conn.cursor()

        cursor.execute(
            "SELECT embedding FROM embeddings_cache WHERE text_hash = ? AND model_name = ?",
            (text_hash, self._model_name)
        )
        row = cursor.fetchone()
        conn.close()

        if row:
            return self._deserialize_embedding(row[0])
        return None

    def _save_to_cache(self, text_hash: str, text: str, embedding: List[float]) -> None:
        """
        Salva embedding no cache.

        Args:
            text_hash: Hash do texto.
            text: Texto original.
            embedding: Vetor de embedding.
        """
        conn = sqlite3.connect(self._db_path)
        cursor = conn.cursor()

        serialized = self._serialize_embedding(embedding)

        cursor.execute(
            """
            INSERT OR REPLACE INTO embeddings_cache (text_hash, text, embedding, model_name)
            VALUES (?, ?, ?, ?)
            """,
            (text_hash, text, serialized, self._model_name)
        )

        conn.commit()
        conn.close()

    def encode(self, text: str) -> List[float]:
        """
        Gera embedding para um texto, com cache.

        Args:
            text: Texto para codificar.

        Returns:
            Vetor de embedding (dimensão EMBEDDING_DIM).
        """
        # Verificar cache
        text_hash = self._hash_text(text)
        cached = self._get_from_cache(text_hash)
        if cached is not None:
            return cached

        # Gerar embedding
        model = self._get_model()
        embedding = model.encode(text).tolist()

        # Salvar no cache
        self._save_to_cache(text_hash, text, embedding)

        return embedding

    def encode_batch(self, texts: List[str]) -> List[List[float]]:
        """
        Gera embeddings para múltiplos textos, com cache.

        Args:
            texts: Lista de textos para codificar.

        Returns:
            Lista de vetores de embedding.
        """
        results = []
        missed_indices = []
        missed_texts = []

        # Primeiro: verificar cache para todos
        for i, text in enumerate(texts):
            text_hash = self._hash_text(text)
            cached = self._get_from_cache(text_hash)
            if cached is not None:
                results.append(cached)
            else:
                results.append(None)  # Placeholder
                missed_indices.append(i)
                missed_texts.append(text)

        # Segundo: gerar embeddings para textos não cacheados
        if missed_texts:
            model = self._get_model()
            new_embeddings = model.encode(missed_texts).tolist()

            # Salvar no cache e preencher resultados
            for idx, text, embedding in zip(missed_indices, missed_texts, new_embeddings):
                text_hash = self._hash_text(text)
                self._save_to_cache(text_hash, text, embedding)
                results[idx] = embedding

        return results  # type: ignore

    def get_dimension(self) -> int:
        """
        Retorna dimensão dos embeddings.

        Returns:
            Dimensão do vetor (384 para modelo MiniLM).
        """
        return EMBEDDING_DIM

    def clear_cache(self) -> None:
        """Limpa todo o cache de embeddings."""
        conn = sqlite3.connect(self._db_path)
        cursor = conn.cursor()
        cursor.execute("DELETE FROM embeddings_cache")
        conn.commit()
        conn.close()


# Singleton global
_embedding_client: Optional[SentenceTransformerEmbedding] = None


def get_embedding_client() -> SentenceTransformerEmbedding:
    """
    Retorna instância singleton do cliente de embedding.

    Returns:
        Instância do SentenceTransformerEmbedding.
    """
    global _embedding_client
    if _embedding_client is None:
        _embedding_client = SentenceTransformerEmbedding()
    return _embedding_client
