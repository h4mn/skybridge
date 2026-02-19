# -*- coding: utf-8 -*-
"""
Testes para TrelloKanbanListsConfig.

TDD Estrito: Testes que documentam o comportamento esperado da configuração.

DOC: runtime/config/config.py - TrelloKanbanListsConfig
DOC: core.kanban.domain.kanban_lists_config - FONTE ÚNICA DA VERDADE
"""
import pytest

from runtime.config.config import TrelloKanbanListsConfig


class TestTrelloKanbanListsConfigProperties:
    """Testa propriedades de conveniência para compatibilidade."""

    def test_todo_property_returns_nome_lista_a_fazer(self):
        """
        DOC: Propriedade 'todo' deve retornar nome da lista 'A Fazer' (SEM emoji).

        Compatibilidade com código legado em trello_service.py que usa:
            target_list_name=self.kanban_config.todo

        NOTA: get_list_names() retorna nomes SEM emoji (FONTE ÚNICA DA VERDADE).
        Para nomes com emoji, use get_list_names_with_emoji().
        """
        config = TrelloKanbanListsConfig()
        assert config.todo == "A Fazer"

    def test_progress_property_returns_nome_lista_em_andamento(self):
        """
        DOC: Propriedade 'progress' deve retornar nome da lista 'Em Andamento' (SEM emoji).

        Compatibilidade com código legado em trello_service.py que usa:
            target_list_name=self.kanban_config.progress

        NOTA: get_list_names() retorna nomes SEM emoji (FONTE ÚNICA DA VERDADE).
        Para nomes com emoji, use get_list_names_with_emoji().
        """
        config = TrelloKanbanListsConfig()
        assert config.progress == "Em Andamento"


class TestTrelloKanbanListsConfigLabelMapping:
    """Testa mapeamento de labels do GitHub para Trello."""

    def test_label_mapping_attribute_exists(self):
        """
        DOC: Atributo 'label_mapping' deve existir.

        Compatibilidade com código legado em trello_service.py que usa:
            label_mapping = self.kanban_config.label_mapping
        """
        config = TrelloKanbanListsConfig()
        assert hasattr(config, "label_mapping")
        assert isinstance(config.label_mapping, dict)

    def test_label_mapping_has_github_standard_labels(self):
        """
        DOC: label_mapping deve conter mapeamento para labels padrão GitHub.

        Labels mapeados: bug, feature, enhancement, documentation, good-first-issue
        """
        config = TrelloKanbanListsConfig()
        assert "bug" in config.label_mapping
        assert "feature" in config.label_mapping
        assert "enhancement" in config.label_mapping
        assert "documentation" in config.label_mapping
        assert "good-first-issue" in config.label_mapping

    def test_label_mapping_values_are_tuples(self):
        """
        DOC: Cada label deve mapear para (nome_trello, cor).

        Formato esperado: ("nome", "cor")
        """
        config = TrelloKanbanListsConfig()
        for key, value in config.label_mapping.items():
            assert isinstance(value, tuple)
            assert len(value) == 2
            assert isinstance(value[0], str)  # nome
            assert isinstance(value[1], str)  # cor


class TestTrelloKanbanListsConfigAutoCreateLists:
    """Testa flag de auto-configuração de listas."""

    def test_auto_create_lists_attribute_exists(self):
        """
        DOC: Atributo 'auto_create_lists' deve existir.

        Compatibilidade com código legado em trello_service.py que usa:
            if not self.kanban_config.auto_create_lists:
        """
        config = TrelloKanbanListsConfig()
        assert hasattr(config, "auto_create_lists")
        assert isinstance(config.auto_create_lists, bool)

    def test_auto_create_lists_default_is_false(self):
        """
        DOC: auto_create_lists deve ser False por padrão.

        Auto-configuração de listas deve ser opt-in para evitar
        modificações acidentais no board do Trello.
        """
        config = TrelloKanbanListsConfig()
        assert config.auto_create_lists is False


class TestTrelloKanbanListsConfigListMethods:
    """Testa métodos para obter nomes e cores das listas."""

    def test_get_list_names_returns_list(self):
        """
        DOC: get_list_names() deve retornar lista de nomes das listas (SEM emoji).

        Compatibilidade com código legado em trello_service.py que usa:
            list_names = self.kanban_config.get_list_names()

        NOTA: Retorna nomes SEM emoji. Para nomes com emoji, use get_list_names_with_emoji().
        """
        config = TrelloKanbanListsConfig()
        names = config.get_list_names()
        assert isinstance(names, list)
        assert all(isinstance(name, str) for name in names)

    def test_get_list_names_contains_standard_lists(self):
        """
        DOC: get_list_names() deve conter listas padrão Kanban (SEM emoji).

        get_list_names() retorna nomes SEM emoji (FONTE ÚNICA DA VERDADE).
        Para nomes com emoji, use get_list_names_with_emoji().

        Listas esperadas: Issues, Brainstorm, A Fazer, Em Andamento, Em Revisão, Publicar
        """
        config = TrelloKanbanListsConfig()
        names = config.get_list_names()
        assert "Issues" in names
        assert "Brainstorm" in names
        assert "A Fazer" in names
        assert "Em Andamento" in names
        assert "Em Revisão" in names
        assert "Publicar" in names

    def test_get_list_names_with_emoji_contains_standard_lists(self):
        """
        DOC: get_list_names_with_emoji() deve conter listas padrão Kanban COM emoji.

        Para uso no Trello e frontend onde emojis são necessários.
        """
        config = TrelloKanbanListsConfig()
        names = config.get_list_names_with_emoji()
        assert "📥 Issues" in names
        assert "🧠 Brainstorm" in names
        assert "📋 A Fazer" in names
        assert "🚧 Em Andamento" in names
        assert "👀 Em Revisão" in names
        assert "🚀 Publicar" in names

    def test_get_list_colors_returns_dict(self):
        """
        DOC: get_list_colors() deve retornar dict nome -> cor.

        Compatibilidade com código legado em trello_service.py que usa:
            list_colors = self.kanban_config.get_list_colors()

        NOTA: Chaves são nomes SEM emoji. Para chaves com emoji, use get_list_colors_with_emoji().
        """
        config = TrelloKanbanListsConfig()
        colors = config.get_list_colors()
        assert isinstance(colors, dict)
        assert all(isinstance(k, str) for k in colors.keys())
        assert all(isinstance(v, str) for v in colors.values())

    def test_get_list_colors_matches_list_names(self):
        """
        DOC: get_list_colors() deve ter cores para todas as listas.

        Cada lista em get_list_names() deve ter uma cor correspondente.
        Chaves são nomes SEM emoji (FONTE ÚNICA DA VERDADE).
        """
        config = TrelloKanbanListsConfig()
        names = config.get_list_names()
        colors = config.get_list_colors()

        for name in names:
            assert name in colors, f"Lista '{name}' não tem cor definida"
