"""Testes para IMovementState (Task 1.1).

Spec ref: movement-state-machine — Interface IMovementState
- Cada estado implementa GetTargetPosition, GetLookAt, GetWingSpeed, ShouldTransition
- Novo estado pode ser integrado sem modificar existentes
"""
import pytest

from src.core.companion.movement.interfaces import IMovementState
from src.core.companion.movement.context import MovementContext


def _make_context(**overrides) -> MovementContext:
    defaults = dict(
        player_position=(0.0, 0.0, 0.0),
        player_forward=(1.0, 0.0, 0.0),
        player_velocity=(0.0, 0.0, 0.0),
        camera_position=(0.0, 1.0, 0.0),
        camera_forward=(1.0, 0.0, 0.0),
        is_player_moving=False,
        time_since_player_stopped=0.0,
        is_speaking=False,
        current_message="",
    )
    defaults.update(overrides)
    return MovementContext(**defaults)


class ConcreteState(IMovementState):
    """Estado concreto para testar a interface."""

    def get_target_position(self, ctx: MovementContext) -> tuple[float, float, float] | None:
        return (1.0, 2.0, 3.0)

    def get_look_at(self, ctx: MovementContext) -> tuple[float, float, float] | None:
        return ctx.player_position

    def get_wing_speed(self, ctx: MovementContext) -> float:
        return 2.0

    def should_transition(self, ctx: MovementContext) -> str | None:
        return None


class TestIMovementStateInterface:
    """Interface IMovementState é implementável e extensível."""

    def test_estado_concreto_get_target_position(self):
        state = ConcreteState()
        ctx = _make_context()
        pos = state.get_target_position(ctx)
        assert pos == (1.0, 2.0, 3.0)

    def test_estado_concreto_get_look_at(self):
        state = ConcreteState()
        ctx = _make_context(player_position=(5.0, 0.0, 0.0))
        look = state.get_look_at(ctx)
        assert look == (5.0, 0.0, 0.0)

    def test_estado_concreto_get_wing_speed(self):
        state = ConcreteState()
        ctx = _make_context()
        assert state.get_wing_speed(ctx) == 2.0

    def test_estado_concreto_should_transition_none(self):
        state = ConcreteState()
        ctx = _make_context()
        assert state.should_transition(ctx) is None

    def test_nao_pode_instanciar_interface_diretamente(self):
        """IMovementState é ABC — não pode instanciar diretamente."""
        with pytest.raises(TypeError):
            IMovementState()

    def test_estado_sem_metodos_abstratos_falha(self):
        """Classe sem implementar métodos abstratos falha."""
        class IncompleteState(IMovementState):
            pass

        with pytest.raises(TypeError):
            IncompleteState()
