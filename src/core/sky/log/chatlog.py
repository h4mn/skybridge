# coding: utf-8
"""
ChatLog 2.0 - Widget principal de log com ring buffer e virtualização.

Este módulo implementa o widget ChatLog para exibição de logs em tempo real
na UI Textual, com as seguintes características:

Características:
    - Ring buffer configurável (limita memória)
    - Virtualização de widgets (renderiza apenas visíveis)
    - Filtro por nível (DEBUG, INFO, WARNING, ERROR, CRITICAL)
    - Filtro por escopo (SYSTEM, USER, API, DATABASE, NETWORK, VOICE, MEMORY)
    - Busca reativa com highlight de matches
    - Buffer when_closed (economiza memória quando widget fechado)
    - Flush em batch (evita flicker)

Uso:
    >>> from core.sky.log import ChatLog, ChatLogConfig
    >>>
    >>> config = ChatLogConfig(
    ...     max_entries=1000,
    ...     buffer_when_closed=100,
    ...     virtualization_threshold=50
    ... )
    >>> chat_log = ChatLog(config=config)
    >>>
    >>> # Escrever logs via LogConsumer Protocol
    >>> entry = LogEntry(level=logging.INFO, message="Test", ...)
    >>> chat_log.write_log(entry)

Integração:
    - Usa LogConsumer Protocol para receber logs
    - Emite VisibleEntriesChanged para LogCopier
    - Recebe FilterChanged e SearchChanged dos widgets
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
    virtualization_margin: int = 20  # Margem acima/abaixo do visível


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

    .-current-match {
        background: $accent;
        text-style: bold;
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
        # Buffer para quando o widget está fechado
        self._closed_buffer: List[LogEntry] = []
        self._was_closed = False

    def write_log(self, entry: LogEntry) -> None:
        """Adiciona entry ao buffer (implementa LogConsumer).

        Args:
            entry: LogEntry para adicionar
        """
        # Verificar se widget está visível (tem app e está montado)
        # Usa getattr com padrão True para contextos onde is_visible não existe
        is_widget_visible = (
            hasattr(self, 'app') and
            self.app is not None and
            getattr(self, 'is_visible', True)
        )

        # Se widget está fechado/oculto, usa buffer reduzido
        if not is_widget_visible:
            self._closed_buffer.append(entry)
            # Mantém apenas buffer_when_closed entries
            if len(self._closed_buffer) > self._config.buffer_when_closed:
                self._closed_buffer = self._closed_buffer[-self._config.buffer_when_closed:]
            self._was_closed = True
        else:
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

    def on_show(self) -> None:
        """Chamado quando widget fica visível.

        Restaura entries do buffer if widget estava fechado.
        """
        if self._was_closed and self._closed_buffer:
            # Restaurar entries do buffer
            for entry in self._closed_buffer:
                self._entries.append(entry)
            self._closed_buffer.clear()
            self._was_closed = False
        self._schedule_refresh()

    def on_hide(self) -> None:
        """Chamado quando widget fica oculto.

        Marca que widget está fechado para ativar buffer reduzido.
        """
        # As próximas writes vão para _closed_buffer
        pass

    def _get_visible_range(self, total_entries: int) -> tuple[int, int]:
        """Calcula range de entries visíveis na tela.

        Args:
            total_entries: Número total de entries para considerar

        Returns:
            Tupla (start_index, end_index) do range visível com margem
        """
        # Altura visível em linhas (estimado)
        try:
            height = self.region.height
        except Exception:
            height = 20  # Fallback

        # Altura aproximada de cada linha (1 linha de texto + padding)
        line_height = 1

        # Quantas linhas cabem na tela
        visible_lines = height // line_height if height > 0 else 20

        # Scroll atual (0 = topo, 1 = base)
        try:
            scroll_pos = self.scroll_y(0).fraction if hasattr(self, 'scroll_y') else 0
        except Exception:
            scroll_pos = 0

        # Índice baseado na posição do scroll
        if total_entries <= visible_lines:
            return 0, total_entries

        # Calcular start baseado no scroll
        max_scroll = total_entries - visible_lines
        start = int(scroll_pos * max_scroll) if scroll_pos < 1 else total_entries - visible_lines

        # Aplicar margem
        start = max(0, start - self._config.virtualization_margin)
        end = min(total_entries, start + visible_lines + 2 * self._config.virtualization_margin)

        return start, end

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
                # scope pode ser LogScope ou string (compatibilidade com testes)
                scope_value = entry.scope.value if isinstance(entry.scope, LogScope) else str(entry.scope)
                searchable_text = f"{entry.message} {scope_value} {logging.getLevelName(entry.level)}".lower()

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
            # Calcular range visível
            start_idx, end_idx = self._get_visible_range(len(visible))
            to_render = visible[start_idx:end_idx]

        # Remove todos os filhos
        self.remove_children()

        # Adiciona entries visíveis com highlight
        for entry in to_render:
            level_class = self._get_level_class(entry.level)
            formatted_message = self._highlight_match(entry.message)

            timestamp = entry.timestamp.strftime("%H:%M:%S")
            level_name = logging.getLevelName(entry.level)
            # scope pode ser LogScope ou string (compatibilidade com testes)
            if isinstance(entry.scope, LogScope):
                scope_str = entry.scope.value.upper()
            else:
                scope_str = str(entry.scope).upper()

            self.mount(
                Static(
                    f"{timestamp} [{level_name}] {scope_str}: {formatted_message}",
                    classes=f"log-entry {level_class}",
                )
            )

        # Emite evento com entries visíveis para o LogCopier
        self.post_message(VisibleEntriesChanged(visible))

        # Atualiza contador de matches no LogSearch
        from core.sky.log.widgets.search import LogSearch
        try:
            search_widget = self.app.query_one(LogSearch)
            search_widget.set_match_count(len(visible))
        except Exception:
            pass

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
        from core.sky.log.widgets.search import LogSearch

        # Obter pattern do LogSearch
        try:
            search_widget = self.app.query_one(LogSearch)
            self._search_pattern = search_widget.get_search_pattern()
        except Exception:
            self._search_pattern = None

        self._search_term = event.search_term
        self._schedule_refresh()

    @on("NavigateMatch")
    def on_navigate_match(self, event) -> None:
        """Handle navegação entre matches (F3/Shift+F3)."""
        # Obter entries visíveis filtradas
        visible = self._get_visible_entries()

        if not visible or event.index >= len(visible):
            return

        # Encontrar o widget na posição do match e scroll até ele
        target_entry = visible[event.index]

        # Encontrar widget correspondente (os widgets são montados em ordem)
        # Precisamos encontrar o widget que contém a mensagem do target_entry
        widgets = list(self.query(Static))
        if event.index < len(widgets):
            target_widget = widgets[event.index]
            target_widget.scroll_visible()
            # Adiciona highlight temporário no match atual
            target_widget.add_class("-current-match")


__all__ = ["ChatLog", "ChatLogConfig"]
