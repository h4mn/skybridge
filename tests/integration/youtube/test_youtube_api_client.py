"""Testes de integração para YouTube API Client.

DOC: src/core/youtube/infrastructure/youtube_api_client.py
"""

import pytest
import os
from src.core.youtube import YouTubeAPIClient


@pytest.mark.integration
class TestYouTubeAPIClientIntegration:
    """Testes de integração reais com YouTube API."""

    @pytest.fixture
    def api_client(self):
        """Cliente autenticado com OAuth."""
        # Requer GOOGLE_OAUTH_TOKEN no environment
        token = os.getenv("GOOGLE_OAUTH_TOKEN")
        if not token:
            pytest.skip("GOOGLE_OAUTH_TOKEN não definido")

        return YouTubeAPIClient(access_token=token)

    def test_list_favorites(self, api_client):
        """Testa listar vídeos dos favoritos (Liked Videos)."""
        # Playlist LL = Liked Videos
        favorites = api_client.get_playlist_items(
            playlist_id="LL",
            max_results=5
        )

        # Deve retornar lista de vídeos
        assert isinstance(favorites, list)

        if len(favorites) > 0:
            video = favorites[0]
            assert "video_id" in video
            assert "title" in video
            assert "channel" in video
            assert "duration_seconds" in video or "duration" in video

    def test_list_watch_later(self, api_client):
        """Testa listar vídeos do 'Assistir Mais Tarde'."""
        # Playlist WL = Watch Later
        watch_later = api_client.get_playlist_items(
            playlist_id="WL",
            max_results=5
        )

        assert isinstance(watch_later, list)

    def test_list_my_playlists(self, api_client):
        """Testa listar playlists do usuário."""
        playlists = api_client.get_my_playlists()

        assert isinstance(playlists, list)

        if len(playlists) > 0:
            playlist = playlists[0]
            assert "id" in playlist
            assert "title" in playlist
            assert "item_count" in playlist or "count" in playlist

    def test_video_details(self, api_client):
        """Testa buscar detalhes de vídeo específico."""
        # Video ID de um vídeo público para teste
        details = api_client.get_video_details("dQw4w9WgXcQ")  # Rick Roll

        assert details is not None
        assert "title" in details
        assert "channel" in details
        assert "duration_seconds" in details or "duration" in details


@pytest.mark.unit
class TestYouTubeAPIClientUnit:
    """Testes unitários sem chamadas reais à API."""

    def test_init_without_token_raises_error(self):
        """Testa que cliente sem token levanta erro."""
        with pytest.raises(ValueError, match="access_token"):
            YouTubeAPIClient(access_token=None)

    def test_init_with_empty_token_raises_error(self):
        """Testa que token vazio levanta erro."""
        with pytest.raises(ValueError, match="access_token"):
            YouTubeAPIClient(access_token="   ")
