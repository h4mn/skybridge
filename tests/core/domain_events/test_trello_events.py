# -*- coding: utf-8 -*-
"""
Testes para eventos de domínio do Trello.

Cobre DoDs relacionados:
- DoD #2: TrelloCardMovedToListEvent criado
- TrelloWebhookReceivedEvent
- TrelloCardMovedToListEvent
"""

import pytest
from datetime import datetime
from dataclasses import FrozenInstanceError

from src.core.domain_events.trello_events import (
    TrelloWebhookReceivedEvent,
    TrelloCardMovedToListEvent,
)
from src.core.domain_events.domain_event import DomainEvent


class TestTrelloWebhookReceivedEvent:
    """Testes para TrelloWebhookReceivedEvent."""

    def test_event_can_be_created(self):
        """TrelloWebhookReceivedEvent deve ser instanciável."""
        event = TrelloWebhookReceivedEvent(aggregate_id="card-123")
        assert event is not None
        assert event.aggregate_id == "card-123"

    def test_event_has_all_fields(self):
        """Evento deve ter todos os campos especificados."""
        event = TrelloWebhookReceivedEvent(
            aggregate_id="card-123",
            webhook_id="webhook-456",
            action_type="updateCard",
            card_id="card-123",
            card_name="Test Card",
            list_before_name="💡 Brainstorm",
            list_after_name="📋 A Fazer",
        )

        assert event.webhook_id == "webhook-456"
        assert event.action_type == "updateCard"
        assert event.card_id == "card-123"
        assert event.card_name == "Test Card"

    def test_event_has_default_values(self):
        """Evento deve ter valores padrão."""
        event = TrelloWebhookReceivedEvent(aggregate_id="card-123")

        assert event.webhook_id == ""
        assert event.action_type == ""
        assert event.card_id == ""
        assert event.card_name == ""

    def test_event_to_dict(self):
        """Evento deve ser serializável para dict."""
        event = TrelloWebhookReceivedEvent(
            aggregate_id="card-123",
            webhook_id="webhook-456",
            card_id="card-123",
        )

        data = event.to_dict()

        assert data["webhook_id"] == "webhook-456"
        assert data["card_id"] == "card-123"


class TestTrelloCardMovedToListEvent:
    """Testes para TrelloCardMovedToListEvent."""

    def test_event_can_be_created(self):
        """TrelloCardMovedToListEvent deve ser instanciável."""
        event = TrelloCardMovedToListEvent(aggregate_id="card-123")
        assert event is not None

    def test_event_has_all_fields(self):
        """Evento deve ter todos os campos especificados."""
        event = TrelloCardMovedToListEvent(
            aggregate_id="card-123",
            card_id="card-123",
            card_name="Test Card",
            list_name="📋 A Fazer",
            issue_number=123,
        )

        assert event.card_id == "card-123"
        assert event.card_name == "Test Card"
        assert event.list_name == "📋 A Fazer"
        assert event.issue_number == 123

    def test_event_has_default_values(self):
        """Evento deve ter valores padrão."""
        event = TrelloCardMovedToListEvent(aggregate_id="card-123")

        assert event.card_id == ""
        assert event.card_name == ""
        assert event.list_name == ""
        assert event.issue_number is None

    def test_event_to_dict(self):
        """Evento deve ser serializável para dict."""
        event = TrelloCardMovedToListEvent(
            aggregate_id="card-123",
            card_id="card-123",
            card_name="Test Card",
            list_name="📋 A Fazer",
            issue_number=123,
        )

        data = event.to_dict()

        assert data["card_id"] == "card-123"
        assert data["card_name"] == "Test Card"
        assert data["list_name"] == "📋 A Fazer"
        assert data["issue_number"] == 123

    def test_event_without_issue_number(self):
        """Evento pode ser criado sem issue_number."""
        event = TrelloCardMovedToListEvent(
            aggregate_id="card-123",
            card_id="card-123",
            card_name="Test Card",
            list_name="💡 Brainstorm",
        )

        assert event.issue_number is None

    def test_event_with_issue_number(self):
        """Evento pode ser criado com issue_number."""
        event = TrelloCardMovedToListEvent(
            aggregate_id="card-123",
            card_id="card-123",
            card_name="#123 Feature",
            list_name="📋 A Fazer",
            issue_number=123,
        )

        assert event.issue_number == 123


class TestTrelloEventsIntegration:
    """Testes de integração dos eventos Trello."""

    def test_both_events_exist(self):
        """
        DoD #2: TrelloCardMovedToListEvent criado.

        Verifica que ambos os eventos existem.
        """
        assert TrelloWebhookReceivedEvent is not None
        assert TrelloCardMovedToListEvent is not None

    def test_events_are_importable(self):
        """Eventos devem ser importáveis do módulo."""
        from src.core.domain_events import trello_events

        assert hasattr(trello_events, "TrelloWebhookReceivedEvent")
        assert hasattr(trello_events, "TrelloCardMovedToListEvent")

    def test_webhook_received_to_moved_event_flow(self):
        """
        Fluxo: TrelloWebhookReceivedEvent → TrelloCardMovedToListEvent.

        Simula o fluxo de criação de eventos quando um card é movido.
        """
        # 1. Webhook recebido
        webhook_event = TrelloWebhookReceivedEvent(
            aggregate_id="card-123",
            webhook_id="webhook-456",
            action_type="updateCard",
            card_id="card-123",
            card_name="#123 Feature",
            list_before_name="💡 Brainstorm",
            list_after_name="📋 A Fazer",
        )

        # 2. Extrai issue_number do card_name
        import re
        match = re.search(r"#(\d+)", webhook_event.card_name)
        issue_number = int(match.group(1)) if match else None

        # 3. Cria evento de movimento
        moved_event = TrelloCardMovedToListEvent(
            aggregate_id=webhook_event.card_id,
            card_id=webhook_event.card_id,
            card_name=webhook_event.card_name,
            list_name=webhook_event.list_after_name,
            issue_number=issue_number,
        )

        assert moved_event.issue_number == 123
        assert moved_event.list_name == "📋 A Fazer"


class TestTrelloEventsPrd020:
    """Testes específicos para PRD020 - Fluxo Bidirecional."""

    def test_event_represents_brainstorm_movement(self):
        """Evento deve representar movimento para 💡 Brainstorm."""
        event = TrelloWebhookReceivedEvent(
            aggregate_id="card-123",
            action_type="updateCard",
            card_id="card-123",
            card_name="#456 Research",
            list_before_name="📥 Issues",
            list_after_name="💡 Brainstorm",
        )

        assert event.list_after_name == "💡 Brainstorm"
        assert event.action_type == "updateCard"

    def test_event_represents_a_fazer_movement(self):
        """Evento deve representar movimento para 📋 A Fazer."""
        event = TrelloWebhookReceivedEvent(
            aggregate_id="card-123",
            action_type="updateCard",
            card_id="card-123",
            card_name="#789 Feature",
            list_before_name="💡 Brainstorm",
            list_after_name="📋 A Fazer",
        )

        assert event.list_after_name == "📋 A Fazer"

    def test_event_represents_publicar_movement(self):
        """Evento deve representar movimento para 🚀 Publicar."""
        event = TrelloCardMovedToListEvent(
            aggregate_id="card-123",
            card_id="card-123",
            card_name="#999 Feature",
            list_name="🚀 Publicar",
            issue_number=999,
        )

        assert event.list_name == "🚀 Publicar"
        assert event.issue_number == 999


@pytest.mark.unit
class TestTrelloEventsValidation:
    """Testes de validação dos eventos."""

    def test_webhook_received_event_creates_with_defaults(self):
        """Evento deve ser criado com aggregate_id."""
        # DomainEvent tem aggregate_id com valor padrão ""
        event = TrelloWebhookReceivedEvent()
        assert event.aggregate_id == ""

    def test_moved_event_creates_with_defaults(self):
        """Evento deve ser criado com aggregate_id."""
        # DomainEvent tem aggregate_id com valor padrão ""
        event = TrelloCardMovedToListEvent()
        assert event.aggregate_id == ""

    def test_events_preserve_card_information(self):
        """Eventos devem preservar informações do card."""
        card_id = "card-abc-123"
        card_name = "#123 Important Feature"

        webhook_event = TrelloWebhookReceivedEvent(
            aggregate_id=card_id,
            card_id=card_id,
            card_name=card_name,
        )

        moved_event = TrelloCardMovedToListEvent(
            aggregate_id=card_id,
            card_id=card_id,
            card_name=card_name,
            list_name="📋 A Fazer",
        )

        assert webhook_event.card_id == card_id
        assert webhook_event.card_name == card_name
        assert moved_event.card_id == card_id
        assert moved_event.card_name == card_name


@pytest.mark.integration
class TestTrelloEventsDoD:
    """Testes de DoD do PRD020."""

    def test_dod_2_trello_webhook_received_event_exists(self):
        """
        DoD #2: TrelloWebhookReceivedEvent criado.

        Verifica que o evento existe e pode ser instanciado.
        """
        event = TrelloWebhookReceivedEvent(aggregate_id="test")
        assert event is not None

    def test_dod_2_trello_card_moved_to_list_event_exists(self):
        """
        DoD #2: TrelloCardMovedToListEvent criado.

        Verifica que o evento existe e pode ser instanciado.
        """
        event = TrelloCardMovedToListEvent(aggregate_id="test")
        assert event is not None

    def test_events_support_all_kanban_lists(self):
        """
        DoD #5: Regras por lista Trello.

        Verifica que os eventos suportam todas as listas Kanban.
        """
        lists = [
            "💡 Brainstorm",
            "📋 A Fazer",
            "🚧 Em Andamento",
            "👁️ Em Revisão",
            "🚀 Publicar",
        ]

        for list_name in lists:
            event = TrelloCardMovedToListEvent(
                aggregate_id="card-123",
                card_id="card-123",
                card_name="Test",
                list_name=list_name,
            )

            assert event.list_name == list_name


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
