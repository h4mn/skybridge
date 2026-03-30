# -*- coding: utf-8 -*-
"""
Modelos Pydantic legados para o Discord MCP Server.

Estes DTOs foram movidos de models.py durante a migração DDD.
Mantidos para compatibilidade durante a transição.

TODO: Migrar gradualmente para presentation/dto/tool_schemas.py
"""

from __future__ import annotations

from enum import Enum
from pathlib import Path
from typing import Annotated, Literal

from pydantic import BaseModel, Field, field_validator


# =============================================================================
# Access Control Models (access.json)
# =============================================================================


class DMPolicy(str, Enum):
    """Política de acesso para mensagens privadas."""

    PAIRING = "pairing"  # Requer código de pareamento
    ALLOWLIST = "allowlist"  # Apenas usuários na lista
    DISABLED = "disabled"  # Bloqueia todas


class GroupPolicy(BaseModel):
    """Política de acesso para canais de grupo/servidor."""

    require_mention: bool = True
    allow_from: list[str] = Field(default_factory=list)


class PendingEntry(BaseModel):
    """Entrada pendente de pareamento."""

    sender_id: str
    chat_id: str  # DM channel ID
    created_at: int  # Unix timestamp (ms)
    expires_at: int  # Unix timestamp (ms)
    replies: int = 1


class Access(BaseModel):
    """Schema completo do access.json."""

    dm_policy: DMPolicy = Field(default=DMPolicy.PAIRING, alias="dmPolicy")
    allow_from: list[str] = Field(default_factory=list, alias="allowFrom")
    groups: dict[str, GroupPolicy] = Field(default_factory=dict)
    pending: dict[str, PendingEntry] = Field(default_factory=dict)
    mention_patterns: list[str] | None = Field(default=None, alias="mentionPatterns")

    # Delivery/UX config
    ack_reaction: str | None = Field(default=None, alias="ackReaction")
    reply_to_mode: Literal["off", "first", "all"] | None = Field(
        default="first", alias="replyToMode"
    )
    text_chunk_limit: int | None = Field(default=2000, alias="textChunkLimit")
    chunk_mode: Literal["length", "newline"] | None = Field(
        default="length", alias="chunkMode"
    )

    class Config:
        populate_by_name = True  # Permite usar snake_case ou camelCase


# =============================================================================
# Tool Input/Output Models
# =============================================================================


class ReplyInput(BaseModel):
    """Input para tool reply."""

    chat_id: str = Field(description="ID do canal ou thread")
    text: str = Field(description="Texto da mensagem")
    reply_to: str | None = Field(
        default=None, description="Message ID para thread/resposta"
    )
    files: list[str] | None = Field(
        default=None, description="Paths absolutos de arquivos para anexar"
    )

    @field_validator("files")
    @classmethod
    def validate_files(cls, v: list[str] | None) -> list[str] | None:
        if v is None:
            return v
        if len(v) > 10:
            raise ValueError("Discord permite no máximo 10 anexos por mensagem")
        return v


class ReplyOutput(BaseModel):
    """Output do tool reply."""

    message_id: str
    sent_count: int = 1  # Número de chunks enviados


class FetchMessagesInput(BaseModel):
    """Input para tool fetch_messages."""

    channel: str = Field(description="ID do canal")
    limit: int = Field(default=20, ge=1, le=100, description="Máximo de mensagens")


class MessageAttachment(BaseModel):
    """Informação de anexo em mensagem."""

    name: str
    content_type: str | None
    size_kb: int


class FetchedMessage(BaseModel):
    """Mensagem retornada pelo fetch_messages."""

    id: str
    author: str
    content: str
    timestamp: str
    attachments: list[MessageAttachment] = Field(default_factory=list)
    is_bot: bool = False


class FetchMessagesOutput(BaseModel):
    """Output do tool fetch_messages."""

    messages: list[FetchedMessage]
    channel_id: str


class ReactInput(BaseModel):
    """Input para tool react."""

    chat_id: str = Field(description="ID do canal")
    message_id: str = Field(description="ID da mensagem")
    emoji: str = Field(description="Emoji para reagir")


class ReactOutput(BaseModel):
    """Output do tool react."""

    success: bool = True


class EditMessageInput(BaseModel):
    """Input para tool edit_message."""

    chat_id: str = Field(description="ID do canal")
    message_id: str = Field(description="ID da mensagem do bot")
    text: str = Field(description="Novo texto da mensagem")


class EditMessageOutput(BaseModel):
    """Output do tool edit_message."""

    message_id: str
    edited: bool = True


class DownloadAttachmentInput(BaseModel):
    """Input para tool download_attachment."""

    chat_id: str = Field(description="ID do canal")
    message_id: str = Field(description="ID da mensagem com anexos")


class DownloadedFile(BaseModel):
    """Arquivo baixado."""

    path: str
    name: str
    content_type: str | None
    size_kb: int


class DownloadAttachmentOutput(BaseModel):
    """Output do tool download_attachment."""

    files: list[DownloadedFile]
    count: int


# =============================================================================
# Thread Tools Models
# =============================================================================


class CreateThreadInput(BaseModel):
    """Input para tool create_thread."""

    channel_id: str = Field(description="ID do canal onde criar a thread")
    message_id: str = Field(description="ID da mensagem base para a thread")
    name: str = Field(description="Nome da thread")
    auto_archive_duration: Literal[60, 1440, 4320, 10080] = Field(
        default=1440,
        description="Duração antes de auto-arquivar (minutos): 60=1h, 1440=24h, 4320=3d, 10080=7d",
    )


class CreateThreadOutput(BaseModel):
    """Output do tool create_thread."""

    thread_id: str
    thread_name: str
    parent_channel_id: str
    message_id: str


class ListThreadsInput(BaseModel):
    """Input para tool list_threads."""

    channel_id: str = Field(description="ID do canal")
    include_archived: bool = Field(
        default=False, description="Incluir threads arquivadas"
    )


class ThreadInfo(BaseModel):
    """Informação de uma thread."""

    id: str
    name: str
    message_count: int
    created_at: str
    archived: bool
    parent_channel_id: str


class ListThreadsOutput(BaseModel):
    """Output do tool list_threads."""

    threads: list[ThreadInfo]
    channel_id: str
    total: int


class ArchiveThreadInput(BaseModel):
    """Input para tool archive_thread."""

    thread_id: str = Field(description="ID da thread para arquivar")


class ArchiveThreadOutput(BaseModel):
    """Output do tool archive_thread."""

    thread_id: str
    archived: bool = True


class RenameThreadInput(BaseModel):
    """Input para tool rename_thread."""

    thread_id: str = Field(description="ID da thread para renomear")
    name: str = Field(description="Novo nome da thread")


class RenameThreadOutput(BaseModel):
    """Output do tool rename_thread."""

    thread_id: str
    old_name: str
    new_name: str


# =============================================================================
# MCP Notification Models
# =============================================================================


class ChannelNotification(BaseModel):
    """Notificação recebida de canal Discord."""

    content: str
    chat_id: str
    message_id: str
    user: str
    user_id: str
    ts: str
    attachment_count: int | None = None
    attachments: str | None = None  # Lista serializada de anexos


class PermissionNotification(BaseModel):
    """Notificação de permissão (permission relay)."""

    request_id: str
    behavior: Literal["allow", "deny"]


# =============================================================================
# Rich Content Tools Models (DDD Presentation Layer)
# =============================================================================


class EmbedField(BaseModel):
    """Campo para embed Discord."""

    name: str
    value: str
    inline: bool = False


class SendEmbedInput(BaseModel):
    """Input para tool send_embed."""

    chat_id: str = Field(description="ID do canal")
    title: str = Field(description="Título do embed")
    description: str | None = Field(default=None, description="Descrição do embed")
    color: int = Field(default=3447003, description="Cor do embed (decimal)")
    fields: list[EmbedField] | None = Field(default=None, description="Campos do embed")
    footer: str | None = Field(default=None, description="Texto do footer")


class SendEmbedOutput(BaseModel):
    """Output do tool send_embed."""

    message_id: str | None
    status: str
    error: str | None = None


class ButtonConfig(BaseModel):
    """Configuração de botão."""

    id: str = Field(description="ID único do botão")
    label: str = Field(description="Texto do botão")
    style: Literal["primary", "secondary", "success", "danger"] = "primary"


class SendButtonsInput(BaseModel):
    """Input para tool send_buttons."""

    chat_id: str = Field(description="ID do canal")
    title: str = Field(description="Título do embed")
    description: str | None = Field(default=None, description="Descrição do embed")
    buttons: list[ButtonConfig] = Field(description="Lista de botões")


class SendButtonsOutput(BaseModel):
    """Output do tool send_buttons."""

    message_id: str | None
    status: str
    error: str | None = None


class MenuOption(BaseModel):
    """Opção de menu suspenso."""

    label: str = Field(description="Texto visível da opção")
    value: str = Field(description="Valor retornado ao selecionar")
    description: str | None = Field(default=None, description="Descrição da opção")
    emoji: str | None = Field(default=None, description="Emoji da opção")


class SendMenuInput(BaseModel):
    """Input para tool send_menu."""

    chat_id: str = Field(description="ID do canal")
    placeholder: str = Field(default="Selecione uma opção...", description="Texto placeholder")
    options: list[MenuOption] = Field(description="Lista de opções")


class SendMenuOutput(BaseModel):
    """Output do tool send_menu."""

    message_id: str | None
    status: str
    error: str | None = None


class SendProgressInput(BaseModel):
    """Input para tool send_progress."""

    chat_id: str = Field(description="ID do canal")
    title: str = Field(default="Processando", description="Título do progresso")
    current: int = Field(description="Valor atual de progresso")
    total: int = Field(description="Valor total de progresso")
    status: str | None = Field(default=None, description="Mensagem de status")
    tracking_id: str | None = Field(default=None, description="ID para rastrear atualizações")


class SendProgressOutput(BaseModel):
    """Output do tool send_progress."""

    message_id: str | None
    status: str
    tracking_id: str | None = None
    error: str | None = None
