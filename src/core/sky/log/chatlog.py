# coding: utf-8
"""
ChatLog 2.0 - Widget principal de log.

Ring buffer com virtualização e filtros por nível/escopo.
"""

import logging
import re
from collections import deque
from dataclasses import dataclass
from datetime import datetime
from typing import List

from textual import on
from textual.containers import VerticalScroll
from textual.widgets import Static

from core.sky.log.events import VisibleEntriesChanged
from core.sky.log.entry import LogEntry
from core.sky.log.protocol import LogConsumer
from core.sky.log.scope import LogScope
from core.sky.log.widgets.filter import FilterChanged
from core.sky.log.widgets.search import SearchChanged


@dataclass
class ChatLogConfig:
    """Configuração do ChatLog."""

    max_entries: int = 1000
    buffer_when_closed: int = 100
    virtualization_threshold: int = 50


class ChatLog(VerticalScroll):
    """Widget de log com ring buffer e filtros.

    Implementa o protocolo LogConsumer através do método write_log.
    """

    DEFAULT_CSS = """
    ChatLog {
        background: $panel;
    }

    .log-entry {
        padding: 0 1;
    }

    .log-entry-debug {
        text-style: dim;
    }

    .log-entry-info {
        color: cyan;
    }

    .log-entry-warning {
        color: yellow;
    }

    .log-entry-error {
        color: red;
    }

    .log-entry-critical {
        color: red;
        text-style: bold;
    }

    .highlight {
        text-style: bold reverse;
    }
    """

    def __init__(self, config: ChatLogConfig, **kwargs) -> None:
        """Inicializa ChatLog.

        Args:
            config: Configuração do ChatLog
        """
        VerticalScroll.__init__(self, **kwargs)
        self._config = config
        self._entries: deque[LogEntry] = deque(maxlen=config.max_entries)
        self._min_level: int = logging.NOTSET
        self._scope_filter: LogScope = LogScope.ALL
        self._search_term: str = ""
        self._search_pattern: re.Pattern[str] | None = None
        self._pending_refresh = False

    def write_log(self, entry: LogEntry) -> None:
        """Adiciona entry ao buffer (implementa LogConsumer).

        Args:
            entry: LogEntry para adicionar
        """
        self._entries.append(entry)
        self._schedule_refresh()

    def set_min_level(self, level: int) -> None:
        """Define filtro de nível mínimo.

        Args:
            level: Nível mínimo (logging.DEBUG, etc.)
        """
        self._min_level = level
        self._schedule_refresh()

    def set_scope(self, scope: LogScope) -> None:
        """Define filtro de escopo.

        Args:
            scope: Escopo desejado
        """
        self._scope_filter = scope
        self._schedule_refresh()

    def set_search_term(self, term: str, pattern: re.Pattern[str] | None = None) -> None:
        """Define termo de busca.

        Args:
            term: Termo para buscar (já em lowercase)
            pattern: Pattern compilado opcional (para curingas)
        """
        self._search_term = term
        self._search_pattern = pattern
        self._schedule_refresh()

    def _schedule_refresh(self) -> None:
        """Agenda refresh para evitar flicker (batch flush)."""
        if not self._pending_refresh:
            self._pending_refresh = True
            self.set_timer(0.05, self._refresh)

    def _get_visible_entries(self) -> List[LogEntry]:
        """Retorna entries filtradas."""
        visible = []
        for entry in self._entries:
            # Filtro de nível
            if entry.level < self._min_level:
                continue

            # Filtro de escopo
            if self._scope_filter is not LogScope.ALL and entry.scope != self._scope_filter:
                continue

            # Filtro de busca (pattern ou substring)
            if self._search_term:
                # Texto para busca inclui mensagem, escopo e nível
                searchable_text = f"{entry.message} {entry.scope.value} {logging.getLevelName(entry.level)}".lower()

                if self._search_pattern:
                    # Usa pattern com curingas
                    if not self._search_pattern.search(searchable_text):
                        continue
                else:
                    # Busca simples case-insensitive
                    if self._search_term not in searchable_text:
                        continue

            visible.append(entry)

        return visible

    def _highlight_match(self, text: str) -> str:
        """Aplica highlight nos matches de busca.

        Args:
            text: Texto para highlight

        Returns:
            Texto com markup de highlight
        """
        if not self._search_term:
            return text

        if self._search_pattern:
            # Highlight com pattern
            result = []
            last_end = 0
            for match in self._search_pattern.finditer(text):
                result.append(text[last_end:match.start()])
                result.append(f"[reverse]{match.group()}[/reverse]")
                last_end = match.end()
            result.append(text[last_end:])
            return "".join(result)
        else:
            # Highlight simples
            lower_text = text.lower()
            result = []
            last_end = 0
            start = 0

            while True:
                idx = lower_text.find(self._search_term, start)
                if idx == -1:
                    break
                result.append(text[last_end:idx])
                result.append(f"[reverse]{text[idx:idx + len(self._search_term)]}[/reverse]")
                last_end = idx + len(self._search_term)
                start = idx + 1

            result.append(text[last_end:])
            return "".join(result)

    def _refresh(self) -> None:
        """Atualiza display com entries visíveis."""
        self._pending_refresh = False

        # Virtualização: se muitos entries, renderiza apenas visíveis + margem
        visible = self._get_visible_entries()
        to_render = visible

        if len(visible) > self._config.virtualization_threshold:
            # TODO: Implementar virtualização verdadeira (scroll_region)
            # Por enquanto, renderiza todos até o threshold
            to_render = visible[: self._config.virtualization_threshold]

        # Remove todos os filhos
        self.remove_children()

        # Adiciona entries visíveis com highlight
        for entry in to_render:
            level_class = self._get_level_class(entry.level)
            formatted_message = self._highlight_match(entry.message)

            timestamp = entry.timestamp.strftime("%H:%M:%S")
            level_name = logging.getLevelName(entry.level)
            scope_str = entry.scope.value.upper()

            self.mount(
                Static(
                    f"{timestamp} [{level_name}] {scope_str}: {formatted_message}",
                    classes=f"log-entry {level_class}",
                )
            )

        # Emite evento com entries visíveis para o LogCopier
        self.post_message(VisibleEntriesChanged(visible))

    def _get_level_class(self, level: int) -> str:
        """Retorna classe CSS para o nível."""
        if level >= logging.CRITICAL:
            return "log-entry-critical"
        if level >= logging.ERROR:
            return "log-entry-error"
        if level >= logging.WARNING:
            return "log-entry-warning"
        if level >= logging.INFO:
            return "log-entry-info"
        if level >= logging.DEBUG:
            return "log-entry-debug"
        return ""

    def clear(self) -> None:
        """Limpa todos os entries."""
        self._entries.clear()
        self._schedule_refresh()

    @on(FilterChanged)
    def on_filter_changed(self, event: FilterChanged) -> None:
        """Handle mudança de filtro."""
        self._min_level = event.level
        self._scope_filter = event.scope
        self._schedule_refresh()

    @on(SearchChanged)
    def on_search_changed(self, event: SearchChanged) -> None:
        """Handle mudança de busca."""
        # TODO: Obter pattern do LogSearch via algum mecanismo
        self._search_term = event.search_term
        self._search_pattern = None
        self._schedule_refresh()


__all__ = ["ChatLog", "ChatLogConfig"]
