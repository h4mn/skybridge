"""
Testes unitários para tools/react.py - TDD Estrito.
"""

import pytest
from unittest.mock import AsyncMock, Mock, patch


class TestReactInput:
    """Testes para validação de entrada."""

    def test_chat_id_obrigatorio(self):
        """RED → GREEN: chat_id é obrigatório."""
        from src.core.discord.models import ReactInput

        with pytest.raises(Exception):
            ReactInput(message_id="123", emoji="👍")

    def test_message_id_obrigatorio(self):
        """RED → GREEN: message_id é obrigatório."""
        from src.core.discord.models import ReactInput

        with pytest.raises(Exception):
            ReactInput(chat_id="123", emoji="👍")

    def test_emoji_obrigatorio(self):
        """RED → GREEN: emoji é obrigatório."""
        from src.core.discord.models import ReactInput

        with pytest.raises(Exception):
            ReactInput(chat_id="123", message_id="456")


class TestHandleReact:
    """Testes para handle_react()."""

    @pytest.fixture
    def mock_client(self):
        """Cliente Discord mockado."""
        client = Mock()
        return client

    @pytest.fixture
    def mock_channel(self):
        """Canal Discord mockado."""
        channel = Mock()

        # Mensagem mock
        message = Mock()
        message.id = 111222333
        message.add_reaction = AsyncMock()

        channel.fetch_message = AsyncMock(return_value=message)
        return channel, message

    @pytest.mark.asyncio
    async def test_adiciona_reaction_emoji_unicode(
        self, mock_client, mock_channel, access_file
    ):
        """RED → GREEN: handle_react adiciona emoji Unicode."""
        from src.core.discord.tools import react as react_module
        from src.core.discord.tools.react import handle_react

        channel, message = mock_channel

        with patch.object(react_module, "fetch_allowed_channel", return_value=channel):
            result = await handle_react(
                mock_client,
                {"chat_id": "123", "message_id": "456", "emoji": "👍"},
            )

        assert result.success is True
        message.add_reaction.assert_called_once_with("👍")

    @pytest.mark.asyncio
    async def test_adiciona_reaction_emoji_custom(
        self, mock_client, mock_channel, access_file
    ):
        """RED → GREEN: handle_react adiciona emoji custom <:name:id>."""
        from src.core.discord.tools import react as react_module
        from src.core.discord.tools.react import handle_react

        channel, message = mock_channel

        with patch.object(react_module, "fetch_allowed_channel", return_value=channel):
            result = await handle_react(
                mock_client,
                {
                    "chat_id": "123",
                    "message_id": "456",
                    "emoji": "<:custom:123456789>",
                },
            )

        assert result.success is True
        message.add_reaction.assert_called_once_with("<:custom:123456789>")

    @pytest.mark.asyncio
    async def test_mensagem_nao_encontrada_gera_erro(
        self, mock_client, access_file
    ):
        """RED → GREEN: mensagem não encontrada gera ValueError."""
        from src.core.discord.tools import react as react_module
        from src.core.discord.tools.react import handle_react

        channel = Mock()
        channel.fetch_message = AsyncMock(return_value=None)

        with patch.object(react_module, "fetch_allowed_channel", return_value=channel):
            with pytest.raises(ValueError, match="(?i)não encontrada"):
                await handle_react(
                    mock_client,
                    {"chat_id": "123", "message_id": "456", "emoji": "👍"},
                )

    @pytest.mark.asyncio
    async def test_erro_ao_adicionar_reaction_gera_erro(
        self, mock_client, mock_channel, access_file
    ):
        """RED → GREEN: erro no add_reaction gera ValueError."""
        from src.core.discord.tools import react as react_module
        from src.core.discord.tools.react import handle_react

        channel, message = mock_channel
        message.add_reaction = AsyncMock(side_effect=Exception("Unknown emoji"))

        with patch.object(react_module, "fetch_allowed_channel", return_value=channel):
            with pytest.raises(ValueError, match="(?i)falha"):
                await handle_react(
                    mock_client,
                    {"chat_id": "123", "message_id": "456", "emoji": "invalid"},
                )
