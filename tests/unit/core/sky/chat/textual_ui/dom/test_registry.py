# coding: utf-8
"""
Testes unitários de SkyTextualDOM Registry.
"""

import pytest
from textual.widgets import Static

from core.sky.chat.textual_ui.dom.registry import SkyTextualDOM
from core.sky.chat.textual_ui.dom.node import DOMNode


@pytest.fixture(autouse=True)
def reset_singleton():
    """Reseta o singleton antes de cada teste."""
    SkyTextualDOM._instance = None
    SkyTextualDOM._initialized = False
    yield
    SkyTextualDOM._instance = None
    SkyTextualDOM._initialized = False


class TestSkyTextualDOM:
    """Testes da classe SkyTextualDOM."""

    def test_singleton_pattern(self):
        """SkyTextualDOM é um singleton."""
        dom1 = SkyTextualDOM()
        dom2 = SkyTextualDOM()

        assert dom1 is dom2

    def test_register_widget_simples(self):
        """register() cria DOMNode para widget."""
        dom = SkyTextualDOM()
        widget = Static("Test")

        node = dom.register(widget)

        assert isinstance(node, DOMNode)
        assert node.widget is widget
        assert node.dom_id in dom._registry

    def test_register_com_dom_id_customizado(self):
        """register() aceita dom_id customizado."""
        dom = SkyTextualDOM()
        widget = Static("Test")

        node = dom.register(widget, dom_id="meu_id")

        assert node.dom_id == "meu_id"

    def test_register_com_parent(self):
        """register() vincula parent e children."""
        dom = SkyTextualDOM()
        parent = Static("Parent")
        child = Static("Child")

        parent_node = dom.register(parent)
        child_node = dom.register(child, parent=parent)

        assert child_node.parent is parent_node
        assert child_node in parent_node.children

    def test_unregister_remove_node(self):
        """unregister() remove node do registro."""
        dom = SkyTextualDOM()
        widget = Static("Test")
        node = dom.register(widget)

        result = dom.unregister(node.dom_id)

        assert result is True
        assert node.dom_id not in dom._registry

    def test_unregister_remove_descendants(self):
        """unregister() remove recursivamente descendants."""
        dom = SkyTextualDOM()
        root = Static("Root")
        child1 = Static("Child1")
        child2 = Static("Child2")

        root_node = dom.register(root)
        child1_node = dom.register(child1, parent=root)
        child2_node = dom.register(child2, parent=child1)

        # unregister root deve remover todos
        dom.unregister(root_node.dom_id)

        assert root_node.dom_id not in dom._registry
        assert child1_node.dom_id not in dom._registry
        assert child2_node.dom_id not in dom._registry

    def test_get_retorna_node_por_id(self):
        """get() retorna node por dom_id."""
        dom = SkyTextualDOM()
        widget = Static("Test")
        node = dom.register(widget, dom_id="test_id")

        result = dom.get("test_id")

        assert result is node

    def test_get_retorna_none_se_inexistente(self):
        """get() retorna None se ID não existe."""
        dom = SkyTextualDOM()

        result = dom.get("inexistente")

        assert result is None

    def test_query_por_classe(self):
        """query() busca por nome de classe."""
        dom = SkyTextualDOM()
        w1 = Static("A")
        w2 = Static("B")

        dom.register(w1, dom_id="static_1")
        dom.register(w2, dom_id="static_2")

        results = dom.query("Static")

        assert len(results) == 2
        assert all(n.class_name == "Static" for n in results)

    def test_query_por_id(self):
        """query() busca por ID com #."""
        dom = SkyTextualDOM()
        w = Static("Test")
        dom.register(w, dom_id="meu_widget")

        results = dom.query("#meu_widget")

        assert len(results) == 1
        assert results[0].dom_id == "meu_widget"

    def test_query_por_attr_valor(self):
        """query() busca por attr/value."""
        dom = SkyTextualDOM()
        w = Static("Test")
        node = dom.register(w)
        node.state["custom"] = "value"

        results = dom.query("[custom=value]")

        assert len(results) == 1
        assert results[0] is node

    def test_query_composta_classe_attr(self):
        """query() busca com classe + attr."""
        dom = SkyTextualDOM()
        w1 = Static("A")
        w2 = Static("B")

        n1 = dom.register(w1, dom_id="s1")
        n2 = dom.register(w2, dom_id="s2")

        n1.state["visible"] = True
        n2.state["visible"] = False

        results = dom.query("Static[visible=False]")

        assert len(results) == 1
        assert results[0].dom_id == "s2"

    def test_query_vazio_retorna_lista_vazia(self):
        """query() retorna [] se nenhum match."""
        dom = SkyTextualDOM()

        results = dom.query("Inexistente")

        assert results == []

    def test_tree_retorna_string_formatada(self):
        """tree() retorna árvore formatada."""
        dom = SkyTextualDOM()
        root = Static("Root")
        child = Static("Child")

        dom.register(root, dom_id="root")
        dom.register(child, parent=root, dom_id="child")

        result = dom.tree()

        assert "root" in result
        assert "child" in result
        assert "└─" in result

    def test_tree_vazio_retorna_empty(self):
        """tree() retorna (empty) se nenhum widget."""
        dom = SkyTextualDOM()

        result = dom.tree()

        assert result == "(empty)"

    def test_configure_atualiza_config(self):
        """configure() atualiza parâmetros."""
        dom = SkyTextualDOM()

        dom.configure(history_limit=100, event_buffer_size=2000)

        assert dom._config["history_limit"] == 100
        assert dom._config["event_buffer_size"] == 2000

    def test_get_config_retorna_copia(self):
        """get_config() retorna cópia da config."""
        dom = SkyTextualDOM()

        config1 = dom.get_config()
        config1["history_limit"] = 999

        config2 = dom.get_config()

        assert config2["history_limit"] != 999


class TestThreadSafety:
    """Testes de thread-safety."""

    def test_register_concorrente(self, threading_pool):
        """Múltiplas threads podem registrar simultaneamente."""
        import threading

        dom = SkyTextualDOM()
        errors = []
        nodes = []

        def register_widget(i):
            try:
                w = Static(f"Widget{i}")
                node = dom.register(w, dom_id=f"w{i}")
                nodes.append(node.dom_id)
            except Exception as e:
                errors.append(e)

        threads = [threading.Thread(target=register_widget, args=(i,)) for i in range(20)]

        for t in threads:
            t.start()
        for t in threads:
            t.join()

        assert not errors
        assert len(nodes) == 20
        assert len(dom._registry) == 20
