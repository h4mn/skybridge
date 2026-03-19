# coding: utf-8
"""
Testes para LogConsumer Protocol.

DOC: openspec/changes/chatlog-2-0-refactor/specs/log-consumer/spec.md
TDD: Red → Green → Refactor
"""

import logging
from datetime import datetime
from typing import TYPE_CHECKING

import pytest

from core.sky.log.entry import LogEntry
from core.sky.log.scope import LogScope

if TYPE_CHECKING:
    from core.sky.log.protocol import LogConsumer


class TestLogConsumer:
    """Testa o Protocol LogConsumer."""

    def test_log_consumer_protocol_define_write_log(self):
        """
        QUANDO uma classe implementa LogConsumer
        ENTÃO deve ter método write_log que recebe LogEntry
        """
        # Arrange & Act - implementação mínima do protocolo
        class MockConsumer:
            """Mock consumer para teste."""

            def write_log(self, entry: LogEntry) -> None:
                """Escreve log entry."""
                pass

        consumer = MockConsumer()

        # Assert - chamada funciona sem erro
        entry = LogEntry(
            level=logging.INFO,
            message="Test",
            timestamp=datetime.now(),
            scope=LogScope.ALL,
        )
        consumer.write_log(entry)  # type: ignore[arg-type]

    def test_log_consumer_nao_retorna_valor(self):
        """
        QUANDO write_log é chamado
        ENTÃO retorna None (procedimento, não função)
        """
        # Arrange
        class MockConsumer:
            def write_log(self, entry: LogEntry) -> None:
                pass

        consumer = MockConsumer()
        entry = LogEntry(
            level=logging.INFO,
            message="Test",
            timestamp=datetime.now(),
            scope=LogScope.ALL,
        )

        # Act & Assert
        result = consumer.write_log(entry)  # type: ignore[arg-type]
        assert result is None


__all__ = ["TestLogConsumer"]
