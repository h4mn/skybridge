"""Testes E2E — push direto via POST /incoming.

Fluxo: mod POSTa evento → MCP server notifica Claude Code.
Tools ainda chamam o mock mod via HTTP.
"""
from __future__ import annotations

import json
import time

import pytest

from tests.unit.mcp.mock_mod_server import MockModServer


# ============================================================================
# E2E: MCP Tools → Mock Mod Server
# ============================================================================

class TestE2eToolToMock:
    @pytest.mark.asyncio
    async def test_send_message_arrives_at_mock(self):
        from apps.mcp_servers.planet_crafter_companion import handle_tool_call
        import httpx

        with MockModServer() as mock:
            async with httpx.AsyncClient() as client:
                result = await handle_tool_call(
                    "send_companion_message",
                    {"text": "Olá do teste E2E!"},
                    http_client=client,
                    base_url=mock.base_url,
                )

            assert len(mock.actions) == 1
            assert mock.actions[0]["text"] == "Olá do teste E2E!"

    @pytest.mark.asyncio
    async def test_move_goto_coords_arrives_at_mock(self):
        from apps.mcp_servers.planet_crafter_companion import handle_tool_call
        import httpx

        with MockModServer() as mock:
            async with httpx.AsyncClient() as client:
                await handle_tool_call(
                    "move_companion_to",
                    {"strategy": "goto_coords", "x": 100, "y": 50, "z": 200},
                    http_client=client,
                    base_url=mock.base_url,
                )

            assert mock.actions[0]["x"] == 100

    @pytest.mark.asyncio
    async def test_get_game_state_from_mock(self):
        from apps.mcp_servers.planet_crafter_companion import handle_tool_call
        import httpx

        with MockModServer() as mock:
            mock.set_game_state(Oxygen=45.2)
            async with httpx.AsyncClient() as client:
                result = await handle_tool_call(
                    "get_game_state", {}, http_client=client, base_url=mock.base_url,
                )
            state = json.loads(result)
            assert state["Terraform"]["Oxygen"] == 45.2


# ============================================================================
# E2E: Direct Push — simula mod POSTando no MCP server
# ============================================================================

class TestE2eDirectPush:
    """Simula o fluxo direto: mod POSTa evento → MCP notifica."""

    @pytest.mark.asyncio
    async def test_skychat_push_sends_notification(self):
        from apps.mcp_servers.planet_crafter_companion import (
            create_push_handler, CompanionSessionManager,
        )
        from unittest.mock import AsyncMock

        mock_write = AsyncMock()
        session_mgr = CompanionSessionManager()
        handler = create_push_handler(mock_write, session_mgr)

        # Simula POST do mod C#
        request = AsyncMock()
        request.json = AsyncMock(return_value={
            "type": "skychat",
            "description": "onde tem mais ferro?",
        })

        response = await handler(request)

        assert response.status == 200
        mock_write.send.assert_called_once()
        notif = mock_write.send.call_args[0][0]
        content = notif.root.params.get("content", "")
        assert "ferro" in content

    @pytest.mark.asyncio
    async def test_milestone_push_sends_notification(self):
        from apps.mcp_servers.planet_crafter_companion import (
            create_push_handler, CompanionSessionManager,
        )
        from unittest.mock import AsyncMock

        mock_write = AsyncMock()
        session_mgr = CompanionSessionManager()
        handler = create_push_handler(mock_write, session_mgr)

        request = AsyncMock()
        request.json = AsyncMock(return_value={
            "type": "milestone",
            "description": "Primeira chuva!",
        })

        await handler(request)
        mock_write.send.assert_called_once()


# ============================================================================
# E2E: Full Pipeline (push + tool response)
# ============================================================================

class TestE2eFullPipeline:
    @pytest.mark.asyncio
    async def test_skychat_push_then_tool_response(self):
        """Simula fluxo completo: push → notificação → tool → ação no mod."""
        from apps.mcp_servers.planet_crafter_companion import (
            create_push_handler, handle_tool_call, CompanionSessionManager,
        )
        from unittest.mock import AsyncMock
        import httpx

        with MockModServer() as mock:
            mock_write = AsyncMock()
            session_mgr = CompanionSessionManager()
            handler = create_push_handler(mock_write, session_mgr)

            # 1. Mod POSTa /skychat
            request = AsyncMock()
            request.json = AsyncMock(return_value={
                "type": "skychat",
                "description": "onde tem mais ferro?",
            })
            await handler(request)

            # 2. Notificação enviada ao Claude Code
            assert mock_write.send.call_count == 1
            assert "ferro" in mock_write.send.call_args[0][0].root.params.get("content", "")

            # 3. Claude responde via tool → POST /action no mod
            async with httpx.AsyncClient() as client:
                result = await handle_tool_call(
                    "send_companion_message",
                    {"text": "Ferro tem perto das cavernas ao norte!"},
                    http_client=client,
                    base_url=mock.base_url,
                    session_manager=session_mgr,
                )

            assert len(mock.actions) == 1
            assert mock.actions[0]["text"] == "Ferro tem perto das cavernas ao norte!"
            assert session_mgr.is_active
