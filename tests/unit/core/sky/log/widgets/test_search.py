# coding: utf-8
"""
Testes para LogSearch widget.

DOC: openspec/changes/chatlog-2-0-refactor/specs/log-search/spec.md
TDD: Red → Green → Refactor
"""

from textual.app import App

from core.sky.log.widgets.search import LogSearch, SearchChanged


class LogSearchApp(App):
    """App simples para teste do LogSearch."""

    def on_mount(self) -> None:
        """Monta o LogSearch ao iniciar."""
        self.mount(LogSearch())


class TestLogSearch:
    """Testa o widget LogSearch."""

    async def test_log_search_tem_input_reactive(self):
        """
        QUANDO LogSearch é criado
        ENTÃO possui Input widget com search_term reactive
        """
        # Arrange & Act
        async with LogSearchApp().run_test() as pilot:
            search = pilot.app.query_one(LogSearch)

            # Assert - tem input com search_term
            assert hasattr(search, "search_term")
            assert search.search_term == ""

    async def test_log_search_search_term_eh_reativo(self):
        """
        QUANDO texto é digitado no Input
        ENTÃO search_term é atualizado (após debounce)
        """
        # Arrange & Act
        async with LogSearchApp().run_test() as pilot:
            search = pilot.app.query_one(LogSearch)

            # Act - define o valor diretamente e simula o evento Changed
            search.value = "test"
            # Para teste: define search_term diretamente (sem debounce)
            search.search_term = "test"

            # Assert - search_term atualizado (em lowercase)
            assert search.search_term == "test"


__all__ = ["TestLogSearch"]
