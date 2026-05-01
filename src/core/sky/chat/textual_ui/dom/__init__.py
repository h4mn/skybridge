# coding: utf-8
"""
SkyTextualDOM - Sistema DOM-like para Textual TUI.

Fornece registro global de widgets, rastreamento de estado reactive,
snapshots, event tracing e interface DevTools.

API principal:
    SkyTextualDOM - Singleton para registro/queries
    register() / unregister() - Gerenciar widgets
    get() / query() - Buscar widgets
    snapshot() / diff() - Capturar e comparar estado
    trace() / untrace() - Rastrear mudanças de props
    print() - Imprimir árvore de widgets
"""

from textual.widget import Widget

from core.sky.chat.textual_ui.dom.node import DOMNode
from core.sky.chat.textual_ui.dom.registry import SkyTextualDOM
from core.sky.chat.textual_ui.dom.mixin import SkyWidgetMixin, is_dom_widget
from core.sky.chat.textual_ui.dom.watcher import ReactiveWatcher
from core.sky.chat.textual_ui.dom.tracer import EventType, EventEntry, EventTracer
from core.sky.chat.textual_ui.dom.snapshot import DOMSnapshot, create_snapshot, diff_snapshots
from core.sky.chat.textual_ui.dom.differ import diff_state, format_diff

__all__ = [
    "DOMNode",
    "SkyTextualDOM",
    "SkyWidgetMixin",
    "is_dom_widget",
    "ReactiveWatcher",
    "EventType",
    "EventEntry",
    "EventTracer",
    "DOMSnapshot",
    "create_snapshot",
    "diff_snapshots",
    "diff_state",
    "format_diff",
]


def _ensure_dom_id(widget: Widget) -> str:
    """Helper para gerar dom_id se widget não tiver."""
    if hasattr(widget, "_dom_id") and widget._dom_id:
        return widget._dom_id
    return f"{widget.__class__.__name__}_{id(widget)}"
