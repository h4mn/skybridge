"""Testes de integração para YouTube State Repository.

Testa integração real com SQLite:
- Schema creation
- CRUD operations
- CQRS read/write operations
"""

import pytest
import tempfile
from pathlib import Path
from datetime import datetime, timedelta

from src.core.youtube import YouTubeStateRepository, VideoState, PlaylistSyncState


@pytest.mark.integration
class TestYouTubeStateRepositoryIntegration:
    """Testes de integração com SQLite real."""

    @pytest.fixture
    def temp_db_path(self):
        """Cria banco temporário."""
        db_path = tempfile.mktemp(suffix=".db")
        yield db_path
        # Cleanup
        Path(db_path).unlink(missing_ok=True)

    @pytest.fixture
    def repo(self, temp_db_path):
        """Cria repositório com banco real."""
        repo = YouTubeStateRepository(db_path=temp_db_path)
        yield repo
        repo.close()

    @pytest.fixture
    def sample_video(self):
        """Vídeo de exemplo."""
        return VideoState(
            video_id="test123",
            title="Test Video - Python Tutorial",
            channel="Test Channel",
            duration_seconds=600,
            playlist_id="LL",
            added_at=datetime.now(),
            synced_at=datetime.now(),
            thumbnail="http://example.com/thumb.jpg"
        )

    # ========================================================================
    # TEST: Schema Creation
    # ========================================================================

    def test_database_creation(self, repo):
        """Testa que banco e tabelas são criados."""
        # Verifica se arquivo foi criado
        assert Path(repo.db_path).exists()

        # Verifica tabelas
        tables = repo.conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table'"
        ).fetchall()

        table_names = [t[0] for t in tables]
        assert "video_state" in table_names
        assert "playlist_sync" in table_names

    # ========================================================================
    # TEST: Write Operations (Commands)
    # ========================================================================

    def test_save_video_insert(self, repo, sample_video):
        """Testa inserir novo vídeo."""
        repo.save_video(sample_video)

        # Verifica se foi salvo
        result = repo.get_video("test123")

        assert result is not None
        assert result.video_id == "test123"
        assert result.title == "Test Video - Python Tutorial"
        assert result.status == "pending"

    def test_save_video_update(self, repo, sample_video):
        """Testa atualizar vídeo existente (UPSERT)."""
        # Insert inicial
        repo.save_video(sample_video)

        # Update
        updated_video = VideoState(
            video_id="test123",
            title="UPDATED TITLE",
            channel=sample_video.channel,
            duration_seconds=sample_video.duration_seconds,
            playlist_id=sample_video.playlist_id,
            added_at=sample_video.added_at,
            synced_at=datetime.now(),
            notified_at=datetime.now()
        )

        repo.save_video(updated_video)

        # Verifica update
        result = repo.get_video("test123")
        assert result.title == "UPDATED TITLE"
        assert result.notified_at is not None

    def test_mark_as_synced(self, repo, sample_video):
        """Testa marcar vídeo como sincronizado."""
        repo.save_video(sample_video)

        # Marca como synced
        repo.mark_as_synced("test123")

        result = repo.get_video("test123")
        assert result.synced_at is not None
        assert result.status == "synced"

    def test_mark_as_notified(self, repo, sample_video):
        """Testa marcar vídeo como notificado."""
        repo.save_video(sample_video)

        # Marca como notified
        repo.mark_as_notified("test123")

        result = repo.get_video("test123")
        assert result.notified_at is not None

    def test_mark_as_transcribed(self, repo, sample_video):
        """Testa marcar vídeo como transcrito."""
        repo.save_video(sample_video)

        # Marca como transcribed
        repo.mark_as_transcribed("test123")

        result = repo.get_video("test123")
        assert result.transcribed_at is not None
        assert result.status == "transcribed"

    def test_save_playlist_sync(self, repo):
        """Testa salvar estado de sincronização."""
        sync_state = PlaylistSyncState(
            playlist_id="LL",
            last_sync_at=datetime.now(),
            total_videos=10,
            new_videos_found=3
        )

        repo.save_playlist_sync(sync_state)

        # Recupera
        result = repo.get_playlist_sync("LL")
        assert result is not None
        assert result.total_videos == 10
        assert result.new_videos_found == 3

    # ========================================================================
    # TEST: Read Operations (Queries)
    # ========================================================================

    def test_get_video(self, repo, sample_video):
        """Testa buscar vídeo por ID."""
        repo.save_video(sample_video)

        result = repo.get_video("test123")
        assert result is not None
        assert result.video_id == "test123"

    def test_get_video_not_found(self, repo):
        """Testa buscar vídeo inexistente."""
        result = repo.get_video("naoexiste")
        assert result is None

    def test_get_videos_by_playlist(self, repo):
        """Testa buscar vídeos de uma playlist."""
        # Adiciona alguns vídeos
        for i in range(3):
            video = VideoState(
                video_id=f"video{i}",
                title=f"Video {i}",
                channel="Channel",
                duration_seconds=600,
                playlist_id="LL"
            )
            repo.save_video(video)

        # Busca
        videos = repo.get_videos_by_playlist("LL")

        assert len(videos) == 3
        assert all(v.playlist_id == "LL" for v in videos)

    def test_find_new_videos(self, repo):
        """Testa encontrar vídeos não sincronizados."""
        # Vídeo sincronizado
        synced = VideoState(
            video_id="synced123",
            title="Synced",
            channel="Channel",
            duration_seconds=600,
            playlist_id="LL",
            synced_at=datetime.now()
        )
        repo.save_video(synced)

        # Vídeo não sincronizado (novo)
        new_video = VideoState(
            video_id="new123",
            title="New",
            channel="Channel",
            duration_seconds=600,
            playlist_id="LL"
        )
        repo.save_video(new_video)

        # Busca novos
        new_videos = repo.find_new_videos("LL")

        assert len(new_videos) == 1
        assert new_videos[0].video_id == "new123"

    def test_find_pending_notification(self, repo):
        """Testa encontrar vídeos pendentes de notificação."""
        # Vídeo notificado
        notified = VideoState(
            video_id="notified123",
            title="Notified",
            channel="Channel",
            duration_seconds=600,
            playlist_id="LL",
            notified_at=datetime.now()
        )
        repo.save_video(notified)

        # Vídeo pendente
        pending = VideoState(
            video_id="pending123",
            title="Pending",
            channel="Channel",
            duration_seconds=600,
            playlist_id="LL"
        )
        repo.save_video(pending)

        # Busca pendentes
        pending_videos = repo.find_pending_notification()

        assert len(pending_videos) == 1
        assert pending_videos[0].video_id == "pending123"

    def test_get_playlist_stats(self, repo):
        """Testa estatísticas de playlist."""
        # Adiciona 5 vídeos
        for i in range(5):
            video = VideoState(
                video_id=f"video{i}",
                title=f"Video {i}",
                channel="Channel",
                duration_seconds=600,
                playlist_id="LL"
            )
            repo.save_video(video)

        # Marca 2 como notificados
        repo.mark_as_notified("video0")
        repo.mark_as_notified("video1")

        # Stats
        stats = repo.get_playlist_stats("LL")

        assert stats["total_videos"] == 5
        assert stats["pending"] == 3
        assert stats["notified"] == 2

    def test_get_playlist_sync_not_found(self, repo):
        """Testa buscar sync de playlist não sincronizada."""
        result = repo.get_playlist_sync("NAO_EXISTE")
        assert result is None

    def test_get_all_playlists_stats(self, repo):
        """Testa estatísticas de todas as playlists."""
        # Vídeos em múltiplas playlists
        for playlist_id in ["LL", "WL", "PL123"]:
            for i in range(2):
                video = VideoState(
                    video_id=f"{playlist_id}_video{i}",
                    title=f"Video {i}",
                    channel="Channel",
                    duration_seconds=600,
                    playlist_id=playlist_id
                )
                repo.save_video(video)

        # Stats
        all_stats = repo.get_all_playlists_stats()

        assert len(all_stats) == 3
        assert all(s["total_videos"] == 2 for s in all_stats)

    # ========================================================================
    # TEST: CQRS Integration
    # ========================================================================

    def test_sync_workflow(self, repo):
        """Testa fluxo completo de sincronização."""
        # 1. Estado inicial: nenhum vídeo
        assert repo.get_playlist_stats("LL")["total_videos"] == 0

        # 2. Simula sync: adiciona 3 vídeos
        now = datetime.now()
        for i in range(3):
            video = VideoState(
                video_id=f"sync{i}",
                title=f"Sync Video {i}",
                channel="Channel",
                duration_seconds=600,
                playlist_id="LL",
                added_at=now,
                synced_at=now
            )
            repo.save_video(video)

        # 3. Salva estado da sync
        sync_state = PlaylistSyncState(
            playlist_id="LL",
            last_sync_at=now,
            total_videos=3,
            new_videos_found=3
        )
        repo.save_playlist_sync(sync_state)

        # 4. Verifica
        stats = repo.get_playlist_stats("LL")
        assert stats["total_videos"] == 3
        assert stats["synced"] == 3

        sync_result = repo.get_playlist_sync("LL")
        assert sync_result.total_videos == 3
        assert sync_result.new_videos_found == 3

    def test_query_pending_workflow(self, repo):
        """Testa fluxo de query de vídeos pendentes."""
        # 1. Adiciona 5 vídeos, 2 notificados
        for i in range(5):
            video = VideoState(
                video_id=f"pending{i}",
                title=f"Pending {i}",
                channel="Channel",
                duration_seconds=600,
                playlist_id="LL"
            )
            repo.save_video(video)

        # Marca 2 como notificados
        repo.mark_as_notified("pending0")
        repo.mark_as_notified("pending1")

        # 2. Query pendentes
        pending = repo.find_pending_notification_by_playlist("LL")

        assert len(pending) == 3
        assert all(v.notified_at is None for v in pending)
