# coding: utf-8
"""
Snapshot de estado - Captura e comparação de estado completo.
"""

import json
import uuid
from dataclasses import asdict, dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any

from textual.widget import Widget

from core.sky.chat.textual_ui.dom.differ import diff_state
# Import tardio para evitar circular import
# SkyTextualDOM é importado dentro de create_snapshot()


@dataclass
class DOMSnapshot:
    """
    Snapshot do estado completo do DOM em um momento.

    Atributos:
        snapshot_id: ID único do snapshot
        timestamp: Momento da captura
        name: Nome opcional do snapshot
        description: Descrição opcional
        nodes: Estado de todos os nodes (dom_id -> dict)
        structure: Árvore hierárquica (parent_id -> children_ids)
        metadata: Metadados da sessão
    """

    snapshot_id: str
    timestamp: datetime
    name: str | None = None
    description: str | None = None
    nodes: dict[str, dict] = field(default_factory=dict)
    structure: dict[str, list[str]] = field(default_factory=dict)
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict:
        """Converte para dict JSON-serializável."""
        return {
            "snapshot_id": self.snapshot_id,
            "timestamp": self.timestamp.isoformat(),
            "name": self.name,
            "description": self.description,
            "nodes": self.nodes,
            "structure": self.structure,
            "metadata": self.metadata,
        }

    def save(self, path: str) -> None:
        """Salva snapshot em arquivo JSON."""
        with open(path, "w", encoding="utf-8") as f:
            json.dump(self.to_dict(), f, indent=2, cls=DOMJSONEncoder)

    @classmethod
    def load(cls, path: str) -> "DOMSnapshot":
        """Carrega snapshot de arquivo JSON."""
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)

        data["timestamp"] = datetime.fromisoformat(data["timestamp"])
        return cls(**data)


class DOMJSONEncoder(json.JSONEncoder):
    """Encoder JSON para tipos do DOM."""

    def default(self, obj: Any) -> Any:
        if isinstance(obj, datetime):
            return obj.isoformat()
        if hasattr(obj, "__dom_state__"):
            return obj.__dom_state__()
        if hasattr(obj, "__dataclass_fields__"):
            return asdict(obj)
        return super().default(obj)


def create_snapshot(
    name: str | None = None, description: str | None = None
) -> DOMSnapshot:
    """
    Cria snapshot do estado atual do DOM.

    Args:
        name: Nome opcional do snapshot
        description: Descrição opcional

    Returns:
        DOMSnapshot capturado
    """
    # Import tardio para evitar circular import
    from core.sky.chat.textual_ui.dom.registry import SkyTextualDOM

    dom = SkyTextualDOM()

    snapshot = DOMSnapshot(
        snapshot_id=str(uuid.uuid4()),
        timestamp=datetime.now(),
        name=name,
        description=description,
    )

    # Capturar estado de todos os nodes
    for dom_id, node in dom._registry.items():
        snapshot.nodes[dom_id] = node.to_dict()

    # Capturar estrutura (parent -> children)
    for dom_id, node in dom._registry.items():
        children_ids = [c.dom_id for c in node.children]
        if children_ids:
            snapshot.structure[dom_id] = children_ids

    # Metadados
    snapshot.metadata = {
        "widget_count": len(dom._registry),
        "config": dom.get_config(),
    }

    return snapshot


def diff_snapshots(before: DOMSnapshot, after: DOMSnapshot) -> dict[str, dict]:
    """
    Compara dois snapshots e retorna as diferenças.

    Args:
        before: Snapshot anterior
        after: Snapshot posterior

    Returns:
        Dict de diffs por dom_id
    """
    result = {}

    # Nodes adicionados
    for dom_id in after.nodes:
        if dom_id not in before.nodes:
            result[dom_id] = {"type": "ADDED", "node": after.nodes[dom_id]}

    # Nodes removidos
    for dom_id in before.nodes:
        if dom_id not in after.nodes:
            result[dom_id] = {"type": "REMOVED", "node": before.nodes[dom_id]}

    # Nodes modificados
    for dom_id in before.nodes:
        if dom_id in after.nodes:
            old_state = before.nodes[dom_id]
            new_state = after.nodes[dom_id]

            state_diff = diff_state(old_state, new_state)
            if state_diff:
                result[dom_id] = {"type": "MODIFIED", "diff": state_diff}

    return result


__all__ = [
    "DOMSnapshot",
    "DOMJSONEncoder",
    "create_snapshot",
    "diff_snapshots",
]
