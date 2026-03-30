# -*- coding: utf-8 -*-
"""
Testes de Tool Schemas - Pydantic DTOs.

Valida schemas de entrada/saída das tools MCP.
"""

import pytest
from pydantic import ValidationError

from src.core.discord.presentation.dto.tool_schemas import (
    ReplyInput,
    ReplyOutput,
    SendEmbedInput,
    SendProgressInput,
    CreateThreadInput,
    ListThreadsInput,
)


class TestReplySchemas:
    """Testes de schemas de reply."""

    def test_reply_input_valido(self):
        """Testa input válido de reply."""
        data = {
            "chat_id": "123456",
            "content": "Olá mundo!"
        }
        schema = ReplyInput(**data)
        assert schema.chat_id == "123456"
        assert schema.content == "Olá mundo!"

    def test_reply_input_com_reply_to(self):
        """Testa input com reply_to."""
        data = {
            "chat_id": "123456",
            "content": "Respondendo",
            "reply_to": "789012"
        }
        schema = ReplyInput(**data)
        assert schema.reply_to == "789012"

    def test_reply_output_success(self):
        """Testa output de sucesso."""
        data = {
            "status": "success",
            "message_id": "msg123"
        }
        schema = ReplyOutput(**data)
        assert schema.status == "success"
        assert schema.message_id == "msg123"


class TestSendEmbedSchemas:
    """Testes de schemas de send_embed."""

    def test_send_embed_input_minimo(self):
        """Testa input mínimo de send_embed."""
        data = {
            "chat_id": "123456",
            "title": "Título"
        }
        schema = SendEmbedInput(**data)
        assert schema.title == "Título"
        assert schema.description is None

    def test_send_embed_input_com_fields(self):
        """Testa input com campos."""
        data = {
            "chat_id": "123456",
            "title": "Portfolio",
            "fields": [
                {"name": "BTC", "value": "1.0", "inline": True},
                {"name": "USD", "value": "50000", "inline": True}
            ]
        }
        schema = SendEmbedInput(**data)
        assert len(schema.fields) == 2
        assert schema.fields[0].name == "BTC"


class TestSendProgressSchemas:
    """Testes de schemas de send_progress."""

    def test_send_progress_input_com_tracking_id(self):
        """Testa input com tracking_id."""
        data = {
            "chat_id": "123456",
            "title": "Processando",
            "current": 50,
            "total": 100,
            "tracking_id": "abc123"
        }
        schema = SendProgressInput(**data)
        assert schema.tracking_id == "abc123"
        assert schema.current == 50


class TestThreadSchemas:
    """Testes de schemas de threads."""

    def test_create_thread_input_valido(self):
        """Testa input válido de create_thread."""
        data = {
            "chat_id": "123456",
            "message_id": "789012",
            "name": "Discussão"
        }
        schema = CreateThreadInput(**data)
        assert schema.name == "Discussão"
        assert schema.auto_archive_duration == 1440

    def test_list_threads_input_com_archived(self):
        """Testa input listando threads arquivadas."""
        data = {
            "chat_id": "123456",
            "include_archived": True
        }
        schema = ListThreadsInput(**data)
        assert schema.include_archived is True
