"""
Testes unitários para tools/download_attachment.py - TDD Estrito.

DOC: src/core/discord/tools/download_attachment.py
Spec: discord-mcp-server - Tool download_attachment baixa anexos
"""

import pytest
from unittest.mock import AsyncMock, Mock, patch
from pathlib import Path


class TestDownloadAttachmentInput:
    """Testes para validação de entrada do download_attachment."""

    def test_chat_id_obrigatorio(self):
        """RED → GREEN: chat_id é obrigatório."""
        from src.core.discord.models import DownloadAttachmentInput

        with pytest.raises(Exception):  # ValidationError
            DownloadAttachmentInput(message_id="123")

    def test_message_id_obrigatorio(self):
        """RED → GREEN: message_id é obrigatório."""
        from src.core.discord.models import DownloadAttachmentInput

        with pytest.raises(Exception):  # ValidationError
            DownloadAttachmentInput(chat_id="123")

    def test_campos_validos(self):
        """RED → GREEN: campos válidos são aceitos."""
        from src.core.discord.models import DownloadAttachmentInput

        inp = DownloadAttachmentInput(chat_id="123456", message_id="789012")
        assert inp.chat_id == "123456"
        assert inp.message_id == "789012"


class TestDownloadedFile:
    """Testes para modelo DownloadedFile."""

    def test_criacao_completa(self):
        """RED → GREEN: criação com todos os campos."""
        from src.core.discord.models import DownloadedFile

        f = DownloadedFile(
            path="/tmp/inbox/file.png",
            name="file.png",
            content_type="image/png",
            size_kb=100,
        )
        assert f.path == "/tmp/inbox/file.png"
        assert f.name == "file.png"
        assert f.content_type == "image/png"
        assert f.size_kb == 100

    def test_content_type_opcional(self):
        """RED → GREEN: content_type pode ser None."""
        from src.core.discord.models import DownloadedFile

        f = DownloadedFile(
            path="/tmp/inbox/file.bin",
            name="file.bin",
            content_type=None,
            size_kb=50,
        )
        assert f.content_type is None


class TestDownloadAttachmentOutput:
    """Testes para modelo DownloadAttachmentOutput."""

    def test_lista_vazia(self):
        """RED → GREEN: output com lista vazia."""
        from src.core.discord.models import DownloadAttachmentOutput

        out = DownloadAttachmentOutput(files=[], count=0)
        assert out.files == []
        assert out.count == 0

    def test_lista_com_arquivos(self):
        """RED → GREEN: output com arquivos baixados."""
        from src.core.discord.models import DownloadAttachmentOutput, DownloadedFile

        files = [
            DownloadedFile(path="/a.png", name="a.png", content_type="image/png", size_kb=10),
            DownloadedFile(path="/b.pdf", name="b.pdf", content_type="application/pdf", size_kb=20),
        ]
        out = DownloadAttachmentOutput(files=files, count=2)
        assert out.count == 2
        assert len(out.files) == 2


class TestHandleDownloadAttachment:
    """Testes para handle_download_attachment()."""

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
        channel.id = 123456789
        channel.fetch_message = AsyncMock()
        return channel

    @pytest.fixture
    def mock_attachment(self, temp_state_dir):
        """Anexo mockado."""
        att = Mock()
        att.id = 999
        att.filename = "test_file.png"
        att.content_type = "image/png"
        att.size = 1024  # 1KB
        att.url = "https://example.com/file.png"
        return att

    @pytest.mark.asyncio
    async def test_canal_nao_autorizado_erro(self, mock_client):
        """
        RED → GREEN: canal não autorizado retorna erro.

        Scenario: Canal não autorizado
        WHEN download_attachment é chamado para canal não em groups
        THEN erro "channel not allowlisted" é retornado
        """
        from src.core.discord.tools.download_attachment import handle_download_attachment

        with patch(
            "src.core.discord.client.fetch_allowed_channel",
            side_effect=ValueError("channel not allowlisted"),
        ):
            with pytest.raises(ValueError, match="channel not allowlisted"):
                await handle_download_attachment(
                    mock_client,
                    {"chat_id": "999", "message_id": "123"},
                )

    @pytest.mark.asyncio
    async def test_mensagem_sem_anexos_retorna_vazio(self, mock_client, mock_channel):
        """
        RED → GREEN: mensagem sem anexos retorna lista vazia.

        Scenario: Download de anexo único
        WHEN download_attachment é chamado em mensagem SEM anexo
        THEN retorna files=[], count=0
        """
        from src.core.discord.tools.download_attachment import handle_download_attachment

        # Mensagem sem anexos
        mock_msg = Mock()
        mock_msg.id = 111
        mock_msg.attachments = []
        mock_channel.fetch_message.return_value = mock_msg

        with patch(
            "src.core.discord.client.fetch_allowed_channel",
            return_value=mock_channel,
        ):
            result = await handle_download_attachment(
                mock_client,
                {"chat_id": "123", "message_id": "111"},
            )

        assert result.count == 0
        assert result.files == []

    @pytest.mark.asyncio
    async def test_baixa_anexo_com_sucesso(self, mock_client, mock_channel, mock_attachment, temp_state_dir):
        """
        RED → GREEN: download de anexo único retorna path.

        Scenario: Download de anexo único
        WHEN download_attachment(chat_id, message_id) é chamado em mensagem com anexo
        THEN anexo é baixado para inbox e caminho é retornado
        """
        from src.core.discord.tools.download_attachment import handle_download_attachment

        mock_msg = Mock()
        mock_msg.id = 111
        mock_msg.attachments = [mock_attachment]
        mock_channel.fetch_message.return_value = mock_msg

        # Mock do download_attachment utility
        async def fake_download(att):
            inbox = temp_state_dir / "inbox"
            inbox.mkdir(parents=True, exist_ok=True)
            path = inbox / f"{att.id}.png"
            path.write_bytes(b"fake_content")
            return str(path)

        with patch(
            "src.core.discord.client.fetch_allowed_channel",
            return_value=mock_channel,
        ):
            with patch(
                "src.core.discord.tools.download_attachment.download_attachment",
                side_effect=fake_download,
            ):
                result = await handle_download_attachment(
                    mock_client,
                    {"chat_id": "123", "message_id": "111"},
                )

        assert result.count == 1
        assert len(result.files) == 1
        assert result.files[0].name == "test_file.png"
        assert result.files[0].content_type == "image/png"
        assert result.files[0].size_kb == 1  # 1024 bytes / 1024 = 1KB

    @pytest.mark.asyncio
    async def test_anexo_muito_grande_ignorado(self, mock_client, mock_channel, temp_state_dir):
        """
        RED → GREEN: anexo > 25MB é ignorado com warning.

        Scenario: Anexo muito grande
        WHEN anexo excede 25MB
        THEN é ignorado (não baixado)
        """
        from src.core.discord.tools.download_attachment import handle_download_attachment
        from src.core.discord.utils import MAX_ATTACHMENT_BYTES

        # Anexo grande (26MB)
        big_att = Mock()
        big_att.id = 888
        big_att.filename = "big_file.zip"
        big_att.content_type = "application/zip"
        big_att.size = MAX_ATTACHMENT_BYTES + (1024 * 1024)  # 26MB
        big_att.url = "https://example.com/big.zip"

        mock_msg = Mock()
        mock_msg.id = 111
        mock_msg.attachments = [big_att]
        mock_channel.fetch_message.return_value = mock_msg

        with patch(
            "src.core.discord.client.fetch_allowed_channel",
            return_value=mock_channel,
        ):
            result = await handle_download_attachment(
                mock_client,
                {"chat_id": "123", "message_id": "111"},
            )

        # Anexo grande é ignorado, retorna lista vazia
        assert result.count == 0
        assert result.files == []

    @pytest.mark.asyncio
    async def test_multiplos_anexos(self, mock_client, mock_channel, temp_state_dir):
        """
        RED → GREEN: múltiplos anexos são todos baixados.
        """
        from src.core.discord.tools.download_attachment import handle_download_attachment

        # Dois anexos
        att1 = Mock()
        att1.id = 101
        att1.filename = "file1.png"
        att1.content_type = "image/png"
        att1.size = 2048

        att2 = Mock()
        att2.id = 102
        att2.filename = "file2.pdf"
        att2.content_type = "application/pdf"
        att2.size = 4096

        mock_msg = Mock()
        mock_msg.id = 111
        mock_msg.attachments = [att1, att2]
        mock_channel.fetch_message.return_value = mock_msg

        async def fake_download(att):
            inbox = temp_state_dir / "inbox"
            inbox.mkdir(parents=True, exist_ok=True)
            ext = "png" if "png" in att.filename else "pdf"
            path = inbox / f"{att.id}.{ext}"
            path.write_bytes(b"fake_content")
            return str(path)

        with patch(
            "src.core.discord.client.fetch_allowed_channel",
            return_value=mock_channel,
        ):
            with patch(
                "src.core.discord.tools.download_attachment.download_attachment",
                side_effect=fake_download,
            ):
                result = await handle_download_attachment(
                    mock_client,
                    {"chat_id": "123", "message_id": "111"},
                )

        assert result.count == 2
        assert len(result.files) == 2
        names = [f.name for f in result.files]
        assert "file1.png" in names
        assert "file2.pdf" in names

    @pytest.mark.asyncio
    async def test_mensagem_nao_encontrada_erro(self, mock_client, mock_channel):
        """
        RED → GREEN: mensagem inexistente retorna erro.

        Scenario: Mensagem não encontrada
        WHEN download_attachment é chamado com message_id inexistente
        THEN erro "não encontrada" é retornado
        """
        from src.core.discord.tools.download_attachment import handle_download_attachment

        mock_channel.fetch_message.return_value = None

        with patch(
            "src.core.discord.client.fetch_allowed_channel",
            return_value=mock_channel,
        ):
            with pytest.raises(ValueError, match="não encontrada"):
                await handle_download_attachment(
                    mock_client,
                    {"chat_id": "123", "message_id": "999"},
                )
