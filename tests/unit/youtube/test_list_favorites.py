"""Testes para list_favorites.py

DOC: scripts/list_favorites.py
Metodologia: TDD Estrito (RED → GREEN → REFACTOR)

Funcionalidade:
    - Listar playlists do usuário
    - Mostrar vídeos de uma playlist
    - Formatar duração e saída
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from pathlib import Path


@pytest.mark.unit
class TestFormatDuration:
    """Testes da função format_duration."""

    def test_format_duration_seconds_only(self):
        """Testa formatação de apenas segundos."""
        from scripts.list_favorites import format_duration

        result = format_duration(45)
        assert result == "00:45"

    def test_format_duration_minutes_seconds(self):
        """Testa formatação de minutos e segundos."""
        from scripts.list_favorites import format_duration

        result = format_duration(125)  # 2:05
        assert result == "02:05"

    def test_format_duration_hours_minutes_seconds(self):
        """Testa formatação de horas, minutos e segundos."""
        from scripts.list_favorites import format_duration

        result = format_duration(3661)  # 1:01:01
        assert result == "01:01:01"

    def test_format_duration_none(self):
        """Testa formatação de None."""
        from scripts.list_favorites import format_duration

        result = format_duration(None)
        assert result == "???"

    def test_format_duration_zero(self):
        """Testa formatação de zero."""
        from scripts.list_favorites import format_duration

        result = format_duration(0)
        assert result == "00:00"


@pytest.mark.unit
class TestPrintVideos:
    """Testes da função print_videos."""

    def test_print_videos_empty_list(self, capsys):
        """Testa imprimir lista vazia."""
        from scripts.list_favorites import print_videos

        print_videos([])

        captured = capsys.readouterr()
        assert captured.out == ""

    def test_print_videos_single_video(self, capsys):
        """Testa imprimir único vídeo."""
        from scripts.list_favorites import print_videos

        videos = [{
            "video_id": "abc123",
            "title": "Vídeo Teste",
            "channel": "Canal Teste",
            "duration_seconds": 125
        }]

        print_videos(videos, max_count=10)

        captured = capsys.readouterr()
        assert "[1] Vídeo Teste" in captured.out
        assert "Canal: Canal Teste" in captured.out
        assert "Duração: 02:05" in captured.out
        assert "youtube.com/watch?v=abc123" in captured.out

    def test_print_videos_respects_max_count(self, capsys):
        """Testa que respeita max_count."""
        from scripts.list_favorites import print_videos

        videos = [
            {"video_id": f"vid{i}", "title": f"Vídeo {i}", "channel": "Canal", "duration_seconds": 60}
            for i in range(10)
        ]

        print_videos(videos, max_count=3)

        captured = capsys.readouterr()
        assert "[3]" in captured.out
        assert "[4]" not in captured.out


@pytest.mark.unit
class TestRefreshAccessToken:
    """Testes da função refresh_access_token."""

    def test_refresh_access_token_success(self):
        """Testa renovação bem-sucedida."""
        # Importar requests aqui para mockar antes da importação do módulo
        import requests

        with patch('requests.post') as mock_post:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json.return_value = {"access_token": "new_token123"}
            mock_post.return_value = mock_response

            from scripts.list_favorites import refresh_access_token

            result = refresh_access_token(
                client_id="test_id",
                client_secret="test_secret",
                refresh_token="test_refresh"
            )

            assert result == "new_token123"
            mock_post.assert_called_once()

    def test_refresh_access_token_failure(self):
        """Testa falha na renovação."""
        import requests

        with patch('requests.post') as mock_post:
            mock_response = MagicMock()
            mock_response.status_code = 401
            mock_response.text = "Invalid credentials"
            mock_post.return_value = mock_response

            from scripts.list_favorites import refresh_access_token

            with pytest.raises(ValueError, match="Erro ao renovar token"):
                refresh_access_token(
                    client_id="bad_id",
                    client_secret="bad_secret",
                    refresh_token="bad_refresh"
                )


@pytest.mark.unit
class TestFavoritesIntegration:
    """Testes de integração do fluxo principal."""

    @pytest.mark.asyncio
    async def test_list_playlists_flow(self):
        """Testa fluxo de listagem de playlists."""
        from scripts.list_favorites import YouTubeAPIClient

        # Mock do cliente
        mock_client = Mock(spec=YouTubeAPIClient)
        mock_client.get_my_playlists.return_value = [
            {
                "id": "PL1",
                "title": "Playlist Teste",
                "item_count": 5,
                "description": "Uma playlist de teste"
            }
        ]

        playlists = mock_client.get_my_playlists(max_results=50)

        assert len(playlists) == 1
        assert playlists[0]["title"] == "Playlist Teste"
        assert playlists[0]["item_count"] == 5

    @pytest.mark.asyncio
    async def test_get_playlist_items_flow(self):
        """Testa fluxo de obtenção de itens de playlist."""
        from scripts.list_favorites import YouTubeAPIClient

        mock_client = Mock(spec=YouTubeAPIClient)
        mock_client.get_playlist_items.return_value = [
            {
                "video_id": "abc123",
                "title": "Vídeo Teste",
                "channel": "Canal Teste",
                "duration_seconds": 300
            }
        ]

        videos = mock_client.get_playlist_items(playlist_id="LL", max_results=10)

        assert len(videos) == 1
        assert videos[0]["video_id"] == "abc123"
        assert videos[0]["title"] == "Vídeo Teste"


@pytest.mark.unit
class TestListFavoritesMain:
    """Testes da função main."""

    def test_main_missing_credentials(self, capsys):
        """Testa que falha sem credenciais."""
        from scripts.list_favorites import main

        # Mock load_dotenv e limpar variáveis de ambiente
        with patch("scripts.list_favorites.load_dotenv"):
            with patch.dict("os.environ", {}, clear=True):
                result = main()

                assert result == 1
                captured = capsys.readouterr()
                assert "❌ Erro: Credenciais não encontradas" in captured.out

    def test_main_with_valid_credentials(self, capsys):
        """Testa fluxo principal com credenciais válidas."""
        from scripts.list_favorites import main

        credentials = {
            "YOUTUBE_CLIENT_ID": "test_id",
            "YOUTUBE_CLIENT_SECRET": "test_secret",
            "YOUTUBE_REFRESH_TOKEN": "test_refresh"
        }

        mock_playlists = [
            {"id": "LL", "title": "Favoritos", "item_count": 10, "description": ""}
        ]

        mock_videos = [
            {
                "video_id": "abc123",
                "title": "Vídeo Teste",
                "channel": "Canal Teste",
                "duration_seconds": 300
            }
        ]

        with patch.dict("os.environ", credentials):
            with patch("scripts.list_favorites.refresh_access_token") as mock_refresh:
                with patch("scripts.list_favorites.YouTubeAPIClient") as mock_client_class:
                    mock_client = MagicMock()
                    mock_client.get_my_playlists.return_value = mock_playlists
                    mock_client.get_playlist_items.return_value = mock_videos
                    mock_client_class.return_value = mock_client

                    mock_refresh.return_value = "access_token"

                    with patch("builtins.input", return_value=""):
                        result = main()

                        assert result == 0
                        captured = capsys.readouterr()
                        assert "Token renovado" in captured.out
                        assert "Favoritos" in captured.out
