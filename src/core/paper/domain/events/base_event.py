"""
Evento Base de Domínio.

Todos os eventos de domínio herdam de DomainEvent.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any
from dataclasses import dataclass, field


@dataclass(frozen=True, kw_only=True)
class DomainEvent:
    """
    Evento base de domínio.

    Todos os eventos contêm:
    - occurred_at: Timestamp de quando ocorreu
    - event_type: Tipo do evento (para routing)
    - metadata: Dados adicionais opcionais
    """

    occurred_at: datetime = field(default_factory=datetime.now)
    event_type: str = field(init=False)
    metadata: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        """Define event_type baseado no nome da classe."""
        if not getattr(self, "event_type", None):
            object.__setattr__(self, "event_type", self.__class__.__name__)

    def to_dict(self) -> dict[str, Any]:
        """Converte evento para dict (para serialização)."""
        from dataclasses import asdict

        data = asdict(self)
        data["occurred_at"] = self.occurred_at.isoformat()
        data["event_type"] = self.event_type
        return data

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> DomainEvent:
        """Cria evento a partir de dict (para deserialização)."""
        # Remove event_type (é init=False, definido automaticamente)
        data_copy = data.copy()
        data_copy.pop("event_type", None)

        if "occurred_at" in data_copy:
            data_copy["occurred_at"] = datetime.fromisoformat(data_copy["occurred_at"])
        return cls(**data_copy)


__all__ = ["DomainEvent"]
