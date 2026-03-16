# coding: utf-8
"""
Embedding Client - Geração de embeddings locais.

Interface e implementação para embeddings usando sentence-transformers.
"""

from __future__ import annotations

import hashlib
import os
import re
import sqlite3
import sys
import threading
from abc import ABC, abstractmethod
from contextlib import contextmanager
from io import StringIO
from pathlib import Path
from typing import Callable, List, Optional

from core.sky.observability import SkyLogger, SilentLogger

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

# Thread-local para armazenar callback de progresso (usado durante carregamento)
_progress_callback = threading.local()


class _ProgressCapture(StringIO):
    """
    Captura stdout/stderr e extrai porcentagens de progresso do tqdm.

    O tqdm escreve barras de progresso neste formato:
    "Loading weights:  45%|█| 90/199 [00:00<00:00, 274.59it/s]"

    Esta classe parseia essas linhas e extrai o valor de %.
    """

    def __init__(self, on_progress: Optional[Callable[[int], None]] = None):
        """
        Args:
            on_progress: Callback chamado quando uma nova porcentagem é detectada.
                        Recebe o valor inteiro (0-100).
        """
        super().__init__()
        self._on_progress = on_progress
        self._last_percent = -1
        # Regex para capturar porcentagem do tqdm
        # Formato: "Loading weights:  45%|" ou "  45%|"
        self._percent_pattern = re.compile(r'(\d+)%')

    def write(self, text: str) -> int:
        """Sobrescreve write para parsear porcentagens."""
        # Chama write original para armazenar no buffer
        result = super().write(text)

        # Tenta extrair porcentagem
        match = self._percent_pattern.search(text)
        if match:
            try:
                percent = int(match.group(1))
                # Só notifica se mudou (evita duplicatas)
                if percent != self._last_percent and self._on_progress:
                    self._last_percent = percent
                    self._on_progress(percent)
            except (ValueError, IndexError):
                pass

        return result

    def flush(self) -> None:
        """Sobrescreve flush."""
        super().flush()


@contextmanager
def _capture_tqdm_progress(on_progress: Callable[[int], None]):
    """
    Context manager que captura stderr e extrai progresso do tqdm.

    Args:
        on_progress: Callback que recebe a porcentagem (0-100) quando detectada.

    Example:
        def my_callback(percent: int):
            print(f"Progresso: {percent}%")

        with _capture_tqdm_progress(my_callback):
            model = SentenceTransformer("model_name")
    """
    original_stderr = sys.stderr

    # Cria capturador com callback
    capture = _ProgressCapture(on_progress)
    # Escreve também no stderr original para debug (opcional - comentar para silenciar)
    # capture = _TeeCapture(capture, original_stderr)

    sys.stderr = capture

    try:
        yield
    finally:
        sys.stderr = original_stderr


def set_progress_callback(callback: Optional[Callable[[int], None]]) -> None:
    """
    Define callback de progresso para carregamento do modelo.

    Args:
        callback: Função que recebe porcentagem (0-100), ou None para limpar.
    """
    _progress_callback.value = callback


def get_progress_callback() -> Optional[Callable[[int], None]]:
    """Retorna o callback de progresso atual, ou None."""
    return getattr(_progress_callback, "value", None)


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
        logger: Optional[SkyLogger] = None,
    ):
        """
        Inicializa cliente de embedding.

        Args:
            model_name: Nome do modelo HuggingFace.
            db_path: Caminho para banco de cache. Padrão: ~/.skybridge/sky_memory.db
            logger: Logger para observabilidade. Padrão: SilentLogger.
        """
        self._model_name = model_name
        self._model: Optional[SentenceTransformer] = None
        self._logger = logger or SilentLogger()

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
        conn.execute("PRAGMA journal_mode=WAL")
        conn.execute("PRAGMA busy_timeout=5000")
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

        Configura HF_HUB_OFFLINE=1 para usar apenas cache local,
        evitando verificações remotas e garantindo funcionamento offline.

        Returns:
            Instância do SentenceTransformer.

        Raises:
            RuntimeError: Se o modelo não está cacheado e não há conexão.
        """
        if self._model is None:
            os.environ["HF_HUB_OFFLINE"] = "1"
            self._logger.debug(f"Carregando modelo de embedding: {self._model_name}")
            try:
<<<<<<< Updated upstream
                self._model = SentenceTransformer(self._model_name)
                self._logger.debug(f"Modelo de embedding carregado: {self._model_name}")
=======
                # Captura progresso do tqdm e passa para callback (se definido)
                callback = get_progress_callback()
                with _capture_tqdm_progress(callback or (lambda _: None)):
                    self._model = SentenceTransformer(self._model_name)
                logger.structured("Modelo de embedding carregado", {
                    "model": self._model_name,
                }, level="debug")
>>>>>>> Stashed changes
            except Exception as e:
                self._logger.error(f"Erro ao carregar modelo de embedding: model={self._model_name}, error={e}")
                raise RuntimeError(
                    f"Não foi possível carregar o modelo '{self._model_name}' em modo offline.\n"
                    f"O modelo precisa estar cacheado em ~/.cache/huggingface/hub/\n\n"
                    f"Para baixar o modelo, execute uma vez com conexão:\n"
                    f"  HF_HUB_OFFLINE=0 python -c \"from sentence_transformers import SentenceTransformer; SentenceTransformer('{self._model_name}')\"\n\n"
                    f"Erro original: {e}"
                ) from e
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
        conn.execute("PRAGMA journal_mode=WAL")
        conn.execute("PRAGMA busy_timeout=5000")
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
        conn.execute("PRAGMA journal_mode=WAL")
        conn.execute("PRAGMA busy_timeout=5000")
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
        conn.execute("PRAGMA journal_mode=WAL")
        conn.execute("PRAGMA busy_timeout=5000")
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
