"""MovementContext — dados imutáveis por frame para a state machine de movimentação.

Spec ref: movement-state-machine — MovementContext fornecido a cada frame
"""
from __future__ import annotations

import math
from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    pass


@dataclass(frozen=True)
class MovementContext:
    """Struct imutável com dados do frame atual.

    Montado uma vez por frame pelo CompanionController e passado à state machine.
    """
    player_position: tuple[float, float, float]
    player_forward: tuple[float, float, float]
    player_velocity: tuple[float, float, float]
    camera_position: tuple[float, float, float]
    camera_forward: tuple[float, float, float]
    is_player_moving: bool
    time_since_player_stopped: float
    is_speaking: bool
    current_message: str

    @property
    def horizontal_speed(self) -> float:
        """Velocidade horizontal (ignora eixo Y) — usada para lead."""
        vx, _, vz = self.player_velocity
        return math.sqrt(vx * vx + vz * vz)

    @staticmethod
    def smooth_velocity(buffer: list[float]) -> float:
        """Média móvel dos últimos N frames para suavizar velocidade."""
        if not buffer:
            return 0.0
        return sum(buffer) / len(buffer)
