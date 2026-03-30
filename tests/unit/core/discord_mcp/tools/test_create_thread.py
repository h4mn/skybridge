"""
Testes unitários para tools/create_thread.py - TDD Estrito.
"""

import pytest
from unittest.mock import AsyncMock, Mock, patch


class TestCreateThreadInput:
    """Testes para validação de entrada."""

    def test_channel_id_obrigatorio(self):
        """RED → GREEN: channel_id é obrigatório."""
        from src.core.discord.models import CreateThreadInput

        with pytest.raises(Exception):
            CreateThreadInput(message_id="123", name="Thread")

    def test_message_id_obrigatorio(self):
        """RED → GREEN: message_id é obrigatório."""
        from src.core.discord.models import CreateThreadInput

        with pytest.raises(Exception):
            CreateThreadInput(channel_id="123", name="Thread")

    def test_name_obrigatorio(self):
        """RED → GREEN: name é obrigatório."""
        from src.core.discord.models import CreateThreadInput

        with pytest.raises(Exception):
            CreateThreadInput(channel_id="123", message_id="456")

    def test_auto_archive_duration_default(self):
        """RED → GREEN: auto_archive_duration tem default 1440 (24h)."""
        from src.core.discord.models import CreateThreadInput

        inp = CreateThreadInput(channel_id="123", message_id="456", name="Thread")
        assert inp.auto_archive_duration == 1440


class TestHandleCreateThread:
    """Testes para handle_create_thread()."""

    @pytest.fixture
    def mock_client(self):
        """Cliente Discord mockado."""
        return Mock()

    @pytest.fixture
    def mock_channel(self):
        """Canal Discord mockado."""
        channel = Mock()
        channel.id = 111222333

        # Mensagem mock
        message = Mock()
        message.id = 444555666

        # Thread mock
        thread = Mock()
        thread.id = 777888999
        thread.name = "Test Thread"

        message.create_thread = AsyncMock(return_value=thread)
        channel.fetch_message = AsyncMock(return_value=message)

        return channel, message, thread

    @pytest.mark.asyncio
    async def test_cria_thread_com_sucesso(
        self, mock_client, mock_channel, access_file
    ):
        """RED → GREEN: handle_create_thread cria thread com sucesso."""
        from src.core.discord.tools import create_thread as ct_module
        from src.core.discord.tools.create_thread import handle_create_thread

        channel, message, thread = mock_channel

        with patch.object(ct_module, "fetch_allowed_channel", return_value=channel):
            result = await handle_create_thread(
                mock_client,
                {
                    "channel_id": "123",
                    "message_id": "456",
                    "name": "Test Thread",
                },
            )

        assert result.thread_id == "777888999"
        assert result.thread_name == "Test Thread"
        assert result.parent_channel_id == "111222333"
        message.create_thread.assert_called_once()

    @pytest.mark.asyncio
    async def test_usa_auto_archive_duration_custom(
        self, mock_client, mock_channel, access_file
    ):
        """RED → GREEN: auto_archive_duration custom é passado."""
        from src.core.discord.tools import create_thread as ct_module
        from src.core.discord.tools.create_thread import handle_create_thread

        channel, message, thread = mock_channel

        with patch.object(ct_module, "fetch_allowed_channel", return_value=channel):
            await handle_create_thread(
                mock_client,
                {
                    "channel_id": "123",
                    "message_id": "456",
                    "name": "Thread",
                    "auto_archive_duration": 60,
                },
            )

        message.create_thread.assert_called_once_with(
            name="Thread", auto_archive_duration=60
        )

    @pytest.mark.asyncio
    async def test_mensagem_nao_encontrada_gera_erro(
        self, mock_client, access_file
    ):
        """RED → GREEN: mensagem não encontrada gera ValueError."""
        from src.core.discord.tools import create_thread as ct_module
        from src.core.discord.tools.create_thread import handle_create_thread

        channel = Mock()
        channel.fetch_message = AsyncMock(side_effect=Exception("Not found"))

        with patch.object(ct_module, "fetch_allowed_channel", return_value=channel):
            with pytest.raises(ValueError, match="(?i)não encontrada"):
                await handle_create_thread(
                    mock_client,
                    {
                        "channel_id": "123",
                        "message_id": "456",
                        "name": "Thread",
                    },
                )

    @pytest.mark.asyncio
    async def test_erro_ao_criar_thread_gera_erro(
        self, mock_client, mock_channel, access_file
    ):
        """RED → GREEN: erro no create_thread gera ValueError."""
        from src.core.discord.tools import create_thread as ct_module
        from src.core.discord.tools.create_thread import handle_create_thread

        channel, message, thread = mock_channel
        message.create_thread = AsyncMock(side_effect=Exception("Rate limited"))

        with patch.object(ct_module, "fetch_allowed_channel", return_value=channel):
            with pytest.raises(ValueError, match="(?i)falha"):
                await handle_create_thread(
                    mock_client,
                    {
                        "channel_id": "123",
                        "message_id": "456",
                        "name": "Thread",
                    },
                )
