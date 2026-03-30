"""
Testes unitários para tools/edit_message.py - TDD Estrito.
"""

import pytest
from unittest.mock import AsyncMock, Mock, patch


class TestEditMessageInput:
    """Testes para validação de entrada."""

    def test_chat_id_obrigatorio(self):
        """RED → GREEN: chat_id é obrigatório."""
        from src.core.discord.models import EditMessageInput

        with pytest.raises(Exception):
            EditMessageInput(message_id="123", text="new text")

    def test_message_id_obrigatorio(self):
        """RED → GREEN: message_id é obrigatório."""
        from src.core.discord.models import EditMessageInput

        with pytest.raises(Exception):
            EditMessageInput(chat_id="123", text="new text")

    def test_text_obrigatorio(self):
        """RED → GREEN: text é obrigatório."""
        from src.core.discord.models import EditMessageInput

        with pytest.raises(Exception):
            EditMessageInput(chat_id="123", message_id="456")


class TestHandleEditMessage:
    """Testes para handle_edit_message()."""

    @pytest.fixture
    def mock_client(self):
        """Cliente Discord mockado."""
        client = Mock()
        client.user = Mock()
        client.user.id = 999888777
        return client

    @pytest.fixture
    def mock_channel(self):
        """Canal Discord mockado."""
        channel = Mock()
        return channel

    @pytest.mark.asyncio
    async def test_edita_mensagem_do_bot(
        self, mock_client, mock_channel, access_file
    ):
        """RED → GREEN: handle_edit_message edita mensagem do próprio bot."""
        from src.core.discord.tools import edit_message as em_module
        from src.core.discord.tools.edit_message import handle_edit_message

        # Mensagem do bot
        message = Mock()
        message.id = 111222333
        message.author = Mock()
        message.author.id = 999888777  # Mesmo ID do client.user
        message.edit = AsyncMock(return_value=message)

        mock_channel.fetch_message = AsyncMock(return_value=message)

        with patch.object(em_module, "fetch_allowed_channel", return_value=mock_channel):
            result = await handle_edit_message(
                mock_client,
                {"chat_id": "123", "message_id": "456", "text": "Updated!"},
            )

        assert result.edited is True
        assert result.message_id == "111222333"
        message.edit.assert_called_once_with(content="Updated!")

    @pytest.mark.asyncio
    async def test_recusa_editar_mensagem_de_outro(
        self, mock_client, mock_channel, access_file
    ):
        """RED → GREEN: não edita mensagem de outro usuário."""
        from src.core.discord.tools import edit_message as em_module
        from src.core.discord.tools.edit_message import handle_edit_message

        # Mensagem de outro usuário
        message = Mock()
        message.id = 111222333
        message.author = Mock()
        message.author.id = 111222  # ID diferente

        mock_channel.fetch_message = AsyncMock(return_value=message)

        with patch.object(em_module, "fetch_allowed_channel", return_value=mock_channel):
            with pytest.raises(ValueError, match="(?i)só é possível editar"):
                await handle_edit_message(
                    mock_client,
                    {"chat_id": "123", "message_id": "456", "text": "Updated!"},
                )

    @pytest.mark.asyncio
    async def test_mensagem_nao_encontrada_gera_erro(
        self, mock_client, mock_channel, access_file
    ):
        """RED → GREEN: mensagem não encontrada gera ValueError."""
        from src.core.discord.tools import edit_message as em_module
        from src.core.discord.tools.edit_message import handle_edit_message

        mock_channel.fetch_message = AsyncMock(return_value=None)

        with patch.object(em_module, "fetch_allowed_channel", return_value=mock_channel):
            with pytest.raises(ValueError, match="(?i)não encontrada"):
                await handle_edit_message(
                    mock_client,
                    {"chat_id": "123", "message_id": "456", "text": "Updated!"},
                )

    @pytest.mark.asyncio
    async def test_erro_ao_editar_gera_erro(
        self, mock_client, mock_channel, access_file
    ):
        """RED → GREEN: erro no edit gera ValueError."""
        from src.core.discord.tools import edit_message as em_module
        from src.core.discord.tools.edit_message import handle_edit_message

        message = Mock()
        message.id = 111222333
        message.author = Mock()
        message.author.id = 999888777
        message.edit = AsyncMock(side_effect=Exception("Rate limited"))

        mock_channel.fetch_message = AsyncMock(return_value=message)

        with patch.object(em_module, "fetch_allowed_channel", return_value=mock_channel):
            with pytest.raises(ValueError, match="(?i)falha"):
                await handle_edit_message(
                    mock_client,
                    {"chat_id": "123", "message_id": "456", "text": "Updated!"},
                )
