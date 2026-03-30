"""
Testes unitários para tools/list_threads.py - TDD Estrito.
"""

import pytest
from unittest.mock import AsyncMock, Mock, patch
from datetime import datetime


class TestListThreadsInput:
    """Testes para validação de entrada."""

    def test_channel_id_obrigatorio(self):
        """RED → GREEN: channel_id é obrigatório."""
        from src.core.discord.models import ListThreadsInput

        with pytest.raises(Exception):
            ListThreadsInput(include_archived=True)

    def test_include_archived_default_false(self):
        """RED → GREEN: include_archived default é False."""
        from src.core.discord.models import ListThreadsInput

        inp = ListThreadsInput(channel_id="123")
        assert inp.include_archived is False


class TestHandleListThreads:
    """Testes para handle_list_threads()."""

    @pytest.fixture
    def mock_client(self):
        """Cliente Discord mockado."""
        return Mock()

    @pytest.fixture
    def mock_channel(self):
        """Canal Discord mockado com threads."""
        channel = Mock()
        channel.id = 111222333

        # Threads mock
        thread1 = Mock()
        thread1.id = 444
        thread1.name = "Thread 1"
        thread1.message_count = 5
        thread1.created_at = datetime(2024, 1, 1, 12, 0)
        thread1.archived = False

        thread2 = Mock()
        thread2.id = 555
        thread2.name = "Thread 2"
        thread2.message_count = 10
        thread2.created_at = datetime(2024, 1, 2, 12, 0)
        thread2.archived = False

        channel.threads = [thread1, thread2]
        return channel, [thread1, thread2]

    @pytest.mark.asyncio
    async def test_lista_threads_ativas(
        self, mock_client, mock_channel, access_file
    ):
        """RED → GREEN: handle_list_threads lista threads ativas."""
        from src.core.discord.tools import list_threads as lt_module
        from src.core.discord.tools.list_threads import handle_list_threads

        channel, threads = mock_channel

        with patch.object(lt_module, "fetch_allowed_channel", return_value=channel):
            result = await handle_list_threads(
                mock_client, {"channel_id": "123"}
            )

        assert result.total == 2
        assert len(result.threads) == 2
        assert result.threads[0].name == "Thread 1"
        assert result.threads[1].name == "Thread 2"

    @pytest.mark.asyncio
    async def test_inclui_threads_arquivadas(
        self, mock_client, mock_channel, access_file
    ):
        """RED → GREEN: include_archived=True inclui threads arquivadas."""
        from src.core.discord.tools import list_threads as lt_module
        from src.core.discord.tools.list_threads import handle_list_threads

        channel, threads = mock_channel

        # Thread arquivada mock
        archived_thread = Mock()
        archived_thread.id = 666
        archived_thread.name = "Archived"
        archived_thread.message_count = 3
        archived_thread.created_at = datetime(2024, 1, 3, 12, 0)
        archived_thread.archived = True

        # Mock async iterator
        async def mock_archived(limit):
            yield archived_thread

        channel.archived_threads = mock_archived

        with patch.object(lt_module, "fetch_allowed_channel", return_value=channel):
            result = await handle_list_threads(
                mock_client, {"channel_id": "123", "include_archived": True}
            )

        assert result.total == 3  # 2 ativas + 1 arquivada

    @pytest.mark.asyncio
    async def test_canal_sem_threads_retorna_vazio(
        self, mock_client, access_file
    ):
        """RED → GREEN: canal sem threads retorna lista vazia."""
        from src.core.discord.tools import list_threads as lt_module
        from src.core.discord.tools.list_threads import handle_list_threads

        channel = Mock()
        channel.id = 111
        channel.threads = []

        with patch.object(lt_module, "fetch_allowed_channel", return_value=channel):
            result = await handle_list_threads(
                mock_client, {"channel_id": "123"}
            )

        assert result.total == 0
        assert result.threads == []
