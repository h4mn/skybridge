# -*- coding: utf-8 -*-
"""
Testes de domínio para Kanban Context.

Valida entidades de domínio e seus comportamentos.
"""

import pytest
from datetime import datetime, timedelta

from core.kanban.domain import Card, CardStatus, CardPriority, Board


class TestCard:
    """Testes para entidade Card."""

    def test_create_card_minimal(self):
        """Testa criar card com dados mínimos."""
        card = Card(
            id="card-123",
            title="Implementar feature X",
        )

        assert card.id == "card-123"
        assert card.title == "Implementar feature X"
        assert card.description is None
        assert card.status == CardStatus.TODO
        assert card.priority == CardPriority.MEDIUM
        assert card.labels == []
        assert card.external_source == "unknown"

    def test_create_card_full(self):
        """Testa criar card com todos os campos."""
        now = datetime.utcnow()
        due = now + timedelta(days=7)

        card = Card(
            id="card-456",
            title="Fix bug Y",
            description="Corrigir erro de validação",
            status=CardStatus.IN_PROGRESS,
            priority=CardPriority.HIGH,
            labels=["bug", "urgent"],
            due_date=due,
            url="https://trello.com/c/456",
            correlation_id="job-abc-123",
            external_source="trello",
        )

        assert card.id == "card-456"
        assert card.status == CardStatus.IN_PROGRESS
        assert card.priority == CardPriority.HIGH
        assert len(card.labels) == 2
        assert card.correlation_id == "job-abc-123"
        assert card.external_source == "trello"

    def test_card_is_blocked(self):
        """Testa método is_blocked()."""
        card = Card(id="card-1", title="Test", status=CardStatus.BLOCKED)
        assert card.is_blocked() is True

        card.status = CardStatus.TODO
        assert card.is_blocked() is False

    def test_card_is_completed(self):
        """Testa método is_completed()."""
        card = Card(id="card-1", title="Test", status=CardStatus.DONE)
        assert card.is_completed() is True

        card.status = CardStatus.IN_PROGRESS
        assert card.is_completed() is False

    def test_card_is_overdue(self):
        """Testa método is_overdue()."""
        past = datetime.utcnow() - timedelta(days=1)
        future = datetime.utcnow() + timedelta(days=1)

        card = Card(id="card-1", title="Test", due_date=past)
        assert card.is_overdue() is True

        card.due_date = future
        assert card.is_overdue() is False

        card.due_date = None
        assert card.is_overdue() is False

    def test_add_label(self):
        """Testa adicionar label ao card."""
        card = Card(id="card-1", title="Test")

        card.add_label("bug")
        assert "bug" in card.labels
        assert len(card.labels) == 1

        # Adicionar duplicata não deve duplicar
        card.add_label("bug")
        assert len(card.labels) == 1

        card.add_label("urgent")
        assert len(card.labels) == 2

    def test_remove_label(self):
        """Testa remover label do card."""
        card = Card(id="card-1", title="Test", labels=["bug", "urgent"])

        result = card.remove_label("bug")
        assert result is True
        assert "bug" not in card.labels
        assert len(card.labels) == 1

        # Remover inexistente retorna False
        result = card.remove_label("inexistente")
        assert result is False


class TestBoard:
    """Testes para entidade Board."""

    def test_create_board(self):
        """Testa criar board."""
        board = Board(
            id="board-123",
            name="Sprint 1",
            url="https://trello.com/b/123",
            external_source="trello",
        )

        assert board.id == "board-123"
        assert board.name == "Sprint 1"
        assert board.url == "https://trello.com/b/123"
        assert board.external_source == "trello"


class TestCardStatus:
    """Testes para enum CardStatus."""

    def test_status_values(self):
        """Testa valores do enum."""
        assert CardStatus.TODO.value == "todo"
        assert CardStatus.IN_PROGRESS.value == "in_progress"
        assert CardStatus.DONE.value == "done"
        assert CardStatus.BLOCKED.value == "blocked"
