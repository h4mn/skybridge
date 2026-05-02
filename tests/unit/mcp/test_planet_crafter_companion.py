"""Testes TDD para o Channel MCP do Planet Crafter.

Specs:
- channel-mcp-companion: polling, throttling, capability, reconnect
- companion-tools: send_companion_message, move_companion_to, set_companion_animation, get_game_state
- companion-session: criação, eventos, notas, encerramento, resumo
"""
from __future__ import annotations

import json
import time
from unittest.mock import AsyncMock, MagicMock, patch

import pytest


# ============================================================================
# 7.1 — Criação do MCP Server
# ============================================================================

class TestMcpServerCreation:
    """Task 7.1: Criar planet-crafter-channel.py com MCP Server via stdio."""

    def test_server_importable(self):
        """RED: módulo planet_crafter_channel deve ser importável."""
        from apps.mcp_servers.planet_crafter_companion import create_server

        server = create_server()
        assert server is not None
        assert server.name == "planet-crafter-channel"

    def test_server_has_list_tools_handler(self):
        """RED: server deve registrar handler de list_tools."""
        from apps.mcp_servers.planet_crafter_companion import create_server

        server = create_server()
        assert hasattr(server, "list_tools")
        assert server.list_tools is not None

    def test_server_has_call_tool_handler(self):
        """RED: server deve ter método para registrar call_tool."""
        from apps.mcp_servers.planet_crafter_companion import create_server

        server = create_server()
        assert hasattr(server, "call_tool")
        assert callable(server.call_tool)


# ============================================================================
# 7.2 — Capability claude/channel
# ============================================================================

class TestCapabilityDeclaration:
    """Task 7.2: Declarar capability experimental claude/channel."""

    def test_initialization_options_includes_channel_capability(self):
        """RED: init options deve incluir claude/channel capability."""
        from apps.mcp_servers.planet_crafter_companion import create_initialization_options

        opts = create_initialization_options()
        assert hasattr(opts, "capabilities")
        experimental = opts.capabilities.experimental
        assert "claude/channel" in experimental


# ============================================================================
# 7.3 — Polling GET /events com JSONRPCNotification
# ============================================================================

class TestEventPolling:
    """Task 7.3: Polling de GET /events a cada 10s."""

    @pytest.mark.asyncio
    async def test_poll_events_sends_notification_when_events_exist(self):
        """RED: quando GET /events retorna eventos, envia JSONRPCNotification."""
        from apps.mcp_servers.planet_crafter_companion import EventPoller

        mock_write = AsyncMock()

        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = [
            {"type": "milestone", "description": "Primeira chuva!", "timestamp": "2026-01-01T00:00:00"}
        ]
        mock_resp.raise_for_status = MagicMock()

        mock_http = AsyncMock()
        mock_http.get.return_value = mock_resp

        poller = EventPoller(
            base_url="http://localhost:17234",
            write_stream=mock_write,
            http_client=mock_http,
        )

        await poller.poll_once()

        mock_write.send.assert_called_once()
        call_args = mock_write.send.call_args[0][0]
        assert call_args.root.method == "notifications/claude/channel"
        params = call_args.root.params
        assert "Primeira chuva" in params.get("content", "")

    @pytest.mark.asyncio
    async def test_poll_events_no_notification_when_empty(self):
        """RED: quando GET /events retorna vazio, não envia notificação."""
        from apps.mcp_servers.planet_crafter_companion import EventPoller

        mock_write = AsyncMock()

        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = []
        mock_resp.raise_for_status = MagicMock()

        mock_http = AsyncMock()
        mock_http.get.return_value = mock_resp

        poller = EventPoller(
            base_url="http://localhost:17234",
            write_stream=mock_write,
            http_client=mock_http,
        )

        await poller.poll_once()

        mock_write.send.assert_not_called()


# ============================================================================
# 7.4 — Throttling de 30s
# ============================================================================

class TestThrottling:
    """Task 7.4: Throttling mínimo de 30s entre notificações."""

    @pytest.mark.asyncio
    async def test_events_grouped_within_throttle_window(self):
        """RED: dois eventos rápidos são agrupados em uma notificação."""
        from apps.mcp_servers.planet_crafter_companion import EventPoller

        mock_write = AsyncMock()

        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = [{"type": "milestone", "description": "Evento 1"}]
        mock_resp.raise_for_status = MagicMock()

        mock_http = AsyncMock()
        mock_http.get.return_value = mock_resp

        poller = EventPoller(
            base_url="http://localhost:17234",
            write_stream=mock_write,
            http_client=mock_http,
            throttle_seconds=30,
        )
        poller._last_notification_time = time.monotonic() - 5  # 5s atrás

        await poller.poll_once()

        mock_write.send.assert_not_called()  # Throttled

    @pytest.mark.asyncio
    async def test_events_sent_after_throttle_window(self):
        """RED: evento enviado após janela de throttle."""
        from apps.mcp_servers.planet_crafter_companion import EventPoller

        mock_write = AsyncMock()

        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = [{"type": "milestone", "description": "Evento novo"}]
        mock_resp.raise_for_status = MagicMock()

        mock_http = AsyncMock()
        mock_http.get.return_value = mock_resp

        poller = EventPoller(
            base_url="http://localhost:17234",
            write_stream=mock_write,
            http_client=mock_http,
            throttle_seconds=30,
        )
        poller._last_notification_time = time.monotonic() - 35  # 35s atrás

        await poller.poll_once()

        mock_write.send.assert_called_once()  # Deve enviar


# ============================================================================
# 7.5 — Reconexão automática
# ============================================================================

class TestAutoReconnect:
    """Task 7.5: Reconexão automática ao mod."""

    @pytest.mark.asyncio
    async def test_poll_continues_on_connection_error(self):
        """RED: polling não crasha quando mod está indisponível."""
        from apps.mcp_servers.planet_crafter_companion import EventPoller

        mock_write = AsyncMock()
        mock_http = AsyncMock()
        mock_http.get.side_effect = ConnectionRefusedError("Connection refused")

        poller = EventPoller(
            base_url="http://localhost:17234",
            write_stream=mock_write,
            http_client=mock_http,
        )

        # Não deve levantar exceção
        await poller.poll_once()

        mock_write.send.assert_not_called()

    @pytest.mark.asyncio
    async def test_poll_resumes_when_mod_returns(self):
        """RED: polling retoma quando mod volta a responder."""
        from apps.mcp_servers.planet_crafter_companion import EventPoller

        mock_write = AsyncMock()
        mock_http = AsyncMock()

        poller = EventPoller(
            base_url="http://localhost:17234",
            write_stream=mock_write,
            http_client=mock_http,
        )

        # Primeira chamada: falha
        mock_http.get.side_effect = ConnectionRefusedError()
        await poller.poll_once()

        # Segunda chamada: sucesso
        mock_http.get.side_effect = None
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = [{"type": "milestone", "description": "Retornou!"}]
        mock_resp.raise_for_status = MagicMock()
        mock_http.get.return_value = mock_resp
        await poller.poll_once()

        mock_write.send.assert_called_once()

    @pytest.mark.asyncio
    async def test_poll_success_starts_session(self):
        """RED: polling bem-sucedido inicia sessão via session_manager."""
        from apps.mcp_servers.planet_crafter_companion import EventPoller, CompanionSessionManager

        mock_write = AsyncMock()
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = [{"type": "milestone", "description": "Test"}]
        mock_resp.raise_for_status = MagicMock()

        mock_http = AsyncMock()
        mock_http.get.return_value = mock_resp

        session_mgr = CompanionSessionManager()
        assert not session_mgr.is_active

        poller = EventPoller(
            base_url="http://localhost:17234",
            write_stream=mock_write,
            http_client=mock_http,
            session_manager=session_mgr,
        )
        await poller.poll_once()

        assert session_mgr.is_active

    @pytest.mark.asyncio
    async def test_poll_failure_tracks_consecutive_failures(self):
        """RED: polling falho notifica session_manager.on_poll_failure."""
        from apps.mcp_servers.planet_crafter_companion import EventPoller, CompanionSessionManager

        mock_write = AsyncMock()
        mock_http = AsyncMock()
        mock_http.get.side_effect = ConnectionRefusedError()

        session_mgr = CompanionSessionManager(timeout_failures=2)
        session_mgr.on_poll_success()
        assert session_mgr.is_active

        poller = EventPoller(
            base_url="http://localhost:17234",
            write_stream=mock_write,
            http_client=mock_http,
            session_manager=session_mgr,
        )
        await poller.poll_once()
        await poller.poll_once()

        assert not session_mgr.is_active  # Encerrou após 2 falhas consecutivas


# ============================================================================
# 7.6-7.9 — MCP Tools
# ============================================================================

class TestCompanionTools:
    """Tasks 7.6-7.9: Ferramentas MCP."""

    @pytest.mark.asyncio
    async def test_send_companion_message_posts_action(self):
        """RED: send_companion_message envia POST /action com show_message."""
        from apps.mcp_servers.planet_crafter_companion import handle_tool_call

        mock_http = AsyncMock()
        mock_http.post.return_value.status_code = 200

        result = await handle_tool_call(
            "send_companion_message",
            {"text": "Olá! Vi que atingiu o primeiro milestone!"},
            http_client=mock_http,
            base_url="http://localhost:17234",
        )

        mock_http.post.assert_called_once()
        call_url = mock_http.post.call_args[0][0]
        call_body = mock_http.post.call_args[1].get("json", {})
        assert "/action" in call_url
        assert call_body["type"] == "show_message"
        assert "milestone" in call_body["text"]

    @pytest.mark.asyncio
    async def test_send_companion_message_returns_error_when_unavailable(self):
        """RED: send_companion_message retorna erro quando mod indisponível."""
        from apps.mcp_servers.planet_crafter_companion import handle_tool_call

        mock_http = AsyncMock()
        mock_http.post.side_effect = ConnectionRefusedError()

        result = await handle_tool_call(
            "send_companion_message",
            {"text": "teste"},
            http_client=mock_http,
            base_url="http://localhost:17234",
        )

        assert "não está disponível" in result or "indisponível" in result.lower()

    @pytest.mark.asyncio
    async def test_move_companion_to_posts_action(self):
        """RED: move_companion_to envia POST /action com estratégia."""
        from apps.mcp_servers.planet_crafter_companion import handle_tool_call

        mock_http = AsyncMock()
        mock_http.post.return_value.status_code = 200

        await handle_tool_call(
            "move_companion_to",
            {"strategy": "follow_player"},
            http_client=mock_http,
            base_url="http://localhost:17234",
        )

        call_body = mock_http.post.call_args[1]["json"]
        assert call_body["type"] == "move"
        assert call_body["strategy"] == "follow_player"

    @pytest.mark.asyncio
    async def test_move_companion_goto_coords_sends_xyz(self):
        """RED: goto_coords envia coordenadas x, y, z no body."""
        from apps.mcp_servers.planet_crafter_companion import handle_tool_call

        mock_http = AsyncMock()
        mock_http.post.return_value.status_code = 200

        await handle_tool_call(
            "move_companion_to",
            {"strategy": "goto_coords", "x": 100, "y": 50, "z": 200},
            http_client=mock_http,
            base_url="http://localhost:17234",
        )

        call_body = mock_http.post.call_args[1]["json"]
        assert call_body["type"] == "move"
        assert call_body["strategy"] == "goto_coords"
        assert call_body["x"] == 100
        assert call_body["y"] == 50
        assert call_body["z"] == 200

    @pytest.mark.asyncio
    async def test_move_companion_goto_named_sends_name(self):
        """RED: goto_named envia nome do local no body."""
        from apps.mcp_servers.planet_crafter_companion import handle_tool_call

        mock_http = AsyncMock()
        mock_http.post.return_value.status_code = 200

        await handle_tool_call(
            "move_companion_to",
            {"strategy": "goto_named", "name": "base"},
            http_client=mock_http,
            base_url="http://localhost:17234",
        )

        call_body = mock_http.post.call_args[1]["json"]
        assert call_body["type"] == "move"
        assert call_body["strategy"] == "goto_named"
        assert call_body["name"] == "base"

    @pytest.mark.asyncio
    async def test_move_companion_returns_error_when_unavailable(self):
        """RED: move_companion_to retorna erro quando mod indisponível."""
        from apps.mcp_servers.planet_crafter_companion import handle_tool_call

        mock_http = AsyncMock()
        mock_http.post.side_effect = ConnectionRefusedError()

        result = await handle_tool_call(
            "move_companion_to",
            {"strategy": "follow_player"},
            http_client=mock_http,
            base_url="http://localhost:17234",
        )

        assert "não está disponível" in result or "indisponível" in result.lower()

    @pytest.mark.asyncio
    async def test_set_companion_animation_returns_error_when_unavailable(self):
        """RED: set_companion_animation retorna erro quando mod indisponível."""
        from apps.mcp_servers.planet_crafter_companion import handle_tool_call

        mock_http = AsyncMock()
        mock_http.post.side_effect = ConnectionRefusedError()

        result = await handle_tool_call(
            "set_companion_animation",
            {"animation": "thinking"},
            http_client=mock_http,
            base_url="http://localhost:17234",
        )

        assert "não está disponível" in result or "indisponível" in result.lower()

    @pytest.mark.asyncio
    async def test_set_companion_animation_validates_animation(self):
        """RED: animação inválida retorna erro."""
        from apps.mcp_servers.planet_crafter_companion import handle_tool_call

        mock_http = AsyncMock()

        result = await handle_tool_call(
            "set_companion_animation",
            {"animation": "dancing"},
            http_client=mock_http,
            base_url="http://localhost:17234",
        )

        assert "inválid" in result.lower() or "válid" in result.lower()

    @pytest.mark.asyncio
    async def test_set_companion_animation_sends_valid_animation(self):
        """RED: animação válida envia POST /action."""
        from apps.mcp_servers.planet_crafter_companion import handle_tool_call

        mock_http = AsyncMock()
        mock_http.post.return_value.status_code = 200

        await handle_tool_call(
            "set_companion_animation",
            {"animation": "thinking"},
            http_client=mock_http,
            base_url="http://localhost:17234",
        )

        call_body = mock_http.post.call_args[1]["json"]
        assert call_body["type"] == "set_animation"
        assert call_body["animation"] == "thinking"

    @pytest.mark.asyncio
    async def test_get_game_state_returns_state(self):
        """RED: get_game_state faz GET /state e retorna resultado."""
        from apps.mcp_servers.planet_crafter_companion import handle_tool_call

        mock_http = AsyncMock()
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {
            "terraform": {"oxygen": 45.2},
            "player": {"position": {"x": 100, "y": 50, "z": 200}},
        }
        mock_http.get.return_value = mock_resp

        result = await handle_tool_call(
            "get_game_state",
            {},
            http_client=mock_http,
            base_url="http://localhost:17234",
        )

        mock_http.get.assert_called_once()
        assert "oxygen" in result or "45.2" in result

    @pytest.mark.asyncio
    async def test_get_game_state_returns_error_when_unavailable(self):
        """RED: get_game_state retorna erro quando mod não responde."""
        from apps.mcp_servers.planet_crafter_companion import handle_tool_call

        mock_http = AsyncMock()
        mock_http.get.side_effect = ConnectionRefusedError()

        result = await handle_tool_call(
            "get_game_state",
            {},
            http_client=mock_http,
            base_url="http://localhost:17234",
        )

        assert "não está disponível" in result or "indisponível" in result.lower()


# ============================================================================
# 8.1-8.6 — Sessão de Jogatina
# ============================================================================

class TestSessionManagement:
    """Tasks 8.1-8.5: Sessão de jogatina."""

    def test_session_starts_on_first_successful_poll(self):
        """RED: sessão é criada no primeiro polling bem-sucedido."""
        from apps.mcp_servers.planet_crafter_companion import CompanionSessionManager

        manager = CompanionSessionManager()
        manager.on_poll_success()

        assert manager.is_active
        assert manager.session is not None
        assert manager.session.start_time is not None

    def test_session_not_created_on_failure(self):
        """RED: sessão não é criada em polling falho."""
        from apps.mcp_servers.planet_crafter_companion import CompanionSessionManager

        manager = CompanionSessionManager()
        manager.on_poll_failure()

        assert not manager.is_active
        assert manager.session is None

    def test_session_ends_after_unavailability_timeout(self):
        """RED: sessão encerra após N falhas consecutivas (default 6 ≈ 60s)."""
        from apps.mcp_servers.planet_crafter_companion import CompanionSessionManager

        manager = CompanionSessionManager(timeout_failures=2)
        manager.on_poll_success()  # Inicia sessão
        assert manager.is_active

        manager.on_poll_failure()
        manager.on_poll_failure()

        assert not manager.is_active

    def test_session_does_not_end_on_temporary_failure(self):
        """RED: sessão não encerra em 1-2 falhas temporárias."""
        from apps.mcp_servers.planet_crafter_companion import CompanionSessionManager

        manager = CompanionSessionManager(timeout_failures=5)
        manager.on_poll_success()

        manager.on_poll_failure()  # 1 falha
        assert manager.is_active  # Ainda ativa

    def test_session_logs_events(self):
        """RED: eventos são registrados na sessão."""
        from apps.mcp_servers.planet_crafter_companion import CompanionSessionManager

        manager = CompanionSessionManager()
        manager.on_poll_success()

        manager.log_event("milestone", "Primeira chuva!")
        manager.log_event("skychat", "onde tem mais ferro?")

        assert len(manager.session.events) == 2
        assert manager.session.events[0]["type"] == "milestone"

    def test_session_accepts_notes(self):
        """RED: notas podem ser adicionadas via add_session_note."""
        from apps.mcp_servers.planet_crafter_companion import CompanionSessionManager

        manager = CompanionSessionManager()
        manager.on_poll_success()

        manager.add_note("Jogador preferiu focar em O2 primeiro")

        assert len(manager.session.events) == 1
        assert manager.session.events[0]["type"] == "note"

    def test_session_summary_returns_data(self):
        """RED: get_session_summary retorna duração, eventos, milestones."""
        from apps.mcp_servers.planet_crafter_companion import CompanionSessionManager

        manager = CompanionSessionManager()
        manager.on_poll_success()
        manager.log_event("milestone", "Chuva!")
        manager.add_note("Nota importante")

        summary = manager.get_summary()

        assert "duration_seconds" in summary
        assert "events" in summary
        assert summary["event_counts"]["milestone"] == 1
        assert summary["event_counts"]["note"] == 1

    @pytest.mark.asyncio
    async def test_add_session_note_tool(self):
        """RED: tool add_session_note adiciona nota à sessão."""
        from apps.mcp_servers.planet_crafter_companion import handle_tool_call, CompanionSessionManager

        manager = CompanionSessionManager()
        manager.on_poll_success()

        result = await handle_tool_call(
            "add_session_note",
            {"text": "Jogador focou em O2"},
            session_manager=manager,
        )

        assert len(manager.session.events) == 1
        assert manager.session.events[0]["type"] == "note"

    @pytest.mark.asyncio
    async def test_get_session_summary_tool(self):
        """RED: tool get_session_summary retorna resumo."""
        from apps.mcp_servers.planet_crafter_companion import handle_tool_call, CompanionSessionManager

        manager = CompanionSessionManager()
        manager.on_poll_success()
        manager.log_event("milestone", "Chuva!")

        result = await handle_tool_call(
            "get_session_summary",
            {},
            session_manager=manager,
        )

        assert "Chuva" in result or "milestone" in result
