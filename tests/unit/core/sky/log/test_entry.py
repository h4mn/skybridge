# coding: utf-8
"""
Testes para LogEntry dataclass.

DOC: openspec/changes/chatlog-2-0-refactor/specs/log-consumer/spec.md
TDD: Red → Green → Refactor
"""

import logging
from datetime import datetime

import pytest

from core.sky.log.entry import LogEntry
from core.sky.log.scope import LogScope


class TestLogEntry:
    """Testa o dataclass LogEntry."""

    def test_log_entry_criacao_com_dados_validos(self):
        """
        QUANDO LogEntry é criado com dados válidos
        ENTÃO o entry contém os valores fornecidos
        """
        # Arrange & Act
        entry = LogEntry(
            level=logging.INFO,
            message="Test message",
            timestamp=datetime.now(),
            scope=LogScope.API,
            context={"key": "value"},
        )

        # Assert
        assert entry.level == logging.INFO
        assert entry.message == "Test message"
        assert entry.scope == LogScope.API
        assert entry.context == {"key": "value"}

    def test_log_entry_eh_imutavel(self):
        """
        QUANDO LogEntry é criado
        ENTÃO os atributos são somente leitura (frozen)
        """
        # Arrange
        entry = LogEntry(
            level=logging.INFO,
            message="Test",
            timestamp=datetime.now(),
            scope=LogScope.ALL,
        )

        # Act & Assert - tentar modificar deve falhar
        with pytest.raises(Exception):  # FrozenInstanceError ou similar
            entry.level = logging.ERROR

        with pytest.raises(Exception):
            entry.message = "Modified"

    def test_log_entry_context_eh_opcional(self):
        """
        QUANDO LogEntry é criado sem context
        ENTÃO context é None por padrão
        """
        # Arrange & Act
        entry = LogEntry(
            level=logging.INFO,
            message="Test",
            timestamp=datetime.now(),
            scope=LogScope.ALL,
        )

        # Assert
        assert entry.context is None

    def test_log_entry_matches_filter_por_nivel(self):
        """
        QUANDO entry.matches_filter é chamado com nível min_level
        ENTÃO retorna True se entry.level >= min_level
        """
        # Arrange
        entry_info = LogEntry(
            level=logging.INFO,
            message="Info message",
            timestamp=datetime.now(),
            scope=LogScope.ALL,
        )
        entry_error = LogEntry(
            level=logging.ERROR,
            message="Error message",
            timestamp=datetime.now(),
            scope=LogScope.ALL,
        )

        # Act & Assert - WARNING filtra WARNING e acima (INFO não passa)
        assert not entry_info.matches_filter(level_min=logging.WARNING, scope=LogScope.ALL)
        assert entry_error.matches_filter(level_min=logging.WARNING, scope=LogScope.ALL)

        # ERROR é maior que INFO
        assert entry_error.matches_filter(level_min=logging.INFO, scope=LogScope.ALL)

    def test_log_entry_matches_filter_por_escopo(self):
        """
        QUANDO entry.matches_filter é chamado com scope
        ENTÃO retorna True apenas se entry.scope == scope ou scope == ALL
        """
        # Arrange
        entry_api = LogEntry(
            level=logging.INFO,
            message="API message",
            timestamp=datetime.now(),
            scope=LogScope.API,
        )

        # Act & Assert - escopo ALL retorna True
        assert entry_api.matches_filter(level_min=logging.INFO, scope=LogScope.ALL)

        # Escopo específico bate
        assert entry_api.matches_filter(level_min=logging.INFO, scope=LogScope.API)

        # Escopo diferente não bate
        assert not entry_api.matches_filter(level_min=logging.INFO, scope=LogScope.VOICE)

    def test_log_entry_matches_filter_combinado(self):
        """
        QUANDO entry.matches_filter é chamado com nível e escopo
        ENTÃO retorna True apenas se AMBOS batem (AND lógico)
        """
        # Arrange
        entry = LogEntry(
            level=logging.ERROR,
            message="Voice error",
            timestamp=datetime.now(),
            scope=LogScope.VOICE,
        )

        # Act & Assert - AMBOS devem bater
        assert entry.matches_filter(level_min=logging.ERROR, scope=LogScope.VOICE)

        # Nível não bate (ERROR < CRITICAL é False)
        assert not entry.matches_filter(level_min=logging.CRITICAL, scope=LogScope.VOICE)

        # Escopo não bate
        assert not entry.matches_filter(level_min=logging.ERROR, scope=LogScope.API)

        # Nível OK mas escopo diferente
        assert not entry.matches_filter(level_min=logging.WARNING, scope=LogScope.API)


__all__ = ["TestLogEntry"]
