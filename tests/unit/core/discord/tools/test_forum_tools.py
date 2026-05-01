# -*- coding: utf-8 -*-
"""
Testes unitários para forum_tools.py.

DOC: DDD Migration - Testes Unitários
"""

from unittest.mock import Mock, AsyncMock, patch
import pytest

from src.core.discord.presentation.tools.forum_tools import (
    handle_list_forum_posts,
    handle_create_forum_post,
    handle_get_forum_post,
    handle_add_forum_comment,
    handle_list_forum_comments,
    handle_update_forum_post,
    handle_close_forum_post,
    handle_create_forum,
    handle_archive_forum,
    handle_delete_forum,
    handle_update_forum_settings,
)
from src.core.discord.application.services.discord_service import DiscordService


@pytest.fixture
def mock_discord_service():
    """Fixture para DiscordService mockado."""
    service = Mock(spec=DiscordService)
    service._client = Mock()
    return service


@pytest.mark.asyncio
async def test_list_forum_posts_success(mock_discord_service):
    """Testa listagem bem-sucedida de posts de fórum."""
    mock_discord_service.list_forum_posts = AsyncMock(
        return_value=[
            {
                "id": "123",
                "title": "Test Post",
                "content": "Test content",
                "author_id": "456",
                "author_name": "TestUser",
                "created_at": "2026-04-04T00:00:00",
                "archived": False,
                "locked": False,
                "total_messages": 1,
            }
        ]
    )

    result = await handle_list_forum_posts(
        mock_discord_service,
        {"channel_id": "789", "limit": 20, "archived": False}
    )

    assert result["status"] == "success"
    assert result["total"] == 1
    assert result["posts"][0]["title"] == "Test Post"
    mock_discord_service.list_forum_posts.assert_called_once_with(
        channel_id="789", limit=20, archived=False
    )


@pytest.mark.asyncio
async def test_list_forum_posts_missing_channel_id(mock_discord_service):
    """Testa erro quando channel_id não é fornecido."""
    result = await handle_list_forum_posts(
        mock_discord_service,
        {"limit": 20}
    )

    assert result["status"] == "error"
    assert "channel_id é obrigatório" in result["error"]


@pytest.mark.asyncio
async def test_create_forum_post_success(mock_discord_service):
    """Testa criação bem-sucedida de post em fórum."""
    mock_discord_service.create_forum_post = AsyncMock(
        return_value={
            "id": "123",
            "title": "New Post",
            "content": "New content",
            "author_id": "456",
            "created_at": "2026-04-04T00:00:00",
            "url": "https://discord.com/channels/123/456",
            "status": "success"
        }
    )

    result = await handle_create_forum_post(
        mock_discord_service,
        {
            "channel_id": "789",
            "title": "New Post",
            "content": "New content",
            "tags": ["tag1", "tag2"]
        }
    )

    assert result["status"] == "success"
    assert result["post_id"] == "123"
    assert result["title"] == "New Post"
    mock_discord_service.create_forum_post.assert_called_once()


@pytest.mark.asyncio
async def test_get_forum_post_success(mock_discord_service):
    """Testa obtenção bem-sucedida de post de fórum."""
    mock_discord_service.get_forum_post = AsyncMock(
        return_value={
            "id": "123",
            "title": "Test Post",
            "content": "Test content",
            "author_id": "456",
            "author_name": "TestUser",
            "channel_id": "789",
            "created_at": "2026-04-04T00:00:00",
            "archived": False,
            "locked": False,
            "comments": [],
            "status": "success"
        }
    )

    result = await handle_get_forum_post(
        mock_discord_service,
        {"post_id": "123"}
    )

    assert result["status"] == "success"
    assert result["post"]["title"] == "Test Post"
    mock_discord_service.get_forum_post.assert_called_once_with("123")


@pytest.mark.asyncio
async def test_add_forum_comment_success(mock_discord_service):
    """Testa adição bem-sucedida de comentário."""
    mock_discord_service.add_forum_comment = AsyncMock(
        return_value={
            "id": "999",
            "content": "Nice post!",
            "author_id": "456",
            "created_at": "2026-04-04T00:00:00",
            "status": "success"
        }
    )

    result = await handle_add_forum_comment(
        mock_discord_service,
        {"post_id": "123", "content": "Nice post!"}
    )

    assert result["status"] == "success"
    assert result["comment_id"] == "999"
    mock_discord_service.add_forum_comment.assert_called_once_with("123", "Nice post!")


@pytest.mark.asyncio
async def test_list_forum_comments_success(mock_discord_service):
    """Testa listagem bem-sucedida de comentários."""
    mock_discord_service.list_forum_comments = AsyncMock(
        return_value=[
            {
                "id": "999",
                "content": "Nice post!",
                "author_id": "456",
                "author_name": "Commenter",
                "created_at": "2026-04-04T00:00:00",
            }
        ]
    )

    result = await handle_list_forum_comments(
        mock_discord_service,
        {"post_id": "123", "limit": 50}
    )

    assert result["status"] == "success"
    assert result["total"] == 1
    assert result["comments"][0]["content"] == "Nice post!"


@pytest.mark.asyncio
async def test_update_forum_post_success(mock_discord_service):
    """Testa atualização bem-sucedida de post."""
    mock_discord_service.update_forum_post = AsyncMock(
        return_value={
            "id": "123",
            "edited_at": "2026-04-04T01:00:00",
            "status": "success"
        }
    )

    result = await handle_update_forum_post(
        mock_discord_service,
        {"post_id": "123", "title": "Updated Title"}
    )

    assert result["status"] == "success"
    assert result["post_id"] == "123"


@pytest.mark.asyncio
async def test_close_forum_post_success(mock_discord_service):
    """Testa fechamento bem-sucedido de post."""
    mock_discord_service.close_forum_post = AsyncMock(
        return_value={
            "id": "123",
            "locked": True,
            "status": "success"
        }
    )

    result = await handle_close_forum_post(
        mock_discord_service,
        {"post_id": "123"}
    )

    assert result["status"] == "success"
    assert result["locked"] is True


@pytest.mark.asyncio
async def test_create_forum_success(mock_discord_service):
    """Testa criação bem-sucedida de fórum."""
    mock_forum_channel = AsyncMock()
    mock_forum_channel.id = 789
    mock_forum_channel.name = "New Forum"

    mock_guild = AsyncMock()
    mock_guild.id = 123
    mock_guild.create_forum = AsyncMock(return_value=mock_forum_channel)

    mock_discord_service._client.fetch_guild = AsyncMock(return_value=mock_guild)

    result = await handle_create_forum(
        mock_discord_service,
        {"guild_id": "123", "name": "New Forum", "layout": "classic"}
    )

    assert result["status"] == "success"
    assert result["forum_id"] == "789"


@pytest.mark.asyncio
async def test_archive_forum_success(mock_discord_service):
    """Testa arquivamento bem-sucedido de fórum."""
    mock_discord_service.archive_forum = AsyncMock(
        return_value={
            "forum_id": "789",
            "archived": True,
            "status": "success"
        }
    )

    result = await handle_archive_forum(
        mock_discord_service,
        {"forum_id": "789"}
    )

    assert result["status"] == "success"
    assert result["archived"] is True


@pytest.mark.asyncio
async def test_delete_forum_requires_confirm(mock_discord_service):
    """Testa que delete_forum requer confirm=true."""
    result = await handle_delete_forum(
        mock_discord_service,
        {"forum_id": "789", "confirm": False}
    )

    assert result["status"] == "error"
    assert "confirm=true é obrigatório" in result["error"]


@pytest.mark.asyncio
async def test_delete_forum_success_with_confirm(mock_discord_service):
    """Testa deleção bem-sucedida com confirmação."""
    mock_discord_service.delete_forum = AsyncMock(
        return_value={
            "forum_id": "789",
            "deleted": True,
            "status": "success"
        }
    )

    result = await handle_delete_forum(
        mock_discord_service,
        {"forum_id": "789", "confirm": True}
    )

    assert result["status"] == "success"
    assert result["deleted"] is True


@pytest.mark.asyncio
async def test_update_forum_settings_success(mock_discord_service):
    """Testa atualização bem-sucedida de configurações de fórum."""
    mock_discord_service.update_forum_settings = AsyncMock(
        return_value={
            "forum_id": "789",
            "updated": ["name"],
            "status": "success"
        }
    )

    result = await handle_update_forum_settings(
        mock_discord_service,
        {"forum_id": "789", "name": "Renamed Forum"}
    )

    assert result["status"] == "success"
    assert result["updated_fields"] == ["name"]


@pytest.mark.asyncio
async def test_update_forum_settings_requires_at_least_one_field(mock_discord_service):
    """Testa update_forum_settings com apenas forum_id e campos opcionais None."""
    mock_discord_service.update_forum_settings = AsyncMock(
        return_value={
            "forum_id": "789",
            "updated": [],
            "status": "success"
        }
    )

    result = await handle_update_forum_settings(
        mock_discord_service,
        {"forum_id": "789"}
    )

    assert result["status"] == "success"
    assert result["forum_id"] == "789"
