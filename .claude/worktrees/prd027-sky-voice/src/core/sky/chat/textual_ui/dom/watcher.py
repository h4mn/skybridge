# coding: utf-8
"""
ReactiveWatcher - Rastreamento automático de props reactive.

Detecta mudanças em props reactive de widgets Textual e mantém histórico.
"""

import time
from collections import deque, defaultdict
from datetime import datetime
from typing import Any

from textual.reactive import Reactive

from core.sky.chat.textual_ui.dom.node import DOMNode, PropChange
# Logger removido - usando ChatLogger isolado
# from runtime.observability.logger import get_logger
# logger = get_logger("sky.chat.dom.watcher", level="DEBUG")


class ReactiveWatcher:
    """
    Rastreador de props reactive para widgets Textual.

    Instancia única usada pelo SkyTextualDOM para monitorar
    mudanças em props reactive de todos os widgets registrados.
    """

    def __init__(self, history_limit: int = 50):
        """
        Inicializa o watcher.

        Args:
            history_limit: Limite padrão do histórico de mudanças
        """
        self._history_limit = history_limit
        self._traced_widgets: set[str] = set()  # dom_ids sendo traceados
        self._traced_props: dict[str, set[str]] = defaultdict(set)  # dom_id -> props

        # Detecção de loops
        self._change_counts: dict[str, deque] = defaultdict(
            lambda: deque(maxlen=100)
        )  # dom_id -> timestamps
        self._loop_threshold = 100  # mudanças
        self._loop_window = 1.0  # segundos

    def watch_widget(self, node: DOMNode) -> None:
        """
        Configura rastreamento de props reactive para um widget.

        Descobre props reactive via introspecção e instala watch methods.

        Args:
            node: DOMNode do widget a monitorar
        """
        reactive_props = self._discover_reactive_props(node.widget)

        for prop_name in reactive_props:
            # Inicializar histórico vazio
            if prop_name not in node.prop_history:
                node.prop_history[prop_name] = deque(maxlen=self._history_limit)

            # Configurar watch no widget Textual
            self._install_watch(node, prop_name)

    def _discover_reactive_props(self, widget) -> list[str]:
        """
        Descobre props reactive via introspecção.

        Args:
            widget: Widget Textual

        Returns:
            Lista de nomes de props reactive
        """
        reactive_props = []

        for attr_name in dir(widget):
            if attr_name.startswith("_"):
                continue

            attr = getattr(type(widget), attr_name, None)
            if isinstance(attr, Reactive):
                reactive_props.append(attr_name)

        return reactive_props

    def _install_watch(self, node: DOMNode, prop_name: str) -> None:
        """
        Instala watch method dinâmico para uma prop.

        O watch method chamará on_prop_changed quando a prop mudar.

        Args:
            node: DOMNode do widget
            prop_name: Nome da prop reactive
        """
        widget = node.widget

        # Criar watch method
        def watch_prop(old_value: Any, new_value: Any) -> None:
            self._on_prop_changed(node, prop_name, old_value, new_value)

        # Instalar usando o mecanismo do Textual
        watch_method_name = f"watch_{prop_name}"

        # Criar método na classe se não existe
        if not hasattr(type(widget), watch_method_name):
            setattr(type(widget), watch_method_name, watch_prop)

    def _on_prop_changed(
        self, node: DOMNode, prop: str, old_value: Any, new_value: Any
    ) -> None:
        """
        Callback quando uma prop reactive muda.

        Registra a mudança no histórico e loga se tracing está ativo.

        Args:
            node: DOMNode do widget
            prop: Nome da propriedade
            old_value: Valor anterior
            new_value: Novo valor
        """
        # Registrar mudança no histórico
        node.add_prop_change(prop, old_value, new_value)

        # Detectar loops
        self._check_for_loop(node.dom_id, prop)

        # Log se tracing está ativo
        if node.dom_id in self._traced_widgets:
            if not self._traced_props[node.dom_id] or prop in self._traced_props[
                node.dom_id
            ]:
                self._log_change(node, prop, old_value, new_value)

    def _check_for_loop(self, dom_id: str, prop: str) -> None:
        """
        Detecta loops de mudança rápida.

        Args:
            dom_id: ID do widget
            prop: Nome da propriedade
        """
        now = time.time()
        key = f"{dom_id}:{prop}"
        self._change_counts[key].append(now)

        # Limpar timestamps antigos fora da janela
        cutoff = now - self._loop_window
        while self._change_counts[key] and self._change_counts[key][0] < cutoff:
            self._change_counts[key].popleft()

        # Verificar threshold
        if len(self._change_counts[key]) > self._loop_threshold:
            self._emit_loop_alert(dom_id, prop)

    def _emit_loop_alert(self, dom_id: str, prop: str) -> None:
        """Emite alerta de loop detectado."""
        from core.sky.chat.textual_ui.dom import SkyTextualDOM

        dom = SkyTextualDOM()
        node = dom.get(dom_id)

        if node:
            # logger.structured("Loop reactivo detectado", {
            #     "widget": node.class_name,
            #     "prop": prop,
            #     "changes": f">{self._loop_threshold}",
            #     "window": f"{self._loop_window}s",
            # }, level="warning")
            pass  # Silenciado - loops reativos não são mais logados

    def _log_change(
        self, node: DOMNode, prop: str, old_value: Any, new_value: Any
    ) -> None:
        """Loga mudança se tracing está ativo."""
        # timestamp = datetime.now().strftime("%H:%M:%S.%f")[:-3]
        # logger.structured("Prop reactiva alterada", {
        #     "timestamp": timestamp,
        #     "widget": node.dom_id,
        #     "prop": prop,
        #     "old_value": str(old_value),
        #     "new_value": str(new_value),
        # }, level="debug")
        pass  # Silenciado - props reativas não são mais logadas

    def trace(self, dom_id: str, prop: str | None = None) -> None:
        """
        Habilita tracing para um widget/prop.

        Args:
            dom_id: ID do widget
            prop: Nome da prop ou None para todas as props
        """
        self._traced_widgets.add(dom_id)
        if prop:
            self._traced_props[dom_id].add(prop)

    def untrace(self, dom_id: str) -> None:
        """
        Desabilita tracing para um widget.

        Args:
            dom_id: ID do widget
        """
        self._traced_widgets.discard(dom_id)
        if dom_id in self._traced_props:
            del self._traced_props[dom_id]

    def get_history(self, dom_id: str, prop: str) -> deque[PropChange]:
        """
        Retorna histórico de mudanças de uma prop.

        Args:
            dom_id: ID do widget
            prop: Nome da propriedade

        Returns:
            Deque de PropChange
        """
        from core.sky.chat.textual_ui.dom import SkyTextualDOM

        dom = SkyTextualDOM()
        node = dom.get(dom_id)

        if node:
            return node.get_prop_history(prop)
        return deque()


__all__ = ["ReactiveWatcher"]
