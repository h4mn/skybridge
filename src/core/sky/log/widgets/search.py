# coding: utf-8
"""
LogSearch - Widget de busca reativa em logs.

Busca com debounce de 300ms, highlight de matches,
indicador de quantos matches foram encontrados e
navegação Next/Previous (F3/Shift+F3).
"""

import re
from textual import on
from textual.message import Message
from textual.reactive import reactive
from textual.widgets import Input, TextArea

from core.sky.log.widgets.filter import FilterChanged


class SearchChanged(Message):
    """Mensagem emitida quando o termo de busca muda."""

    bubble = True

    def __init__(self, search_term: str) -> None:
        """Inicializa mensagem.

        Args:
            search_term: Termo de busca atual
        """
        super().__init__()
        self.search_term = search_term


class NavigateMatch(Message):
    """Mensagem emitida para navegar entre matches."""

    bubble = True

    def __init__(self, direction: str, index: int) -> None:
        """Inicializa mensagem de navegação.

        Args:
            direction: "next" ou "previous"
            index: Índice do match para navegar (0-based)
        """
        super().__init__()
        self.direction = direction
        self.index = index


class LogSearch(Input):
    """Input de busca reativa com debounce e navegação."""

    DEFAULT_CSS = """
    LogSearch {
        background: $surface;
        border: tall $primary-darken-2;
        color: $foreground;
        height: auto;
        min-height: 1;
        padding: 0 1;
        margin: 0;
        width: 1fr;
    }

    LogSearch:focus {
        border: tall $accent;
        background: $surface-lighten-1;
    }

    LogSearch.-no-results {
        border: tall $error;
        color: $error;
    }

    LogSearch.-has-results {
        border: tall $success;
    }
    """

    search_term: reactive[str] = ""
    DEBOUNCE_MS = 300

    def __init__(self, **kwargs) -> None:
        """Inicializa widget de busca."""
        super().__init__(placeholder="Buscar logs... (escopo, nível, texto) [F3=next]", id="search-input", **kwargs)
        self._match_count = 0
        self._current_match_index = -1  # -1 = nenhum selecionado
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
        self.remove_class("-no-results", "-has-results")
        
        if self.search_term and self._match_count > 0:
            self.placeholder = f"{self._match_count} matches encontrados"
            self.add_class("-has-results")
        elif self.search_term:
            self.placeholder = "Nenhum resultado"
            self.add_class("-no-results")
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
        """Limpa a busca.

        Método público para ser chamado externamente (ex: pelo botão X ou tecla ESC).
        """
        if hasattr(self, '_debounce_timer') and self._debounce_timer:
            try:
                self._debounce_timer.stop()
            except:
                pass

        self.search_term = ""
        self._match_count = 0
        self.value = ""
        self._update_match_indicator()
        # Emite evento para notificar ChatLog
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

    def next_match(self) -> None:
        """Navega para o próximo match (F3)."""
        if self._match_count == 0:
            return

        # Avança para próximo, com wrap-around
        self._current_match_index = (self._current_match_index + 1) % self._match_count
        self.post_message(NavigateMatch("next", self._current_match_index))
        self._update_placeholder_with_navigation()

    def previous_match(self) -> None:
        """Navega para o match anterior (Shift+F3)."""
        if self._match_count == 0:
            return

        # Volta para anterior, com wrap-around
        self._current_match_index = (self._current_match_index - 1) % self._match_count
        self.post_message(NavigateMatch("previous", self._current_match_index))
        self._update_placeholder_with_navigation()

    def _update_placeholder_with_navigation(self) -> None:
        """Atualiza placeholder mostrando posição atual na navegação."""
        if self._match_count > 0:
            # Mostra "X/Y" onde X é atual (1-based) e Y é total
            display_index = self._current_match_index + 1
            self.placeholder = f"{display_index}/{self._match_count} matches [F3=next]"
        else:
            self._update_match_indicator()

    def on_key(self, event) -> None:
        """Handle teclas globais para navegação.

        F3: próximo match
        Shift+F3: match anterior
        """
        if event.key == "f3":
            self.next_match()
            event.stop()
        elif event.key == "shift+f3":
            self.previous_match()
            event.stop()


__all__ = ["LogSearch", "SearchChanged", "NavigateMatch"]
