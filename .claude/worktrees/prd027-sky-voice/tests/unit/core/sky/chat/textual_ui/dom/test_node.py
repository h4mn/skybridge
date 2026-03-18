# coding: utf-8
"""
Testes unitários de DOMNode.
"""

from datetime import datetime

import pytest
from textual.widgets import Static

from core.sky.chat.textual_ui.dom.node import DOMNode, PropChange


class TestDOMNode:
    """Testes da classe DOMNode."""

    def test_init_basico(self, sample_widget):
        """DOMNode é criado com valores básicos corretos."""
        node = DOMNode(dom_id="test_1", widget=sample_widget)

        assert node.dom_id == "test_1"
        assert node.widget is sample_widget
        assert node.parent is None
        assert node.children == []
        assert node.class_name == "Static"
        assert node.state is not None
        assert node.reactive_props is not None

    def test_to_dict_serializa(self, sample_widget):
        """to_dict() retorna dict serializável sem referências circulares."""
        node = DOMNode(dom_id="test_1", widget=sample_widget)

        result = node.to_dict()

        assert result["dom_id"] == "test_1"
        assert result["class_name"] == "Static"
        assert "widget" not in result  # Não serializa a referência
        assert isinstance(result["state"], dict)
        assert isinstance(result["position"], tuple)

    def test_add_prop_change(self, sample_widget):
        """add_prop_change() adiciona mudança ao histórico."""
        node = DOMNode(dom_id="test_1", widget=sample_widget)

        node.add_prop_change("count", 0, 1, "user")

        history = node.get_prop_history("count")
        assert len(history) == 1

        change = history[0]
        assert isinstance(change, PropChange)
        assert change.old_value == 0
        assert change.new_value == 1
        assert change.source == "user"
        assert isinstance(change.timestamp, datetime)

    def test_prop_history_respeita_limit(self, sample_widget):
        """Histórico respeita maxlen configurado."""
        node = DOMNode(dom_id="test_1", widget=sample_widget, _history_limit=3)

        for i in range(10):
            node.add_prop_change("x", i, i + 1)

        history = node.get_prop_history("x")
        assert len(history) == 3  # Apenas as últimas 3

        # Deve ser 7→8, 8→9, 9→10 (mais recentes)
        assert history[0].old_value == 7
        assert history[-1].new_value == 10

    def test_set_history_limit(self, sample_widget):
        """set_history_limit() ajusta limite e trunca se necessário."""
        node = DOMNode(dom_id="test_1", widget=sample_widget, _history_limit=10)

        for i in range(10):
            node.add_prop_change("y", i, i + 1)

        assert len(node.get_prop_history("y")) == 10

        # Reduzir limite
        node.set_history_limit(3)
        assert len(node.get_prop_history("y")) == 3

    def test_get_prop_history_vazio(self, sample_widget):
        """get_prop_history() retorna deque vazio para prop inexistente."""
        node = DOMNode(dom_id="test_1", widget=sample_widget)

        history = node.get_prop_history("inexistente")
        assert len(history) == 0

    def test_parent_children_relationship(self):
        """Parent e children são mantidos corretamente."""
        parent = Static(id="parent")
        child = Static(id="child")

        parent_node = DOMNode(dom_id="parent_1", widget=parent)
        child_node = DOMNode(dom_id="child_1", widget=child, parent=parent_node)

        assert child_node.parent is parent_node
        assert child_node in parent_node.children

    def test_state_snapshot_inclui_position(self, sample_widget):
        """get_state_snapshot() inclui posição atual."""
        node = DOMNode(dom_id="test_1", widget=sample_widget)

        snapshot = node.get_state_snapshot()

        assert "position" in snapshot["state"]
        assert len(snapshot["position"]) == 4  # x, y, w, h

    def test_serialize_value_primitivos(self):
        """_serialize_value() mantém primitivos como estão."""
        node = DOMNode(dom_id="test_1", widget=Static())

        assert node._serialize_value("text") == "text"
        assert node._serialize_value(42) == 42
        assert node._serialize_value(3.14) == 3.14
        assert node._serialize_value(True) is True
        assert node._serialize_value(None) is None

    def test_serialize_value_listas(self):
        """_serialize_value() serializa listas recursivamente."""
        node = DOMNode(dom_id="test_1", widget=Static())

        result = node._serialize_value([1, "a", None])
        assert result == [1, "a", None]

    def test_serialize_value_dict(self):
        """_serialize_value() serializa dicts recursivamente."""
        node = DOMNode(dom_id="test_1", widget=Static())

        result = node._serialize_value({"a": 1, "b": [2, 3]})
        assert result == {"a": 1, "b": [2, 3]}

    def test_serialize_value_dataclass(self):
        """_serialize_value() converte dataclass para dict."""
        from dataclasses import dataclass

        @dataclass
        class DummyData:
            x: int
            y: str

        node = DOMNode(dom_id="test_1", widget=Static())
        value = DummyData(x=1, y="test")

        result = node._serialize_value(value)
        assert result == {"x": 1, "y": "test"}

    def test_serialize_value_outro_tipo_converte_string(self):
        """_serialize_value() converte outros tipos para string."""
        node = DOMNode(dom_id="test_1", widget=Static())

        class DummyClass:
            def __str__(self):
                return "Dummy"

        result = node._serialize_value(DummyClass())
        assert result == "Dummy"


# Fixtures
@pytest.fixture
def sample_widget():
    """Widget de exemplo para testes."""
    return Static("Test Widget", id="test_widget")
