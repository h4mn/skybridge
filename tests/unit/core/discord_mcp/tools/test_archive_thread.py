"""
Testes unitários para tools/archive_thread.py - TDD Estrito.
"""

import pytest
from unittest.mock import AsyncMock, Mock, patch


class TestArchiveThreadInput:
    """Testes para validação de entrada."""

    def test_thread_id_obrigatorio(self):
        """RED → GREEN: thread_id é obrigatório."""
        from src.core.discord.models import ArchiveThreadInput

        with pytest.raises(Exception):
            ArchiveThreadInput()


class TestHandleArchiveThread:
    """Testes para handle_archive_thread()."""

    @pytest.fixture
    def mock_client(self):
        """Cliente Discord mockado."""
        client = Mock()
        return client

    @pytest.fixture
    def mock_thread(self):
        """Thread Discord mockada."""
        thread = Mock()
        thread.id = 777888999
        thread.name = "Test Thread"
        thread.archived = False
        thread.parent_id = 987654321  # Canal pai autorizado (do sample_access_data)
        thread.edit = AsyncMock()
        return thread

    @pytest.mark.asyncio
    async def test_arquiva_thread_com_sucesso(
        self, mock_client, mock_thread, access_file
    ):
        """RED → GREEN: handle_archive_thread arquiva thread."""
        from src.core.discord.tools.archive_thread import handle_archive_thread

        mock_client.get_channel = Mock(return_value=mock_thread)

        result = await handle_archive_thread(
            mock_client, {"thread_id": "777888999"}
        )

        assert result.archived is True
        assert result.thread_id == "777888999"
        mock_thread.edit.assert_called_once_with(archived=True)

    @pytest.mark.asyncio
    async def test_thread_nao_encontrada_gera_erro(
        self, mock_client, access_file
    ):
        """RED → GREEN: thread não encontrada gera ValueError."""
        from src.core.discord.tools.archive_thread import handle_archive_thread

        mock_client.get_channel = Mock(return_value=None)
        mock_client.fetch_channel = AsyncMock(side_effect=Exception("Not found"))

        with pytest.raises(ValueError, match="(?i)não encontrada"):
            await handle_archive_thread(
                mock_client, {"thread_id": "999"}
            )

    @pytest.mark.asyncio
    async def test_canal_nao_e_thread_gera_erro(
        self, mock_client, access_file
    ):
        """RED → GREEN: canal sem atributo 'archived' não é thread."""
        from src.core.discord.tools.archive_thread import handle_archive_thread

        # Canal normal (não thread)
        channel = Mock()
        del channel.archived  # Remove atributo
        mock_client.get_channel = Mock(return_value=channel)

        with pytest.raises(ValueError, match="(?i)não é uma thread"):
            await handle_archive_thread(
                mock_client, {"thread_id": "123"}
            )

    @pytest.mark.asyncio
    async def test_thread_em_canal_nao_autorizado_gera_erro(
        self, mock_client, empty_state_dir
    ):
        """RED → GREEN: thread em canal não autorizado gera erro."""
        from src.core.discord.tools.archive_thread import handle_archive_thread

        thread = Mock()
        thread.id = 777
        thread.archived = False
        thread.parent_id = 999999  # Canal não autorizado
        mock_client.get_channel = Mock(return_value=thread)

        with pytest.raises(ValueError, match="(?i)não autorizado"):
            await handle_archive_thread(
                mock_client, {"thread_id": "777"}
            )

    @pytest.mark.asyncio
    async def test_erro_ao_arquivar_gera_erro(
        self, mock_client, mock_thread, access_file
    ):
        """RED → GREEN: erro no edit gera ValueError."""
        from src.core.discord.tools.archive_thread import handle_archive_thread

        mock_thread.edit = AsyncMock(side_effect=Exception("Permission denied"))
        mock_client.get_channel = Mock(return_value=mock_thread)

        with pytest.raises(ValueError, match="(?i)falha"):
            await handle_archive_thread(
                mock_client, {"thread_id": "777888999"}
            )
