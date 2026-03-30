"""
Testes unitários para server.py - TDD Estrito.

DOC: src/core/discord/server.py
Spec: discord-mcp-server - MCP Server expõe tools de mensagens Discord
"""

import pytest
from unittest.mock import AsyncMock, Mock, patch, MagicMock
import asyncio


class TestIsMentioned:
    """Testes para função is_mentioned()."""

    @pytest.fixture
    def mock_message(self):
        """Mensagem mockada."""
        msg = Mock()
        msg.content = "Hello world"
        msg.mentions = []
        msg.reference = None
        msg.guild = None
        return msg

    @pytest.fixture
    def mock_message_with_guild(self):
        """Mensagem com guild mockada."""
        msg = Mock()
        msg.content = "Hello <@bot_id>"
        msg.mentions = []
        msg.reference = None

        # Mock guild
        guild = Mock()
        bot_member = Mock()
        guild.me = bot_member
        msg.guild = guild

        return msg, bot_member

    @pytest.mark.asyncio
    async def test_direto_mention_retorna_true(self, mock_message_with_guild):
        """
        RED → GREEN: menção direta ao bot retorna True.

        Scenario: Canal de grupo com menção
        WHEN requireMention é true E bot é mencionado
        THEN is_mentioned retorna True
        """
        from src.core.discord.server import is_mentioned

        msg, bot_member = mock_message_with_guild
        msg.mentions = [bot_member]

        result = await is_mentioned(msg, None)
        assert result is True

    @pytest.mark.asyncio
    async def test_sem_mencao_retorna_false(self, mock_message):
        """
        RED → GREEN: sem menção retorna False.
        """
        from src.core.discord.server import is_mentioned

        result = await is_mentioned(mock_message, None)
        assert result is False

    @pytest.mark.asyncio
    async def test_mention_pattern_match_retorna_true(self, mock_message):
        """
        RED → GREEN: pattern customizado match retorna True.

        Scenario: mentionPatterns configurado
        WHEN mensagem contém pattern do mentionPatterns
        THEN is_mentioned retorna True
        """
        from src.core.discord.server import is_mentioned

        mock_message.content = "Sky, pode me ajudar?"

        result = await is_mentioned(mock_message, [r"Sky[,!]?"])
        assert result is True

    @pytest.mark.asyncio
    async def test_reply_nossa_mensagem_retorna_true(self, mock_message):
        """
        RED → GREEN: reply a uma de nossas mensagens retorna True.
        """
        from src.core.discord.server import is_mentioned

        mock_message.reference = Mock()
        mock_message.reference.message_id = "123456"

        with patch("src.core.discord.server.is_recently_sent", return_value=True):
            result = await is_mentioned(mock_message, None)
            assert result is True


class TestGate:
    """Testes para função gate()."""

    @pytest.fixture
    def mock_dm_message(self):
        """Mensagem DM mockada."""
        msg = Mock()
        msg.author = Mock()
        msg.author.id = 12345
        msg.author.bot = False
        msg.channel = Mock()
        msg.channel.id = 999
        msg.content = "Hello"
        return msg

    @pytest.fixture
    def mock_group_message(self):
        """Mensagem de grupo mockada."""
        msg = Mock()
        msg.author = Mock()
        msg.author.id = 12345
        msg.author.bot = False
        msg.channel = Mock()
        msg.channel.id = 111222
        msg.content = "Hello @bot"
        return msg

    @pytest.mark.asyncio
    async def test_dm_policy_disabled_drop(self, mock_dm_message, temp_state_dir):
        """
        RED → GREEN: dmPolicy disabled dropa todas as mensagens.

        Scenario: DM com usuário não autorizado em modo pairing
        WHEN dmPolicy é disabled
        THEN mensagem é dropada
        """
        from src.core.discord.server import gate
        from src.core.discord.access import Access, DMPolicy

        # Cria access.json com policy disabled
        import json
        access_data = {
            "dmPolicy": "disabled",
            "allowFrom": [],
            "groups": {},
            "pending": {}
        }
        access_file = temp_state_dir / "access.json"
        access_file.write_text(json.dumps(access_data))

        with patch("src.core.discord.access.STATE_DIR", temp_state_dir), \
             patch("src.core.discord.access.ACCESS_FILE", access_file), \
             patch("src.core.discord.server.load_access") as mock_load:
            mock_load.return_value = Access.model_validate(access_data)

            # Mock is_dm_channel
            with patch("src.core.discord.server.is_dm_channel", return_value=True):
                result = await gate(mock_dm_message)

        assert result["action"] == "drop"

    @pytest.mark.asyncio
    async def test_canal_nao_configurado_drop(self, mock_group_message):
        """
        RED → GREEN: canal não listado em groups é dropado.

        Scenario: Canal não configurado
        WHEN mensagem é recebida em canal não listado em groups
        THEN mensagem é ignorada (drop)
        """
        from src.core.discord.server import gate
        from src.core.discord.access import Access

        access = Access(
            dm_policy="pairing",
            allow_from=[],
            groups={},  # Nenhum canal configurado
            pending={},
        )

        with patch("src.core.discord.server.load_access", return_value=access), \
             patch("src.core.discord.server.prune_expired", return_value=False), \
             patch("src.core.discord.server.is_dm_channel", return_value=False), \
             patch("src.core.discord.server.is_thread_channel", return_value=False), \
             patch("src.core.discord.server.gate_group") as mock_gate_group:
            mock_gate_group.return_value = Mock(action="drop")

            result = await gate(mock_group_message)

        assert result["action"] == "drop"


class TestHandleInbound:
    """Testes para função handle_inbound()."""

    @pytest.fixture
    def mock_client(self):
        """Cliente Discord mockado."""
        return Mock()

    @pytest.fixture
    def mock_server(self):
        """MCP Server mockado."""
        server = Mock()
        server.notify = AsyncMock()
        return server

    @pytest.fixture
    def mock_message(self):
        """Mensagem mockada."""
        msg = Mock()
        msg.author = Mock()
        msg.author.id = 12345
        msg.author.name = "TestUser"
        msg.author.bot = False
        msg.channel = Mock()
        msg.channel.id = 999888
        msg.channel.typing = AsyncMock()
        msg.id = 111222333
        msg.content = "Hello bot!"
        msg.created_at = Mock()
        msg.created_at.isoformat = Mock(return_value="2024-01-01T12:00:00")
        msg.attachments = []
        msg.add_reaction = AsyncMock()
        msg.reply = AsyncMock()
        return msg

    @pytest.mark.asyncio
    async def test_mensagem_dropada_nao_entregue(self, mock_client, mock_server, mock_message):
        """
        RED → GREEN: mensagem dropada não é entregue ao Claude.
        """
        from src.core.discord.server import handle_inbound

        with patch("src.core.discord.server.gate", return_value={"action": "drop"}):
            await handle_inbound(mock_client, mock_server, mock_message)

        # notify não deve ser chamado
        mock_server.notify.assert_not_called()

    @pytest.mark.asyncio
    async def test_pairing_envia_codigo(self, mock_client, mock_server, mock_message):
        """
        RED → GREEN: pairing mode envia código de pareamento.

        Scenario: DM com usuário não autorizado em modo pairing
        WHEN mensagem privada é recebida de usuário NÃO em allowFrom
        THEN sistema gera código de pareamento e responde com instruções
        """
        from src.core.discord.server import handle_inbound

        with patch("src.core.discord.server.gate", return_value={"action": "pair", "code": "abc123", "is_resend": False}):
            await handle_inbound(mock_client, mock_server, mock_message)

        # Deve ter enviado reply com código de pareamento
        mock_message.reply.assert_called_once()
        call_args = mock_message.reply.call_args[0][0]
        assert "abc123" in call_args
        assert "/discord:access pair" in call_args

    @pytest.mark.asyncio
    async def test_deliver_envia_notificacao(self, mock_client, mock_server, mock_message):
        """
        RED → GREEN: deliver envia notificação MCP ao Claude.

        Scenario: DM com usuário allowlisted
        WHEN mensagem privada é recebida de usuário em allowFrom
        THEN mensagem é entregue ao Claude via notificação MCP
        """
        from src.core.discord.server import handle_inbound
        from src.core.discord.access import Access

        access = Access(dm_policy="allowlist", allow_from=["12345"])

        with patch("src.core.discord.server.gate", return_value={"action": "deliver", "access": access}):
            await handle_inbound(mock_client, mock_server, mock_message)

        # notify deve ser chamado com notificação de canal
        mock_server.notify.assert_called_once()
        call_args = mock_server.notify.call_args
        assert call_args[0][0] == "notifications/claude/channel"

        notification = call_args[0][1]
        assert notification["content"] == "Hello bot!"
        assert notification["meta"]["chat_id"] == "999888"
        assert notification["meta"]["user"] == "TestUser"

    @pytest.mark.asyncio
    async def test_typing_indicator_enviado(self, mock_client, mock_server, mock_message):
        """
        RED → GREEN: typing indicator é enviado.

        Spec: 8.5 Implementar typing indicator
        """
        from src.core.discord.server import handle_inbound
        from src.core.discord.access import Access

        access = Access(dm_policy="allowlist", allow_from=["12345"])

        with patch("src.core.discord.server.gate", return_value={"action": "deliver", "access": access}):
            await handle_inbound(mock_client, mock_server, mock_message)

        # typing deve ter sido chamado
        mock_message.channel.typing.assert_called_once()

    @pytest.mark.asyncio
    async def test_ack_reaction_enviado(self, mock_client, mock_server, mock_message):
        """
        RED → GREEN: ack reaction é enviado quando configurado.

        Spec: 8.6 Implementar ack reaction
        """
        from src.core.discord.server import handle_inbound
        from src.core.discord.access import Access

        access = Access(dm_policy="allowlist", allow_from=["12345"], ack_reaction="✅")

        with patch("src.core.discord.server.gate", return_value={"action": "deliver", "access": access}):
            await handle_inbound(mock_client, mock_server, mock_message)

        # add_reaction deve ter sido chamado com ack_reaction
        mock_message.add_reaction.assert_called()
        # Primeira chamada é ack_reaction
        first_call = mock_message.add_reaction.call_args_list[0]
        assert first_call[0][0] == "✅"

    @pytest.mark.asyncio
    async def test_anexos_incluidos_na_notificacao(self, mock_client, mock_server, mock_message):
        """
        RED → GREEN: anexos são incluídos na notificação.

        Spec: Tool download_attachment - mensagens com attachment_count
        """
        from src.core.discord.server import handle_inbound
        from src.core.discord.access import Access

        access = Access(dm_policy="allowlist", allow_from=["12345"])

        # Adiciona anexo
        att = Mock()
        att.filename = "file.png"
        att.content_type = "image/png"
        att.size = 2048
        mock_message.attachments = [att]

        with patch("src.core.discord.server.gate", return_value={"action": "deliver", "access": access}):
            await handle_inbound(mock_client, mock_server, mock_message)

        notification = mock_server.notify.call_args[0][1]
        assert notification["meta"]["attachment_count"] == "1"
        assert "file.png" in notification["meta"]["attachments"]


class TestPermissionReply:
    """Testes para interceptação de permission replies."""

    @pytest.fixture
    def mock_client(self):
        return Mock()

    @pytest.fixture
    def mock_server(self):
        server = Mock()
        server.notify = AsyncMock()
        return server

    @pytest.fixture
    def mock_message(self):
        msg = Mock()
        msg.author = Mock()
        msg.author.id = 12345
        msg.author.name = "TestUser"
        msg.author.bot = False
        msg.channel = Mock()
        msg.channel.id = 999888
        msg.channel.typing = AsyncMock()
        msg.id = 111222333
        msg.content = "yes abcde"
        msg.created_at = Mock()
        msg.created_at.isoformat = Mock(return_value="2024-01-01T12:00:00")
        msg.attachments = []
        msg.add_reaction = AsyncMock()
        return msg

    @pytest.mark.asyncio
    async def test_permission_reply_yes_envia_notificacao(self, mock_client, mock_server, mock_message):
        """
        RED → GREEN: "yes xxxxx" envia notificação de permissão allow.
        """
        from src.core.discord.server import handle_inbound
        from src.core.discord.access import Access

        access = Access(dm_policy="allowlist", allow_from=["12345"])

        with patch("src.core.discord.server.gate", return_value={"action": "deliver", "access": access}):
            await handle_inbound(mock_client, mock_server, mock_message)

        # Deve ter enviado notificação de permissão
        calls = mock_server.notify.call_args_list
        permission_call = [c for c in calls if c[0][0] == "notifications/claude/channel/permission"]
        assert len(permission_call) == 1

        notification = permission_call[0][0][1]
        assert notification["request_id"] == "abcde"
        assert notification["behavior"] == "allow"

    @pytest.mark.asyncio
    async def test_permission_reply_no_envia_notificacao(self, mock_client, mock_server, mock_message):
        """
        RED → GREEN: "no xxxxx" envia notificação de permissão deny.
        """
        from src.core.discord.server import handle_inbound
        from src.core.discord.access import Access

        access = Access(dm_policy="allowlist", allow_from=["12345"])
        mock_message.content = "no abcde"

        with patch("src.core.discord.server.gate", return_value={"action": "deliver", "access": access}):
            await handle_inbound(mock_client, mock_server, mock_message)

        calls = mock_server.notify.call_args_list
        permission_call = [c for c in calls if c[0][0] == "notifications/claude/channel/permission"]
        assert len(permission_call) == 1

        notification = permission_call[0][0][1]
        assert notification["request_id"] == "abcde"
        assert notification["behavior"] == "deny"
