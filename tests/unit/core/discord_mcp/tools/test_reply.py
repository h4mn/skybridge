"""
Testes unitários para tools/reply.py - TDD Estrito.
"""

import pytest
from unittest.mock import AsyncMock, Mock, patch
from pathlib import Path


class TestReplyInput:
    """Testes para validação de entrada do reply."""

    def test_chat_id_obrigatorio(self):
        """RED → GREEN: chat_id é obrigatório."""
        from src.core.discord.models import ReplyInput

        with pytest.raises(Exception):  # ValidationError
            ReplyInput(text="hello")

    def test_text_obrigatorio(self):
        """RED → GREEN: text é obrigatório."""
        from src.core.discord.models import ReplyInput

        with pytest.raises(Exception):
            ReplyInput(chat_id="123")

    def test_campos_opcionais(self):
        """RED → GREEN: reply_to e files são opcionais."""
        from src.core.discord.models import ReplyInput

        inp = ReplyInput(chat_id="123", text="hello")
        assert inp.reply_to is None
        assert inp.files is None


class TestHandleReply:
    """Testes para handle_reply()."""

    @pytest.fixture
    def mock_client(self):
        """Cliente Discord mockado."""
        client = Mock()
        client.get_channel = AsyncMock()
        return client

    @pytest.fixture
    def mock_channel(self):
        """Canal Discord mockado."""
        channel = Mock()
        channel.send = AsyncMock()
        # Simula mensagem enviada
        sent_msg = Mock()
        sent_msg.id = 999888777
        channel.send.return_value = sent_msg
        return channel

    @pytest.mark.asyncio
    async def test_envia_mensagem_simples(
        self, mock_client, mock_channel, access_file
    ):
        """RED → GREEN: handle_reply envia mensagem simples."""
        from src.core.discord.tools import reply as reply_module
        from src.core.discord.tools.reply import handle_reply

        with patch.object(
            reply_module, "fetch_allowed_channel", return_value=mock_channel
        ):
            result = await handle_reply(
                mock_client, {"chat_id": "123", "text": "Hello world"}
            )

        assert result.message_id == "999888777"
        assert result.sent_count == 1
        mock_channel.send.assert_called_once()

    @pytest.mark.asyncio
    async def test_divide_texto_longo_em_chunks(
        self, mock_client, mock_channel, access_file
    ):
        """RED → GREEN: handle_reply divide texto > 2000 chars."""
        from src.core.discord.tools import reply as reply_module
        from src.core.discord.tools.reply import handle_reply

        # Texto de 3000 chars
        long_text = "a" * 3000

        with patch.object(
            reply_module, "fetch_allowed_channel", return_value=mock_channel
        ):
            result = await handle_reply(
                mock_client, {"chat_id": "123", "text": long_text}
            )

        # Deve enviar 2 chunks
        assert result.sent_count == 2
        assert mock_channel.send.call_count == 2

    @pytest.mark.asyncio
    async def test_reply_to_adiciona_reference(
        self, mock_client, mock_channel, access_file
    ):
        """RED → GREEN: reply_to adiciona reference ao primeiro chunk."""
        from src.core.discord.tools import reply as reply_module
        from src.core.discord.tools.reply import handle_reply

        with patch.object(
            reply_module, "fetch_allowed_channel", return_value=mock_channel
        ):
            await handle_reply(
                mock_client,
                {
                    "chat_id": "123",
                    "text": "Replying",
                    "reply_to": "111222333",
                },
            )

        # Verifica que reference foi passado
        call_kwargs = mock_channel.send.call_args[1]
        assert "reference" in call_kwargs
        assert call_kwargs["reference"]["message_id"] == 111222333

    @pytest.mark.asyncio
    async def test_arquivo_grande_gera_erro(
        self, mock_client, mock_channel, access_file, temp_state_dir
    ):
        """RED → GREEN: arquivo > 25MB gera ValueError."""
        from src.core.discord.tools import reply as reply_module
        from src.core.discord.tools.reply import handle_reply

        # Cria arquivo grande fake
        inbox = temp_state_dir / "inbox"
        inbox.mkdir(exist_ok=True)
        big_file = inbox / "big.txt"
        big_file.write_bytes(b"x" * (26 * 1024 * 1024))  # 26MB

        with patch.object(
            reply_module, "fetch_allowed_channel", return_value=mock_channel
        ):
            with pytest.raises(ValueError, match="(?i)grande"):
                await handle_reply(
                    mock_client,
                    {
                        "chat_id": "123",
                        "text": "test",
                        "files": [str(big_file)],
                    },
                )

    @pytest.mark.asyncio
    async def test_arquivo_inexistente_gera_erro(
        self, mock_client, mock_channel, access_file
    ):
        """RED → GREEN: arquivo inexistente gera ValueError."""
        from src.core.discord.tools import reply as reply_module
        from src.core.discord.tools.reply import handle_reply

        with patch.object(
            reply_module, "fetch_allowed_channel", return_value=mock_channel
        ):
            with pytest.raises(ValueError, match="(?i)não encontrado"):
                await handle_reply(
                    mock_client,
                    {
                        "chat_id": "123",
                        "text": "test",
                        "files": ["/nonexistent/file.txt"],
                    },
                )

    @pytest.mark.asyncio
    async def test_mais_de_10_anexos_gera_erro(
        self, mock_client, mock_channel, access_file, temp_state_dir
    ):
        """RED → GREEN: mais de 10 anexos gera ValueError."""
        from src.core.discord.tools import reply as reply_module
        from src.core.discord.tools.reply import handle_reply

        inbox = temp_state_dir / "inbox"
        inbox.mkdir(exist_ok=True)

        # Cria 11 arquivos pequenos
        files = []
        for i in range(11):
            f = inbox / f"file{i}.txt"
            f.write_text("test")
            files.append(str(f))

        with patch.object(
            reply_module, "fetch_allowed_channel", return_value=mock_channel
        ):
            with pytest.raises(ValueError, match="(?i)máximo 10"):
                await handle_reply(
                    mock_client,
                    {"chat_id": "123", "text": "test", "files": files},
                )
