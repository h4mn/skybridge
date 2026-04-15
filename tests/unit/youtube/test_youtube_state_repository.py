"""Testes para State Repository do YouTube Copilot.

DOC: src/core/youtube/infrastructure/youtube_state_repository.py
"""

import pytest
import sqlite3
import tempfile
from pathlib import Path
from datetime import datetime, timedelta

from src.core.youtube.infrastructure.youtube_state_repository import (
    YouTubeStateRepository,
    VideoState,
    PlaylistSyncState
)


@pytest.fixture
def temp_db():
    """Banco SQLite temporário para testes."""
    db_path = tempfile.mktemp(suffix=".db")
    repo = YouTubeStateRepository(db_path=db_path)
    yield repo
    # Cleanup - fecha conexão antes de deletar
    repo.close()
    Path(db_path).unlink(missing_ok=True)


@pytest.mark.unit
class TestVideoState:
    """Testes do VideoState value object."""

    def test_create_video_state(self):
        """Testa criação de VideoState."""
        state = VideoState(
            video_id="abc123",
            title="Test Video",
            channel="Test Channel",
            duration_seconds=600,
            playlist_id="LL",
            added_at=datetime.now(),
            synced_at=datetime.now()
        )

        assert state.video_id == "abc123"
        assert state.title == "Test Video"
        assert state.status == "pending"

    def test_video_state_defaults(self):
        """Testa valores padrão de VideoState."""
        state = VideoState(
            video_id="abc123",
            title="Test",
            channel="Channel",
            duration_seconds=600,
            playlist_id="LL"
        )

        assert state.status == "pending"
        assert state.notified_at is None
        assert state.transcribed_at is None


@pytest.mark.unit
class TestYouTubeStateRepository:
    """Testes unitários do State Repository."""

    def test_init_creates_schema(self, temp_db):
        """Testa que init cria schema do banco."""
        # Verifica se tabelas foram criadas
        tables = temp_db.conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table'"
        ).fetchall()

        table_names = [t[0] for t in tables]
        assert "video_state" in table_names
        assert "playlist_sync" in table_names

    def test_save_video(self, temp_db):
        """Testa salvar estado de vídeo."""
        state = VideoState(
            video_id="abc123",
            title="Test Video",
            channel="Test Channel",
            duration_seconds=600,
            playlist_id="LL",
            added_at=datetime.now()
        )

        temp_db.save_video(state)

        # Verifica se foi salvo
        result = temp_db.get_video("abc123")
        assert result is not None
        assert result.video_id == "abc123"
        assert result.title == "Test Video"

    def test_save_video_updates_existing(self, temp_db):
        """Testa que salvar vídeo atualiza se já existe."""
        # Primeiro save
        state1 = VideoState(
            video_id="abc123",
            title="Original Title",
            channel="Channel",
            duration_seconds=600,
            playlist_id="LL"
        )
        temp_db.save_video(state1)

        # Update com novo título
        state2 = VideoState(
            video_id="abc123",
            title="Updated Title",
            channel="Channel",
            duration_seconds=600,
            playlist_id="LL"
        )
        temp_db.save_video(state2)

        # Verifica update
        result = temp_db.get_video("abc123")
        assert result.title == "Updated Title"

    def test_find_new_videos(self, temp_db):
        """Testa encontrar vídeos novos (não sincronizados)."""
        # Vídeo antigo (synced)
        old_video = VideoState(
            video_id="old123",
            title="Old Video",
            channel="Channel",
            duration_seconds=600,
            playlist_id="LL",
            synced_at=datetime.now() - timedelta(hours=1)
        )
        temp_db.save_video(old_video)

        # Vídeo novo (not synced)
        new_video = VideoState(
            video_id="new123",
            title="New Video",
            channel="Channel",
            duration_seconds=600,
            playlist_id="LL"
        )
        temp_db.save_video(new_video)

        # Busca vídeos novos
        new_videos = temp_db.find_new_videos()

        assert len(new_videos) == 1
        assert new_videos[0].video_id == "new123"

    def test_find_notified_videos(self, temp_db):
        """Testa encontrar vídeos notificados."""
        # Vídeo notificado
        notified = VideoState(
            video_id="notified123",
            title="Notified",
            channel="Channel",
            duration_seconds=600,
            playlist_id="LL",
            notified_at=datetime.now()
        )
        temp_db.save_video(notified)

        # Vídeo não notificado
        pending = VideoState(
            video_id="pending123",
            title="Pending",
            channel="Channel",
            duration_seconds=600,
            playlist_id="LL"
        )
        temp_db.save_video(pending)

        # Busca pendentes de notificação
        pending_videos = temp_db.find_pending_notification()

        assert len(pending_videos) == 1
        assert pending_videos[0].video_id == "pending123"

    def test_mark_as_notified(self, temp_db):
        """Testa marcar vídeo como notificado."""
        video = VideoState(
            video_id="abc123",
            title="Test",
            channel="Channel",
            duration_seconds=600,
            playlist_id="LL"
        )
        temp_db.save_video(video)

        # Marca como notificado
        temp_db.mark_as_notified("abc123")

        # Verifica
        result = temp_db.get_video("abc123")
        assert result.notified_at is not None

    def test_get_playlist_stats(self, temp_db):
        """Testa estatísticas de playlist."""
        # Adiciona alguns vídeos
        for i in range(5):
            video = VideoState(
                video_id=f"video{i}",
                title=f"Video {i}",
                channel="Channel",
                duration_seconds=600,
                playlist_id="LL"
            )
            temp_db.save_video(video)

        # Marca 2 como notificados
        temp_db.mark_as_notified("video0")
        temp_db.mark_as_notified("video1")

        # Stats
        stats = temp_db.get_playlist_stats("LL")

        assert stats["total_videos"] == 5
        assert stats["pending"] == 3
        assert stats["notified"] == 2

    def test_get_all_videos_by_playlist(self, temp_db):
        """Testa buscar todos vídeos de uma playlist."""
        # Vídeos em playlists diferentes
        video_ll = VideoState(
            video_id="ll123",
            title="LL Video",
            channel="Channel",
            duration_seconds=600,
            playlist_id="LL"
        )
        video_wl = VideoState(
            video_id="wl123",
            title="WL Video",
            channel="Channel",
            duration_seconds=600,
            playlist_id="WL"
        )
        temp_db.save_video(video_ll)
        temp_db.save_video(video_wl)

        # Busca só LL
        ll_videos = temp_db.get_videos_by_playlist("LL")

        assert len(ll_videos) == 1
        assert ll_videos[0].video_id == "ll123"

    def test_playlist_sync_state(self, temp_db):
        """Testa estado de sincronização de playlist."""
        # Primeira sync
        sync_state = temp_db.get_playlist_sync("LL")
        assert sync_state is None  # Nunca sincronizado

        # Salva estado
        state = PlaylistSyncState(
            playlist_id="LL",
            last_sync_at=datetime.now(),
            total_videos=10
        )
        temp_db.save_playlist_sync(state)

        # Recupera
        retrieved = temp_db.get_playlist_sync("LL")
        assert retrieved is not None
        assert retrieved.total_videos == 10
