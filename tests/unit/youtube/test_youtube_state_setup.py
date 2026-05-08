"""Testes para youtube_state_setup.

DOC: src/core/youtube/infrastructure/youtube_state_setup.py
Metodologia: TDD Estrito (RED → GREEN → REFACTOR)

Funcionalidade:
    - Setup do schema SQLite
    - Verificação do estado
    - Idempotência
"""

import pytest
from pathlib import Path
import sqlite3


@pytest.mark.unit
class TestSetupYouTubeState:
    """Testes do setup do State Repository."""

    def test_setup_creates_database(self, tmp_path):
        """Testa que setup cria banco e tabelas."""
        from src.core.youtube import setup_youtube_state

        db_path = tmp_path / "test.db"

        setup_youtube_state(str(db_path))

        assert db_path.exists()

        # Verificar schema
        conn = sqlite3.connect(str(db_path))
        cursor = conn.cursor()

        cursor.execute("""
            SELECT name FROM sqlite_master
            WHERE type='table'
            ORDER BY name
        """)

        tables = [row[0] for row in cursor.fetchall()]

        assert "video_state" in tables
        assert "playlist_sync" in tables

        conn.close()

    def test_setup_is_idempotent(self, tmp_path):
        """Testa que setup pode ser chamado múltiplas vezes."""
        from src.core.youtube import setup_youtube_state

        db_path = tmp_path / "test.db"

        # Setup 1ª vez
        setup_youtube_state(str(db_path))

        # Adicionar dados
        conn = sqlite3.connect(str(db_path))
        conn.execute(
            "INSERT INTO video_state (video_id, title, channel, duration_seconds, playlist_id) VALUES (?, ?, ?, ?, ?)",
            ("abc123", "Teste", "Canal", 120, "LL")
        )
        conn.commit()
        conn.close()

        # Setup 2ª vez (não deve perder dados)
        setup_youtube_state(str(db_path))

        conn = sqlite3.connect(str(db_path))
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM video_state")
        count = cursor.fetchone()[0]
        conn.close()

        assert count == 1  # Dados preservados

    def test_setup_force_recreate_drops_data(self, tmp_path):
        """Testa que force_recreate reinicia o banco."""
        from src.core.youtube import setup_youtube_state

        db_path = tmp_path / "test.db"

        # Setup inicial + dados
        setup_youtube_state(str(db_path))

        conn = sqlite3.connect(str(db_path))
        conn.execute(
            "INSERT INTO video_state (video_id, title, channel, duration_seconds, playlist_id) VALUES (?, ?, ?, ?, ?)",
            ("abc123", "Teste", "Canal", 120, "LL")
        )
        conn.commit()
        conn.close()

        # Recreate
        setup_youtube_state(str(db_path), force_recreate=True)

        # Deve estar vazio
        conn = sqlite3.connect(str(db_path))
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM video_state")
        count = cursor.fetchone()[0]
        conn.close()

        assert count == 0


@pytest.mark.unit
class TestVerifyYouTubeState:
    """Testes da verificação do estado."""

    def test_verify_nonexistent_database(self, tmp_path):
        """Testa verificação de banco inexistente."""
        from src.core.youtube import verify_youtube_state

        db_path = tmp_path / "nao_existe.db"

        status = verify_youtube_state(str(db_path))

        assert status["exists"] is False
        assert "error" in status

    def test_verify_valid_database(self, tmp_path):
        """Testa verificação de banco válido."""
        from src.core.youtube import setup_youtube_state, verify_youtube_state

        db_path = tmp_path / "test.db"

        setup_youtube_state(str(db_path))

        status = verify_youtube_state(str(db_path))

        assert status["exists"] is True
        assert status["status"] == "ok"
        assert "video_state" in status["tables"]
        assert "playlist_sync" in status["tables"]

    def test_verify_counts_records(self, tmp_path):
        """Testa contagem de registros."""
        from src.core.youtube import setup_youtube_state, verify_youtube_state

        db_path = tmp_path / "test.db"

        setup_youtube_state(str(db_path))

        # Adicionar dados
        conn = sqlite3.connect(str(db_path))
        conn.execute(
            "INSERT INTO video_state (video_id, title, channel, duration_seconds, playlist_id) VALUES (?, ?, ?, ?, ?)",
            ("abc123", "Teste", "Canal", 120, "LL")
        )
        conn.execute(
            "INSERT INTO playlist_sync (playlist_id, last_sync_at, total_videos) VALUES (?, datetime('now'), 10)",
            ("LL",)
        )
        conn.commit()
        conn.close()

        status = verify_youtube_state(str(db_path))

        assert status["video_count"] == 1
        assert status["playlist_count"] == 1


@pytest.mark.unit
class TestGetYouTubeStatePath:
    """Testes do utilitário de caminho."""

    def test_get_default_path(self):
        """Testa retorna caminho padrão."""
        from src.core.youtube import get_youtube_state_path

        path = get_youtube_state_path()

        assert path == "data/youtube_copilot.db"

    def test_get_path_from_env(self, monkeypatch):
        """Testa lê caminho da variável de ambiente."""
        from src.core.youtube import get_youtube_state_path

        monkeypatch.setenv("YOUTUBE_STATE_DB", "custom/path.db")

        path = get_youtube_state_path()

        assert path == "custom/path.db"
