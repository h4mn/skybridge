# coding: utf-8
"""
Collections - Configuração e gerenciamento de coleções vetoriais.

Define as coleções de memória e suas políticas de retenção.
"""

from __future__ import annotations

import sqlite3
from dataclasses import dataclass
from datetime import datetime, timedelta
from enum import Enum
from pathlib import Path
from typing import Optional

from runtime.observability.logger import get_logger

logger = get_logger("sky.memory.collections", level="INFO")


class SourceType(Enum):
    """Tipos de fonte de memória."""

    CHAT = "chat"
    CODE = "code"
    DOCS = "docs"
    LOGS = "logs"
    USER = "user"
    DEMO = "demo"


@dataclass
class CollectionConfig:
    """
    Configuração de uma coleção de memória.

    Attributes:
        name: Nome único da coleção.
        purpose: Descrição do propósito da coleção.
        retention_days: Dias de retenção (None = permanente).
        embedding_enabled: Se embeddings são gerados para esta coleção.
    """

    name: str
    purpose: str
    retention_days: Optional[int] = None
    embedding_enabled: bool = True

    @property
    def is_permanent(self) -> bool:
        """Retorna True se a coleção é permanente."""
        return self.retention_days is None

    @property
    def expiration_date(self, since: datetime) -> Optional[datetime]:
        """
        Calcula data de expiração para uma memória.

        Args:
            since: Data de criação da memória.

        Returns:
            Data de expiração ou None se permanente.
        """
        if self.is_permanent:
            return None
        return since + timedelta(days=self.retention_days)  # type: ignore


# Configurações padrão das coleções
DEFAULT_COLLECTIONS = [
    CollectionConfig(
        name="identity",
        purpose="Quem Sky é, suas características e personalidade",
        retention_days=None,  # Permanente
    ),
    CollectionConfig(
        name="shared-moments",
        purpose="Memórias afetivas e momentos compartilhados",
        retention_days=None,  # Permanente
    ),
    CollectionConfig(
        name="teachings",
        purpose="Ensinamentos do pai",
        retention_days=None,  # Permanente
    ),
    CollectionConfig(
        name="operational",
        purpose="Contexto recente, ações e estado operacional",
        retention_days=30,  # 30 dias
    ),
]


class CollectionManager:
    """
    Gerencia coleções de memória.

    Responsável por:
    - Criar/dropar coleções
    - Pruning de memórias expiradas
    - Consultar configurações
    """

    def __init__(self, db_path: Optional[Path] = None):
        """
        Inicializa CollectionManager.

        Args:
            db_path: Caminho para banco SQLite. Padrão: ~/.skybridge/sky_memory.db
        """
        if db_path is None:
            data_dir = Path.home() / ".skybridge"
            data_dir.mkdir(parents=True, exist_ok=True)
            db_path = data_dir / "sky_memory.db"

        self._db_path = db_path
        self._init_collections()

    def _init_collections(self) -> None:
        """Inicializa configurações das coleções no banco."""
        conn = sqlite3.connect(self._db_path)
        conn.execute("PRAGMA journal_mode=WAL")
        conn.execute("PRAGMA busy_timeout=5000")
        cursor = conn.cursor()

        # Criar tabela de configuração
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS collection_config (
                name TEXT PRIMARY KEY,
                purpose TEXT NOT NULL,
                retention_days INTEGER,
                embedding_enabled INTEGER DEFAULT 1,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # Inserir configurações padrão
        for config in DEFAULT_COLLECTIONS:
            cursor.execute(
                """
                INSERT OR REPLACE INTO collection_config
                (name, purpose, retention_days, embedding_enabled)
                VALUES (?, ?, ?, ?)
                """,
                (
                    config.name,
                    config.purpose,
                    config.retention_days,
                    1 if config.embedding_enabled else 0,
                ),
            )

        conn.commit()
        conn.close()

    def get_collection(self, name: str) -> Optional[CollectionConfig]:
        """
        Retorna configuração de uma coleção.

        Args:
            name: Nome da coleção.

        Returns:
            CollectionConfig ou None se não existir.
        """
        conn = sqlite3.connect(self._db_path)
        conn.execute("PRAGMA journal_mode=WAL")
        conn.execute("PRAGMA busy_timeout=5000")
        cursor = conn.cursor()

        cursor.execute(
            "SELECT purpose, retention_days, embedding_enabled FROM collection_config WHERE name = ?",
            (name,)
        )
        row = cursor.fetchone()
        conn.close()

        if row:
            purpose, retention_days, emb_enabled = row
            return CollectionConfig(
                name=name,
                purpose=purpose,
                retention_days=retention_days,
                embedding_enabled=bool(emb_enabled),
            )
        return None

    def list_collections(self) -> list[CollectionConfig]:
        """
        Lista todas as coleções configuradas.

        Returns:
            Lista de CollectionConfig.
        """
        conn = sqlite3.connect(self._db_path)
        conn.execute("PRAGMA journal_mode=WAL")
        conn.execute("PRAGMA busy_timeout=5000")
        cursor = conn.cursor()

        cursor.execute("SELECT name, purpose, retention_days, embedding_enabled FROM collection_config")
        rows = cursor.fetchall()
        conn.close()

        return [
            CollectionConfig(
                name=name,
                purpose=purpose,
                retention_days=retention_days,
                embedding_enabled=bool(emb_enabled),
            )
            for name, purpose, retention_days, emb_enabled in rows
        ]

    def prune_expired_memories(self, collection_name: Optional[str] = None) -> int:
        """
        Remove memórias expiradas baseado na política de retenção.

        Args:
            collection_name: Nome da coleção específica ou None para todas.

        Returns:
            Número de memórias removidas.
        """
        conn = sqlite3.connect(self._db_path)
        conn.execute("PRAGMA journal_mode=WAL")
        conn.execute("PRAGMA busy_timeout=5000")
        cursor = conn.cursor()

        # Construir query baseada em retenção
        if collection_name:
            collections = [self.get_collection(collection_name)]
        else:
            collections = self.list_collections()

        total_deleted = 0

        for config in collections:
            if config is None or config.is_permanent:
                continue  # Skip permanent collections

            # Calcular data de corte
            cutoff_date = datetime.now() - timedelta(days=config.retention_days)  # type: ignore

            # Deletar memórias antigas
            cursor.execute(
                """
                DELETE FROM memory_metadata
                WHERE collection = ?
                  AND created_at < ?
                """,
                (config.name, cutoff_date.isoformat())
            )

            deleted = cursor.rowcount
            total_deleted += deleted

            if deleted > 0:
                logger.structured("Memórias expiradas removidas", {
                    "collection": config.name,
                    "deleted": deleted,
                }, level="info")

        conn.commit()
        conn.close()

        return total_deleted

    def get_collection_stats(self, collection_name: str) -> dict:
        """
        Retorna estatísticas de uma coleção.

        Args:
            collection_name: Nome da coleção.

        Returns:
            Dict com count, oldest, newest.
        """
        conn = sqlite3.connect(self._db_path)
        conn.execute("PRAGMA journal_mode=WAL")
        conn.execute("PRAGMA busy_timeout=5000")
        cursor = conn.cursor()

        cursor.execute(
            """
            SELECT
                COUNT(*) as count,
                MIN(created_at) as oldest,
                MAX(created_at) as newest
            FROM memory_metadata
            WHERE collection = ?
            """,
            (collection_name,)
        )
        row = cursor.fetchone()
        conn.close()

        if row and row[0] > 0:
            count, oldest, newest = row
            return {
                "count": count,
                "oldest": oldest,
                "newest": newest,
            }
        return {"count": 0, "oldest": None, "newest": None}


# Singleton global
_collection_manager: Optional[CollectionManager] = None


def get_collection_manager() -> CollectionManager:
    """
    Retorna instância singleton do CollectionManager.

    Returns:
        Instância do CollectionManager.
    """
    global _collection_manager
    if _collection_manager is None:
        _collection_manager = CollectionManager()
    return _collection_manager
