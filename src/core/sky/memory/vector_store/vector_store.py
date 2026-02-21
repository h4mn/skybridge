# coding: utf-8
"""
Vector Store - Wrapper sqlite-vec para busca vetorial.

Implementa armazenamento e busca de embeddings usando sqlite-vec.
"""

from __future__ import annotations

import sqlite3
import struct
from dataclasses import dataclass
from pathlib import Path
from typing import Any, List, Optional

try:
    import sqlite_vec  # type: ignore
except ImportError:
    raise ImportError(
        "sqlite-vec é necessário. Instale com: pip install sqlite-vec"
    )


# Dimensão do embedding modelo MiniLM
EMBEDDING_DIM = 384


def _serialize_vector(vector: List[float]) -> bytes:
    """
    Serializa vetor para bytes (formato sqlite-vec).

    Args:
        vector: Lista de floats.

    Returns:
        Bytes representando o vetor.
    """
    # Empacotar floats como little-endian
    return struct.pack(f"{len(vector)}f", *vector)


def _deserialize_vector(data: bytes, dim: int) -> List[float]:
    """
    Deserializa bytes para vetor.

    Args:
        data: Bytes do vetor.
        dim: Dimensão esperada.

    Returns:
        Lista de floats.
    """
    return list(struct.unpack(f"{dim}f", data))


@dataclass
class SearchResult:
    """Resultado de busca vetorial."""

    id: int
    distance: float
    content: str
    metadata: dict[str, Any]


class VectorStore:
    """
    Vector Store usando sqlite-vec.

    Gerencia tabelas virtuais para busca de similaridade semântica.
    """

    # Coleções disponíveis
    COLLECTIONS = [
        "identity",
        "shared-moments",
        "teachings",
        "operational",
    ]

    def __init__(self, db_path: Path | None = None):
        """
        Inicializa Vector Store.

        Args:
            db_path: Caminho para o banco SQLite. Padrão: ~/.skybridge/sky_memory.db
        """
        if db_path is None:
            data_dir = Path.home() / ".skybridge"
            data_dir.mkdir(parents=True, exist_ok=True)
            db_path = data_dir / "sky_memory.db"

        self._db_path = db_path
        self._conn: sqlite3.Connection | None = None

        # Inicializar banco e tabelas
        self._init_db()

    def _init_db(self) -> None:
        """Inicializa banco de dados e tabelas virtuais."""
        self._conn = sqlite3.connect(self._db_path)
        conn = self._conn

        # Carregar extensão sqlite-vec
        conn.enable_load_extension(True)
        sqlite_vec.load(conn)

        # Criar tabelas virtuais para cada coleção
        for collection in self.COLLECTIONS:
            table_name = f"vec_{collection.replace('-', '_')}"
            self._create_vector_table(table_name)

        # Criar índices para metadata
        self._create_metadata_table()

        self._conn.commit()

    def _create_vector_table(self, table_name: str) -> None:
        """
        Cria tabela virtual para embeddings de uma coleção.

        Args:
            table_name: Nome da tabela virtual.
        """
        assert self._conn is not None
        cursor = self._conn.cursor()

        # Sintaxe sqlite-vec 0.1+: usar array notation
        cursor.execute(f"""
            CREATE VIRTUAL TABLE IF NOT EXISTS {table_name} USING vec0(
                embedding FLOAT[{EMBEDDING_DIM}]
            )
        """)

    def _create_metadata_table(self) -> None:
        """Cria tabela de metadados das memórias vetoriais."""
        assert self._conn is not None
        cursor = self._conn.cursor()

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS memory_metadata (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                content TEXT NOT NULL,
                collection TEXT NOT NULL,
                source_type TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                vector_rowid INTEGER
            )
        """)

    def _get_vector_table_name(self, collection: str) -> str:
        """
        Retorna nome da tabela vetorial para a coleção.

        Args:
            collection: Nome da coleção.

        Returns:
            Nome da tabela virtual (com hífen substituído).
        """
        if collection not in self.COLLECTIONS:
            raise ValueError(
                f"Coleção inválida: {collection}. "
                f"Disponíveis: {', '.join(self.COLLECTIONS)}"
            )
        return f"vec_{collection.replace('-', '_')}"

    def insert_vector(
        self,
        collection: str,
        embedding: List[float],
        content: str,
        metadata: dict[str, Any] | None = None,
    ) -> int:
        """
        Insere vetor na coleção especificada.

        Args:
            collection: Nome da coleção (identity, shared-moments, teachings, operational).
            embedding: Vetor de embedding (dimensão EMBEDDING_DIM).
            content: Conteúdo textual da memória.
            metadata: Metadados adicionais (opcional).

        Returns:
            ID da memória inserida.

        Raises:
            ValueError: Se embedding tiver dimensão incorreta.
        """
        assert self._conn is not None
        cursor = self._conn.cursor()

        # Validar dimensão
        if len(embedding) != EMBEDDING_DIM:
            raise ValueError(
                f"Embedding deve ter dimensão {EMBEDDING_DIM}, "
                f"recebido: {len(embedding)}"
            )

        # Inserir na tabela vetorial
        table_name = self._get_vector_table_name(collection)
        serialized = _serialize_vector(embedding)
        cursor.execute(
            f"INSERT INTO {table_name}(embedding) VALUES (?)",
            [serialized]
        )
        vector_rowid = cursor.lastrowid

        # Inserir metadados
        source_type = metadata.get("source_type", "unknown") if metadata else "unknown"
        cursor.execute(
            """
            INSERT INTO memory_metadata (content, collection, source_type, vector_rowid)
            VALUES (?, ?, ?, ?)
            """,
            (content, collection, source_type, vector_rowid)
        )

        self._conn.commit()
        return cursor.lastrowid

    def search_vectors(
        self,
        collection: str,
        query_vector: List[float],
        k: int = 5,
        threshold: float | None = None,
    ) -> List[SearchResult]:
        """
        Busca vetores mais similares na coleção.

        Args:
            collection: Nome da coleção para buscar.
            query_vector: Vetor de consulta (dimensão EMBEDDING_DIM).
            k: Número máximo de resultados.
            threshold: Score mínimo de similaridade (0-1). Opcional.

        Returns:
            Lista de resultados ordenados por distância (menor = mais similar).
        """
        assert self._conn is not None
        cursor = self._conn.cursor()

        # Validar dimensão
        if len(query_vector) != EMBEDDING_DIM:
            raise ValueError(
                f"Query vector deve ter dimensão {EMBEDDING_DIM}, "
                f"recebido: {len(query_vector)}"
            )

        table_name = self._get_vector_table_name(collection)

        # Serializar query vector
        serialized_query = _serialize_vector(query_vector)

        # Buscar K vizinhos mais próximos
        # sqlite-vec 0.1+ usa sintaxe MATCH + k
        query = f"""
            SELECT
                v.rowid as vector_rowid,
                m.id,
                m.content,
                distance
            FROM {table_name} v
            LEFT JOIN memory_metadata m ON m.vector_rowid = v.rowid
            WHERE v.embedding MATCH ?
              AND k = ?
              AND m.collection = ?
            ORDER BY distance
        """

        cursor.execute(query, [serialized_query, k, collection])
        rows = cursor.fetchall()

        # Converter para SearchResult
        results = []
        for vector_rowid, memory_id, content, distance in rows:
            # Aplicar threshold se especificado
            if threshold is not None:
                # Converter distância euclidiana para similaridade (0-1)
                # Para normalização simples: sim = 1 / (1 + distance)
                similarity = 1.0 / (1.0 + distance)
                if similarity < threshold:
                    continue

            results.append(SearchResult(
                id=memory_id,
                distance=distance,
                content=content,
                metadata={"vector_rowid": vector_rowid}
            ))

        return results

    def get_collection_stats(self, collection: str) -> dict[str, int]:
        """
        Retorna estatísticas de uma coleção.

        Args:
            collection: Nome da coleção.

        Returns:
            Dict com count (número de memórias).
        """
        assert self._conn is not None
        cursor = self._conn.cursor()

        cursor.execute(
            "SELECT COUNT(*) FROM memory_metadata WHERE collection = ?",
            (collection,)
        )
        count = cursor.fetchone()[0]

        return {"count": count}

    def close(self) -> None:
        """Fecha conexão com banco."""
        if self._conn:
            self._conn.close()
            self._conn = None

    def __enter__(self) -> VectorStore:
        """Context manager entry."""
        return self

    def __exit__(self, *args: object) -> None:
        """Context manager exit."""
        self.close()


# Singleton global
_vector_store: VectorStore | None = None


def get_vector_store() -> VectorStore:
    """
    Retorna instância singleton do VectorStore.

    Returns:
        Instância do VectorStore.
    """
    global _vector_store
    if _vector_store is None:
        _vector_store = VectorStore()
    return _vector_store
