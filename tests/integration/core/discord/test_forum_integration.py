# -*- coding: utf-8 -*-
"""
Testes de integração para Discord Forum MCP.

Estes testes requerem um ambiente Discord real configurado.
Usam o fórum do PyroPaws para testes de integração.

DOC: DDD Migration - Integration Tests
"""

import pytest
from unittest.mock import Mock, AsyncMock

from src.core.discord.application.services.discord_service import DiscordService
from src.core.discord.presentation.tools.forum_tools import (
    handle_list_forum_posts,
    handle_create_forum_post,
    handle_get_forum_post,
    handle_add_forum_comment,
)


@pytest.fixture
def mock_discord_client():
    """Fixture para cliente Discord mockado."""
    client = Mock()
    client.is_ready = Mock(return_value=True)
    return client


@pytest.fixture
def discord_service(mock_discord_client):
    """Fixture para DiscordService configurado."""
    service = DiscordService(client=mock_discord_client)
    return service


@pytest.mark.integration
@pytest.mark.asyncio
async def test_discord_service_list_forum_posts_integration(discord_service):
    """
    Testa integração de list_forum_posts com DiscordService.

    Este teste valida que:
    - DiscordService.list_forum_posts() pode ser chamado via handler
    - O handler usa corretamente a fachada do serviço
    """
    # Mock do método do serviço (não queremos chamar Discord real)
    discord_service.list_forum_posts = AsyncMock(
        return_value=[
            {
                "id": "123456",
                "title": "Integration Test Post",
                "content": "Test content for integration",
                "author_id": "789",
                "author_name": "TestBot",
                "created_at": "2026-04-04T12:00:00",
                "archived": False,
                "locked": False,
                "total_messages": 1,
            }
        ]
    )

    result = await handle_list_forum_posts(
        discord_service,
        {"channel_id": "test_forum_channel", "limit": 10}
    )

    assert result["status"] == "success"
    assert result["total"] == 1
    assert result["posts"][0]["title"] == "Integration Test Post"
    discord_service.list_forum_posts.assert_called_once()


@pytest.mark.integration
@pytest.mark.asyncio
async def test_discord_service_create_forum_post_integration(discord_service):
    """
    Testa integração de create_forum_post com DiscordService.

    Valida que o handler usa corretamente o DiscordService.
    """
    discord_service.create_forum_post = AsyncMock(
        return_value={
            "id": "789",
            "title": "New Integration Post",
            "content": "Integration test content",
            "author_id": "123",
            "created_at": "2026-04-04T12:00:00",
            "url": "https://discord.com/channels/guild/789",
            "status": "success"
        }
    )

    result = await handle_create_forum_post(
        discord_service,
        {
            "channel_id": "test_forum",
            "title": "New Integration Post",
            "content": "Integration test content",
            "tags": []
        }
    )

    assert result["status"] == "success"
    assert result["post_id"] == "789"
    discord_service.create_forum_post.assert_called_once()


@pytest.mark.integration
@pytest.mark.asyncio
async def test_discord_service_get_forum_post_integration(discord_service):
    """
    Testa integração de get_forum_post com DiscordService.

    Valida que comentários são incluídos no resultado.
    """
    discord_service.get_forum_post = AsyncMock(
        return_value={
            "id": "789",
            "title": "Post with Comments",
            "content": "Main content",
            "author_id": "123",
            "author_name": "Author",
            "channel_id": "forum_id",
            "created_at": "2026-04-04T12:00:00",
            "archived": False,
            "locked": False,
            "comments": [
                {
                    "id": "1",
                    "content": "First comment",
                    "author_id": "456",
                    "author_name": "Commenter1",
                    "created_at": "2026-04-04T12:30:00",
                },
                {
                    "id": "2",
                    "content": "Second comment",
                    "author_id": "789",
                    "author_name": "Commenter2",
                    "created_at": "2026-04-04T13:00:00",
                },
            ],
            "status": "success"
        }
    )

    result = await handle_get_forum_post(
        discord_service,
        {"post_id": "789"}
    )

    assert result["status"] == "success"
    assert len(result["post"]["comments"]) == 2
    assert result["post"]["comments"][0]["content"] == "First comment"


@pytest.mark.integration
@pytest.mark.asyncio
async def test_discord_service_add_comment_integration(discord_service):
    """
    Testa integração de add_forum_comment com DiscordService.
    """
    discord_service.add_forum_comment = AsyncMock(
        return_value={
            "id": "999",
            "content": "Integration test comment",
            "author_id": "123",
            "created_at": "2026-04-04T14:00:00",
            "status": "success"
        }
    )

    result = await handle_add_forum_comment(
        discord_service,
        {"post_id": "789", "content": "Integration test comment"}
    )

    assert result["status"] == "success"
    assert result["comment_id"] == "999"
    discord_service.add_forum_comment.assert_called_once_with("789", "Integration test comment")


@pytest.mark.integration
@pytest.mark.asyncio
async def test_error_handling_in_discord_service(discord_service):
    """
    Testa que erros do DiscordService são tratados corretamente pelos handlers.
    """
    # Simula erro no serviço
    discord_service.list_forum_posts = AsyncMock(return_value=None)

    result = await handle_list_forum_posts(
        discord_service,
        {"channel_id": "test_forum"}
    )

    assert result["status"] == "error"
    assert "Falha ao listar posts" in result["error"]
