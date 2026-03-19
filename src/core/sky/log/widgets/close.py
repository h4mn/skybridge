# coding: utf-8
"""
LogClose - Botão para fechar/limpar todos os filtros.

Botão que limpa filtros de nível e busca.
"""

import logging

from textual import on
from textual.widgets import Button

from core.sky.log.widgets.filter import FilterChanged
from core.sky.log.widgets.search import SearchChanged


class LogClose(Button):
    """Botão para limpar filtros."""

    DEFAULT_CSS = """
    LogClose {
        width: 3;
        min-width: 3;
    }
    """

    def __init__(self, **kwargs) -> None:
        """Inicializa widget."""
        super().__init__(label="🔄", id="close-button", **kwargs)

    @on(FilterChanged)
    @on(SearchChanged)
    def on_filters_changed(self, event) -> None:
        """Handle mudança de filtros - atualiza emoji."""
        # Verifica se há filtros ativos
        has_filters = (
            hasattr(event, 'level') and event.level != logging.NOTSET
        ) or (
            hasattr(event, 'search_term') and event.search_term != ""
        )
        self.label = "🔄" if has_filters else "✕"

    def on_press(self) -> None:
        """Handle botão pressionado - limpa tudo."""
        from core.sky.log.widgets.search import LogSearch
        from core.sky.log.widgets.filter import LogFilter

        # Emite eventos para limpar
        self.post_message(FilterChanged(logging.NOTSET, None))
        self.post_message(SearchChanged(""))

        self.label = "✕"


__all__ = ["LogClose"]
