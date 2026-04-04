# -*- coding: utf-8 -*-
"""
Tool: create_forum

Cria um novo canal de fórum na guild.

DOC: DDD Migration - Presentation Layer
"""

from __future__ import annotations

import logging
from typing import Any

from ...application.services.discord_service import DiscordService
from .dto.forum_dto import ForumSettingsDTO, ForumPostDTO, ForumCommentDTO, ForumTagDTO

logger = logging.getLogger(__name__)


async def handle_create_forum(
    discord_service: DiscordService,
    args: dict[str, Any]
) -> dict[str, Any]:
    """
    Handler para tool create_forum.

    Args:
        discord_service: Instância do DiscordService
        args: Argumentos do tool

    Returns:
        Dict com forum_id, forum_name, status
    """
    guild_id = args.get("guild_id")
    name = args.get("name")
    layout = args.get("layout", "classic")

    if not guild_id or not name:
        return {
            "status": "error",
            "error": "guild_id e name são obrigatórios"
        }

    try:
        guild = await discord_service._client.fetch_guild(int(guild_id))

        # Criar canal de fórum
        forum_channel = await guild.create_forum(
            name=name,
            layout_type=layout
        )

        logger.info(f"Fórum criado: {forum_channel.name} ({forum_channel.id})")

        return {
            "forum_id": str(forum_channel.id),
            "forum_name": forum_channel.name,
            "guild_id": str(guild.id),
            "status": "success"
        }
    except Exception as e:
        logger.error(f"Erro ao criar fórum: {e}")
        return {
            "status": "error",
            "error": str(e)
        }


# Tool definition para registro no MCP
TOOL_DEFINITION = {
    "name": "create_forum",
    "description": (
        "Create a new forum channel in a Discord guild. "
        "Forums provide structured discussion spaces with tags and post management."
    ),
    "inputSchema": {
        "type": "object",
        "properties": {
            "guild_id": {"type": "string", "description": "Guild ID where to create the forum"},
            "name": {"type": "string", "description": "Name for the new forum channel"},
            "layout": {
                "type": "string",
                "enum": ["classic", "list"],
                "default": "classic",
                "description": "Forum layout style"
            },
        },
        "required": ["guild_id", "name"],
    },
}


# =============================================================================
# POSTS / COMENTÁRIOS
# =============================================================================

async def handle_list_forum_posts(
    discord_service: DiscordService,
    args: dict[str, Any]
) -> dict[str, Any]:
    """
    Lista posts de um canal de fórum com paginação.

    Args:
        discord_service: Instância do DiscordService
        args: {channel_id, limit, archived}

    Returns:
        Dict com posts, total, status
    """
    channel_id = args.get("channel_id")
    limit = args.get("limit", 20)
    archived = args.get("archived", False)

    if not channel_id:
        return {"status": "error", "error": "channel_id é obrigatório"}

    try:
        channel = await discord_service._client.fetch_channel(int(channel_id))

        posts = []
        async for thread in channel.archived_threads(limit=limit) if archived else channel.threads(limit=limit):
            post_dto = ForumPostDTO.from_discord_thread(thread)
            posts.append({
                "id": post_dto.id,
                "title": post_dto.title,
                "content": post_dto.content,
                "author_id": post_dto.author_id,
                "author_name": post_dto.author_name,
                "created_at": post_dto.created_at.isoformat() if post_dto.created_at else None,
                "archived": post_dto.archived,
                "locked": post_dto.locked,
                "total_messages": post_dto.total_messages,
            })

        return {
            "posts": posts,
            "total": len(posts),
            "channel_id": channel_id,
            "status": "success"
        }
    except Exception as e:
        logger.error(f"Erro ao listar posts: {e}")
        return {"status": "error", "error": str(e)}


LIST_FORUM_POSTS_TOOL = {
    "name": "list_forum_posts",
    "description": "List posts from a Discord forum channel with pagination.",
    "inputSchema": {
        "type": "object",
        "properties": {
            "channel_id": {"type": "string", "description": "Forum channel ID"},
            "limit": {"type": "integer", "default": 20, "description": "Max posts to return"},
            "archived": {"type": "boolean", "default": False, "description": "Include archived posts"},
        },
        "required": ["channel_id"],
    },
}


async def handle_create_forum_post(
    discord_service: DiscordService,
    args: dict[str, Any]
) -> dict[str, Any]:
    """
    Cria um novo post em um canal de fórum.

    Args:
        discord_service: Instância do DiscordService
        args: {channel_id, title, content, tags}

    Returns:
        Dict com post_id, title, status
    """
    channel_id = args.get("channel_id")
    title = args.get("title")
    content = args.get("content", "")
    tags = args.get("tags", [])

    if not channel_id or not title:
        return {"status": "error", "error": "channel_id e title são obrigatórios"}

    try:
        channel = await discord_service._client.fetch_channel(int(channel_id))

        # Converter tag IDs para objetos
        applied_tags = []
        if tags:
            available_tags = getattr(channel, "available_tags", [])
            tag_map = {str(t.id): t for t in available_tags}
            applied_tags = [tag_map[t] for t in tags if t in tag_map]

        # Criar post (thread)
        thread = await channel.create_thread(
            name=title,
            content=content,
            applied_tags=applied_tags
        )

        logger.info(f"Post criado: {thread.name} ({thread.id})")

        return {
            "post_id": str(thread.id),
            "title": thread.name,
            "channel_id": channel_id,
            "status": "success"
        }
    except Exception as e:
        logger.error(f"Erro ao criar post: {e}")
        return {"status": "error", "error": str(e)}


CREATE_FORUM_POST_TOOL = {
    "name": "create_forum_post",
    "description": "Create a new post in a Discord forum channel.",
    "inputSchema": {
        "type": "object",
        "properties": {
            "channel_id": {"type": "string", "description": "Forum channel ID"},
            "title": {"type": "string", "description": "Post title"},
            "content": {"type": "string", "description": "Post content (markdown supported)"},
            "tags": {"type": "array", "items": {"type": "string"}, "description": "Tag IDs to apply"},
        },
        "required": ["channel_id", "title"],
    },
}


async def handle_get_forum_post(
    discord_service: DiscordService,
    args: dict[str, Any]
) -> dict[str, Any]:
    """
    Obtém detalhes completos de um post de fórum.

    Args:
        discord_service: Instância do DiscordService
        args: {post_id}

    Returns:
        Dict com post details
    """
    post_id = args.get("post_id")

    if not post_id:
        return {"status": "error", "error": "post_id é obrigatório"}

    try:
        thread = await discord_service._client.fetch_channel(int(post_id))
        post_dto = ForumPostDTO.from_discord_thread(thread)

        return {
            "post": {
                "id": post_dto.id,
                "title": post_dto.title,
                "content": post_dto.content,
                "author_id": post_dto.author_id,
                "author_name": post_dto.author_name,
                "channel_id": post_dto.channel_id,
                "created_at": post_dto.created_at.isoformat() if post_dto.created_at else None,
                "edited_at": post_dto.edited_at.isoformat() if post_dto.edited_at else None,
                "archived": post_dto.archived,
                "locked": post_dto.locked,
                "pinned": post_dto.pinned,
                "total_messages": post_dto.total_messages,
            },
            "status": "success"
        }
    except Exception as e:
        logger.error(f"Erro ao obter post: {e}")
        return {"status": "error", "error": str(e)}


GET_FORUM_POST_TOOL = {
    "name": "get_forum_post",
    "description": "Get detailed information about a specific forum post.",
    "inputSchema": {
        "type": "object",
        "properties": {
            "post_id": {"type": "string", "description": "Post/thread ID"},
        },
        "required": ["post_id"],
    },
}


async def handle_add_forum_comment(
    discord_service: DiscordService,
    args: dict[str, Any]
) -> dict[str, Any]:
    """
    Adiciona um comentário a um post de fórum.

    Args:
        discord_service: Instância do DiscordService
        args: {post_id, content}

    Returns:
        Dict com comment_id, status
    """
    post_id = args.get("post_id")
    content = args.get("content")

    if not post_id or not content:
        return {"status": "error", "error": "post_id e content são obrigatórios"}

    try:
        thread = await discord_service._client.fetch_channel(int(post_id))
        message = await thread.send(content)

        logger.info(f"Comentário adicionado ao post {post_id}")

        return {
            "comment_id": str(message.id),
            "post_id": post_id,
            "status": "success"
        }
    except Exception as e:
        logger.error(f"Erro ao adicionar comentário: {e}")
        return {"status": "error", "error": str(e)}


ADD_FORUM_COMMENT_TOOL = {
    "name": "add_forum_comment",
    "description": "Add a comment to a forum post.",
    "inputSchema": {
        "type": "object",
        "properties": {
            "post_id": {"type": "string", "description": "Post/thread ID"},
            "content": {"type": "string", "description": "Comment content (markdown supported)"},
        },
        "required": ["post_id", "content"],
    },
}


async def handle_list_forum_comments(
    discord_service: DiscordService,
    args: dict[str, Any]
) -> dict[str, Any]:
    """
    Lista comentários de um post de fórum.

    Args:
        discord_service: Instância do DiscordService
        args: {post_id, limit}

    Returns:
        Dict com comments, total, status
    """
    post_id = args.get("post_id")
    limit = args.get("limit", 50)

    if not post_id:
        return {"status": "error", "error": "post_id é obrigatório"}

    try:
        thread = await discord_service._client.fetch_channel(int(post_id))

        comments = []
        async for msg in thread.history(limit=limit):
            # Pular a primeira mensagem (é o post principal)
            if msg.type == 31:  # Thread starter
                continue

            comment_dto = ForumCommentDTO.from_discord_message(msg, post_id)
            comments.append({
                "id": comment_dto.id,
                "content": comment_dto.content,
                "author_id": comment_dto.author_id,
                "author_name": comment_dto.author_name,
                "created_at": comment_dto.created_at.isoformat() if comment_dto.created_at else None,
            })

        return {
            "comments": comments,
            "total": len(comments),
            "post_id": post_id,
            "status": "success"
        }
    except Exception as e:
        logger.error(f"Erro ao listar comentários: {e}")
        return {"status": "error", "error": str(e)}


LIST_FORUM_COMMENTS_TOOL = {
    "name": "list_forum_comments",
    "description": "List comments from a forum post.",
    "inputSchema": {
        "type": "object",
        "properties": {
            "post_id": {"type": "string", "description": "Post/thread ID"},
            "limit": {"type": "integer", "default": 50, "description": "Max comments to return"},
        },
        "required": ["post_id"],
    },
}


async def handle_update_forum_post(
    discord_service: DiscordService,
    args: dict[str, Any]
) -> dict[str, Any]:
    """
    Edita um post de fórum (apenas título/conteúdo da primeira mensagem).

    Args:
        discord_service: Instância do DiscordService
        args: {post_id, title, content}

    Returns:
        Dict com post_id, status
    """
    post_id = args.get("post_id")
    title = args.get("title")
    content = args.get("content")

    if not post_id:
        return {"status": "error", "error": "post_id é obrigatório"}

    if not title and not content:
        return {"status": "error", "error": "title ou content devem ser fornecidos"}

    try:
        thread = await discord_service._client.fetch_channel(int(post_id))

        # Buscar a primeira mensagem (post principal)
        async for msg in thread.history(limit=1):
            # Editar título (nome da thread) e/ou conteúdo
            if title:
                await thread.edit(name=title)
            if content:
                await msg.edit(content=content)

            logger.info(f"Post {post_id} editado")

            return {
                "post_id": post_id,
                "title": thread.name,
                "status": "success"
            }

        return {"status": "error", "error": "Post não encontrado"}
    except Exception as e:
        logger.error(f"Erro ao editar post: {e}")
        return {"status": "error", "error": str(e)}


UPDATE_FORUM_POST_TOOL = {
    "name": "update_forum_post",
    "description": "Edit a forum post title or content.",
    "inputSchema": {
        "type": "object",
        "properties": {
            "post_id": {"type": "string", "description": "Post/thread ID"},
            "title": {"type": "string", "description": "New post title"},
            "content": {"type": "string", "description": "New post content"},
        },
        "required": ["post_id"],
    },
}


async def handle_close_forum_post(
    discord_service: DiscordService,
    args: dict[str, Any]
) -> dict[str, Any]:
    """
    Fecha um post de fórum (marca como resolvido/locked).

    Args:
        discord_service: Instância do DiscordService
        args: {post_id, locked, archived}

    Returns:
        Dict com post_id, status
    """
    post_id = args.get("post_id")
    locked = args.get("locked", True)
    archived = args.get("archived", False)

    if not post_id:
        return {"status": "error", "error": "post_id é obrigatório"}

    try:
        thread = await discord_service._client.fetch_channel(int(post_id))

        # Editar thread
        await thread.edit(locked=locked, archived=archived)

        logger.info(f"Post {post_id} fechado (locked={locked}, archived={archived})")

        return {
            "post_id": post_id,
            "locked": locked,
            "archived": archived,
            "status": "success"
        }
    except Exception as e:
        logger.error(f"Erro ao fechar post: {e}")
        return {"status": "error", "error": str(e)}


CLOSE_FORUM_POST_TOOL = {
    "name": "close_forum_post",
    "description": "Close a forum post (lock and optionally archive).",
    "inputSchema": {
        "type": "object",
        "properties": {
            "post_id": {"type": "string", "description": "Post/thread ID"},
            "locked": {"type": "boolean", "default": True, "description": "Lock the post"},
            "archived": {"type": "boolean", "default": False, "description": "Archive the post"},
        },
        "required": ["post_id"],
    },
}


# =============================================================================
# MODERAÇÃO DE FÓRUNS
# =============================================================================

async def handle_archive_forum(
    discord_service: DiscordService,
    args: dict[str, Any]
) -> dict[str, Any]:
    """
    Arquiva um canal de fórum.

    Args:
        discord_service: Instância do DiscordService
        args: {forum_id}

    Returns:
        Dict com forum_id, status
    """
    forum_id = args.get("forum_id")

    if not forum_id:
        return {"status": "error", "error": "forum_id é obrigatório"}

    try:
        channel = await discord_service._client.fetch_channel(int(forum_id))
        await channel.edit(archived=True)

        logger.info(f"Fórum {forum_id} arquivado")

        return {
            "forum_id": forum_id,
            "archived": True,
            "status": "success"
        }
    except Exception as e:
        logger.error(f"Erro ao arquivar fórum: {e}")
        return {"status": "error", "error": str(e)}


ARCHIVE_FORUM_TOOL = {
    "name": "archive_forum",
    "description": "Archive a Discord forum channel.",
    "inputSchema": {
        "type": "object",
        "properties": {
            "forum_id": {"type": "string", "description": "Forum channel ID"},
        },
        "required": ["forum_id"],
    },
}


async def handle_delete_forum(
    discord_service: DiscordService,
    args: dict[str, Any]
) -> dict[str, Any]:
    """
    Deleta um canal de fórum.

    Args:
        discord_service: Instância do DiscordService
        args: {forum_id, confirm}

    Returns:
        Dict com forum_id, status
    """
    forum_id = args.get("forum_id")
    confirm = args.get("confirm", False)

    if not forum_id:
        return {"status": "error", "error": "forum_id é obrigatório"}

    if not confirm:
        return {
            "status": "error",
            "error": "confirm=true é obrigatório para deletar (proteção contra acidentes)"
        }

    try:
        channel = await discord_service._client.fetch_channel(int(forum_id))
        await channel.delete()

        logger.info(f"Fórum {forum_id} deletado")

        return {
            "forum_id": forum_id,
            "deleted": True,
            "status": "success"
        }
    except Exception as e:
        logger.error(f"Erro ao deletar fórum: {e}")
        return {"status": "error", "error": str(e)}


DELETE_FORUM_TOOL = {
    "name": "delete_forum",
    "description": "Delete a Discord forum channel (requires confirm=true for safety).",
    "inputSchema": {
        "type": "object",
        "properties": {
            "forum_id": {"type": "string", "description": "Forum channel ID"},
            "confirm": {"type": "boolean", "description": "Must be true to confirm deletion"},
        },
        "required": ["forum_id", "confirm"],
    },
}


async def handle_update_forum_settings(
    discord_service: DiscordService,
    args: dict[str, Any]
) -> dict[str, Any]:
    """
    Atualiza configurações de um canal de fórum.

    Args:
        discord_service: Instância do DiscordService
        args: {forum_id, name, layout, default_sort_order}

    Returns:
        Dict com forum_id, status
    """
    forum_id = args.get("forum_id")
    name = args.get("name")
    layout = args.get("layout")
    default_sort_order = args.get("default_sort_order")

    if not forum_id:
        return {"status": "error", "error": "forum_id é obrigatório"}

    try:
        channel = await discord_service._client.fetch_channel(int(forum_id))

        # Preparar kwargs apenas com valores fornecidos
        kwargs = {}
        if name is not None:
            kwargs["name"] = name
        if layout is not None:
            # Discord usa layout_type, não layout
            kwargs["layout_type"] = layout
        if default_sort_order is not None:
            kwargs["default_sort_order"] = default_sort_order

        if not kwargs:
            return {"status": "error", "error": "Pelo menos um campo deve ser fornecido"}

        await channel.edit(**kwargs)

        logger.info(f"Fórum {forum_id} atualizado: {kwargs}")

        return {
            "forum_id": forum_id,
            "updated_fields": list(kwargs.keys()),
            "status": "success"
        }
    except Exception as e:
        logger.error(f"Erro ao atualizar fórum: {e}")
        return {"status": "error", "error": str(e)}


UPDATE_FORUM_SETTINGS_TOOL = {
    "name": "update_forum_settings",
    "description": "Update settings for a Discord forum channel (name, layout, sort order).",
    "inputSchema": {
        "type": "object",
        "properties": {
            "forum_id": {"type": "string", "description": "Forum channel ID"},
            "name": {"type": "string", "description": "New forum name"},
            "layout": {"type": "string", "enum": ["classic", "list"], "description": "Forum layout"},
            "default_sort_order": {"type": "integer", "description": "Default sort order (0=recent, 1=created)"},
        },
        "required": ["forum_id"],
    },
}


# =============================================================================
# TODAS AS TOOLS
# =============================================================================

ALL_FORUM_TOOLS = [
    (handle_create_forum, TOOL_DEFINITION),
    (handle_list_forum_posts, LIST_FORUM_POSTS_TOOL),
    (handle_create_forum_post, CREATE_FORUM_POST_TOOL),
    (handle_get_forum_post, GET_FORUM_POST_TOOL),
    (handle_add_forum_comment, ADD_FORUM_COMMENT_TOOL),
    (handle_list_forum_comments, LIST_FORUM_COMMENTS_TOOL),
    (handle_update_forum_post, UPDATE_FORUM_POST_TOOL),
    (handle_close_forum_post, CLOSE_FORUM_POST_TOOL),
    (handle_archive_forum, ARCHIVE_FORUM_TOOL),
    (handle_delete_forum, DELETE_FORUM_TOOL),
    (handle_update_forum_settings, UPDATE_FORUM_SETTINGS_TOOL),
]

ALL_FORUM_TOOL_DEFINITIONS = [tool_def for _, tool_def in ALL_FORUM_TOOLS]
