# coding: utf-8
"""
Testes para LogScope enum.

DOC: openspec/changes/chatlog-2-0-refactor/specs/log-consumer/spec.md
"""

import pytest

from core.sky.log.scope import LogScope


class TestLogScope:
    """Testa o enum LogScope."""

    def test_log_scope_tem_valores_definidos(self):
        """
        QUANDO LogScope é importado
        ENTÃO possui todos os escopos definidos
        """
        # Assert - verifica existência dos valores
        assert hasattr(LogScope, "ALL")
        assert hasattr(LogScope, "SYSTEM")
        assert hasattr(LogScope, "USER")
        assert hasattr(LogScope, "API")
        assert hasattr(LogScope, "DATABASE")
        assert hasattr(LogScope, "NETWORK")
        assert hasattr(LogScope, "VOICE")
        assert hasattr(LogScope, "MEMORY")

    def test_log_scope_all_eh_primeiro_valor(self):
        """
        QUANDO LogScope é criado
        ENTÃO ALL é o primeiro valor e usado como padrão
        """
        # Arrange & Act
        first_member = list(LogScope)[0]

        # Assert
        assert first_member == LogScope.ALL
        assert first_member.value == "all"

    def test_log_scope_values_sao_strings_corretas(self):
        """
        QUANDO os valores de LogScope são consultados
        ENTÃO retornam as strings corretas
        """
        assert LogScope.ALL.value == "all"
        assert LogScope.SYSTEM.value == "system"
        assert LogScope.USER.value == "user"
        assert LogScope.API.value == "api"
        assert LogScope.DATABASE.value == "database"
        assert LogScope.NETWORK.value == "network"
        assert LogScope.VOICE.value == "voice"
        assert LogScope.MEMORY.value == "memory"


__all__ = ["TestLogScope"]
