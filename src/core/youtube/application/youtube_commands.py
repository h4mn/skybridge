"""YouTube Copilot CQRS Commands.

Commands (Write) e Queries (Read) para gerenciar playlists YouTube.

Separação CQRS:
- Commands: sync_video(), mark_notified(), etc.
- Queries: find_new_videos(), get_stats(), etc.
"""

import os
from dataclasses import dataclass
from datetime import datetime
from typing import Optional, List

from dotenv import load_dotenv

from src.core.youtube.infrastructure.youtube_api_client import YouTubeAPIClient
from src.core.youtube.infrastructure.youtube_state_repository import (
    YouTubeStateRepository,
    VideoState,
    PlaylistSyncState
)

load_dotenv()


# =========================================================================
# VALUE OBJECTS (Resultados)
# =========================================================================

@dataclass
class SyncResult:
    """Resultado de uma sincronização."""
    playlist_id: str
    total_videos: int
    new_videos: int
    updated_videos: int
    synced_at: datetime
    error: Optional[str] = None

    def is_success(self) -> bool:
        return self.error is None


@dataclass
class StatusResult:
    """Resultado de status de playlist."""
    playlist_id: str
    total_videos: int
    pending_notification: int
    notified: int
    transcribed: int
    pending_videos: List[VideoState]


@dataclass
class StatsResult:
    """Resultado de estatísticas gerais."""
    total_playlists: int
    total_videos: int
    total_pending: int
    playlists: List[dict]


@dataclass
class PlaylistListResult:
    """Resultado de listagem de playlists."""
    playlists: List[dict]
    total: int


@dataclass
class VideoListResult:
    """Resultado de listagem de vídeos de uma playlist."""
    playlist_id: str
    videos: List[VideoState]
    total: int


# =========================================================================
# COMMANDS (Write Side)
# =========================================================================

class YouTubeCommandHandler:
    """Handler para Commands (Write Side)."""

    def __init__(
        self,
        access_token: Optional[str] = None,
        state_repo: Optional[YouTubeStateRepository] = None
    ):
        """Inicializa handler.

        Args:
            access_token: Token OAuth YouTube (ou do .env)
            state_repo: Repositório de estado (ou cria novo)
        """
        self.access_token = access_token or os.getenv("GOOGLE_OAUTH_TOKEN")
        if not self.access_token:
            raise ValueError("GOOGLE_OAUTH_TOKEN não encontrado")

        self.youtube_api = YouTubeAPIClient(access_token=self.access_token)
        self.state_repo = state_repo or YouTubeStateRepository()

    def sync_playlist(
        self,
        playlist_id: str = "LL"
    ) -> SyncResult:
        """Sincroniza playlist com YouTube API.

        Args:
            playlist_id: ID da playlist (LL=favoritos, WL=watch later)

        Returns:
            SyncResult com estatísticas
        """
        try:
            # 1. Buscar vídeos da API
            api_videos = self.youtube_api.get_playlist_items(
                playlist_id=playlist_id,
                max_results=50
            )

            if not api_videos:
                return SyncResult(
                    playlist_id=playlist_id,
                    total_videos=0,
                    new_videos=0,
                    updated_videos=0,
                    synced_at=datetime.now(),
                    error="Playlist vazia ou não encontrada"
                )

            # 2. Salvar/Atualizar no banco
            new_count = 0
            updated_count = 0
            now = datetime.now()

            for video_data in api_videos:
                existing = self.state_repo.get_video(video_data["video_id"])

                if existing is None:
                    # Vídeo novo
                    state = VideoState(
                        video_id=video_data["video_id"],
                        title=video_data["title"],
                        channel=video_data["channel"],
                        duration_seconds=video_data.get("duration_seconds", 0),
                        playlist_id=playlist_id,
                        added_at=now,
                        synced_at=now,
                        thumbnail=video_data.get("thumbnail"),
                        description=video_data.get("description")
                    )
                    self.state_repo.save_video(state)
                    new_count += 1
                else:
                    # Vídeo existente - atualiza
                    state = VideoState(
                        video_id=video_data["video_id"],
                        title=video_data["title"],
                        channel=video_data["channel"],
                        duration_seconds=video_data.get("duration_seconds", 0),
                        playlist_id=playlist_id,
                        added_at=existing.added_at,
                        synced_at=now,
                        thumbnail=video_data.get("thumbnail"),
                        description=video_data.get("description")
                    )
                    self.state_repo.save_video(state)
                    updated_count += 1

            # 3. Salvar estado da sync
            sync_state = PlaylistSyncState(
                playlist_id=playlist_id,
                last_sync_at=now,
                total_videos=len(api_videos),
                new_videos_found=new_count
            )
            self.state_repo.save_playlist_sync(sync_state)

            return SyncResult(
                playlist_id=playlist_id,
                total_videos=len(api_videos),
                new_videos=new_count,
                updated_videos=updated_count,
                synced_at=now
            )

        except Exception as e:
            return SyncResult(
                playlist_id=playlist_id,
                total_videos=0,
                new_videos=0,
                updated_videos=0,
                synced_at=datetime.now(),
                error=str(e)
            )

    def mark_as_notified(self, video_id: str) -> bool:
        """Marca vídeo como notificado.

        Args:
            video_id: ID do vídeo

        Returns:
            True se sucesso, False se não encontrou
        """
        try:
            video = self.state_repo.get_video(video_id)
            if video is None:
                return False

            self.state_repo.mark_as_notified(video_id)
            return True
        except Exception:
            return False

    def mark_as_transcribed(self, video_id: str) -> bool:
        """Marca vídeo como transcrito.

        Args:
            video_id: ID do vídeo

        Returns:
            True se sucesso, False se não encontrou
        """
        try:
            video = self.state_repo.get_video(video_id)
            if video is None:
                return False

            self.state_repo.mark_as_transcribed(video_id)
            return True
        except Exception:
            return False


# =========================================================================
# QUERIES (Read Side)
# =========================================================================

class YouTubeQueryHandler:
    """Handler para Queries (Read Side)."""

    def __init__(
        self,
        state_repo: Optional[YouTubeStateRepository] = None
    ):
        """Inicializa handler.

        Args:
            state_repo: Repositório de estado (ou cria novo)
        """
        self.state_repo = state_repo or YouTubeStateRepository()

    def get_status(
        self,
        playlist_id: str = "LL",
        limit: int = 10
    ) -> StatusResult:
        """Busca status de uma playlist.

        Args:
            playlist_id: ID da playlist
            limit: Máximo de vídeos pendentes

        Returns:
            StatusResult com status e vídeos pendentes
        """
        stats = self.state_repo.get_playlist_stats(playlist_id)
        pending = self.state_repo.find_pending_notification_by_playlist(
            playlist_id,
            limit=limit
        )

        return StatusResult(
            playlist_id=playlist_id,
            total_videos=stats["total_videos"],
            pending_notification=stats["pending"],
            notified=stats["notified"],
            transcribed=stats["transcribed"],
            pending_videos=pending
        )

    def get_stats(self) -> StatsResult:
        """Busca estatísticas gerais.

        Returns:
            StatsResult com estatísticas de todas playlists
        """
        playlists_stats = self.state_repo.get_all_playlists_stats()

        total_playlists = len(playlists_stats)
        total_videos = sum(s["total_videos"] for s in playlists_stats)
        total_pending = sum(s["pending"] for s in playlists_stats)

        return StatsResult(
            total_playlists=total_playlists,
            total_videos=total_videos,
            total_pending=total_pending,
            playlists=playlists_stats
        )

    def list_playlists(
        self,
        access_token: Optional[str] = None
    ) -> PlaylistListResult:
        """Lista playlists do YouTube.

        Args:
            access_token: Token OAuth (ou usa do .env)

        Returns:
            PlaylistListResult com playlists
        """
        token = access_token or os.getenv("GOOGLE_OAUTH_TOKEN")
        api = YouTubeAPIClient(access_token=token)

        playlists = api.get_my_playlists(max_results=50)

        return PlaylistListResult(
            playlists=playlists,
            total=len(playlists)
        )

    def list_videos(
        self,
        playlist_id: str,
        limit: int = 20
    ) -> VideoListResult:
        """Lista vídeos de uma playlist.

        Args:
            playlist_id: ID da playlist
            limit: Máximo de vídeos

        Returns:
            VideoListResult com vídeos
        """
        videos = self.state_repo.get_videos_by_playlist(
            playlist_id,
            limit=limit
        )

        return VideoListResult(
            playlist_id=playlist_id,
            videos=videos,
            total=len(videos)
        )

    def find_new_videos(
        self,
        playlist_id: Optional[str] = None
    ) -> List[VideoState]:
        """Encontra vídeos não sincronizados.

        Args:
            playlist_id: Filtrar por playlist (opcional)

        Returns:
            Lista de VideoState não sincronizados
        """
        return self.state_repo.find_new_videos(playlist_id)
