# -*- coding: utf-8 -*-
"""
DomainEvent Base.

Classe base para eventos de domínio.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Self
from uuid import uuid4


@dataclass(frozen=True)
class DomainEvent:
    """
    Base class para eventos de domínio.

    Eventos representam fatos ocorridos no domínio.
    São imutáveis e identificados por ID único.
    """

    event_id: str = field(default_factory=lambda: str(uuid4()))
    occurred_at: datetime = field(default_factory=datetime.now)
    event_type: str = field(default="domain_event")

    def __post_init__(self) -> None:
        # Define event_type automaticamente se não especificado
        if self.event_type == "domain_event":
            object.__setattr__(self, "event_type", self.__class__.__name__)

    def to_dict(self) -> dict:
        """Serializa evento para dicionário."""
        return {
            "event_id": self.event_id,
            "occurred_at": self.occurred_at.isoformat(),
            "event_type": self.event_type,
        }
