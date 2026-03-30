# -*- coding: utf-8 -*-
"""
Tool Schemas - Pydantic DTOs para validação MCP.

Esta camada adicional fornece validação de esquema para as tools MCP,
usando Pydantic para garantir tipos e validar entrada.

DOC: DDD Migration - Presentation Layer DTOs
"""

from __future__ import annotations

from typing import Optional, List
from pydantic import BaseModel, Field


# ============================================================================
# Base Schemas
# ============================================================================

class BaseToolInput(BaseModel):
    """Base para inputs de tool."""
    chat_id: str = Field(description="Channel ID")


class BaseToolOutput(BaseModel):
    """Base para outputs de tool."""
    status: str = Field(description="success ou error")
    error: Optional[str] = Field(None, description="Mensagem de erro se status=error")


# ============================================================================
# Reply
# ============================================================================

class ReplyInput(BaseToolInput):
    """Input para tool reply."""
    content: str = Field(description="Mensagem a enviar")
    reply_to: Optional[str] = Field(None, description="Message ID para reply (threading)")
    files: Optional[List[str]] = Field(None, description="Caminhos de arquivos para anexar")


class ReplyOutput(BaseToolOutput):
    """Output para tool reply."""
    message_id: Optional[str] = Field(None, description="ID da mensagem enviada")


# ============================================================================
# Send Embed
# ============================================================================

class EmbedFieldInput(BaseModel):
    """Campo de embed."""
    name: str = Field(description="Nome do campo")
    value: str = Field(description="Valor do campo")
    inline: bool = Field(False, description="Campo inline")


class SendEmbedInput(BaseToolInput):
    """Input para tool send_embed."""
    title: str = Field(description="Título do embed")
    description: Optional[str] = Field(None, description="Descrição do embed")
    color: int = Field(3447003, description="Cor do embed (decimal)")
    fields: Optional[List[EmbedFieldInput]] = Field(None, description="Campos do embed")
    footer: Optional[str] = Field(None, description="Texto do rodapé")


class SendEmbedOutput(BaseToolOutput):
    """Output para tool send_embed."""
    message_id: Optional[str] = Field(None, description="ID da mensagem enviada")


# ============================================================================
# Send Buttons
# ============================================================================

class ButtonInput(BaseModel):
    """Configuração de botão."""
    label: str = Field(description="Texto do botão")
    style: str = Field(description="Estilo: primary, success, danger, secondary")
    custom_id: str = Field(description="ID único do botão")
    disabled: bool = Field(False, description="Botão desabilitado")


class SendButtonsInput(BaseToolInput):
    """Input para tool send_buttons."""
    title: str = Field(description="Título do embed")
    description: Optional[str] = Field(None, description="Descrição do embed")
    buttons: List[ButtonInput] = Field(description="Lista de botões")


class SendButtonsOutput(BaseToolOutput):
    """Output para tool send_buttons."""
    message_id: Optional[str] = Field(None, description="ID da mensagem enviada")


# ============================================================================
# Send Progress
# ============================================================================

class SendProgressInput(BaseToolInput):
    """Input para tool send_progress."""
    title: str = Field(description="Título do progresso")
    current: int = Field(0, description="Valor atual")
    total: int = Field(100, description="Valor total (100%)")
    status: Optional[str] = Field(None, description="Status adicional")
    tracking_id: Optional[str] = Field(None, description="ID para rastrear e atualizar mesma mensagem")


class SendProgressOutput(BaseToolOutput):
    """Output para tool send_progress."""
    message_id: Optional[str] = Field(None, description="ID da mensagem")
    percentage: int = Field(description="Porcentagem atual")


# ============================================================================
# Send Menu
# ============================================================================

class MenuOptionInput(BaseModel):
    """Opção de menu."""
    label: str = Field(description="Texto da opção")
    value: str = Field(description="Valor interno da opção")
    description: Optional[str] = Field(None, description="Descrição da opção")
    emoji: Optional[str] = Field(None, description="Emoji da opção")


class SendMenuInput(BaseToolInput):
    """Input para tool send_menu."""
    placeholder: str = Field("Selecione uma opção...", description="Texto placeholder")
    options: List[MenuOptionInput] = Field(description="Lista de opções")


class SendMenuOutput(BaseToolOutput):
    """Output para tool send_menu."""
    message_id: Optional[str] = Field(None, description="ID da mensagem enviada")


# ============================================================================
# Update Component
# ============================================================================

class UpdateComponentInput(BaseModel):
    """Input para tool update_component."""
    chat_id: str = Field(description="Channel ID")
    message_id: str = Field(description="Message ID para atualizar")
    new_text: Optional[str] = Field(None, description="Novo conteúdo da mensagem")
    disable_buttons: bool = Field(False, description="Remove botões da mensagem")
    new_progress_percentage: Optional[int] = Field(None, description="Nova porcentagem (0-100)")
    new_progress_status: Optional[str] = Field(None, description="Novo status: running, success, error")


class UpdateComponentOutput(BaseToolOutput):
    """Output para tool update_component."""
    message_id: Optional[str] = Field(None, description="ID da mensagem atualizada")


# ============================================================================
# Fetch Messages
# ============================================================================

class FetchMessagesInput(BaseToolInput):
    """Input para tool fetch_messages."""
    limit: int = Field(20, description="Número máximo de mensagens")


class MessageInfo(BaseModel):
    """Informação de mensagem."""
    id: str
    content: str
    author: str
    timestamp: str
    attachment_count: int = Field(0, description="Número de anexos")


class FetchMessagesOutput(BaseToolOutput):
    """Output para tool fetch_messages."""
    messages: List[MessageInfo] = Field(description="Lista de mensagens")


# ============================================================================
# React
# ============================================================================

class ReactInput(BaseModel):
    """Input para tool react."""
    chat_id: str = Field(description="Channel ID")
    message_id: str = Field(description="Message ID")
    emoji: str = Field(description="Emoji a adicionar (Unicode ou custom)")


class ReactOutput(BaseToolOutput):
    """Output para tool react."""
    # Apenas status/error


# ============================================================================
# Edit Message
# ============================================================================

class EditMessageInput(BaseModel):
    """Input para tool edit_message."""
    chat_id: str = Field(description="Channel ID")
    message_id: str = Field(description="Message ID para editar")
    content: Optional[str] = Field(None, description="Novo conteúdo")


class EditMessageOutput(BaseToolOutput):
    """Output para tool edit_message."""
    message_id: Optional[str] = Field(None, description="ID da mensagem editada")


# ============================================================================
# Create Thread
# ============================================================================

class CreateThreadInput(BaseModel):
    """Input para tool create_thread."""
    chat_id: str = Field(description="Channel ID")
    message_id: str = Field(description="Message ID para criar thread")
    name: str = Field(description="Nome da thread")
    auto_archive_duration: int = Field(1440, description="Duração em minutos: 60, 1440, 4320, 10080")


class CreateThreadOutput(BaseToolOutput):
    """Output para tool create_thread."""
    thread_id: Optional[str] = Field(None, description="ID da thread criada")
    thread_name: Optional[str] = Field(None, description="Nome da thread")


# ============================================================================
# List Threads
# ============================================================================

class ListThreadsInput(BaseToolInput):
    """Input para tool list_threads."""
    include_archived: bool = Field(False, description="Incluir threads arquivadas")


class ThreadInfo(BaseModel):
    """Informação de thread."""
    id: str
    name: str
    message_count: int
    created_at: str
    archived: bool
    parent_channel_id: str


class ListThreadsOutput(BaseToolOutput):
    """Output para tool list_threads."""
    threads: List[ThreadInfo] = Field(description="Lista de threads")
    total: int = Field(description="Total de threads")


# ============================================================================
# Archive Thread
# ============================================================================

class ArchiveThreadInput(BaseModel):
    """Input para tool archive_thread."""
    thread_id: str = Field(description="ID da thread")


class ArchiveThreadOutput(BaseToolOutput):
    """Output para tool archive_thread."""
    thread_id: Optional[str] = Field(None, description="ID da thread arquivada")
    archived: bool = Field(True, description="Confirmação de arquivo")


# ============================================================================
# Rename Thread
# ============================================================================

class RenameThreadInput(BaseModel):
    """Input para tool rename_thread."""
    thread_id: str = Field(description="ID da thread")
    name: str = Field(description="Novo nome")


class RenameThreadOutput(BaseToolOutput):
    """Output para tool rename_thread."""
    thread_id: Optional[str] = Field(None, description="ID da thread renomeada")
    old_name: Optional[str] = Field(None, description="Nome antigo")
    new_name: Optional[str] = Field(None, description="Novo nome")


# ============================================================================
# Download Attachment
# ============================================================================

class DownloadAttachmentInput(BaseModel):
    """Input para tool download_attachment."""
    chat_id: str = Field(description="Channel ID")
    message_id: str = Field(description="Message ID com anexos")


class DownloadedFileInfo(BaseModel):
    """Informação de arquivo baixado."""
    path: str = Field(description="Caminho do arquivo")
    name: str = Field(description="Nome original")
    content_type: Optional[str] = Field(None, description="Content-Type")
    size_kb: int = Field(description="Tamanho em KB")


class DownloadAttachmentOutput(BaseToolOutput):
    """Output para tool download_attachment."""
    files: List[DownloadedFileInfo] = Field(description="Arquivos baixados")
    count: int = Field(description="Número de arquivos")
