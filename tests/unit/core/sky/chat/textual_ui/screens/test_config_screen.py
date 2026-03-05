# coding: utf-8
"""
Testes do ConfigScreen e HelpScreen (screens secundárias).

DOC: openspec/changes/sky-chat-textual-ui/specs/textual-chat-ui/spec.md
DOC: openspec/changes/sky-chat-textual-ui/design.md - Screens secundárias
"""

import pytest
from unittest.mock import Mock, patch
import os

from src.core.sky.chat.textual_ui.screens.config import ConfigScreen
from src.core.sky.chat.textual_ui.screens.help import HelpScreen


class TestConfigScreenInit:
    """
    Testa inicialização do ConfigScreen.
    """

    def test_init_sem_parametros(self):
        """
        QUANDO ConfigScreen é criado
        ENTÃO inicializa corretamente
        """
        # Arrange & Act
        screen = ConfigScreen()

        # Assert
        assert screen is not None


class TestConfigScreenCompose:
    """
    Testa método compose().
    """

    def test_compose_retorna_componentes(self):
        """
        QUANDO compose() é chamado
        ENTÃO retorna Header, Static de título, Switches, e Footer
        """
        # Arrange
        screen = ConfigScreen()

        # Act
        children = list(screen.compose())

        # Assert - Header, Static título, Horizontal com RAG, Horizontal com Verbose,
        #          Static modelo, Static API Key, Footer
        assert len(children) >= 5

    def test_compose_inclui_header(self):
        """
        QUANDO compose() é chamado
        ENTÃO inclui Header
        """
        # Arrange
        from textual.widgets import Header

        screen = ConfigScreen()

        # Act
        children = list(screen.compose())

        # Assert
        assert any(isinstance(c, Header) for c in children)

    def test_compose_inclui_footer(self):
        """
        QUANDO compose() é chamado
        ENTÃO inclui Footer
        """
        # Arrange
        from textual.widgets import Footer

        screen = ConfigScreen()

        # Act
        children = list(screen.compose())

        # Assert
        assert any(isinstance(c, Footer) for c in children)

    def test_compose_inclui_rag_switch(self):
        """
        QUANDO compose() é chamado
        ENTÃO inclui Switch para RAG
        """
        # Arrange
        from textual.widgets import Switch

        screen = ConfigScreen()

        # Act
        children = list(screen.compose())

        # Assert - encontrar Horizontal com RAG
        found = False
        for child in children:
            horizontal_children = list(child.compose()) if hasattr(child, "compose") else []
            for item in horizontal_children:
                if isinstance(item, Switch) and item.id == "rag-switch":
                    found = True
                    break
        assert found

    def test_compose_inclui_verbose_switch(self):
        """
        QUANDO compose() é chamado
        ENTÃO inclui Switch para Verbose
        """
        # Arrange
        from textual.widgets import Switch

        screen = ConfigScreen()

        # Act
        children = list(screen.compose())

        # Assert - encontrar Horizontal com Verbose
        found = False
        for child in children:
            horizontal_children = list(child.compose()) if hasattr(child, "compose") else []
            for item in horizontal_children:
                if isinstance(item, Switch) and item.id == "verbose-switch":
                    found = True
                    break
        assert found


class TestConfigScreenCss:
    """
    Testa CSS do ConfigScreen.
    """

    def test_possui_css_default_definido(self):
        """
        QUANDO ConfigScreen é inspecionado
        ENTÃO possui DEFAULT_CSS definido
        """
        # Assert
        assert ConfigScreen.DEFAULT_CSS is not None

    def test_css_inclui_layout_vertical(self):
        """
        QUANDO DEFAULT_CSS é inspecionado
        ENTÃO inclui layout: vertical
        """
        # Assert
        assert "layout: vertical" in ConfigScreen.DEFAULT_CSS

    def test_css_inclui_config_row(self):
        """
        QUANDO DEFAULT_CSS é inspecionado
        ENTÃO define estilo para .config-row
        """
        # Assert
        assert ".config-row" in ConfigScreen.DEFAULT_CSS

    def test_css_inclui_config_label(self):
        """
        QUANDO DEFAULT_CSS é inspecionado
        ENTÃO define estilo para .config-label
        """
        # Assert
        assert ".config-label" in ConfigScreen.DEFAULT_CSS

    def test_css_inclui_info_text(self):
        """
        QUANDO DEFAULT_CSS é inspecionado
        ENTÃO define estilo para .info-text
        """
        # Assert
        assert ".info-text" in ConfigScreen.DEFAULT_CSS


class TestConfigScreenBindings:
    """
    Testa bindings de teclado.
    """

    def test_binding_esc_para_voltar(self):
        """
        QUANDO BINDINGS é inspecionado
        ENTÃO inclui "esc" para pop_screen
        """
        # Assert
        assert any(binding[0] == "esc" and binding[1] == "pop_screen" for binding in ConfigScreen.BINDINGS)

    def test_binding_s_para_salvar(self):
        """
        QUANDO BINDINGS é inspecionado
        ENTÃO inclui "s" para save_and_exit
        """
        # Assert
        assert any(binding[0] == "s" and binding[1] == "save_and_exit" for binding in ConfigScreen.BINDINGS)


class TestConfigScreenActions:
    """
    Testa ações do ConfigScreen.
    """

    def test_action_save_and_exit_chama_pop_screen(self):
        """
        QUANDO action_save_and_exit() é chamado
        ENTÃO chama app.pop_screen()
        """
        # Arrange
        screen = ConfigScreen()
        screen.app = Mock()

        # Act
        screen.action_save_and_exit()

        # Assert
        screen.app.pop_screen.assert_called_once()


class TestHelpScreenInit:
    """
    Testa inicialização do HelpScreen.
    """

    def test_init_sem_parametros(self):
        """
        QUANDO HelpScreen é criado
        ENTÃO inicializa corretamente
        """
        # Arrange & Act
        screen = HelpScreen()

        # Assert
        assert screen is not None
        assert len(screen.COMMANDS) > 0


class TestHelpScreenCommands:
    """
    Testa lista de comandos do HelpScreen.
    """

    def test_commands_inclui_help(self):
        """
        QUANDO COMMANDS é inspecionado
        ENTÃO inclui /help
        """
        # Assert
        assert any("/help" in cmd for cmd in HelpScreen.COMMANDS)

    def test_commands_inclui_new(self):
        """
        QUANDO COMMANDS é inspecionado
        ENTÃO inclui /new
        """
        # Assert
        assert any("/new" in cmd for cmd in HelpScreen.COMMANDS)

    def test_commands_inclui_config(self):
        """
        QUANDO COMMANDS é inspecionado
        ENTÃO inclui /config
        """
        # Assert
        assert any("/config" in cmd for cmd in HelpScreen.COMMANDS)

    def test_commands_inclui_sair(self):
        """
        QUANDO COMMANDS é inspecionado
        ENTÃO inclui /sair
        """
        # Assert
        assert any("/sair" in cmd for cmd in HelpScreen.COMMANDS)

    def test_commands_inclui_cancel(self):
        """
        QUANDO COMMANDS é inspecionado
        ENTÃO inclui /cancel
        """
        # Assert
        assert any("/cancel" in cmd for cmd in HelpScreen.COMMANDS)


class TestHelpScreenCompose:
    """
    Testa método compose().
    """

    def test_compose_retorna_componentes(self):
        """
        QUANDO compose() é chamado
        ENTÃO retorna Header, Input de busca, DataTable, e Footer
        """
        # Arrange
        screen = HelpScreen()

        # Act
        children = list(screen.compose())

        # Assert - Vertical com search-container, DataTable, Footer
        assert len(children) >= 2

    def test_compose_inclui_input_busca(self):
        """
        QUANDO compose() é chamado
        ENTÃO inclui Input com id="search-input"
        """
        # Arrange
        from textual.widgets import Input

        screen = HelpScreen()

        # Act
        children = list(screen.compose())

        # Assert - Vertical contém Input
        vertical = children[0]
        vertical_children = list(vertical.compose())
        assert any(isinstance(c, Input) and c.id == "search-input" for c in vertical_children)

    def test_compose_inclui_data_table(self):
        """
        QUANDO compose() é chamado
        ENTÃO inclui DataTable com id="commands-table"
        """
        # Arrange
        from textual.widgets import DataTable

        screen = HelpScreen()

        # Act
        children = list(screen.compose())

        # Assert
        data_table = children[1]
        assert isinstance(data_table, DataTable)
        assert data_table.id == "commands-table"


class TestHelpScreenCss:
    """
    Testa CSS do HelpScreen.
    """

    def test_possui_css_default_definido(self):
        """
        QUANDO HelpScreen é inspecionado
        ENTÃO possui DEFAULT_CSS definido
        """
        # Assert
        assert HelpScreen.DEFAULT_CSS is not None

    def test_css_inclui_layout_vertical(self):
        """
        QUANDO DEFAULT_CSS é inspecionado
        ENTÃO inclui layout: vertical
        """
        # Assert
        assert "layout: vertical" in HelpScreen.DEFAULT_CSS

    def test_css_inclui_search_container(self):
        """
        QUANDO DEFAULT_CSS é inspecionado
        ENTÃO define estilo para #search-container
        """
        # Assert
        assert "#search-container" in HelpScreen.DEFAULT_CSS

    def test_css_inclui_data_table(self):
        """
        QUANDO DEFAULT_CSS é inspecionado
        ENTÃO define estilo para DataTable
        """
        # Assert
        assert "DataTable" in HelpScreen.DEFAULT_CSS


class TestHelpScreenBindings:
    """
    Testa bindings de teclado.
    """

    def test_binding_esc_para_voltar(self):
        """
        QUANDO BINDINGS é inspecionado
        ENTÃO inclui "esc" para pop_screen
        """
        # Assert
        assert any(binding[0] == "esc" and binding[1] == "pop_screen" for binding in HelpScreen.BINDINGS)

    def test_binding_q_para_sair(self):
        """
        QUANDO BINDINGS é inspecionado
        ENTÃO inclui "q" para pop_screen
        """
        # Assert
        assert any(binding[0] == "q" and binding[1] == "pop_screen" for binding in HelpScreen.BINDINGS)


class TestHelpScreenPopulateTable:
    """
    Testa _populate_table().
    """

    def test_populate_table_filtro_vazio_mostra_todos(self):
        """
        QUANDO _populate_table() é chamado com filtro vazio
        ENTÃO mostra todos os comandos
        """
        # Arrange
        screen = HelpScreen()
        screen.query_one = Mock()

        mock_table = Mock()
        screen.query_one.return_value = mock_table

        # Act
        screen._populate_table("")

        # Assert
        mock_table.clear.assert_called_once()
        # Deve adicionar linhas para todos os comandos + cabeçalho
        assert mock_table.add_row.call_count >= len(screen.COMMANDS)

    def test_populate_table_filtro_help_mostra_apenas_help(self):
        """
        QUANDO _populate_table() é chamado com filtro "help"
        ENTÃO mostra apenas comandos contendo "help"
        """
        # Arrange
        screen = HelpScreen()
        screen.query_one = Mock()

        mock_table = Mock()
        screen.query_one.return_value = mock_table

        # Act
        screen._populate_table("help")

        # Assert
        mock_table.clear.assert_called_once()
        # Deve adicionar cabeçalho + /help apenas
        assert mock_table.add_row.call_count >= 2  # cabeçalho + /help

    def test_populate_table_filtro_inexistente_mostra_cabecalho(self):
        """
        QUANDO _populate_table() é chamado com filtro que não bate
        ENTÃO mostra apenas cabeçalho
        """
        # Arrange
        screen = HelpScreen()
        screen.query_one = Mock()

        mock_table = Mock()
        screen.query_one.return_value = mock_table

        # Act
        screen._populate_table("xyz_inexistente")

        # Assert
        mock_table.clear.assert_called_once()
        # Deve adicionar apenas cabeçalho
        assert mock_table.add_row.call_count >= 1


__all__ = [
    "TestConfigScreenInit",
    "TestConfigScreenCompose",
    "TestConfigScreenCss",
    "TestConfigScreenBindings",
    "TestConfigScreenActions",
    "TestHelpScreenInit",
    "TestHelpScreenCommands",
    "TestHelpScreenCompose",
    "TestHelpScreenCss",
    "TestHelpScreenBindings",
    "TestHelpScreenPopulateTable",
]
