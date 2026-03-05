# coding: utf-8
"""
SkyTextualDOM - Registro global de widgets Textual.

Singleton que mantém a árvore DOM completa com:
- Registro/desregistro de widgets
- Queries por ID ou seletores CSS
- Impressão da árvore formatada
- Snapshots e diff de estado
- Tracing de props reactive
- Thread-safety para operações de mutação
"""

import re
import threading
from collections.abc import Iterator
from dataclasses import dataclass, field
from typing import Any

from textual.widget import Widget

from core.sky.chat.textual_ui.dom.node import DOMNode
from core.sky.chat.textual_ui.dom.watcher import ReactiveWatcher
from core.sky.chat.textual_ui.dom.tracer import EventTracer, EventType
from core.sky.chat.textual_ui.dom.snapshot import create_snapshot, diff_snapshots, DOMSnapshot


class SkyTextualDOM:
    """
    Singleton para registro global de widgets Textual.

    Uso:
        # Registrar widget
        SkyTextualDOM.register(widget, parent=None)

        # Buscar por ID
        node = SkyTextualDOM.get("AnimatedVerb_123")

        # Query por seletor
        nodes = SkyTextualDOM.query("AnimatedVerb")

        # Imprimir árvore
        SkyTextualDOM.print()
    """

    _instance: "SkyTextualDOM | None" = None
    _lock = threading.RLock()

    def __new__(cls) -> "SkyTextualDOM":
        """Implementa singleton pattern."""
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        """Inicializa o registro (apenas uma vez)."""
        if self._initialized:
            return

        self._registry: dict[str, DOMNode] = {}  # dom_id -> DOMNode
        self._snapshots: list["DOMSnapshot"] = []
        self._config: dict[str, Any] = {
            "history_limit": 50,
            "event_buffer_size": 1000,
        }
        self._initialized = True

    # ===================================================================
    # Registro e Desregistro
    # ===================================================================

    def register(
        self, widget: Widget, parent: Widget | None = None, dom_id: str | None = None
    ) -> DOMNode:
        """
        Registra um widget no DOM global.

        Args:
            widget: Widget Textual a registrar
            parent: Widget pai (se conhecido)
            dom_id: ID customizado ou gerado automaticamente

        Returns:
            DOMNode criado para este widget
        """
        from core.sky.chat.textual_ui.dom import _ensure_dom_id

        with self._lock:
            if dom_id is None:
                dom_id = _ensure_dom_id(widget)

            # Buscar parent DOMNode se fornecido
            parent_node = None
            if parent:
                parent_dom_id = _ensure_dom_id(parent)
                parent_node = self._registry.get(parent_dom_id)

            # Criar DOMNode
            node = DOMNode(dom_id=dom_id, widget=widget, parent=parent_node)

            # Adicionar ao parent se existir
            if parent_node and node not in parent_node.children:
                parent_node.children.append(node)

            # Registrar no índice global
            self._registry[dom_id] = node

            return node

    def unregister(self, dom_id: str) -> bool:
        """
        Remove um widget e todos os seus descendants do registro.

        Args:
            dom_id: ID do widget a remover

        Returns:
            True se removido, False se não encontrado
        """
        with self._lock:
            node = self._registry.get(dom_id)
            if not node:
                return False

            # Recursivamente desregistrar children
            for child in list(node.children):  # Copy para modificar durante iter
                self.unregister(child.dom_id)

            # Remover do parent
            if node.parent and node in node.parent.children:
                node.parent.children.remove(node)

            # Remover do registro
            del self._registry[dom_id]

            return True

    # ===================================================================
    # Queries
    # ===================================================================

    def get(self, dom_id: str) -> DOMNode | None:
        """
        Retorna DOMNode por dom_id.

        Args:
            dom_id: ID do widget

        Returns:
            DOMNode ou None se não encontrado
        """
        # Lock-free read
        return self._registry.get(dom_id)

    def query(self, selector: str) -> list[DOMNode]:
        """
        Busca widgets por seletor CSS simples.

        Sintaxe suportada:
            ClassName            - Ex: AnimatedVerb
            #id                  - Ex: #AnimatedVerb_123
            [attr=value]         - Ex: [is_visible=True]
            ClassName[attr=val]  - Combinado

        Args:
            selector: Seletor CSS

        Returns:
            Lista de DOMNodes matching (ordem de registro)
        """
        results = []

        # Parse selector
        parsed = self._parse_selector(selector)
        if not parsed:
            return results

        # Varre todos os nodes
        for node in self._registry.values():
            if self._match_selector(node, parsed):
                results.append(node)

        return results

    def _parse_selector(self, selector: str) -> dict[str, Any] | None:
        """
        Faz parse de seletor CSS simples.

        Returns:
            Dict com {class, id, attr, value} ou None
        """
        selector = selector.strip()

        # ID selector: #id
        id_match = re.match(r"^#(\w+)", selector)
        if id_match:
            return {"id": id_match.group(1)}

        # Attr selector: [attr=value] ou [attr]
        attr_match = re.match(r"^\[([^\]=]+)(?:=([^\]]+))?\]", selector)
        if attr_match:
            return {
                "attr": attr_match.group(1),
                "value": attr_match.group(2),
            }

        # Class selector (pode ter attr suffixo)
        class_match = re.match(r"^(\w+)(?:\[([^\]]+)\])?", selector)
        if class_match:
            result = {"class": class_match.group(1)}
            # Parse attr suffixo se existir
            attr_suffix = class_match.group(2)
            if attr_suffix:
                if "=" in attr_suffix:
                    attr, val = attr_suffix.split("=", 1)
                    result["attr"] = attr
                    result["value"] = val
                else:
                    result["attr"] = attr_suffix
            return result

        return None

    def _match_selector(self, node: DOMNode, parsed: dict[str, Any]) -> bool:
        """Verifica se node matches o selector parseado."""
        # Match by ID
        if "id" in parsed:
            return node.dom_id == parsed["id"]

        # Match by class
        if "class" in parsed:
            if node.class_name != parsed["class"]:
                return False

        # Match by attr
        if "attr" in parsed:
            attr_name = parsed["attr"]
            attr_value = parsed.get("value")

            # Buscar em state e reactive_props
            value = node.state.get(attr_name) or node.reactive_props.get(attr_name)

            if attr_value is not None:
                # Match exato (convertendo para string para comparação)
                return str(value) == attr_value
            else:
                # Presence check
                return value is not None

        return True

    # ===================================================================
    # Árvore
    # ===================================================================

    def tree(self) -> str:
        """
        Retorna representação visual da árvore DOM.

        Returns:
            String com árvore formatada
        """
        lines = []
        root_nodes = self._get_root_nodes()

        for root in root_nodes:
            lines.extend(self._tree_node(root, prefix="", is_last=True))

        return "\n".join(lines) if lines else "(empty)"

    def _get_root_nodes(self) -> list[DOMNode]:
        """Retorna todos os nodes sem parent."""
        return [n for n in self._registry.values() if n.parent is None]

    def _tree_node(
        self, node: DOMNode, prefix: str, is_last: bool
    ) -> list[str]:
        """Gera linhas para um nó e seus descendants."""
        lines = []

        # Linha atual
        connector = "└─" if is_last else "├─"
        lines.append(f"{prefix}{connector} {SkyTextualDOM._node_label(node)}")

        # Children
        children = node.children
        child_prefix = prefix + ("    " if is_last else "│   ")

        for i, child in enumerate(children):
            is_last_child = i == len(children) - 1
            lines.extend(self._tree_node(child, child_prefix, is_last_child))

        return lines

    @staticmethod
    def _node_label(node: DOMNode) -> str:
        """Gera label curto para o nó."""
        label = f"[{node.dom_id}]"

        # Adicionar info extra se disponível
        if not node.is_visible:
            label += " (hidden)"
        elif node.is_focused:
            label += " (focused)"

        return label

    def print(self) -> None:
        """Imprime a árvore DOM no console."""
        print(self.tree())

    # ===================================================================
    # Configuração
    # ===================================================================

    def configure(
        self, history_limit: int | None = None, event_buffer_size: int | None = None
    ) -> None:
        """
        Configura parâmetros globais do DOM.

        Args:
            history_limit: Limite do histórico de props (padrão: 50)
            event_buffer_size: Tamanho do buffer de eventos (padrão: 1000)
        """
        if history_limit is not None:
            self._config["history_limit"] = history_limit
        if event_buffer_size is not None:
            self._config["event_buffer_size"] = event_buffer_size

    def get_config(self) -> dict[str, Any]:
        """Retorna cópia da config atual."""
        return self._config.copy()

    # ===================================================================
    # Snapshots
    # ===================================================================

    def snapshot(
        self, name: str | None = None, description: str | None = None
    ) -> DOMSnapshot:
        """
        Cria snapshot do estado atual.

        Args:
            name: Nome opcional do snapshot
            description: Descrição opcional

        Returns:
            DOMSnapshot capturado
        """
        snap = create_snapshot(name, description)
        self._snapshots.append(snap)
        return snap

    def list_snapshots(self) -> list[DOMSnapshot]:
        """Retorna lista de todos os snapshots (ordem: mais recente primeiro)."""
        return list(reversed(self._snapshots))

    def load_snapshot(self, path: str) -> DOMSnapshot:
        """Carrega snapshot de arquivo."""
        from core.sky.chat.textual_ui.dom.snapshot import DOMSnapshot
        return DOMSnapshot.load(path)

    def diff_snapshots(self, snapshot_a: DOMSnapshot, snapshot_b: DOMSnapshot) -> dict:
        """Compara dois snapshots."""
        return diff_snapshots(snapshot_a, snapshot_b)

    # ===================================================================
    # Tracing
    # ===================================================================

    def trace(self, dom_id: str, prop: str | None = None) -> None:
        """
        Habilita tracing para um widget/prop.

        Args:
            dom_id: ID do widget
            prop: Nome da prop ou None para todas
        """
        if not hasattr(self, "_watcher"):
            self._watcher = ReactiveWatcher(
                history_limit=self._config["history_limit"]
            )

        self._watcher.trace(dom_id, prop)

    def untrace(self, dom_id: str) -> None:
        """
        Desabilita tracing para um widget.

        Args:
            dom_id: ID do widget
        """
        if hasattr(self, "_watcher"):
            self._watcher.untrace(dom_id)

    # ===================================================================
    # Event Tracer
    # ===================================================================

    @property
    def tracer(self) -> EventTracer:
        """Retorna o EventTracer global."""
        if not hasattr(self, "_tracer"):
            self._tracer = EventTracer(
                buffer_size=self._config["event_buffer_size"]
            )
        return self._tracer

    def capture_event(
        self,
        event_type: EventType,
        widget_dom_id: str | None = None,
        widget_class: str | None = None,
        **data,
    ) -> None:
        """Captura um evento no tracer global."""
        self.tracer.capture_event(event_type, widget_dom_id, widget_class, **data)


__all__ = ["SkyTextualDOM"]
