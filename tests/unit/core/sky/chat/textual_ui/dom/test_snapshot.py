# coding: utf-8
"""
Testes unitários de Snapshot e Tracer.
"""

import json
import pytest
from datetime import datetime

from core.sky.chat.textual_ui.dom import SkyTextualDOM
from core.sky.chat.textual_ui.dom.snapshot import create_snapshot, diff_snapshots, DOMSnapshot, DOMJSONEncoder
from core.sky.chat.textual_ui.dom.tracer import EventType, EventTracer, EventEntry


@pytest.fixture(autouse=True)
def reset_singleton():
    """Reseta o singleton antes de cada teste."""
    SkyTextualDOM._instance = None
    SkyTextualDOM._initialized = False
    yield
    SkyTextualDOM._instance = None
    SkyTextualDOM._initialized = False


class TestDOMSnapshot:
    """Testes de DOMSnapshot."""

    def test_create_snapshot_captura_estado(self, sample_widgets):
        """create_snapshot captura estado de todos os widgets."""
        dom = SkyTextualDOM()
        for widget in sample_widgets:
            dom.register(widget)

        snapshot = create_snapshot()

        assert len(snapshot.nodes) == len(sample_widgets)
        assert snapshot.metadata["widget_count"] == len(sample_widgets)

    def test_snapshot_to_dict(self):
        """to_dict() serializa snapshot."""
        snapshot = DOMSnapshot(
            snapshot_id="test",
            timestamp=datetime.now(),
        )
        snapshot.nodes = {"test": {"class": "Static"}}

        result = snapshot.to_dict()

        assert result["snapshot_id"] == "test"
        assert "timestamp" in result
        assert result["nodes"]["test"]["class"] == "Static"

    def test_diff_snapshots_encontra_mudancas(self):
        """diff_snapshots detecta nodes modificados."""
        snap1 = DOMSnapshot(
            snapshot_id="s1",
            timestamp=datetime.now(),
        )
        snap1.nodes = {"w1": {"class": "Static", "count": 1}}

        snap2 = DOMSnapshot(
            snapshot_id="s2",
            timestamp=datetime.now(),
        )
        snap2.nodes = {"w1": {"class": "Static", "count": 2}}

        diff = diff_snapshots(snap1, snap2)

        assert "w1" in diff
        assert diff["w1"]["type"] == "MODIFIED"


class TestDOMJSONEncoder:
    """Testes do encoder JSON customizado."""

    def test_datetime_para_isoformat(self):
        """Datetime é convertido para ISO format."""
        encoder = DOMJSONEncoder()
        dt = datetime(2025, 1, 1, 12, 0, 0)

        result = encoder.default(dt)

        assert result == "2025-01-01T12:00:00"

    def test_dataclass_para_dict(self):
        """Dataclass é convertida para dict."""
        from dataclasses import dataclass

        @dataclass
        class TestData:
            x: int

        encoder = DOMJSONEncoder()
        data = TestData(x=42)

        result = encoder.default(data)

        assert result == {"x": 42}


class TestEventTracer:
    """Testes de EventTracer."""

    def test_capture_event_cria_entry(self):
        """capture_event cria EventEntry."""
        tracer = EventTracer()
        entry = tracer.capture_event(EventType.MOUNT, widget_dom_id="test")

        assert isinstance(entry, EventEntry)
        assert entry.event_type == EventType.MOUNT
        assert entry.widget_dom_id == "test"

    def test_capture_event adiciona_ao_buffer(self):
        """capture_event adiciona ao buffer."""
        tracer = EventTracer(buffer_size=5)
        tracer.capture_event(EventType.MOUNT)
        tracer.capture_event(EventType.UNMOUNT)

        assert len(tracer._buffer) == 2

    def test_buffer_respeita_maxlen(self):
        """Buffer descarta entradas antigas ao atingir limite."""
        tracer = EventTracer(buffer_size=3)

        for _ in range(5):
            tracer.capture_event(EventType.MOUNT)

        assert len(tracer._buffer) == 3

    def test_filter_por_tipo(self):
        """filter() retorna apenas eventos do tipo especificado."""
        tracer = EventTracer()
        tracer.capture_event(EventType.MOUNT)
        tracer.capture_event(EventType.UNMOUNT)
        tracer.capture_event(EventType.ERROR)

        results = tracer.filter(event_types=[EventType.MOUNT, EventType.ERROR])

        assert len(results) == 2

    def test_search_textual(self):
        """search() busca por texto em eventos."""
        tracer = EventTracer()
        tracer.capture_event(EventType.ERROR, widget_dom_id="widget_123")

        results = tracer.search("widget_123")

        assert len(results) == 1

    def test_export_json(self):
        """export(fmt='json') retorna JSON string."""
        tracer = EventTracer()
        tracer.capture_event(EventType.MOUNT, widget_dom_id="test")

        result = tracer.export(fmt="json")

        data = json.loads(result)
        assert len(data) == 1
        assert data[0]["widget_dom_id"] == "test"

    def test_subscribe_callback(self):
        """subscribe() registra callback chamado para novos eventos."""
        tracer = EventTracer()
        called = []

        def callback(entry):
            called.append(entry)

        tracer.subscribe(callback)
        tracer.capture_event(EventType.MOUNT)

        assert len(called) == 1

    def test_clear_limpa_buffers(self):
        """clear() remove todos os eventos."""
        tracer = EventTracer()
        tracer.capture_event(EventType.MOUNT)
        tracer.capture_event(EventType.ERROR)

        tracer.clear()

        assert len(tracer._buffer) == 0
        assert len(tracer._critical) == 0


# Fixtures
@pytest.fixture
def sample_widgets():
    """Widgets de exemplo para testes."""
    from textual.widgets import Static

    return [
        Static("Widget 1", id="w1"),
        Static("Widget 2", id="w2"),
        Static("Widget 3", id="w3"),
    ]
