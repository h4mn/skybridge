# -*- coding: utf-8 -*-
"""
Modelos Pydantic para o Discord MCP Server.

DEPRECATED: Este módulo foi movido para presentation/dto/legacy_dto.py
Mantido aqui como re-export para compatibilidade durante a migração DDD.
"""

# Re-exporta tudo do novo local
from .presentation.dto.legacy_dto import (
    # Access Control
    DMPolicy,
    GroupPolicy,
    PendingEntry,
    Access,
    # Tool I/O
    ReplyInput,
    ReplyOutput,
    FetchMessagesInput,
    FetchedMessage,
    MessageAttachment,
    FetchMessagesOutput,
    ReactInput,
    ReactOutput,
    EditMessageInput,
    EditMessageOutput,
    DownloadAttachmentInput,
    DownloadedFile,
    DownloadAttachmentOutput,
    # Thread Tools
    CreateThreadInput,
    CreateThreadOutput,
    ListThreadsInput,
    ThreadInfo,
    ListThreadsOutput,
    ArchiveThreadInput,
    ArchiveThreadOutput,
    RenameThreadInput,
    RenameThreadOutput,
    # Rich Content Tools (DDD Presentation)
    SendEmbedInput,
    SendEmbedOutput,
    SendButtonsInput,
    SendButtonsOutput,
    SendMenuInput,
    SendMenuOutput,
    SendProgressInput,
    SendProgressOutput,
    EmbedField,
    ButtonConfig,
    MenuOption,
    # Notifications
    ChannelNotification,
    PermissionNotification,
)

__all__ = [
    # Access Control
    "DMPolicy",
    "GroupPolicy",
    "PendingEntry",
    "Access",
    # Tool I/O
    "ReplyInput",
    "ReplyOutput",
    "FetchMessagesInput",
    "FetchedMessage",
    "MessageAttachment",
    "FetchMessagesOutput",
    "ReactInput",
    "ReactOutput",
    "EditMessageInput",
    "EditMessageOutput",
    "DownloadAttachmentInput",
    "DownloadedFile",
    "DownloadAttachmentOutput",
    # Thread Tools
    "CreateThreadInput",
    "CreateThreadOutput",
    "ListThreadsInput",
    "ThreadInfo",
    "ListThreadsOutput",
    "ArchiveThreadInput",
    "ArchiveThreadOutput",
    "RenameThreadInput",
    "RenameThreadOutput",
    # Rich Content Tools (DDD Presentation)
    "SendEmbedInput",
    "SendEmbedOutput",
    "SendButtonsInput",
    "SendButtonsOutput",
    "SendMenuInput",
    "SendMenuOutput",
    "SendProgressInput",
    "SendProgressOutput",
    "EmbedField",
    "ButtonConfig",
    "MenuOption",
    # Notifications
    "ChannelNotification",
    "PermissionNotification",
]
