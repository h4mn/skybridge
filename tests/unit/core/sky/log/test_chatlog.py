# coding: utf-8
"""
Testes para ChatLog widget.

DOC: openspec/changes/chatlog-2-0-refactor/specs/chatlog/spec.md
TDD: Red → Green → Refactor
"""

import logging
from collections import deque
from datetime import datetime

from textual.app import App

from core.sky.log.chatlog import ChatLog, ChatLogConfig
from core.sky.log.entry import LogEntry
from core.sky.log.scope import LogScope


class ChatLogApp(App):
    """App simples para teste do ChatLog."""

    def on_mount(self) -> None:
        """Monta o ChatLog ao iniciar."""
        config = ChatLogConfig(max_entries=100)
        self.mount(ChatLog(config=config))


class TestChatLog:
    """Testa o widget ChatLog."""

    async def test_chatlog_tem_ring_buffer(self):
        """
        QUANDO ChatLog é criado
        ENTÃO possui ring buffer com maxlen configurado
        """
        # Arrange & Act
        async with ChatLogApp().run_test() as pilot:
            chatlog = pilot.app.query_one(ChatLog)

            # Assert
            assert isinstance(chatlog._entries, deque)
            assert chatlog._entries.maxlen == 100

    async def test_chatlog_implementa_log_consumer(self):
        """
        QUANDO ChatLog recebe logs via write_log
        ENTÃO entries são adicionados ao buffer
        """
        # Arrange & Act
        async with ChatLogApp().run_test() as pilot:
            chatlog = pilot.app.query_one(ChatLog)

            # Act - adiciona log
            entry = LogEntry(
                level=logging.INFO,
                message="Test message",
                timestamp=datetime.now(),
                scope=LogScope.ALL,
            )
            chatlog.write_log(entry)
            await pilot.pause()

            # Assert
            assert len(chatlog._entries) == 1
            assert chatlog._entries[0] == entry

    async def test_chatlog_respeita_filtro_nivel(self):
        """
        QUANDO filtro de nível é definido
        ENTÃO apenas entries com nível >= min_level são visíveis
        """
        # Arrange & Act
        async with ChatLogApp().run_test() as pilot:
            chatlog = pilot.app.query_one(ChatLog)

            # Act - adiciona logs de vários níveis
            entries = [
                LogEntry(logging.DEBUG, "Debug", datetime.now(), LogScope.ALL),
                LogEntry(logging.INFO, "Info", datetime.now(), LogScope.ALL),
                LogEntry(logging.ERROR, "Error", datetime.now(), LogScope.ALL),
            ]
            for entry in entries:
                chatlog.write_log(entry)

            # Define filtro para WARNING
            chatlog.set_min_level(logging.WARNING)
            await pilot.pause()

            # Assert - apenas ERROR (40 >= 30) passa
            visible = chatlog._get_visible_entries()
            assert len(visible) == 1
            assert visible[0].level == logging.ERROR

    async def test_chatlog_respeita_filtro_escopo(self):
        """
        QUANDO filtro de escopo é definido
        ENTÃO apenas entries com escopo correspondente são visíveis
        """
        # Arrange & Act
        async with ChatLogApp().run_test() as pilot:
            chatlog = pilot.app.query_one(ChatLog)

            # Act - adiciona logs de vários escopos
            entries = [
                LogEntry(logging.INFO, "API", datetime.now(), LogScope.API),
                LogEntry(logging.INFO, "Voice", datetime.now(), LogScope.VOICE),
            ]
            for entry in entries:
                chatlog.write_log(entry)

            # Define filtro para API
            chatlog.set_scope(LogScope.API)
            await pilot.pause()

            # Assert - apenas API passa
            visible = chatlog._get_visible_entries()
            assert len(visible) == 1
            assert visible[0].scope == LogScope.API


__all__ = ["TestChatLog"]
