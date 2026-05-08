"""
Testes para glitchtip_client.py — Spec: glitchtip-client

Cenários:
- Disponibilidade do server
- Auto-start Docker (sucesso, falha, ausência)
- Parse SSE vs JSON
- Headers com/sem token
- REGRESSION: handshake initialize antes do loop stdio
- Config via ENV (defaults)
"""

import json
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from core.observability.glitchtip_client import (
    _check_server,
    _maybe_start_docker,
    _parse_sse,
    _send_message,
)


class TestServerAvailability:
    """Spec: glitchtip-client — Verificação de disponibilidade."""

    @pytest.mark.asyncio
    async def test_server_disponivel_retorna_true(self):
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_instance = AsyncMock()
        mock_instance.get.return_value = mock_response
        mock_instance.__aenter__ = AsyncMock(return_value=mock_instance)
        mock_instance.__aexit__ = AsyncMock(return_value=None)

        with patch("core.observability.glitchtip_client.httpx.AsyncClient", return_value=mock_instance):
            result = await _check_server()
            assert result is True

    @pytest.mark.asyncio
    async def test_server_indisponivel_retorna_false(self):
        import httpx as real_httpx
        mock_instance = AsyncMock()
        mock_instance.get.side_effect = real_httpx.ConnectError("refused")
        mock_instance.__aenter__ = AsyncMock(return_value=mock_instance)
        mock_instance.__aexit__ = AsyncMock(return_value=None)

        with patch("core.observability.glitchtip_client.httpx.AsyncClient", return_value=mock_instance):
            result = await _check_server()
            assert result is False

    @pytest.mark.asyncio
    async def test_server_500_retorna_false(self):
        mock_response = MagicMock()
        mock_response.status_code = 503
        mock_instance = AsyncMock()
        mock_instance.get.return_value = mock_response
        mock_instance.__aenter__ = AsyncMock(return_value=mock_instance)
        mock_instance.__aexit__ = AsyncMock(return_value=None)

        with patch("core.observability.glitchtip_client.httpx.AsyncClient", return_value=mock_instance):
            result = await _check_server()
            assert result is False


class TestAutoStartDocker:
    """Spec: glitchtip-client — Auto-start Docker quando server indisponível."""

    @pytest.mark.asyncio
    async def test_server_ja_rodando_nao_inicia_docker(self):
        with patch("core.observability.glitchtip_client._check_server", return_value=True):
            with patch("core.observability.glitchtip_client.shutil.which") as mock_which:
                await _maybe_start_docker()
                mock_which.assert_not_called()

    @pytest.mark.asyncio
    async def test_sem_compose_dir_nao_tenta_docker(self):
        with patch("core.observability.glitchtip_client._check_server", return_value=False):
            with patch.dict("os.environ", {"GLITCHTIP_COMPOSE_DIR": ""}):
                with patch("core.observability.glitchtip_client.shutil.which") as mock_which:
                    await _maybe_start_docker()
                    mock_which.assert_not_called()

    @pytest.mark.asyncio
    async def test_docker_nao_instalado_nao_falha(self):
        with patch("core.observability.glitchtip_client._check_server", return_value=False):
            with patch.dict("os.environ", {"GLITCHTIP_COMPOSE_DIR": "/some/path"}):
                with patch("core.observability.glitchtip_client.shutil.which", return_value=None):
                    await _maybe_start_docker()

    @pytest.mark.asyncio
    async def test_compose_dir_inexistente_nao_falha(self):
        with patch("core.observability.glitchtip_client._check_server", return_value=False):
            with patch.dict("os.environ", {"GLITCHTIP_COMPOSE_DIR": "/nonexistent/path"}):
                with patch("core.observability.glitchtip_client.shutil.which", return_value="/usr/bin/docker"):
                    with patch("core.observability.glitchtip_client.Path") as mock_path:
                        mock_path.return_value.exists.return_value = False
                        await _maybe_start_docker()

    @pytest.mark.asyncio
    async def test_compose_falha_nao_falha(self):
        with patch("core.observability.glitchtip_client._check_server", return_value=False):
            with patch.dict("os.environ", {"GLITCHTIP_COMPOSE_DIR": "/some/path"}):
                with patch("core.observability.glitchtip_client.shutil.which", return_value="/usr/bin/docker"):
                    with patch("core.observability.glitchtip_client.Path") as mock_path:
                        mock_path.return_value.exists.return_value = True
                        with patch("asyncio.create_subprocess_exec") as mock_proc:
                            mock_process = AsyncMock()
                            mock_process.communicate.return_value = (b"", b"error")
                            mock_process.returncode = 1
                            mock_proc.return_value = mock_process
                            await _maybe_start_docker()


class TestParseSSE:
    """Spec: glitchtip-client — Parse SSE vs JSON."""

    def test_parse_sse_extrai_json_do_data(self):
        sse_text = 'event: message\ndata: {"jsonrpc":"2.0","id":1,"result":{}}'
        result = _parse_sse(sse_text)
        assert result["jsonrpc"] == "2.0"
        assert result["id"] == 1

    def test_parse_sse_multiplos_campos(self):
        sse_text = 'event: message\nid: 42\ndata: {"status":"ok"}'
        result = _parse_sse(sse_text)
        assert result["status"] == "ok"

    def test_parse_sse_sem_data_levanta_erro(self):
        with pytest.raises(ValueError, match="No data in SSE"):
            _parse_sse("event: message\nid: 42")


class TestSendMessage:
    """Spec: glitchtip-client — Envio de mensagens HTTP/SSE."""

    @pytest.mark.asyncio
    async def test_resposta_json_direta(self):
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.headers = {"content-type": "application/json"}
        mock_response.json.return_value = {"jsonrpc": "2.0", "id": 1, "result": {}}
        mock_response.raise_for_status = MagicMock()

        mock_instance = AsyncMock()
        mock_instance.post.return_value = mock_response
        mock_instance.__aenter__ = AsyncMock(return_value=mock_instance)
        mock_instance.__aexit__ = AsyncMock(return_value=None)

        with patch("core.observability.glitchtip_client.httpx.AsyncClient", return_value=mock_instance):
            result = await _send_message("http://localhost:8000/mcp", {"test": True}, {})
            assert result["jsonrpc"] == "2.0"

    @pytest.mark.asyncio
    async def test_resposta_sse(self):
        sse_body = 'event: message\ndata: {"jsonrpc":"2.0","id":1,"result":{"tools":[]}}'
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.headers = {"content-type": "text/event-stream"}
        mock_response.text = sse_body
        mock_response.raise_for_status = MagicMock()

        mock_instance = AsyncMock()
        mock_instance.post.return_value = mock_response
        mock_instance.__aenter__ = AsyncMock(return_value=mock_instance)
        mock_instance.__aexit__ = AsyncMock(return_value=None)

        with patch("core.observability.glitchtip_client.httpx.AsyncClient", return_value=mock_instance):
            result = await _send_message("http://localhost:8000/mcp", {"test": True}, {})
            assert result["result"]["tools"] == []


class TestInitializeHandshake:
    """
    REGRESSION: Client DEVE fazer handshake initialize antes do loop stdio.

    Em 2026-05-01, uma refatoração removeu o initialize() do client,
    transformando-o em "pure bridge". O Claude Code falhou ao reconectar
    porque o server MCP não estava inicializado quando o primeiro comando
    chegava. O client original sempre fazia initialize() primeiro.

    Este teste garante que main() sempre envia initialize antes do loop.
    """

    @pytest.mark.asyncio
    async def test_main_envia_initialize_antes_do_loop(self):
        """main() deve enviar método 'initialize' ao server antes de ler stdin."""
        import io
        from core.observability.glitchtip_client import main

        init_response = {
            "jsonrpc": "2.0",
            "id": 1,
            "result": {
                "protocolVersion": "2024-11-05",
                "capabilities": {},
                "serverInfo": {"name": "glitchtip", "version": "1.0.0"}
            }
        }
        tool_response = {
            "jsonrpc": "2.0",
            "id": 2,
            "result": {"tools": []}
        }

        sent_messages = []

        async def fake_send_message(url, message, headers):
            sent_messages.append(message)
            if message.get("method") == "initialize":
                return init_response
            return tool_response

        # stdin com tools/list + EOF
        fake_stdin = io.StringIO('{"jsonrpc":"2.0","id":2,"method":"tools/list","params":{}}\n')

        with patch("core.observability.glitchtip_client._maybe_start_docker", new_callable=AsyncMock):
            with patch("core.observability.glitchtip_client._send_message", side_effect=fake_send_message):
                with patch("core.observability.glitchtip_client.sys.stdin", fake_stdin):
                    await main()

        # REGRESSION CHECK: primeira mensagem DEVE ser initialize
        assert len(sent_messages) >= 1, "main() deve enviar pelo menos initialize"
        first = sent_messages[0]
        assert first.get("method") == "initialize", (
            f"Primeira mensagem deve ser 'initialize', mas foi '{first.get('method')}'. "
            "Sem handshake, o Claude Code não consegue reconectar o MCP."
        )
        assert first["params"]["protocolVersion"] == "2024-11-05"
        assert first["params"]["clientInfo"]["name"] == "claude-desktop"

    @pytest.mark.asyncio
    async def test_main_falha_se_initialize_falha(self):
        """Se initialize falha, main() deve chamar sys.exit(1)."""
        from core.observability.glitchtip_client import main

        with patch("core.observability.glitchtip_client._maybe_start_docker", new_callable=AsyncMock):
            with patch("core.observability.glitchtip_client._send_message", side_effect=ConnectionError("refused")):
                with pytest.raises(SystemExit) as exc_info:
                    await main()
                assert exc_info.value.code == 1


class TestConfigDefaults:
    """Spec: glitchtip-client — Configuração via variáveis de ambiente."""

    def test_headers_obrigatorios(self):
        """Headers devem conter Content-Type, Accept e User-Agent."""
        import os
        token = os.getenv("GLITCHTIP_API_TOKEN", "")
        headers = {
            "Content-Type": "application/json",
            "Accept": "application/json, text/event-stream",
            "User-Agent": "Claude-Desktop-MCP-Client",
        }
        if token:
            headers["Authorization"] = f"Bearer {token}"

        assert "Content-Type" in headers
        assert "User-Agent" in headers
        assert headers["User-Agent"] == "Claude-Desktop-MCP-Client"

    def test_url_default(self):
        import os
        url = os.getenv("GLITCHTIP_MCP_URL", "http://localhost:8000/mcp")
        assert "localhost" in url
        assert "/mcp" in url
