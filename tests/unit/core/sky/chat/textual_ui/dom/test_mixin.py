# coding: utf-8
"""
Testes unitários de SkyWidgetMixin.
"""

import pytest
from textual.widgets import Static

from core.sky.chat.textual_ui.dom import SkyTextualDOM, SkyWidgetMixin, is_dom_widget


@pytest.fixture(autouse=True)
def reset_singleton():
    """Reseta o singleton antes de cada teste."""
    SkyTextualDOM._instance = None
    SkyTextualDOM._initialized = False
    yield
    SkyTextualDOM._instance = None
    SkyTextualDOM._initialized = False


class TestSkyWidgetMixin:
    """Testes do SkyWidgetMixin."""

    def test_mixin_cria_widget_registrado(self, app):
        """Widget com mixin é registrado automaticamente."""
        class TestWidget(Static, SkyWidgetMixin):
            pass

        widget = TestWidget("Test")
        app.mount(widget)

        # on_mount é chamado pelo mount
        assert widget._dom_registered
        assert widget._dom_id is not None

    def test_mixin_com_dom_id_customizado(self, app):
        """Mixin usa dom_id customizado se fornecido."""
        class TestWidget(Static, SkyWidgetMixin):
            def __init__(self, *args, **kwargs):
                super().__init__(*args, **kwargs)
                self._dom_id = "my_custom_id"

        widget = TestWidget("Test")
        app.mount(widget)

        assert widget._dom_id == "my_custom_id"

    def test_mixin_unregister_on_unmount(self, app):
        """Widget é desregistrado quando desmontado."""
        class TestWidget(Static, SkyWidgetMixin):
            pass

        widget = TestWidget("Test")
        app.mount(widget)

        dom_id = widget._dom_id
        dom = SkyTextualDOM()

        assert dom.get(dom_id) is not None

        app.unmount(widget)
        assert dom.get(dom_id) is None

    def test_mixin_parent_link(self, app):
        """Mixin detecta parent corretamente."""
        class TestWidget(Static, SkyWidgetMixin):
            pass

        parent = TestWidget("Parent")
        child = TestWidget("Child")

        app.mount(parent)
        parent.mount(child)

        dom = SkyTextualDOM()
        parent_node = dom.get(parent._dom_id)
        child_node = dom.get(child._dom_id)

        assert child_node.parent is parent_node
        assert child_node in parent_node.children

    def test_widget_sem_mixin_nao_registra(self, app):
        """Widget sem mixin não é registrado."""
        widget = Static("Test")
        app.mount(widget)

        dom = SkyTextualDOM()

        assert len(dom._registry) == 0

    def test_get_dom_node(self, app):
        """get_dom_node() retorna o DOMNode."""
        class TestWidget(Static, SkyWidgetMixin):
            pass

        widget = TestWidget("Test")
        app.mount(widget)

        node = widget.get_dom_node()

        assert node is not None
        assert node.widget is widget

    def test_is_dom_widget_helper(self):
        """is_dom_widget() identifica widgets com mixin."""
        class MixinWidget(Static, SkyWidgetMixin):
            pass

        class PlainWidget(Static):
            pass

        mixin = MixinWidget("Test")
        plain = PlainWidget("Test")

        assert is_dom_widget(mixin)
        assert not is_dom_widget(plain)
