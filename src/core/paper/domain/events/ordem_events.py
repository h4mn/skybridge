"""
Eventos de Ordem - Ordens criadas, executadas e canceladas.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from .base_event import DomainEvent


class Lado(str, Enum):
    """Lado da ordem."""

    COMPRA = "compra"
    VENDA = "venda"


@dataclass(frozen=True, kw_only=True)
class OrdemCriada(DomainEvent):
    """
    Evento disparado quando uma nova ordem é registrada.

    Trigger: Usuário cria ordem via API/Discord
    """

    ordem_id: str
    ticker: str
    lado: Lado
    quantidade: int
    preco_limit: float | None = None

    def __post_init__(self):
        super().__post_init__()
        # Normaliza lado para string
        if isinstance(self.lado, Lado):
            object.__setattr__(self, "lado", self.lado.value)


@dataclass(frozen=True, kw_only=True)
class OrdemExecutada(DomainEvent):
    """
    Evento disparado quando uma ordem é executada.

    Trigger: Broker confirma execução
    """

    ordem_id: str
    ticker: str
    lado: Lado
    quantidade_executada: int
    preco_execucao: float

    def __post_init__(self):
        super().__post_init__()
        if isinstance(self.lado, Lado):
            object.__setattr__(self, "lado", self.lado.value)


@dataclass(frozen=True, kw_only=True)
class OrdemCancelada(DomainEvent):
    """
    Evento disparado quando uma ordem é cancelada.

    Trigger: Usuário cancela ou sistema expira
    """

    ordem_id: str
    motivo: str  # "usuario", "expiracao", "saldo_insuficiente", etc


__all__ = ["OrdemCriada", "OrdemExecutada", "OrdemCancelada", "Lado"]
