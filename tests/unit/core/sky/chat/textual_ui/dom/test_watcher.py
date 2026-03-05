# coding: utf-8
"""
Testes unitários de ReactiveWatcher.
"""

import time
import pytest
from textual.widgets import Static
from textual.reactive import reactive

from core.sky.chat.textual_ui.dom import SkyTextualDOM, SkyWidgetMixin
from core.sky.chat.textual_ui.dom.watcher import ReactiveWatcher


@pytest.fixture(autouse=True)
def reset_singleton():
    """Reseta o singleton antes de cada teste."""
    SkyTextualDOM._instance = None
    SkyTextualDOM._initialized = False
    yield
    SkyTextualDOM._instance = None
    SkyTextualDOM._initialized = False


class TestReactiveWatcher:
    """Testes da classe ReactiveWatcher."""

    def test_discover_reactive_props(self):
        """_discover_reactive_props encontra props reactive."""
        class TestWidget(Static):
            count = reactive(0)
            text = reactive("")

        watcher = ReactiveWatcher()
        props = watcher._discover_reactive_props(TestWidget())

        assert "count" in props
        assert "text" in props

    def test_watch_widget_cria_historico(self):
        """watch_widget cria histórico para props."""
        dom = SkyTextualDOM()
        widget = Static("Test")
        node = dom.register(widget)

        watcher = ReactiveWatcher()
        watcher.watch_widget(node)

        assert "text" in node.prop_history

    def test_trace_habilita_log(self):
        """trace() habilita log de mudanças."""
        watcher = ReactiveWatcher()
        watcher.trace("test_id", "count")
        assert "test_id" in watcher._traced_widgets

    def test_untrace_desabilita_log(self):
        """untrace() remove widget do tracing."""
        watcher = ReactiveWatcher()
        watcher.trace("test_id")
        watcher.untrace("test_id")

        assert "test_id" not in watcher._traced_widgets


class TestLoopDetection:
    """Testes de detecção de loops."""

    def test_loop_alerta_muitas_mudancas(self, capsys):
        """Loop é detectado após 100+ mudanças em 1s."""
        watcher = ReactiveWatcher()

        # Simular 101 mudanças rápidas
        for i in range(101):
            watcher._change_counts["test:prop"].append(time.time())

        # Deve emitir alerta
        captured = capsys.readouterr()
        assert "LOOP DETECTED" in captured.out
