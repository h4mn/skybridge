# -*- coding: utf-8 -*-
"""
Testes unitários para MessageSentEvent.

DOC: openspec/changes/discord-ddd-migration/specs/discord-domain/spec.md
"""

from __future__ import annotations

from datetime import datetime

import pytest

from src.core.discord.domain.events import MessageSentEvent


class TestMessageSentEvent:
    """
    Testa MessageSentEvent.

    Evento de domínio emitido quando mensagem é enviada com sucesso.
    """

    def test_criar_evento_com_factory_method(self):
        """
        DOC: specs/discord-domain/spec.md
        Scenario: Criar evento com dados válidos

        WHEN MessageSentEvent.create() é chamado com dados válidos
        THEN SHALL criar evento com todos os campos preenchidos
        """
        event = MessageSentEvent.create(
            message_id="987654321",
            channel_id="123456789",
            content_length=150,
            chunk_count=1,
            had_attachments=False,
            reply_to=None,
        )

        assert event.message_id == "987654321"
        assert event.channel_id == "123456789"
        assert event.content_length == 150
        assert event.chunk_count == 1
        assert event.had_attachments is False
        assert event.reply_to is None
        assert event.event_type == "MessageSentEvent"
        assert isinstance(event.occurred_at, datetime)

    def test_criar_evento_com_reply_to(self):
        """
        DOC: specs/discord-domain/spec.md
        Scenario: Criar evento respondendo outra mensagem

        WHEN MessageSentEvent.create() é chamado com reply_to
        THEN SHALL criar evento com ID da mensagem original
        """
        event = MessageSentEvent.create(
            message_id="987654321",
            channel_id="123456789",
            reply_to="111222333",
        )

        assert event.reply_to == "111222333"

    def test_criar_evento_chunked(self):
        """
        DOC: specs/discord-domain/spec.md
        Scenario: Criar evento para mensagem chunkada

        WHEN MessageSentEvent.create() é chamado com chunk_count > 1
        THEN SHALL indicar que foi dividida em múltiplas partes
        """
        event = MessageSentEvent.create(
            message_id="987654321",
            channel_id="123456789",
            chunk_count=3,
        )

        assert event.chunk_count == 3

    def test_to_dict_serializa_corretamente(self):
        """
        DOC: specs/discord-domain/spec.md
        Scenario: Serializar evento para dict

        WHEN to_dict() é chamado
        THEN SHALL retornar dicionário com todos os campos
        """
        event = MessageSentEvent.create(
            message_id="987654321",
            channel_id="123456789",
            content_length=150,
            chunk_count=1,
            had_attachments=True,
            reply_to="111222333",
        )

        data = event.to_dict()

        assert data["message_id"] == "987654321"
        assert data["channel_id"] == "123456789"
        assert data["content_length"] == 150
        assert data["chunk_count"] == 1
        assert data["had_attachments"] is True
        assert data["reply_to"] == "111222333"
        assert data["event_type"] == "MessageSentEvent"

    def test_from_dict_deserializa_corretamente(self):
        """
        DOC: specs/discord-domain/spec.md
        Scenario: Deserializar evento de dict

        WHEN from_dict() é chamado com dicionário válido
        THEN SHALL restaurar evento com todos os campos
        """
        data = {
            "event_id": "evt-456",
            "occurred_at": "2026-03-29T11:00:00",
            "event_type": "MessageSentEvent",
            "message_id": "987654321",
            "channel_id": "123456789",
            "content_length": 150,
            "chunk_count": 1,
            "had_attachments": True,
            "reply_to": "111222333",
        }

        event = MessageSentEvent.from_dict(data)

        assert event.event_id == "evt-456"
        assert event.message_id == "987654321"
        assert event.channel_id == "123456789"
        assert event.content_length == 150
        assert event.chunk_count == 1
        assert event.had_attachments is True
        assert event.reply_to == "111222333"
        assert event.event_type == "MessageSentEvent"

    def test_serializacao_simetrica(self):
        """
        DOC: specs/discord-domain/spec.md
        Scenario: to_dict() -> from_dict() deve preservar dados

        WHEN evento é serializado e depois deserializado
        THEN SHALL criar evento igual ao original
        """
        original = MessageSentEvent.create(
            message_id="987654321",
            channel_id="123456789",
            content_length=5000,
            chunk_count=3,
            had_attachments=True,
            reply_to="111222333",
        )

        data = original.to_dict()
        restored = MessageSentEvent.from_dict(data)

        assert restored.message_id == original.message_id
        assert restored.channel_id == original.channel_id
        assert restored.content_length == original.content_length
        assert restored.chunk_count == original.chunk_count
        assert restored.had_attachments == original.had_attachments
        assert restored.reply_to == original.reply_to
