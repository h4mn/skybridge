"""Testes para o Channel MCP do Planet Crafter — modelo direto (push).

Fluxo: mod POSTa evento → MCP server notifica Claude Code imediatamente.
Sem polling. Sem throttle.
"""
from __future__ import annotations

import json
from unittest.mock import AsyncMock, MagicMock

import pytest


# ============================================================================
# Server Creation & Capability
# ============================================================================

class TestMcpServerCreation:
    def test_server_importable(self):
        from apps.mcp_servers.planet_crafter_companion import create_server
        server = create_server()
        assert server is not None
        assert server.name == "planet-crafter-channel"

    def test_server_has_list_tools_handler(self):
        from apps.mcp_servers.planet_crafter_companion import create_server
        server = create_server()
        assert hasattr(server, "list_tools")

    def test_server_has_call_tool_handler(self):
        from apps.mcp_servers.planet_crafter_companion import create_server
        server = create_server()
        assert hasattr(server, "call_tool")


class TestCapabilityDeclaration:
    def test_initialization_options_includes_channel_capability(self):
        from apps.mcp_servers.planet_crafter_companion import create_initialization_options
        opts = create_initialization_options()
        assert hasattr(opts, "capabilities")
        experimental = opts.capabilities.experimental
        assert "claude/channel" in experimental


# ============================================================================
# Direct Push: POST /incoming → JSONRPCNotification
# ============================================================================

class TestDirectPush:
    """POST /incoming envia notificação imediata."""

    @pytest.mark.asyncio
    async def test_incoming_event_sends_notification(self):
        from apps.mcp_servers.planet_crafter_companion import (
            create_push_handler, CompanionSessionManager,
        )

        mock_write = AsyncMock()
        session_mgr = CompanionSessionManager()
        handler = create_push_handler(mock_write, session_mgr)

        # Simula request do mod
        request = MagicMock()
        request.json = AsyncMock(return_value={
            "type": "skychat",
            "description": "oi Sky!",
        })

        response = await handler(request)

        assert response.status == 200
        mock_write.send.assert_called_once()
        notif = mock_write.send.call_args[0][0]
        assert notif.root.method == "notifications/claude/channel"
        assert "oi Sky" in notif.root.params.get("content", "")

    @pytest.mark.asyncio
    async def test_incoming_event_registers_in_session(self):
        from apps.mcp_servers.planet_crafter_companion import (
            create_push_handler, CompanionSessionManager,
        )

        mock_write = AsyncMock()
        session_mgr = CompanionSessionManager()
        handler = create_push_handler(mock_write, session_mgr)

        request = MagicMock()
        request.json = AsyncMock(return_value={
            "type": "milestone",
            "description": "Primeira chuva!",
        })

        await handler(request)

        assert session_mgr.is_active
        assert len(session_mgr.session.events) == 1
        assert session_mgr.session.events[0]["type"] == "milestone"

    @pytest.mark.asyncio
    async def test_incoming_invalid_json_returns_error(self):
        from apps.mcp_servers.planet_crafter_companion import (
            create_push_handler, CompanionSessionManager,
        )

        mock_write = AsyncMock()
        session_mgr = CompanionSessionManager()
        handler = create_push_handler(mock_write, session_mgr)

        request = MagicMock()
        request.json = AsyncMock(side_effect=Exception("bad json"))

        response = await handler(request)

        assert response.status == 400
        mock_write.send.assert_not_called()

    @pytest.mark.asyncio
    async def test_multiple_pushes_all_send_notifications(self):
        from apps.mcp_servers.planet_crafter_companion import (
            create_push_handler, CompanionSessionManager,
        )

        mock_write = AsyncMock()
        session_mgr = CompanionSessionManager()
        handler = create_push_handler(mock_write, session_mgr)

        for msg in ["msg 1", "msg 2", "msg 3"]:
            request = MagicMock()
            request.json = AsyncMock(return_value={
                "type": "skychat",
                "description": msg,
            })
            await handler(request)

        assert mock_write.send.call_count == 3
        assert len(session_mgr.session.events) == 3


# ============================================================================
# MCP Tools (still HTTP to mod at localhost:17234)
# ============================================================================

class TestCompanionTools:
    """Tools continuam funcionando via HTTP para o mod."""

    @pytest.mark.asyncio
    async def test_send_companion_message_posts_action(self):
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
        call_body = mock_http.post.call_args[1]["json"]
        assert call_body["type"] == "show_message"

    @pytest.mark.asyncio
    async def test_send_companion_message_returns_error_when_unavailable(self):
        from apps.mcp_servers.planet_crafter_companion import handle_tool_call
        mock_http = AsyncMock()
        mock_http.post.side_effect = ConnectionRefusedError()

        result = await handle_tool_call(
            "send_companion_message",
            {"text": "teste"},
            http_client=mock_http,
        )

        assert "não está disponível" in result or "indisponível" in result.lower()

    @pytest.mark.asyncio
    async def test_move_companion_to_posts_action(self):
        from apps.mcp_servers.planet_crafter_companion import handle_tool_call
        mock_http = AsyncMock()
        mock_http.post.return_value.status_code = 200

        await handle_tool_call(
            "move_companion_to",
            {"strategy": "follow_player"},
            http_client=mock_http,
        )

        call_body = mock_http.post.call_args[1]["json"]
        assert call_body["type"] == "move"
        assert call_body["strategy"] == "follow_player"

    @pytest.mark.asyncio
    async def test_move_companion_goto_coords_sends_xyz(self):
        from apps.mcp_servers.planet_crafter_companion import handle_tool_call
        mock_http = AsyncMock()
        mock_http.post.return_value.status_code = 200

        await handle_tool_call(
            "move_companion_to",
            {"strategy": "goto_coords", "x": 100, "y": 50, "z": 200},
            http_client=mock_http,
        )

        call_body = mock_http.post.call_args[1]["json"]
        assert call_body["x"] == 100

    @pytest.mark.asyncio
    async def test_set_companion_animation_validates_animation(self):
        from apps.mcp_servers.planet_crafter_companion import handle_tool_call
        mock_http = AsyncMock()

        result = await handle_tool_call(
            "set_companion_animation",
            {"animation": "dancing"},
            http_client=mock_http,
        )

        assert "inválid" in result.lower()

    @pytest.mark.asyncio
    async def test_set_companion_animation_sends_valid_animation(self):
        from apps.mcp_servers.planet_crafter_companion import handle_tool_call
        mock_http = AsyncMock()
        mock_http.post.return_value.status_code = 200

        await handle_tool_call(
            "set_companion_animation",
            {"animation": "thinking"},
            http_client=mock_http,
        )

        call_body = mock_http.post.call_args[1]["json"]
        assert call_body["type"] == "set_animation"

    @pytest.mark.asyncio
    async def test_get_game_state_returns_state(self):
        from apps.mcp_servers.planet_crafter_companion import handle_tool_call
        mock_http = AsyncMock()
        mock_resp = MagicMock()
        mock_resp.json.return_value = {"terraform": {"oxygen": 45.2}}
        mock_http.get.return_value = mock_resp

        result = await handle_tool_call("get_game_state", {}, http_client=mock_http)
        assert "oxygen" in result or "45.2" in result

    @pytest.mark.asyncio
    async def test_get_game_state_returns_error_when_unavailable(self):
        from apps.mcp_servers.planet_crafter_companion import handle_tool_call
        mock_http = AsyncMock()
        mock_http.get.side_effect = ConnectionRefusedError()

        result = await handle_tool_call("get_game_state", {}, http_client=mock_http)
        assert "não está disponível" in result or "indisponível" in result.lower()


# ============================================================================
# Session Management (simplified — sem poll)
# ============================================================================

class TestSessionManagement:
    def test_session_starts_on_first_event(self):
        from apps.mcp_servers.planet_crafter_companion import CompanionSessionManager
        mgr = CompanionSessionManager()
        mgr.log_event("milestone", "Chuva!")
        assert mgr.is_active

    def test_session_not_created_without_events(self):
        from apps.mcp_servers.planet_crafter_companion import CompanionSessionManager
        mgr = CompanionSessionManager()
        assert not mgr.is_active

    def test_session_logs_events(self):
        from apps.mcp_servers.planet_crafter_companion import CompanionSessionManager
        mgr = CompanionSessionManager()
        mgr.log_event("milestone", "Chuva!")
        mgr.log_event("skychat", "oi")
        assert len(mgr.session.events) == 2

    def test_session_accepts_notes(self):
        from apps.mcp_servers.planet_crafter_companion import CompanionSessionManager
        mgr = CompanionSessionManager()
        mgr.add_note("Nota importante")
        assert mgr.session.events[0]["type"] == "note"

    def test_session_summary_returns_data(self):
        from apps.mcp_servers.planet_crafter_companion import CompanionSessionManager
        mgr = CompanionSessionManager()
        mgr.log_event("milestone", "Chuva!")
        mgr.add_note("Nota")

        summary = mgr.get_summary()
        assert "duration_seconds" in summary
        assert summary["event_counts"]["milestone"] == 1

    @pytest.mark.asyncio
    async def test_add_session_note_tool(self):
        from apps.mcp_servers.planet_crafter_companion import handle_tool_call, CompanionSessionManager
        mgr = CompanionSessionManager()
        result = await handle_tool_call("add_session_note", {"text": "teste"}, session_manager=mgr)
        assert mgr.session.events[0]["type"] == "note"

    @pytest.mark.asyncio
    async def test_get_session_summary_tool(self):
        from apps.mcp_servers.planet_crafter_companion import handle_tool_call, CompanionSessionManager
        mgr = CompanionSessionManager()
        mgr.log_event("milestone", "Chuva!")
        result = await handle_tool_call("get_session_summary", {}, session_manager=mgr)
        assert "Chuva" in result or "milestone" in result
