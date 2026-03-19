# coding: utf-8
"""
Testes para LogToolbar widget.

DOC: openspec/changes/chatlog-2-0-refactor/specs/log-toolbar/spec.md
TDD: Red → Green → Refactor
"""

from textual.app import App
from textual.containers import Vertical

from core.sky.log.widgets.toolbar import LogToolbar


class LogToolbarApp(App):
    """App simples para teste do LogToolbar."""

    def on_mount(self) -> None:
        """Monta o LogToolbar ao iniciar."""
        self.mount(LogToolbar())


class TestLogToolbar:
    """Testa o widget LogToolbar."""

    async def test_log_toolbar_agrupa_filter_search_close(self):
        """
        QUANDO LogToolbar é criado
        ENTÃO compõe Filter + Search + Copier + Close
        """
        # Arrange & Act
        async with LogToolbarApp().run_test() as pilot:
            toolbar = pilot.app.query_one(LogToolbar)

            # Assert - contém os widgets
            from core.sky.log.widgets.filter import LogFilter
            from core.sky.log.widgets.search import LogSearch
            from core.sky.log.widgets.copier import LogCopier
            from core.sky.log.widgets.close import LogClose

            filter_widget = pilot.app.query_one(LogFilter)
            search_widget = pilot.app.query_one(LogSearch)
            copier_widget = pilot.app.query_one(LogCopier)
            close_widget = pilot.app.query_one(LogClose)

            assert filter_widget is not None
            assert search_widget is not None
            assert copier_widget is not None
            assert close_widget is not None

    async def test_log_toolbar_layout_vertical(self):
        """
        QUANDO LogToolbar é renderizado
        ENTÃO layout é vertical (2 linhas)
        """
        # Arrange & Act
        async with LogToolbarApp().run_test() as pilot:
            toolbar = pilot.app.query_one(LogToolbar)

            # Assert - é Vertical container
            assert isinstance(toolbar, Vertical)


__all__ = ["TestLogToolbar"]
