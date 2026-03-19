# coding: utf-8
"""
Testes para LogFilter widget.

DOC: openspec/changes/chatlog-2-0-refactor/specs/log-filter/spec.md
TDD: Red → Green → Refactor
"""

import logging

from core.sky.log.scope import LogScope
from core.sky.log.widgets.filter import FilterChanged, LogFilter, LevelButton
from textual.app import App

from textual.widgets import Button


class LogFilterApp(App):
    """App simples para teste do LogFilter."""

    def on_mount(self) -> None:
        """Monta o LogFilter ao iniciar."""
        self.mount(LogFilter())


class TestLogFilter:
    """Testa o widget LogFilter."""

    async def test_log_filter_estado_inicial_eh_all(self):
        """
        QUANDO LogFilter é criado
        ENTÃO nível ALL está selecionado (mostra todas as mensagens)
        """
        # Arrange & Act
        async with LogFilterApp().run_test() as pilot:
            log_filter = pilot.app.query_one(LogFilter)

            # Assert - estado inicial é ALL (NOTSET = 0)
            assert log_filter._current_level == logging.NOTSET

            # Botão ALL está selecionado
            all_btn = pilot.app.query_one("#level-0", LevelButton)
            assert "selected" in all_btn.classes

    async def test_log_filter_tem_botoes_nivel(self):
        """
        QUANDO LogFilter é criado
        ENTÃO possui botões para todos os níveis de logging com emojis
        """
        # Arrange & Act
        async with LogFilterApp().run_test() as pilot:
            # Assert - verifica existência dos botões de nível
            app = pilot.app
            level_buttons = app.query(LevelButton)
            assert len(level_buttons) == 6  # ALL, DEBUG, INFO, WARN, ERROR, CRIT

            # Verifica labels (emojis)
            labels = {btn.label for btn in level_buttons}
            assert "🌐" in labels  # ALL
            assert "🐛" in labels  # DEBUG
            assert "ℹ️" in labels  # INFO
            assert "⚠️" in labels  # WARNING
            assert "❌" in labels  # ERROR
            assert "🔥" in labels  # CRITICAL

    async def test_log_filter_atualiza_estado_ao_clicar(self):
        """
        QUANDO um botão de nível é pressionado
        ENTÃO atualiza o estado interno
        """
        # Arrange & Act
        async with LogFilterApp().run_test() as pilot:
            log_filter = pilot.app.query_one(LogFilter)

            # Act - clica no botão ERROR
            error_btn = pilot.app.query_one("#level-40", LevelButton)
            await pilot.click(error_btn)
            await pilot.pause()

            # Assert - estado foi atualizado
            assert log_filter._current_level == logging.ERROR

            # Botão ERROR está selecionado
            assert "selected" in error_btn.classes

    async def test_log_filter_set_level(self):
        """
        QUANDO set_level() é chamado
        ENTÃO atualiza o nível selecionado
        """
        # Arrange & Act
        async with LogFilterApp().run_test() as pilot:
            log_filter = pilot.app.query_one(LogFilter)

            # Act
            log_filter.set_level(logging.ERROR)
            await pilot.pause()

            # Assert - nível foi atualizado
            assert log_filter._current_level == logging.ERROR

            # Botão ERROR está selecionado
            error_btn = log_filter.query_one("#level-40", LevelButton)
            assert "selected" in error_btn.classes

    async def test_log_filter_clear_filters(self):
        """
        QUANDO clear_filters() é chamado
        ENTÃO reseta nível para ALL
        """
        # Arrange & Act
        async with LogFilterApp().run_test() as pilot:
            log_filter = pilot.app.query_one(LogFilter)

            # Define filtro não-ALL
            log_filter.set_level(logging.ERROR)
            await pilot.pause()

            # Act - reseta filtros
            log_filter.clear_filters()
            await pilot.pause()

            # Assert - filtro resetado
            assert log_filter._current_level == logging.NOTSET  # ALL

            # Botão ALL está selecionado
            all_btn = log_filter.query_one("#level-0", LevelButton)
            assert "selected" in all_btn.classes


__all__ = ["TestLogFilter"]
