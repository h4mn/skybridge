# coding: utf-8
"""
LogCopier - Widget para copiar logs para clipboard.

Botão que copia as entradas de log visíveis (respeitando filtros)
para o clipboard, com formatação apropriada.
"""

import logging
from typing import TYPE_CHECKING, List

from textual import on
from textual.widgets import Button

from core.sky.log.clipboard import copy_to_clipboard
from core.sky.log.entry import LogEntry
from core.sky.log.events import VisibleEntriesChanged

if TYPE_CHECKING:
    from core.sky.log.chatlog import ChatLog


class LogCopier(Button):
    """Botão que copia logs para clipboard."""

    DEFAULT_CSS = """
    LogCopier {
        width: 3;
        min-width: 3;
    }
    """

    def __init__(self, **kwargs) -> None:
        """Inicializa widget de cópia."""
        super().__init__(label="📋", id="copy-button", **kwargs)
        self._visible_entries: List[LogEntry] = []

    @on(VisibleEntriesChanged)
    def on_visible_entries_changed(self, event: VisibleEntriesChanged) -> None:
        """Handle mudança nas entries visíveis."""
        self._visible_entries = event.entries

    def set_visible_entries(self, entries: List[LogEntry]) -> None:
        """Define entries visíveis para cópia.

        Args:
            entries: Lista de entries visíveis (já filtradas)
        """
        self._visible_entries = entries

    def on_press(self) -> None:
        """Handle botão pressionado."""
        if not self._visible_entries:
            self.label = "⭕"
            self.set_timer(1.0, self._restore_label)
            return

        # Formata as entries
        lines = []
        for entry in self._visible_entries:
            timestamp = entry.timestamp.strftime("%H:%M:%S")
            level_name = self._level_name(entry.level)
            scope = entry.scope.value.upper()
            lines.append(f"{timestamp} [{level_name}] {scope}: {entry.message}")

        text = "\n".join(lines)

        # Copia para clipboard
        success = copy_to_clipboard(text)

        if success:
            count = len(self._visible_entries)
            self.label = "✓"
        else:
            self.label = "✗"

        # Restaura label após 2 segundos
        self.set_timer(2.0, self._restore_label)

    def _restore_label(self) -> None:
        """Restaura label original."""
        self.label = "📋"

    def _level_name(self, level: int) -> str:
        """Retorna nome do nível de logging."""
        if level >= logging.CRITICAL:
            return "CRITICAL"
        if level >= logging.ERROR:
            return "ERROR"
        if level >= logging.WARNING:
            return "WARNING"
        if level >= logging.INFO:
            return "INFO"
        if level >= logging.DEBUG:
            return "DEBUG"
        return "NOTSET"


__all__ = ["LogCopier"]
