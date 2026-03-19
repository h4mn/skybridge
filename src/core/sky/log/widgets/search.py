# coding: utf-8
"""
LogSearch - Widget de busca reativa em logs.

Busca com debounce de 300ms, highlight de matches e
indicador de quantos matches foram encontrados.
"""

import re
from textual.message import Message
from textual.reactive import reactive
from textual.widgets import Input

from core.sky.log.widgets.filter import FilterChanged


class SearchChanged(Message):
    """Mensagem emitida quando o termo de busca muda."""

    def __init__(self, search_term: str) -> None:
        """Inicializa mensagem.

        Args:
            search_term: Termo de busca atual
        """
        super().__init__()
        self.search_term = search_term


class LogSearch(Input):
    """Input de busca reativa com debounce."""

    search_term: reactive[str] = ""
    DEBOUNCE_MS = 300

    def __init__(self, **kwargs) -> None:
        """Inicializa widget de busca."""
        super().__init__(placeholder="Buscar logs... (escopo, nível, texto)", id="search-input", **kwargs)
        self._match_count = 0
        self._debounce_timer = None

    def on_input_changed(self, event: Input.Changed) -> None:
        """Handle Input changed com debounce."""
        # Cancela timer anterior se existir
        if self._debounce_timer:
            try:
                self._debounce_timer.stop()
            except:
                pass

        # Se vazio, atualiza imediatamente
        if not event.value:
            self.search_term = ""
            self._update_match_indicator()
            self.post_message(SearchChanged(self.search_term))
            return

        # Agenda nova emissão após debounce
        self._debounce_timer = self.set_timer(
            self.DEBOUNCE_MS / 1000,
            lambda: self._emit_search(event.value),
        )

    def _emit_search(self, value: str) -> None:
        """Emite SearchChanged após debounce.

        Args:
            value: Valor do input
        """
        self.search_term = value.lower()  # Case-insensitive
        self._update_match_indicator()
        self.post_message(SearchChanged(self.search_term))

    def _update_match_indicator(self) -> None:
        """Atualiza indicador de matches via placeholder."""
        if self.search_term and self._match_count > 0:
            self.placeholder = f"{self._match_count} matches encontrados"
        elif self.search_term:
            self.placeholder = "Nenhum resultado"
        else:
            self.placeholder = "Buscar logs... (escopo, nível, texto)"

    def set_match_count(self, count: int) -> None:
        """Define número de matches encontrados.

        Args:
            count: Número de matches
        """
        self._match_count = count
        self._update_match_indicator()

    def clear_search(self) -> None:
        """Limpa a busca."""
        if hasattr(self, '_debounce_timer') and self._debounce_timer:
            try:
                self._debounce_timer.stop()
            except:
                pass

        self.search_term = ""
        self._match_count = 0
        self.value = ""
        self._update_match_indicator()
        self.post_message(SearchChanged(""))

    def get_search_pattern(self) -> re.Pattern[str] | None:
        """Retorna pattern compilado da busca (suporta curingas).

        Returns:
            Pattern compilado ou None se busca vazia
        """
        if not self.search_term:
            return None

        # Converte curingas * e ? para regex
        pattern = self.search_term.replace("*", ".*").replace("?", ".")
        try:
            return re.compile(pattern, re.IGNORECASE)
        except re.error:
            return None


__all__ = ["LogSearch", "SearchChanged"]
