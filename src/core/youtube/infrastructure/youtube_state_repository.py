"""State Repository para YouTube Copilot.

Rastreia estado de vídeos e playlists para:
- Detectar vídeos novos
- Evitar notificações duplicadas
- Manter histórico de sincronizações

CQRS Separation:
- Write: save_video(), save_playlist_sync()
- Read: find_new_videos(), get_playlist_stats()
"""

import sqlite3
import logging
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Optional, List, Dict, Any

logger = logging.getLogger(__name__)


@dataclass
class VideoState:
    """Estado de um vídeo monitorado."""

    video_id: str
    title: str
    channel: str
    duration_seconds: int
    playlist_id: str
    added_at: Optional[datetime] = None
    synced_at: Optional[datetime] = None
    notified_at: Optional[datetime] = None
    transcribed_at: Optional[datetime] = None
    status: str = "pending"  # pending, synced, notified, transcribed
    thumbnail: Optional[str] = None
    description: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Converte para dict (para JSON)."""
        return {
            "video_id": self.video_id,
            "title": self.title,
            "channel": self.channel,
            "duration_seconds": self.duration_seconds,
            "playlist_id": self.playlist_id,
            "added_at": self.added_at.isoformat() if self.added_at else None,
            "synced_at": self.synced_at.isoformat() if self.synced_at else None,
            "notified_at": self.notified_at.isoformat() if self.notified_at else None,
            "transcribed_at": self.transcribed_at.isoformat() if self.transcribed_at else None,
            "status": self.status,
            "thumbnail": self.thumbnail,
            "description": self.description
        }


@dataclass
class PlaylistSyncState:
    """Estado da última sincronização de uma playlist."""

    playlist_id: str
    last_sync_at: datetime
    total_videos: int
    new_videos_found: int = 0
    error_message: Optional[str] = None


class YouTubeStateRepository:
    """Repositório de estado para YouTube Copilot.

    Separação CQRS:
    - WRITE: save, update, mark
    - READ: find, get, stats
    """

    # Schema SQL
    _SCHEMA_VIDEO_STATE = """
        CREATE TABLE IF NOT EXISTS video_state (
            video_id TEXT PRIMARY KEY,
            title TEXT NOT NULL,
            channel TEXT NOT NULL,
            duration_seconds INTEGER NOT NULL,
            playlist_id TEXT NOT NULL,
            added_at TIMESTAMP,
            synced_at TIMESTAMP,
            notified_at TIMESTAMP,
            transcribed_at TIMESTAMP,
            status TEXT DEFAULT 'pending',
            thumbnail TEXT,
            description TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );

        CREATE INDEX IF NOT EXISTS idx_video_playlist
            ON video_state(playlist_id);

        CREATE INDEX IF NOT EXISTS idx_video_status
            ON video_state(status);

        CREATE INDEX IF NOT EXISTS idx_video_notified
            ON video_state(notified_at) WHERE notified_at IS NULL;
    """

    _SCHEMA_PLAYLIST_SYNC = """
        CREATE TABLE IF NOT EXISTS playlist_sync (
            playlist_id TEXT PRIMARY KEY,
            last_sync_at TIMESTAMP NOT NULL,
            total_videos INTEGER NOT NULL,
            new_videos_found INTEGER DEFAULT 0,
            error_message TEXT,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
    """

    def __init__(self, db_path: str = "data/youtube_copilot.db"):
        """Inicializa repositório.

        Args:
            db_path: Caminho para arquivo SQLite
        """
        self.db_path = db_path

        # Criar diretório se não existe
        Path(db_path).parent.mkdir(parents=True, exist_ok=True)

        # Conectar e criar schema
        self._conn = None
        self._init_db()

    @property
    def conn(self) -> sqlite3.Connection:
        """Lazy connection."""
        if self._conn is None:
            self._conn = sqlite3.connect(
                self.db_path,
                check_same_thread=False,
                detect_types=sqlite3.PARSE_DECLTYPES
            )
            self._conn.row_factory = sqlite3.Row

        return self._conn

    def _init_db(self):
        """Cria tabelas do banco."""
        with self.conn:
            # Criar tabelas
            self.conn.executescript(self._SCHEMA_VIDEO_STATE)
            self.conn.executescript(self._SCHEMA_PLAYLIST_SYNC)

            logger.info(f"Database initialized: {self.db_path}")

    # =========================================================================
    # WRITE OPERATIONS (Commands)
    # =========================================================================

    def save_video(self, video: VideoState) -> None:
        """Salva ou atualiza estado de vídeo (UPSERT).

        Args:
            video: VideoState a salvar
        """
        now = datetime.now()

        with self.conn:
            self.conn.execute(
                """
                INSERT INTO video_state (
                    video_id, title, channel, duration_seconds, playlist_id,
                    added_at, synced_at, notified_at, transcribed_at,
                    status, thumbnail, description, updated_at
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(video_id) DO UPDATE SET
                    title = excluded.title,
                    channel = excluded.channel,
                    duration_seconds = excluded.duration_seconds,
                    playlist_id = excluded.playlist_id,
                    added_at = COALESCE(excluded.added_at, video_state.added_at),
                    synced_at = COALESCE(excluded.synced_at, video_state.synced_at),
                    notified_at = COALESCE(excluded.notified_at, video_state.notified_at),
                    transcribed_at = COALESCE(excluded.transcribed_at, video_state.transcribed_at),
                    status = COALESCE(excluded.status, video_state.status),
                    thumbnail = COALESCE(excluded.thumbnail, video_state.thumbnail),
                    description = COALESCE(excluded.description, video_state.description),
                    updated_at = ?
                """,
                (
                    video.video_id, video.title, video.channel,
                    video.duration_seconds, video.playlist_id,
                    video.added_at, video.synced_at, video.notified_at,
                    video.transcribed_at, video.status, video.thumbnail,
                    video.description, now
                )
            )

        logger.debug(f"Video saved: {video.video_id}")

    def save_playlist_sync(self, sync_state: PlaylistSyncState) -> None:
        """Salva estado de sincronização de playlist.

        Args:
            sync_state: PlaylistSyncState a salvar
        """
        with self.conn:
            self.conn.execute(
                """
                INSERT INTO playlist_sync (
                    playlist_id, last_sync_at, total_videos,
                    new_videos_found, error_message, updated_at
                )
                VALUES (?, ?, ?, ?, ?, ?)
                ON CONFLICT(playlist_id) DO UPDATE SET
                    last_sync_at = excluded.last_sync_at,
                    total_videos = excluded.total_videos,
                    new_videos_found = excluded.new_videos_found,
                    error_message = excluded.error_message,
                    updated_at = excluded.updated_at
                """,
                (
                    sync_state.playlist_id, sync_state.last_sync_at,
                    sync_state.total_videos, sync_state.new_videos_found,
                    sync_state.error_message, datetime.now()
                )
            )

        logger.debug(f"Playlist sync saved: {sync_state.playlist_id}")

    def mark_as_synced(self, video_id: str) -> None:
        """Marca vídeo como sincronizado.

        Args:
            video_id: ID do vídeo
        """
        with self.conn:
            self.conn.execute(
                """
                UPDATE video_state
                SET synced_at = ?, status = 'synced', updated_at = ?
                WHERE video_id = ?
                """,
                (datetime.now(), datetime.now(), video_id)
            )

    def mark_as_notified(self, video_id: str) -> None:
        """Marca vídeo como notificado ao usuário.

        Args:
            video_id: ID do vídeo
        """
        with self.conn:
            self.conn.execute(
                """
                UPDATE video_state
                SET notified_at = ?, status = 'notified', updated_at = ?
                WHERE video_id = ?
                """,
                (datetime.now(), datetime.now(), video_id)
            )

    def mark_as_transcribed(self, video_id: str) -> None:
        """Marca vídeo como transcrito.

        Args:
            video_id: ID do vídeo
        """
        with self.conn:
            self.conn.execute(
                """
                UPDATE video_state
                SET transcribed_at = ?, status = 'transcribed', updated_at = ?
                WHERE video_id = ?
                """,
                (datetime.now(), datetime.now(), video_id)
            )

    # =========================================================================
    # READ OPERATIONS (Queries)
    # =========================================================================

    def get_video(self, video_id: str) -> Optional[VideoState]:
        """Busca vídeo por ID.

        Args:
            video_id: ID do vídeo

        Returns:
            VideoState ou None se não encontrado
        """
        row = self.conn.execute(
            "SELECT * FROM video_state WHERE video_id = ?",
            (video_id,)
        ).fetchone()

        if row is None:
            return None

        return self._row_to_video_state(row)

    def get_videos_by_playlist(
        self,
        playlist_id: str,
        limit: Optional[int] = None
    ) -> List[VideoState]:
        """Busca vídeos de uma playlist.

        Args:
            playlist_id: ID da playlist
            limit: Máximo de resultados

        Returns:
            Lista de VideoState
        """
        query = """
            SELECT * FROM video_state
            WHERE playlist_id = ?
            ORDER BY added_at DESC
        """

        if limit:
            query += f" LIMIT {limit}"

        rows = self.conn.execute(query, (playlist_id,)).fetchall()

        return [self._row_to_video_state(row) for row in rows]

    def find_new_videos(
        self,
        playlist_id: Optional[str] = None
    ) -> List[VideoState]:
        """Encontra vídeos não sincronizados (synced_at IS NULL).

        Args:
            playlist_id: Filtrar por playlist (opcional)

        Returns:
            Lista de VideoState não sincronizados
        """
        if playlist_id:
            rows = self.conn.execute(
                """
                SELECT * FROM video_state
                WHERE synced_at IS NULL AND playlist_id = ?
                ORDER BY added_at ASC
                """,
                (playlist_id,)
            ).fetchall()
        else:
            rows = self.conn.execute(
                """
                SELECT * FROM video_state
                WHERE synced_at IS NULL
                ORDER BY added_at ASC
                """
            ).fetchall()

        return [self._row_to_video_state(row) for row in rows]

    def find_pending_notification(self) -> List[VideoState]:
        """Encontra vídeos pendentes de notificação (notified_at IS NULL).

        Returns:
            Lista de VideoState pendentes
        """
        rows = self.conn.execute(
            """
            SELECT * FROM video_state
            WHERE notified_at IS NULL
            ORDER BY added_at ASC
            """
        ).fetchall()

        return [self._row_to_video_state(row) for row in rows]

    def find_pending_notification_by_playlist(
        self,
        playlist_id: str,
        limit: int = 10
    ) -> List[VideoState]:
        """Encontra vídeos pendentes de notificação de uma playlist.

        Args:
            playlist_id: ID da playlist
            limit: Máximo de resultados

        Returns:
            Lista de VideoState pendentes
        """
        rows = self.conn.execute(
            """
            SELECT * FROM video_state
            WHERE notified_at IS NULL AND playlist_id = ?
            ORDER BY added_at ASC
            LIMIT ?
            """,
            (playlist_id, limit)
        ).fetchall()

        return [self._row_to_video_state(row) for row in rows]

    def get_playlist_sync(self, playlist_id: str) -> Optional[PlaylistSyncState]:
        """Busca estado de sincronização de playlist.

        Args:
            playlist_id: ID da playlist

        Returns:
            PlaylistSyncState ou None
        """
        row = self.conn.execute(
            "SELECT * FROM playlist_sync WHERE playlist_id = ?",
            (playlist_id,)
        ).fetchone()

        if row is None:
            return None

        return PlaylistSyncState(
            playlist_id=row["playlist_id"],
            last_sync_at=datetime.fromisoformat(row["last_sync_at"]),
            total_videos=row["total_videos"],
            new_videos_found=row["new_videos_found"],
            error_message=row["error_message"]
        )

    def get_playlist_stats(self, playlist_id: str) -> Dict[str, int]:
        """Retorna estatísticas de uma playlist.

        Args:
            playlist_id: ID da playlist

        Returns:
            Dict com stats: total_videos, pending, synced, notified, transcribed
        """
        stats = self.conn.execute(
            """
            SELECT
                COUNT(*) as total_videos,
                SUM(CASE WHEN synced_at IS NULL THEN 1 ELSE 0 END) as pending,
                SUM(CASE WHEN synced_at IS NOT NULL THEN 1 ELSE 0 END) as synced,
                SUM(CASE WHEN notified_at IS NOT NULL THEN 1 ELSE 0 END) as notified,
                SUM(CASE WHEN transcribed_at IS NOT NULL THEN 1 ELSE 0 END) as transcribed
            FROM video_state
            WHERE playlist_id = ?
            """,
            (playlist_id,)
        ).fetchone()

        return {
            "total_videos": stats["total_videos"] or 0,
            "pending": stats["pending"] or 0,
            "synced": stats["synced"] or 0,
            "notified": stats["notified"] or 0,
            "transcribed": stats["transcribed"] or 0
        }

    def get_all_playlists_stats(self) -> List[Dict[str, Any]]:
        """Retorna estatísticas de todas as playlists.

        Returns:
            Lista de dicts com playlist_id e stats
        """
        rows = self.conn.execute(
            """
            SELECT
                playlist_id,
                COUNT(*) as total_videos,
                SUM(CASE WHEN synced_at IS NULL THEN 1 ELSE 0 END) as pending,
                SUM(CASE WHEN notified_at IS NOT NULL THEN 1 ELSE 0 END) as notified
            FROM video_state
            GROUP BY playlist_id
            ORDER BY playlist_id
            """
        ).fetchall()

        return [
            {
                "playlist_id": row["playlist_id"],
                "total_videos": row["total_videos"],
                "pending": row["pending"],
                "notified": row["notified"]
            }
            for row in rows
        ]

    # =========================================================================
    # HELPERS
    # =========================================================================

    def _row_to_video_state(self, row: sqlite3.Row) -> VideoState:
        """Converte row do banco para VideoState.

        Args:
            row: Row do SQLite

        Returns:
            VideoState
        """
        return VideoState(
            video_id=row["video_id"],
            title=row["title"],
            channel=row["channel"],
            duration_seconds=row["duration_seconds"],
            playlist_id=row["playlist_id"],
            added_at=datetime.fromisoformat(row["added_at"]) if row["added_at"] else None,
            synced_at=datetime.fromisoformat(row["synced_at"]) if row["synced_at"] else None,
            notified_at=datetime.fromisoformat(row["notified_at"]) if row["notified_at"] else None,
            transcribed_at=datetime.fromisoformat(row["transcribed_at"]) if row["transcribed_at"] else None,
            status=row["status"],
            thumbnail=row["thumbnail"],
            description=row["description"]
        )

    def close(self) -> None:
        """Fecha conexão com banco."""
        if self._conn is not None:
            self._conn.close()
            self._conn = None

    def __enter__(self):
        """Context manager support."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager cleanup."""
        self.close()
