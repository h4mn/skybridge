"""
Testes unitários para tools/fetch_messages.py - TDD Estrito.
"""

import pytest
from unittest.mock import AsyncMock, Mock, patch
from datetime import datetime


class TestFetchMessagesInput:
    """Testes para validação de entrada."""

    def test_channel_obrigatorio(self):
        """RED → GREEN: channel é obrigatório."""
        from src.core.discord.models import FetchMessagesInput

        with pytest.raises(Exception):
            FetchMessagesInput(limit=10)

    def test_limit_opcional_com_default(self):
        """RED → GREEN: limit é opcional com default."""
        from src.core.discord.models import FetchMessagesInput

        inp = FetchMessagesInput(channel="123")
        assert inp.limit == 20  # default


class TestHandleFetchMessages:
    """Testes para handle_fetch_messages()."""

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

        # Mensagens mock
        msg1 = Mock()
        msg1.id = 111
        msg1.author = Mock()
        msg1.author.name = "User1"
        msg1.author.id = 111111
        msg1.content = "Hello"
        msg1.created_at = datetime(2024, 1, 1, 12, 0)
        msg1.attachments = []

        msg2 = Mock()
        msg2.id = 222
        msg2.author = Mock()
        msg2.author.name = "Bot"
        msg2.author.id = 999888777  # Meu ID
        msg2.content = "Hi there"
        msg2.created_at = datetime(2024, 1, 1, 12, 1)
        msg2.attachments = []

        # history() retorna AsyncIterator
        async def mock_history(limit):
            return [msg2, msg1]  # Mais recentes primeiro

        channel.history = Mock(return_value=mock_history(limit=100))
        return channel, [msg1, msg2]

    @pytest.mark.asyncio
    async def test_busca_mensagens_retorna_lista(
        self, mock_client, access_file
    ):
        """RED → GREEN: handle_fetch_messages retorna lista de mensagens."""
        from src.core.discord.tools import fetch_messages as fm_module
        from src.core.discord.tools.fetch_messages import handle_fetch_messages

        # Mock channel
        channel = Mock()
        msg = Mock()
        msg.id = 111
        msg.author = Mock()
        msg.author.name = "User"
        msg.author.id = 222
        msg.content = "Hello"
        msg.created_at = datetime(2024, 1, 1, 12, 0)
        msg.attachments = []

        async def mock_history(limit):
            return [msg]

        # Mock AsyncIterator
        class MockHistory:
            async def flatten(self):
                return [msg]

        channel.history = Mock(return_value=MockHistory())

        with patch.object(fm_module, "fetch_allowed_channel", return_value=channel):
            result = await handle_fetch_messages(
                mock_client, {"channel": "123"}
            )

        assert result.channel_id == "123"
        assert len(result.messages) == 1
        assert result.messages[0].content == "Hello"

    @pytest.mark.asyncio
    async def test_retorna_mais_antigas_primeiro(
        self, mock_client, access_file
    ):
        """RED → GREEN: mensagens são retornadas oldest-first."""
        from src.core.discord.tools import fetch_messages as fm_module
        from src.core.discord.tools.fetch_messages import handle_fetch_messages

        channel = Mock()

        msg1 = Mock()
        msg1.id = 100
        msg1.author = Mock()
        msg1.author.name = "User"
        msg1.author.id = 111
        msg1.content = "Primeira"
        msg1.created_at = datetime(2024, 1, 1, 10, 0)
        msg1.attachments = []

        msg2 = Mock()
        msg2.id = 200
        msg2.author = Mock()
        msg2.author.name = "User"
        msg2.author.id = 111
        msg2.content = "Segunda"
        msg2.created_at = datetime(2024, 1, 1, 11, 0)
        msg2.attachments = []

        class MockHistory:
            async def flatten(self):
                return [msg2, msg1]  # history retorna newest first

        channel.history = Mock(return_value=MockHistory())

        with patch.object(fm_module, "fetch_allowed_channel", return_value=channel):
            result = await handle_fetch_messages(
                mock_client, {"channel": "123"}
            )

        # Output deve ser oldest first
        assert result.messages[0].id == "100"
        assert result.messages[1].id == "200"

    @pytest.mark.asyncio
    async def test_identifica_mensagens_do_bot(
        self, mock_client, access_file
    ):
        """RED → GREEN: is_bot é True para mensagens do próprio bot."""
        from src.core.discord.tools import fetch_messages as fm_module
        from src.core.discord.tools.fetch_messages import handle_fetch_messages

        channel = Mock()

        msg = Mock()
        msg.id = 111
        msg.author = Mock()
        msg.author.name = "Bot"
        msg.author.id = 999888777  # Mesmo ID do client.user
        msg.content = "My message"
        msg.created_at = datetime(2024, 1, 1, 12, 0)
        msg.attachments = []

        class MockHistory:
            async def flatten(self):
                return [msg]

        channel.history = Mock(return_value=MockHistory())

        with patch.object(fm_module, "fetch_allowed_channel", return_value=channel):
            result = await handle_fetch_messages(
                mock_client, {"channel": "123"}
            )

        assert result.messages[0].is_bot is True

    @pytest.mark.asyncio
    async def test_inclui_anexos(
        self, mock_client, access_file
    ):
        """RED → GREEN: anexos são incluídos no output."""
        from src.core.discord.tools import fetch_messages as fm_module
        from src.core.discord.tools.fetch_messages import handle_fetch_messages

        channel = Mock()

        # Anexo mock
        att = Mock()
        att.filename = "image.png"
        att.content_type = "image/png"
        att.size = 1024 * 50  # 50KB

        msg = Mock()
        msg.id = 111
        msg.author = Mock()
        msg.author.name = "User"
        msg.author.id = 222
        msg.content = ""
        msg.created_at = datetime(2024, 1, 1, 12, 0)
        msg.attachments = [att]

        class MockHistory:
            async def flatten(self):
                return [msg]

        channel.history = Mock(return_value=MockHistory())

        with patch.object(fm_module, "fetch_allowed_channel", return_value=channel):
            result = await handle_fetch_messages(
                mock_client, {"channel": "123"}
            )

        assert len(result.messages[0].attachments) == 1
        assert result.messages[0].attachments[0].name == "image.png"
        assert result.messages[0].content == "(attachment)"

    @pytest.mark.asyncio
    async def test_respeita_limite(
        self, mock_client, access_file
    ):
        """RED → GREEN: limit é respeitado (cap em 100)."""
        from src.core.discord.tools import fetch_messages as fm_module
        from src.core.discord.tools.fetch_messages import handle_fetch_messages

        channel = Mock()

        # Cria 5 mensagens
        msgs = []
        for i in range(5):
            m = Mock()
            m.id = i
            m.author = Mock()
            m.author.name = "User"
            m.author.id = 222
            m.content = f"Msg {i}"
            m.created_at = datetime(2024, 1, 1, 12, i)
            m.attachments = []
            msgs.append(m)

        class MockHistory:
            def __init__(self, limit):
                self.limit = limit

            async def flatten(self):
                return msgs[:self.limit]

        channel.history = Mock(side_effect=lambda limit: MockHistory(limit))

        with patch.object(fm_module, "fetch_allowed_channel", return_value=channel):
            result = await handle_fetch_messages(
                mock_client, {"channel": "123", "limit": 3}
            )

        assert len(result.messages) == 3
