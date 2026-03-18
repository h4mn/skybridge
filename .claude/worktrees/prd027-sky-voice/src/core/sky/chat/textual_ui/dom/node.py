# coding: utf-8
"""
DOMNode - Wrapper para widget Textual com estado e histórico.

Cada DOMNode representa um widget na árvore DOM, mantendo:
- Estado serializável do widget
- Props reactive atuais
- Histórico de mudanças de props
- Referências para parent/children
"""

from collections import deque
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Generic, TypeVar

from textual.geometry import Offset, Size
from textual.widget import Widget

W = TypeVar("W", bound=Widget)


@dataclass
class PropChange:
    """Uma mudança em uma prop reactive."""

    timestamp: datetime
    old_value: Any
    new_value: Any
    source: str = "unknown"  # "user", "system", "timer"


@dataclass
class DOMNode:
    """
    Nó da árvore DOM representando um widget Textual.

    Atributos:
        dom_id: Identificador único do widget
        widget: Referência para o widget Textual
        parent: DOMNode pai ou None (root)
        children: Lista de DOMNodes filhos
        state: Estado serializável do widget
        reactive_props: Props reactive atuais
        prop_history: Histórico de mudanças por prop
        class_name: Nome da classe do widget
        is_visible: Se o widget está visível
        is_focused: Se o widget tem foco
        position: Tupla (x, y, width, height)
    """

    dom_id: str
    widget: Widget
    parent: "DOMNode | None" = None
    children: list["DOMNode"] = field(default_factory=list)

    # Estado serializável
    state: dict[str, Any] = field(default_factory=dict)
    reactive_props: dict[str, Any] = field(default_factory=dict)

    # Histórico de mudanças (configurável)
    prop_history: dict[str, deque[PropChange]] = field(
        default_factory=lambda: {}  # prop -> deque de mudanças
    )

    # Metadata
    class_name: str = ""
    is_visible: bool = True
    is_focused: bool = False
    position: tuple[int, int, int, int] = (0, 0, 0, 0)  # x, y, w, h

    # Configuração
    _history_limit: int = 50

    def __post_init__(self):
        """Inicializa class_name e extrai estado inicial."""
        if not self.class_name:
            self.class_name = self.widget.__class__.__name__
        self._refresh_state()
        self._refresh_reactive_props()

    def to_dict(self) -> dict[str, Any]:
        """
        Converte DOMNode para dict serializável.

        Returns:
            Dict com todos os dados do nó, exceto referência ao widget.
        """
        return {
            "dom_id": self.dom_id,
            "class_name": self.class_name,
            "state": self.state.copy(),
            "reactive_props": self.reactive_props.copy(),
            "is_visible": self.is_visible,
            "is_focused": self.is_focused,
            "position": self.position,
            "parent_dom_id": self.parent.dom_id if self.parent else None,
            "children_dom_ids": [c.dom_id for c in self.children],
        }

    def get_state_snapshot(self) -> dict[str, Any]:
        """
        Extrai snapshot completo do estado atual do widget.

        Atualiza state e reactive_props e retorna dict completo.
        """
        self._refresh_state()
        self._refresh_reactive_props()
        return self.to_dict()

    def add_prop_change(
        self, prop: str, old_value: Any, new_value: Any, source: str = "unknown"
    ) -> None:
        """
        Adiciona uma mudança de prop ao histórico.

        Args:
            prop: Nome da propriedade
            old_value: Valor anterior
            new_value: Novo valor
            source: Origem da mudança (user, system, timer)
        """
        if prop not in self.prop_history:
            self.prop_history[prop] = deque(maxlen=self._history_limit)

        change = PropChange(
            timestamp=datetime.now(),
            old_value=old_value,
            new_value=new_value,
            source=source,
        )
        self.prop_history[prop].append(change)

    def get_prop_history(self, prop: str) -> deque[PropChange]:
        """
        Retorna histórico de mudanças de uma prop.

        Args:
            prop: Nome da propriedade

        Returns:
            Deque de PropChange ou deque vazio se prop não existe.
        """
        return self.prop_history.get(prop, deque())

    def set_history_limit(self, limit: int) -> None:
        """
        Define limite do histórico para futuras mudanças.

        Args:
            limit: Novo limite (número de entradas)
        """
        self._history_limit = limit
        for prop, history in self.prop_history.items():
            # Recriar deque com novo maxlen
            if limit < len(history):
                # Truncar se novo limite é menor
                new_history = deque(list(history)[-limit:], maxlen=limit)
            else:
                new_history = deque(history, maxlen=limit)
            self.prop_history[prop] = new_history

    # ------------------------------------------------------------------
    # Private methods
    # ------------------------------------------------------------------

    def _refresh_state(self) -> None:
        """Atualiza state com metadata atual do widget."""
        self.state = {
            "id": self.widget.id,
            "classes": list(self.widget.classes),  # Copy para evitar mutação
            "disabled": self.widget.disabled,
        }

        # Position e size
        region = self.widget.region
        self.position = (
            region.x,
            region.y,
            region.width,
            region.height,
        )
        self.state["position"] = self.position

        # Visibility
        self.is_visible = self.widget.is_visible
        self.state["is_visible"] = self.is_visible

        # Focus
        self.is_focused = self.widget.has_focus
        self.state["is_focused"] = self.is_focused

    def _refresh_reactive_props(self) -> None:
        """
        Extrai props reactive do widget via introspecção.

        Busca atributos anotados com textual.reactive ou watch_* methods.
        """
        from textual.reactive import Reactive

        self.reactive_props = {}

        # Buscar props com tipo Reactive
        for attr_name in dir(self.widget):
            if attr_name.startswith("_"):
                continue

            attr = getattr(type(self.widget), attr_name, None)
            if isinstance(attr, Reactive):
                # Prop é reactive - pegar valor atual
                try:
                    value = getattr(self.widget, attr_name)
                    self.reactive_props[attr_name] = self._serialize_value(value)
                except Exception:
                    # Falha silenciosa se prop não pode ser lida
                    pass

    def _serialize_value(self, value: Any) -> Any:
        """
        Serializa valor para formato JSON-friendly.

        Args:
            value: Valor a serializar

        Returns:
            Valor serializado (dict, list, primitive)
        """
        if isinstance(value, (str, int, float, bool, type(None))):
            return value

        if isinstance(value, (list, tuple)):
            return [self._serialize_value(v) for v in value]

        if isinstance(value, dict):
            return {k: self._serialize_value(v) for k, v in value.items()}

        # Dataclasses
        if hasattr(value, "__dataclass_fields__"):
            from dataclasses import asdict

            return asdict(value)

        # Outros tipos - converte para string
        return str(value)


__all__ = ["DOMNode", "PropChange"]
