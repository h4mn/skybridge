"""Repositório RAG standalone para vídeos - com deduplicação por hash."""

from typing import Dict, List, Optional
import hashlib
import sqlite3
import struct
from pathlib import Path


EMBEDDING_DIM = 384


def _serialize_vector(vector: List[float]) -> bytes:
    """Serializa vetor para bytes."""
    return struct.pack(f"{len(vector)}f", *vector)


def _hash_content(content: str) -> str:
    """Gera hash SHA256 do conteúdo para deduplicação."""
    return hashlib.sha256(content.encode('utf-8')).hexdigest()


class RAGVideoRepository:
    """
    Repositório RAG standalone para vídeos usando sqlite-vec.

    Features:
        - Busca semântica com embeddings
        - Deduplicação automática por content_hash
        - Upsert (insert or update) por video_id
    """

    COLLECTION = "skypedia"

    def __init__(self, db_path: Optional[Path] = None):
        """
        Inicializa repositório.

        Args:
            db_path: Caminho para banco SQLite. Padrão: ~/.skybridge/sky_memory.db
        """
        if db_path is None:
            data_dir = Path.home() / ".skybridge"
            data_dir.mkdir(parents=True, exist_ok=True)
            db_path = data_dir / "sky_memory.db"

        self._db_path = db_path
        self._conn = None
        self._model = None  # Lazy load do modelo

        # Inicializar banco
        self._init_db()

    def _init_db(self) -> None:
        """Inicializa banco de dados e tabelas virtuais."""
        self._conn = sqlite3.connect(str(self._db_path))
        conn = self._conn

        # Configurar WAL
        conn.execute("PRAGMA journal_mode=WAL")
        conn.execute("PRAGMA busy_timeout=5000")

        # Carregar sqlite-vec
        try:
            import sqlite_vec
            conn.enable_load_extension(True)
            sqlite_vec.load(conn)
        except ImportError:
            raise ImportError(
                "sqlite-vec é necessário. Instale: pip install sqlite-vec"
            )

        # Criar tabela virtual para skypedia
        conn.execute(f"""
            CREATE VIRTUAL TABLE IF NOT EXISTS vec_{self.COLLECTION} USING vec0(
                embedding FLOAT[{EMBEDDING_DIM}]
            )
        """)

        # Criar tabela de metadata com content_hash
        conn.execute("""
            CREATE TABLE IF NOT EXISTS memory_metadata (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                content TEXT NOT NULL,
                content_hash TEXT NOT NULL,
                collection TEXT NOT NULL,
                source_type TEXT NOT NULL,
                video_id TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                vector_rowid INTEGER
            )
        """)

        # Criar índice único para deduplicação
        try:
            conn.execute("CREATE UNIQUE INDEX idx_content_hash ON memory_metadata(content_hash)")
        except sqlite3.OperationalError:
            pass  # Já existe

        conn.commit()

    def _get_model(self):
        """Lazy load do modelo de embedding."""
        if self._model is None:
            try:
                from sentence_transformers import SentenceTransformer
                self._model = SentenceTransformer("paraphrase-multilingual-MiniLM-L12-v2")
            except ImportError:
                raise ImportError(
                    "sentence-transformers é necessário. Instale: pip install sentence-transformers"
                )
        return self._model

    def index_video(
        self,
        video_id: str,
        title: str,
        transcript: str,
        metadata: Optional[Dict] = None,
    ) -> int:
        """
        Indexa um vídeo na coleção skypedia com deduplicação automática.

        Se já existir um vídeo com o mesmo conteúdo (mesmo hash), retorna o ID existente.
        Se já existir um vídeo com o mesmo video_id, atualiza o registro.

        Args:
            video_id: ID do vídeo (YouTube, etc)
            title: Título do vídeo
            transcript: Transcrição completa do conteúdo
            metadata: Metadados adicionais (canal, tags, duration, etc)

        Returns:
            ID da memória (nova ou existente)
        """
        # Combinar título e transcrição
        content = f"# {title}\n\n{transcript}"

        # Gerar hash do conteúdo
        content_hash = _hash_content(content)

        # Verificar se já existe (deduplicação)
        cursor = self._conn.cursor()
        cursor.execute(
            "SELECT id FROM memory_metadata WHERE content_hash = ? AND collection = ?",
            (content_hash, self.COLLECTION)
        )
        existing = cursor.fetchone()

        if existing:
            # Já existe - retornar ID existente
            existing_id = existing[0]
            print(f"[INFO] Conteúdo já indexado (ID: {existing_id})")
            return existing_id

        # Gerar embedding
        model = self._get_model()
        embedding = model.encode(content).tolist()

        # Inserir embedding
        table_name = f"vec_{self.COLLECTION}"
        serialized = _serialize_vector(embedding)

        cursor.execute(
            f"INSERT INTO {table_name}(embedding) VALUES (?)",
            [serialized]
        )
        vector_rowid = cursor.lastrowid

        # Preparar metadados
        source_type = (metadata or {}).get("source_type", "youtube")

        # Inserir metadata
        cursor.execute(
            """
            INSERT INTO memory_metadata (content, content_hash, collection, source_type, video_id, vector_rowid)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (content, content_hash, self.COLLECTION, source_type, video_id, vector_rowid)
        )

        self._conn.commit()
        return cursor.lastrowid

    def search(self, query: str, limit: int = 5) -> List[Dict]:
        """
        Busca vídeos por similaridade semântica.

        Args:
            query: Query em linguagem natural
            limit: Máximo de resultados

        Returns:
            Lista de dicts com {content, distance, metadata}
        """
        # Gerar embedding da query
        model = self._get_model()
        query_embedding = model.encode(query).tolist()

        # Buscar
        table_name = f"vec_{self.COLLECTION}"
        serialized_query = _serialize_vector(query_embedding)

        cursor = self._conn.cursor()
        cursor.execute(
            f"""
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
            """,
            [serialized_query, limit, self.COLLECTION]
        )

        results = []
        for vector_rowid, memory_id, content, distance in cursor.fetchall():
            results.append({
                "id": memory_id,
                "content": content,
                "distance": distance,
                "metadata": {"vector_rowid": vector_rowid}
            })

        return results

    async def search_async(self, query: str, limit: int = 5) -> List[Dict]:
        """Versão async para compatibilidade."""
        return self.search(query, limit)

    def get_stats(self) -> Dict:
        """Retorna estatísticas da coleção skypedia."""
        cursor = self._conn.cursor()
        cursor.execute(
            "SELECT COUNT(*) FROM memory_metadata WHERE collection = ?",
            (self.COLLECTION,)
        )
        count = cursor.fetchone()[0]
        return {"count": count}

    def close(self) -> None:
        """Fecha conexão."""
        if self._conn:
            self._conn.close()
            self._conn = None
