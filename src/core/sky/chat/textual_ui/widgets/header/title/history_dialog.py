# coding: utf-8
"""
TitleHistoryDialog - Diálogo modal com histórico de títulos animados.

DOC: openspec/changes/sky-chat-animated-title-history
"""

from textual.app import ComposeResult
from textual.screen import ModalScreen
from textual.widgets import ListView, ListItem, Static
from textual.containers import Vertical

from core.sky.chat.textual_ui.widgets.header.title.history import TitleHistory, TitleEntry


class HistoryEntryItem(ListItem):
    """
    Item do ListView representando uma entrada do histórico.

    Exibe apenas o título (verbo + predicado).
    """

    def __init__(self, entry: TitleEntry) -> None:
        super().__init__()
        self._entry = entry

    def _formatar_texto(self, verbo: str, predicado: str) -> str:
        """
        Formata o texto para exibição no histórico.

        Remove redundâncias como "codando implementação" → "implementando"
        """
        # Lista de verbos que devem ser substituídos por formas mais naturais
        substituicoes = {
            "codando": "implementando",
            "buscando": "pesquisando",
        }

        # Aplica substituições se o verbo estiver na lista
        verbo_formatado = substituicoes.get(verbo, verbo)

        return f"{verbo_formatado} {predicado}"

    def compose(self) -> ComposeResult:
        estado = self._entry.estado
        texto_formatado = self._formatar_texto(estado.verbo, estado.predicado)
        yield Static(texto_formatado)


class TitleHistoryDialog(ModalScreen):
    """
    Diálogo modal que exibe o histórico completo da sessão.

    Lista simples com a sequência de títulos (verbo + predicado).
    """

    DEFAULT_CSS = """
    TitleHistoryDialog {
        align: center middle;
    }

    TitleHistoryDialog > Vertical {
        width: 60;
        height: 20;
        border: round $accent;
        background: $surface;
        padding: 1 2;
    }

    TitleHistoryDialog #header {
        height: 2;
        content-align: center middle;
        text-style: bold;
        border-bottom: solid $panel;
        margin-bottom: 1;
    }

    TitleHistoryDialog #list-container {
        height: 1fr;
    }

    TitleHistoryDialog ListView {
        height: 1fr;
    }

    TitleHistoryDialog HistoryEntryItem {
        padding: 0 1;
        margin: 0;
    }

    TitleHistoryDialog HistoryEntryItem Static {
        width: 1fr;
    }

    TitleHistoryDialog #footer {
        height: 1;
        content-align: center middle;
        text-style: dim;
        border-top: solid $panel;
        margin-top: 1;
    }
    """

    BINDINGS = [("escape", "dismiss", "Fechar")]

    def __init__(self, history: TitleHistory) -> None:
        super().__init__()
        self._history = history

    def compose(self) -> ComposeResult:
        with Vertical():
            yield Static("Histórico da Sessão", id="header")

            with Vertical(id="list-container"):
                # Filtra entradas para não mostrar verbos repetidos (ex: "codando" + "codou")
                entradas_unicas = self._filtrar_entradas_unicas()
                yield ListView(
                    *[HistoryEntryItem(entry) for entry in entradas_unicas],
                    id="history-list"
                )

            yield Static("ESC para fechar", id="footer")

    def _filtrar_entradas_unicas(self) -> list:
        """
        Filtra entradas do histórico para não mostrar verbos repetidos.

        Remove entradas consecutivas onde o radical do verbo é o mesmo,
        evitando mostrar "codando implementação" seguido de "codou implementação".
        """
        entradas_filtradas = []
        ultimo_radical = None

        for entry in self._history.entries:
            verbo = entry.estado.verbo
            radical = self._extrair_radical(verbo)

            # Só adiciona se for um radical diferente do último
            if radical != ultimo_radical:
                entradas_filtradas.append(entry)
                ultimo_radical = radical

        return entradas_filtradas

    @staticmethod
    def _extrair_radical(verbo: str) -> str:
        """
        Extrai o radical do verbo para comparar formas diferentes.

        Remove terminações de gerúndio (-ando, -endo, -indo) e
        pretérito (-ou, -eu, -iu) para obter o radical comum.
        """
        # Terminações de pretérito perfeito regular
        for term in ["ou", "eu", "iu"]:
            if verbo.endswith(term) and len(verbo) > len(term):
                return verbo[:-len(term)]

        # Terminações de gerúndio
        for term in ["ando", "endo", "indo"]:
            if verbo.endswith(term):
                return verbo[:-len(term)]

        # Fallback: retorna o próprio verbo
        return verbo


__all__ = ["TitleHistoryDialog", "HistoryEntryItem"]
