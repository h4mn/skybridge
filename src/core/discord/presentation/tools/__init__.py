# -*- coding: utf-8 -*-
"""Presentation Tools - MCP Tools da camada de apresentação Discord."""

from .reply import handle_reply, TOOL_DEFINITION as REPLY_TOOL
from .send_embed import handle_send_embed, TOOL_DEFINITION as SEND_EMBED_TOOL
from .send_buttons import handle_send_buttons, TOOL_DEFINITION as SEND_BUTTONS_TOOL
from .send_progress import handle_send_progress, TOOL_DEFINITION as SEND_PROGRESS_TOOL
from .send_menu import handle_send_menu, TOOL_DEFINITION as SEND_MENU_TOOL
from .update_component import handle_update_component, TOOL_DEFINITION as UPDATE_COMPONENT_TOOL
from .fetch_messages import handle_fetch_messages, TOOL_DEFINITION as FETCH_MESSAGES_TOOL
from .react import handle_react, TOOL_DEFINITION as REACT_TOOL
from .edit_message import handle_edit_message, TOOL_DEFINITION as EDIT_MESSAGE_TOOL
from .create_thread import handle_create_thread, TOOL_DEFINITION as CREATE_THREAD_TOOL
from .list_threads import handle_list_threads, TOOL_DEFINITION as LIST_THREADS_TOOL
from .archive_thread import handle_archive_thread, TOOL_DEFINITION as ARCHIVE_THREAD_TOOL
from .rename_thread import handle_rename_thread, TOOL_DEFINITION as RENAME_THREAD_TOOL
from .download_attachment import handle_download_attachment, TOOL_DEFINITION as DOWNLOAD_ATTACHMENT_TOOL
from .forum_tools import (
    handle_create_forum, TOOL_DEFINITION as CREATE_FORUM_TOOL,
    handle_list_forum_posts, LIST_FORUM_POSTS_TOOL,
    handle_create_forum_post, CREATE_FORUM_POST_TOOL,
    handle_get_forum_post, GET_FORUM_POST_TOOL,
    handle_add_forum_comment, ADD_FORUM_COMMENT_TOOL,
    handle_list_forum_comments, LIST_FORUM_COMMENTS_TOOL,
    handle_update_forum_post, UPDATE_FORUM_POST_TOOL,
    handle_close_forum_post, CLOSE_FORUM_POST_TOOL,
    handle_archive_forum, ARCHIVE_FORUM_TOOL,
    handle_delete_forum, DELETE_FORUM_TOOL,
    handle_update_forum_settings, UPDATE_FORUM_SETTINGS_TOOL,
)
from .inbox import handle_inbox_add, TOOL_DEFINITION as INBOX_ADD_TOOL

__all__ = [
    "handle_reply",
    "handle_send_embed",
    "handle_send_buttons",
    "handle_send_progress",
    "handle_send_menu",
    "handle_update_component",
    "handle_fetch_messages",
    "handle_react",
    "handle_edit_message",
    "handle_create_thread",
    "handle_list_threads",
    "handle_archive_thread",
    "handle_rename_thread",
    "handle_download_attachment",
    "handle_create_forum",
    "handle_list_forum_posts",
    "handle_create_forum_post",
    "handle_get_forum_post",
    "handle_add_forum_comment",
    "handle_list_forum_comments",
    "handle_update_forum_post",
    "handle_close_forum_post",
    "handle_archive_forum",
    "handle_delete_forum",
    "handle_update_forum_settings",
    "handle_inbox_add",
    "REPLY_TOOL",
    "SEND_EMBED_TOOL",
    "SEND_BUTTONS_TOOL",
    "SEND_PROGRESS_TOOL",
    "SEND_MENU_TOOL",
    "UPDATE_COMPONENT_TOOL",
    "FETCH_MESSAGES_TOOL",
    "REACT_TOOL",
    "EDIT_MESSAGE_TOOL",
    "CREATE_THREAD_TOOL",
    "LIST_THREADS_TOOL",
    "ARCHIVE_THREAD_TOOL",
    "RENAME_THREAD_TOOL",
    "DOWNLOAD_ATTACHMENT_TOOL",
    "CREATE_FORUM_TOOL",
    "LIST_FORUM_POSTS_TOOL",
    "CREATE_FORUM_POST_TOOL",
    "GET_FORUM_POST_TOOL",
    "ADD_FORUM_COMMENT_TOOL",
    "LIST_FORUM_COMMENTS_TOOL",
    "UPDATE_FORUM_POST_TOOL",
    "CLOSE_FORUM_POST_TOOL",
    "ARCHIVE_FORUM_TOOL",
    "DELETE_FORUM_TOOL",
    "UPDATE_FORUM_SETTINGS_TOOL",
]


# Mapeamento nome → handler para MCP Server
TOOL_HANDLERS = {
    "reply": (handle_reply, REPLY_TOOL),
    "send_embed": (handle_send_embed, SEND_EMBED_TOOL),
    "send_buttons": (handle_send_buttons, SEND_BUTTONS_TOOL),
    "send_progress": (handle_send_progress, SEND_PROGRESS_TOOL),
    "send_menu": (handle_send_menu, SEND_MENU_TOOL),
    "update_component": (handle_update_component, UPDATE_COMPONENT_TOOL),
    "fetch_messages": (handle_fetch_messages, FETCH_MESSAGES_TOOL),
    "react": (handle_react, REACT_TOOL),
    "edit_message": (handle_edit_message, EDIT_MESSAGE_TOOL),
    "create_thread": (handle_create_thread, CREATE_THREAD_TOOL),
    "list_threads": (handle_list_threads, LIST_THREADS_TOOL),
    "archive_thread": (handle_archive_thread, ARCHIVE_THREAD_TOOL),
    "rename_thread": (handle_rename_thread, RENAME_THREAD_TOOL),
    "download_attachment": (handle_download_attachment, DOWNLOAD_ATTACHMENT_TOOL),
    "create_forum": (handle_create_forum, CREATE_FORUM_TOOL),
    "list_forum_posts": (handle_list_forum_posts, LIST_FORUM_POSTS_TOOL),
    "create_forum_post": (handle_create_forum_post, CREATE_FORUM_POST_TOOL),
    "get_forum_post": (handle_get_forum_post, GET_FORUM_POST_TOOL),
    "add_forum_comment": (handle_add_forum_comment, ADD_FORUM_COMMENT_TOOL),
    "list_forum_comments": (handle_list_forum_comments, LIST_FORUM_COMMENTS_TOOL),
    "update_forum_post": (handle_update_forum_post, UPDATE_FORUM_POST_TOOL),
    "close_forum_post": (handle_close_forum_post, CLOSE_FORUM_POST_TOOL),
    "archive_forum": (handle_archive_forum, ARCHIVE_FORUM_TOOL),
    "delete_forum": (handle_delete_forum, DELETE_FORUM_TOOL),
    "update_forum_settings": (handle_update_forum_settings, UPDATE_FORUM_SETTINGS_TOOL),
    "inbox_add": (handle_inbox_add, INBOX_ADD_TOOL),
}


def get_tool_definitions():
    """Retorna todas as definições de tools para registro MCP."""
    return [
        REPLY_TOOL,
        SEND_EMBED_TOOL,
        SEND_BUTTONS_TOOL,
        SEND_PROGRESS_TOOL,
        SEND_MENU_TOOL,
        UPDATE_COMPONENT_TOOL,
        FETCH_MESSAGES_TOOL,
        REACT_TOOL,
        EDIT_MESSAGE_TOOL,
        CREATE_THREAD_TOOL,
        LIST_THREADS_TOOL,
        ARCHIVE_THREAD_TOOL,
        RENAME_THREAD_TOOL,
        DOWNLOAD_ATTACHMENT_TOOL,
        CREATE_FORUM_TOOL,
        LIST_FORUM_POSTS_TOOL,
        CREATE_FORUM_POST_TOOL,
        GET_FORUM_POST_TOOL,
        ADD_FORUM_COMMENT_TOOL,
        LIST_FORUM_COMMENTS_TOOL,
        UPDATE_FORUM_POST_TOOL,
        CLOSE_FORUM_POST_TOOL,
        ARCHIVE_FORUM_TOOL,
        DELETE_FORUM_TOOL,
        UPDATE_FORUM_SETTINGS_TOOL,
        INBOX_ADD_TOOL,
    ]
