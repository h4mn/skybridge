# coding: utf-8
"""
Testes para LogCopier widget.

DOC: openspec/changes/chatlog-2-0-refactor/specs/log-copier/spec.md
TDD: Red → Green → Refactor
"""

from unittest.mock import patch

from textual.app import App
from textual.widgets import Button

from core.sky.log.widgets.copier import LogCopier


class LogCopierApp(App):
    """App simples para teste do LogCopier."""

    def on_mount(self) -> None:
        """Monta o LogCopier ao iniciar."""
        self.mount(LogCopier())


class TestLogCopier:
    """Testa o widget LogCopier."""

    async def test_log_copier_tem_botao_copiar(self):
        """
        QUANDO LogCopier é criado
        ENTÃO possui botão com emoji de clipboard
        """
        # Arrange & Act
        async with LogCopierApp().run_test() as pilot:
            copier = pilot.app.query_one(LogCopier)
            button = pilot.app.query_one(Button)

            # Assert - emoji de clipboard
            assert "📋" in button.label

    async def test_log_copier_copia_entries_visiveis(self):
        """
        QUANDO botão é pressionado
        ENTÃO copia entries visíveis para clipboard
        """
        # Arrange & Act
        async with LogCopierApp().run_test() as pilot:
            copier = pilot.app.query_one(LogCopier)

            # Mock do clipboard
            with patch("core.sky.log.widgets.copier.copy_to_clipboard", return_value=True) as mock_copy:
                # Define entries para copiar
                from datetime import datetime
                import logging
                from core.sky.log.entry import LogEntry
                from core.sky.log.scope import LogScope

                entries = [
                    LogEntry(logging.INFO, "Test 1", datetime.now(), LogScope.ALL),
                    LogEntry(logging.ERROR, "Test 2", datetime.now(), LogScope.API),
                ]

                copier._visible_entries = entries

                # Act - chama on_press diretamente
                copier.on_press()

                # Aguarda timer de restore
                await pilot.pause()

                # Assert - clipboard foi chamado
                mock_copy.assert_called_once()
                copied_text = mock_copy.call_args[0][0]
                assert "Test 1" in copied_text
                assert "Test 2" in copied_text


__all__ = ["TestLogCopier"]
