# coding: utf-8
"""
LogFilter - Widget de filtro por nível de log.

Implementa botões para filtrar logs por nível:
    ALL (mostra tudo), DEBUG, INFO, WARNING, ERROR, CRITICAL

Emite FilterChanged(level, scope) quando a seleção muda.
"""

import logging

from textual import on
from textual.message import Message
from textual.widgets import Button
from textual.containers import Horizontal

from core.sky.log.scope import LogScope


class FilterChanged(Message):
    """Mensagem emitida quando o filtro muda."""

    bubble = True

    def __init__(self, level: int, scope: LogScope) -> None:
        """Inicializa mensagem.

        Args:
            level: Nível mínimo do filtro (logging.DEBUG, etc.)
            scope: Escopo do filtro (sempre LogScope.ALL nesta versão)
        """
        super().__init__()
        self.level = level
        self.scope = scope


class LevelButton(Button):
    """Botão para seleção de nível com texto curto."""

    # Labels de 1 letra para cada nível
    LABELS = {
        logging.NOTSET: "A",
        logging.DEBUG: "D",
        logging.INFO: "I",
        logging.WARNING: "W",
        logging.ERROR: "E",
        logging.CRITICAL: "C",
    }

    def __init__(self, level: int, **kwargs) -> None:
        """Inicializa botão de nível.

        Args:
            level: Nível de logging (ex: logging.INFO)
        """
        self.log_level = level
        label = self.LABELS.get(level, "?")
        super().__init__(label=label, id=f"level-{level}", **kwargs)


class LogFilter(Horizontal):
    """Container de filtro com botões de nível."""

    DEFAULT_CSS = """
    LogFilter {
        height: auto;
        width: 1fr;
        layout: horizontal;
        padding: 0 0;
        margin: 0 0;
    }

    LevelButton {
        width: 10%;
        min-width: 5;
        margin-right: 1;
    }

    LevelButton.selected {
        text-style: bold reverse;
    }
    """

    def __init__(self, **kwargs) -> None:
        """Inicializa widget de filtro."""
        super().__init__(**kwargs)
        self._current_level = logging.NOTSET  # ALL = 0, mostra tudo

        # Níveis de logging
        self._levels = [
            logging.NOTSET,    # ALL
            logging.DEBUG,
            logging.INFO,
            logging.WARNING,
            logging.ERROR,
            logging.CRITICAL,
        ]

    def compose(self):
        """Compora UI do widget."""
        for level in self._levels:
            btn = LevelButton(level)
            if level == self._current_level:
                btn.add_class("selected")
            yield btn

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle botão pressionado."""
        if isinstance(event.button, LevelButton):
            self._current_level = event.button.log_level
            # Atualiza visual
            for btn in self.query(LevelButton):
                btn.remove_class("selected")
            event.button.add_class("selected")
            # Emite mensagem
            self.post_message(FilterChanged(self._current_level, LogScope.ALL))

    def set_level(self, level: int) -> None:
        """Define o nível do filtro.

        Args:
            level: Nível mínimo (logging.DEBUG, etc.)
        """
        try:
            btn = self.query_one(f"#level-{level}", LevelButton)
            self._current_level = level
            self._update_selected_buttons()
            self.post_message(FilterChanged(self._current_level, LogScope.ALL))
        except Exception:
            pass

    def clear_filters(self) -> None:
        """Reseta filtro para ALL."""
        self._current_level = logging.NOTSET
        self._update_selected_buttons()
        self.post_message(FilterChanged(self._current_level, LogScope.ALL))

    @on(FilterChanged)
    def on_filter_changed_event(self, event: FilterChanged) -> None:
        """Handle FilterChanged de outros widgets (ex: LogClose).

        Quando o botão Limpar (X) é pressionado, ele emite FilterChanged(NOTSET, ALL).
        Este handler garante que o visual do filtro também seja atualizado.
        """
        # Se evento veio de fora (não foi o botão clicado), atualiza visual
        if event.level != self._current_level:
            self._current_level = event.level
            self._update_selected_buttons()

    def _update_selected_buttons(self) -> None:
        """Atualiza classes selected dos botões."""
        for btn in self.query(LevelButton):
            if btn.log_level == self._current_level:
                btn.add_class("selected")
            else:
                btn.remove_class("selected")


__all__ = ["LogFilter", "FilterChanged"]
