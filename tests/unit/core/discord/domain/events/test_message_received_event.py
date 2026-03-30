# -*- coding: utf-8 -*-
"""
Testes unitários para MessageReceivedEvent.

DOC: openspec/changes/discord-ddd-migration/specs/discord-domain/spec.md
"""

from __future__ import annotations

from datetime import datetime

import pytest

from src.core.discord.domain.events import MessageReceivedEvent


class TestMessageReceivedEvent:
    """
    Testa MessageReceivedEvent.

    Evento de domínio emitido quando mensagem é recebida do Discord.
    """

    def test_criar_evento_com_factory_method(self):
        """
        DOC: specs/discord-domain/spec.md
        Scenario: Criar evento com dados válidos

        WHEN MessageReceivedEvent.create() é chamado com dados válidos
        THEN SHALL criar evento com todos os campos preenchidos
        """
        event = MessageReceivedEvent.create(
            message_id="123456789",
            channel_id="987654321",
            author_id="111222333",
            author_name="TestUser",
            content="Hello, World!",
            has_attachments=True,
            attachment_count=2,
            is_dm=False,
        )

        assert event.message_id == "123456789"
        assert event.channel_id == "987654321"
        assert event.author_id == "111222333"
        assert event.author_name == "TestUser"
        assert event.content == "Hello, World!"
        assert event.has_attachments is True
        assert event.attachment_count == 2
        assert event.is_dm is False
        assert event.event_type == "MessageReceivedEvent"
        assert isinstance(event.occurred_at, datetime)
        assert len(event.event_id) > 0

    def test_criar_evento_com_valores_minimos(self):
        """
        DOC: specs/discord-domain/spec.md
        Scenario: Criar evento com campos obrigatórios

        WHEN MessageReceivedEvent.create() é chamado sem opcionais
        THEN SHALL criar evento com valores padrão
        """
        event = MessageReceivedEvent.create(
            message_id="123456789",
            channel_id="987654321",
            author_id="111222333",
            author_name="TestUser",
            content="Hello!",
        )

        assert event.has_attachments is False
        assert event.attachment_count == 0
        assert event.is_dm is False

    def test_to_dict_serializa_corretamente(self):
        """
        DOC: specs/discord-domain/spec.md
        Scenario: Serializar evento para dict

        WHEN to_dict() é chamado
        THEN SHALL retornar dicionário com todos os campos
        """
        event = MessageReceivedEvent.create(
            message_id="123456789",
            channel_id="987654321",
            author_id="111222333",
            author_name="TestUser",
            content="Hello!",
            has_attachments=True,
            attachment_count=1,
            is_dm=True,
        )

        data = event.to_dict()

        assert data["message_id"] == "123456789"
        assert data["channel_id"] == "987654321"
        assert data["author_id"] == "111222333"
        assert data["author_name"] == "TestUser"
        assert data["content"] == "Hello!"
        assert data["has_attachments"] is True
        assert data["attachment_count"] == 1
        assert data["is_dm"] is True
        assert data["event_type"] == "MessageReceivedEvent"
        assert "event_id" in data
        assert "occurred_at" in data

    def test_from_dict_deserializa_corretamente(self):
        """
        DOC: specs/discord-domain/spec.md
        Scenario: Deserializar evento de dict

        WHEN from_dict() é chamado com dicionário válido
        THEN SHALL restaurar evento com todos os campos
        """
        data = {
            "event_id": "evt-123",
            "occurred_at": "2026-03-29T10:30:00",
            "event_type": "MessageReceivedEvent",
            "message_id": "123456789",
            "channel_id": "987654321",
            "author_id": "111222333",
            "author_name": "TestUser",
            "content": "Hello!",
            "has_attachments": True,
            "attachment_count": 2,
            "is_dm": True,
        }

        event = MessageReceivedEvent.from_dict(data)

        assert event.event_id == "evt-123"
        assert event.message_id == "123456789"
        assert event.channel_id == "987654321"
        assert event.author_id == "111222333"
        assert event.author_name == "TestUser"
        assert event.content == "Hello!"
        assert event.has_attachments is True
        assert event.attachment_count == 2
        assert event.is_dm is True
        assert event.event_type == "MessageReceivedEvent"

    def test_evento_e_imutavel(self):
        """
        DOC: specs/discord-domain/spec.md
        Scenario: Verificar imutabilidade

        WHEN tentar modificar campo do evento
        THEN SHALL lançar FrozenInstanceError
        """
        event = MessageReceivedEvent.create(
            message_id="123",
            channel_id="456",
            author_id="789",
            author_name="User",
            content="Test",
        )

        with pytest.raises(Exception):  # dataclasses.FrozenInstanceError
            event.content = "Modified"

    def test_serializacao_simetrica(self):
        """
        DOC: specs/discord-domain/spec.md
        Scenario: to_dict() -> from_dict() deve preservar dados

        WHEN evento é serializado e depois deserializado
        THEN SHALL criar evento igual ao original
        """
        original = MessageReceivedEvent.create(
            message_id="123456789",
            channel_id="987654321",
            author_id="111222333",
            author_name="TestUser",
            content="Hello!",
            has_attachments=True,
            attachment_count=2,
            is_dm=True,
        )

        data = original.to_dict()
        restored = MessageReceivedEvent.from_dict(data)

        # Campos específicos
        assert restored.message_id == original.message_id
        assert restored.channel_id == original.channel_id
        assert restored.author_id == original.author_id
        assert restored.author_name == original.author_name
        assert restored.content == original.content
        assert restored.has_attachments == original.has_attachments
        assert restored.attachment_count == original.attachment_count
        assert restored.is_dm == original.is_dm

        # Metadados
        assert restored.event_id == original.event_id
        assert restored.event_type == original.event_type
