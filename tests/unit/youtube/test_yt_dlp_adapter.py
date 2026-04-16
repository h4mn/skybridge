"""Testes para YtDlpAdapter.

DOC: src/core/youtube/infrastructure/yt_dlp_adapter.py
Metodologia: TDD Estrito (RED → GREEN → REFACTOR)
"""

import pytest
from pathlib import Path
from unittest.mock import Mock, patch, AsyncMock


@pytest.mark.unit
class TestYtDlpAdapter:
    """Testes do adaptador yt-dlp."""

    def test_init_creates_download_path(self, tmp_path):
        """Testa que cria diretório de download."""
        from src.core.youtube.infrastructure.yt_dlp_adapter import YtDlpAdapter

        download_dir = tmp_path / "youtube"
        adapter = YtDlpAdapter(download_dir)

        assert download_dir.exists()
        assert adapter._download_path == download_dir

    @pytest.mark.asyncio
    async def test_extract_video_id(self):
        """Testa extração de ID de vídeo."""
        from src.core.youtube.infrastructure.yt_dlp_adapter import YtDlpAdapter

        adapter = YtDlpAdapter(Path("data/youtube"))

        # URLs válidas
        test_cases = [
            ("https://youtube.com/watch?v=abc123", "abc123"),
            ("https://youtu.be/abc123", "abc123"),
            ("https://www.youtube.com/watch?v=abc123&t=10s", "abc123"),
        ]

        for url, expected_id in test_cases:
            result = await adapter.extract_video_id(url)
            assert result == expected_id

    @pytest.mark.asyncio
    async def test_extract_video_id_invalid_url(self):
        """Testa que URL inválida levanta erro."""
        from src.core.youtube.infrastructure.yt_dlp_adapter import YtDlpAdapter

        adapter = YtDlpAdapter(Path("data/youtube"))

        with pytest.raises(ValueError, match="Could not extract video ID"):
            await adapter.extract_video_id("https://google.com")

    @pytest.mark.asyncio
    async def test_get_metadata(self):
        """Testa buscar metadados do vídeo."""
        from src.core.youtube.infrastructure.yt_dlp_adapter import YtDlpAdapter
        from unittest.mock import AsyncMock

        adapter = YtDlpAdapter(Path("data/youtube"))

        # Mock asyncio.create_subprocess_exec
        mock_proc = AsyncMock()
        mock_proc.returncode = 0
        mock_proc.communicate = AsyncMock(return_value=(
            b'{"title":"Test Video","channel":"Test Channel","duration":600}',
            b''
        ))

        with patch('asyncio.create_subprocess_exec', return_value=mock_proc):
            metadata = await adapter.get_metadata("https://youtube.com/watch?v=abc123")

            assert metadata.title == "Test Video"
            assert metadata.channel == "Test Channel"
            assert metadata.duration_seconds == 600

    @pytest.mark.asyncio
    async def test_download_lightweight(self):
        """Testa download em formato leve."""
        from src.core.youtube.infrastructure.yt_dlp_adapter import YtDlpAdapter

        adapter = YtDlpAdapter(Path("data/youtube"))

        # Mock asyncio.create_subprocess_exec
        mock_proc = AsyncMock()
        mock_proc.returncode = 0
        mock_proc.communicate = AsyncMock(return_value=(b'', b''))

        with patch('asyncio.create_subprocess_exec', return_value=mock_proc):
            local_path = await adapter.download_lightweight("https://youtube.com/watch?v=abc123")

            assert local_path is not None
            assert "abc123" in str(local_path)

    @pytest.mark.asyncio
    async def test_download_video(self):
        """Testa download completo."""
        from src.core.youtube.infrastructure.yt_dlp_adapter import YtDlpAdapter

        adapter = YtDlpAdapter(Path("data/youtube"))

        # Mock asyncio.create_subprocess_exec
        mock_proc = AsyncMock()
        mock_proc.returncode = 0
        mock_proc.communicate = AsyncMock(return_value=(b'', b''))

        with patch('asyncio.create_subprocess_exec', return_value=mock_proc):
            local_path = await adapter.download_video("https://youtube.com/watch?v=abc123")

            assert local_path is not None
            assert "abc123" in str(local_path)

    @pytest.mark.asyncio
    async def test_download_audio_only(self):
        """Testa download apenas áudio (MP3) para transcrição."""
        from src.core.youtube.infrastructure.yt_dlp_adapter import YtDlpAdapter

        adapter = YtDlpAdapter(Path("data/youtube"))

        # Mock asyncio.create_subprocess_exec
        mock_proc = AsyncMock()
        mock_proc.returncode = 0
        mock_proc.communicate = AsyncMock(return_value=(b'', b''))

        with patch('asyncio.create_subprocess_exec', return_value=mock_proc) as mock_subproc:
            local_path = await adapter.download_audio_only("https://youtube.com/watch?v=abc123")

            # Verifica que chamou yt-dlp com rate-limit
            call_args = mock_subproc.call_args
            cmd = call_args[0]  # Primeiro argumento posicional é a lista de comandos

            assert "--rate-limit" in cmd
            assert "500K" in cmd
            assert "--extract-audio" in cmd or "--audio-format" in cmd

            assert local_path is not None
            assert "abc123" in str(local_path)
            assert local_path.suffix in [".mp3", ".m4a", ".opus"]


@pytest.mark.unit
class TestYtDlpAdapterIntegration:
    """Testes de integração com yt-dlp (requer yt-dlp instalado)."""

    @pytest.mark.skipif(
        True,  # Marcar como skip por padrão (requer yt-dlp real)
        reason="Requer yt-dlp instalado"
    )
    @pytest.mark.asyncio
    async def test_real_extract_video_id(self):
        """Teste real com yt-dlp (se instalado)."""
        from src.core.youtube.infrastructure.yt_dlp_adapter import YtDlpAdapter

        adapter = YtDlpAdapter(Path("data/youtube"))
        result = await adapter.extract_video_id("https://youtube.com/watch?v=dQw4w9WgXcQ")

        assert result == "dQw4w9WgXcQ"
