# -*- coding: utf-8 -*-
"""
Testes unitários para ButtonClickedEvent.

DOC: openspec/changes/discord-ddd-migration/specs/discord-domain/spec.md
"""

from __future__ import annotations

from datetime import datetime

import pytest

from src.core.discord.domain.events import ButtonClickedEvent


class TestButtonClickedEvent:
    """
    Testa ButtonClickedEvent.

    Evento de domínio emitido quando usuário clica em botão Discord.
    """

    def test_criar_evento_com_factory_method(self):
        """
        DOC: specs/discord-domain/spec.md
        Scenario: Criar evento com dados válidos

        WHEN ButtonClickedEvent.create() é chamado com dados válidos
        THEN SHALL criar evento com todos os campos preenchidos
        """
        event = ButtonClickedEvent.create(
            interaction_id="interaction-123",
            channel_id="987654321",
            message_id="456789123",
            user_id="111222333",
            user_name="TestUser",
            button_label="Confirmar",
            button_custom_id="ordem_confirm",
        )

        assert event.interaction_id == "interaction-123"
        assert event.channel_id == "987654321"
        assert event.message_id == "456789123"
        assert event.user_id == "111222333"
        assert event.user_name == "TestUser"
        assert event.button_label == "Confirmar"
        assert event.button_custom_id == "ordem_confirm"
        assert event.event_type == "ButtonClickedEvent"
        assert isinstance(event.occurred_at, datetime)

    def test_to_dict_serializa_corretamente(self):
        """
        DOC: specs/discord-domain/spec.md
        Scenario: Serializar evento para dict

        WHEN to_dict() é chamado
        THEN SHALL retornar dicionário com todos os campos
        """
        event = ButtonClickedEvent.create(
            interaction_id="interaction-123",
            channel_id="987654321",
            message_id="456789123",
            user_id="111222333",
            user_name="TestUser",
            button_label="Confirmar",
            button_custom_id="ordem_confirm",
        )

        data = event.to_dict()

        assert data["interaction_id"] == "interaction-123"
        assert data["channel_id"] == "987654321"
        assert data["message_id"] == "456789123"
        assert data["user_id"] == "111222333"
        assert data["user_name"] == "TestUser"
        assert data["button_label"] == "Confirmar"
        assert data["button_custom_id"] == "ordem_confirm"
        assert data["event_type"] == "ButtonClickedEvent"

    def test_from_dict_deserializa_corretamente(self):
        """
        DOC: specs/discord-domain/spec.md
        Scenario: Deserializar evento de dict

        WHEN from_dict() é chamado com dicionário válido
        THEN SHALL restaurar evento com todos os campos
        """
        data = {
            "event_id": "evt-789",
            "occurred_at": "2026-03-29T12:00:00",
            "event_type": "ButtonClickedEvent",
            "interaction_id": "interaction-123",
            "channel_id": "987654321",
            "message_id": "456789123",
            "user_id": "111222333",
            "user_name": "TestUser",
            "button_label": "Confirmar",
            "button_custom_id": "ordem_confirm",
        }

        event = ButtonClickedEvent.from_dict(data)

        assert event.event_id == "evt-789"
        assert event.interaction_id == "interaction-123"
        assert event.channel_id == "987654321"
        assert event.message_id == "456789123"
        assert event.user_id == "111222333"
        assert event.user_name == "TestUser"
        assert event.button_label == "Confirmar"
        assert event.button_custom_id == "ordem_confirm"
        assert event.event_type == "ButtonClickedEvent"

    def test_serializacao_simetrica(self):
        """
        DOC: specs/discord-domain/spec.md
        Scenario: to_dict() -> from_dict() deve preservar dados

        WHEN evento é serializado e depois deserializado
        THEN SHALL criar evento igual ao original
        """
        original = ButtonClickedEvent.create(
            interaction_id="interaction-123",
            channel_id="987654321",
            message_id="456789123",
            user_id="111222333",
            user_name="TestUser",
            button_label="Cancelar",
            button_custom_id="ordem_cancel",
        )

        data = original.to_dict()
        restored = ButtonClickedEvent.from_dict(data)

        assert restored.interaction_id == original.interaction_id
        assert restored.channel_id == original.channel_id
        assert restored.message_id == original.message_id
        assert restored.user_id == original.user_id
        assert restored.user_name == original.user_name
        assert restored.button_label == original.button_label
        assert restored.button_custom_id == original.button_custom_id
