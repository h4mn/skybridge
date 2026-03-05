# coding: utf-8
"""
HelpScreen - Tela de ajuda com lista de comandos.

Mostra todos os comandos disponíveis com descrições,
permitindo busca por comandos e navegação via ESC.
"""

from textual.app import ComposeResult
from textual.containers import Vertical
from textual.screen import Screen
from textual.widgets import DataTable, Header, Footer, Input


class HelpScreen(Screen):
    """Screen de ajuda com comandos disponíveis."""

    DEFAULT_CSS = """
    HelpScreen {
        layout: vertical;
    }
    #search-container {
        height: 3;
        padding: 1 2;
    }
    DataTable {
        height: 1fr;
    }
    """

    BINDINGS = [
        ("esc", "pop_screen", "Voltar"),
        ("q", "pop_screen", "Sair"),
    ]

    # Comandos e descrições
    COMMANDS = [
        ("Comando", "Descrição", "Alias"),
        ("/help", "Mostra esta tela de ajuda", "?"),
        ("/new", "Inicia nova sessão (limpa histórico)", None),
        ("/config", "Abre configurações", None),
        ("/sair", "Encerra o chat", "quit, exit"),
        ("/cancel", "Cancela operação pendente", "esc"),
    ]

    def compose(self) -> ComposeResult:
        """Compo̵e a tela de ajuda."""
        yield Header()
        with Vertical(id="search-container"):
            yield Input(
                placeholder="🔍 Buscar comandos...",
                id="search-input",
            )
        yield DataTable(id="commands-table")
        yield Footer()

    def on_mount(self) -> None:
        """Popula a tabela com comandos ao montar."""
        table = self.query_one("#commands-table", DataTable)
        table.zebra_stripes = True

        # Adiciona colunas
        table.add_column("Comando", width=20)
        table.add_column("Descrição", width=50)
        table.add_column("Alias", width=15)

        # Popula com todos os comandos
        self._populate_table("")

        # Foca no input de busca
        search_input = self.query_one("#search-input", Input)
        search_input.focus()

    def on_input_changed(self, event: Input.Changed) -> None:
        """
        Input de busca foi alterado.

        Args:
            event: Evento de mudança do input.
        """
        if event.input.id == "search-input":
            self._populate_table(event.value)

    def _populate_table(self, filter_text: str) -> None:
        """
        Popula a tabela filtrando comandos.

        Args:
            filter_text: Texto para filtrar comandos.
        """
        table = self.query_one("#commands-table", DataTable)
        table.clear()

        # Filtra comandos baseado no texto
        filter_lower = filter_text.lower()

        for row in self.COMMANDS:
            if row[0] == "Comando":
                # Cabeçalho
                table.add_row(*row)
            else:
                # Verifica se alguma coluna contém o filtro
                cmd, desc, alias = row
                alias_text = alias or "-"

                if (
                    filter_text == ""
                    or filter_lower in cmd.lower()
                    or filter_lower in desc.lower()
                    or filter_lower in alias_text.lower()
                ):
                    table.add_row(cmd, desc, alias_text)


__all__ = ["HelpScreen"]
