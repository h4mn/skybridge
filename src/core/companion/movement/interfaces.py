"""IMovementState — interface abstrata para estados de movimentação.

Spec ref: movement-state-machine — Interface IMovementState
"""
from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from src.core.companion.movement.context import MovementContext


class IMovementState(ABC):
    """Interface que cada estado de movimentação DEVE implementar.

    Novos estados = nova classe, sem modificar existentes.
    """

    @abstractmethod
    def get_target_position(self, ctx: MovementContext) -> tuple[float, float, float] | None:
        """Retorna posição alvo do companion neste frame, ou None para manter atual."""

    @abstractmethod
    def get_look_at(self, ctx: MovementContext) -> tuple[float, float, float] | None:
        """Retorna ponto para onde o companion deve olhar, ou None."""

    @abstractmethod
    def get_wing_speed(self, ctx: MovementContext) -> float:
        """Velocidade das asas em Hz (0 = parado, 2 = normal, 4 = rápido)."""

    @abstractmethod
    def should_transition(self, ctx: MovementContext) -> str | None:
        """Nome do estado para o qual transicionar, ou None para manter."""
