# coding: utf-8
"""
LogFilter - Widget de filtro por nível.

Filtro simplificado com emojis para seleção de nível de logging.
"""

import logging

from textual.message import Message
from textual.widgets import Button
from textual.containers import Horizontal

from core.sky.log.scope import LogScope


class FilterChanged(Message):
    """Mensagem emitida quando o filtro muda."""

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
    """Botão para seleção de nível com emoji."""

    # Emojis para cada nível
    EMOJIS = {
        logging.NOTSET: "🌐",
        logging.DEBUG: "🐛",
        logging.INFO: "ℹ️",
        logging.WARNING: "⚠️",
        logging.ERROR: "❌",
        logging.CRITICAL: "🔥",
    }

    def __init__(self, level: int, **kwargs) -> None:
        """Inicializa botão de nível.

        Args:
            level: Nível de logging (ex: logging.INFO)
        """
        self.log_level = level
        emoji = self.EMOJIS.get(level, "?")
        super().__init__(label=emoji, id=f"level-{level}", **kwargs)


class LogFilter(Horizontal):
    """Container de filtro com botões de nível."""

    DEFAULT_CSS = """
    LogFilter {
        height: 1;
    }

    LevelButton {
        width: 3;
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

    def _update_selected_buttons(self) -> None:
        """Atualiza classes selected dos botões."""
        for btn in self.query(LevelButton):
            if btn.log_level == self._current_level:
                btn.add_class("selected")
            else:
                btn.remove_class("selected")


__all__ = ["LogFilter", "FilterChanged"]
