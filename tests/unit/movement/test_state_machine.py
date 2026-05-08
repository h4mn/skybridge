"""Testes para MovementStateMachine (Task 1.3 + 6.1).

Spec ref: movement-state-machine — State machine gerencia transições
- Transição automática por prioridade
- Cooldown entre transições (0.3s configurável)
- Orbit como estado padrão
"""
import pytest

from src.core.companion.movement.state_machine import (
    MovementStateMachine,
    StateType,
)
from src.core.companion.movement.context import MovementContext


def _ctx(**overrides) -> MovementContext:
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


class TestMovementStateMachineInit:
    """State machine inicia em orbit."""

    def test_estado_inicial_eh_orbit(self):
        sm = MovementStateMachine()
        assert sm.current_state == StateType.ORBIT

    def test_current_state_type_comeca_orbit(self):
        sm = MovementStateMachine()
        assert sm.current_state_type == StateType.ORBIT


class TestMovementStateMachineTransitions:
    """Transições manuais via TransitionTo."""

    def test_transicao_para_stay(self):
        sm = MovementStateMachine()
        sm.transition_to(StateType.STAY)
        assert sm.current_state == StateType.STAY

    def test_transicao_para_goto_coords(self):
        sm = MovementStateMachine()
        sm.transition_to(StateType.GOTO_COORDS, target=(10.0, 5.0, 20.0))
        assert sm.current_state == StateType.GOTO_COORDS

    def test_transicao_para_goto_named(self):
        sm = MovementStateMachine()
        sm.register_location("base", (100.0, 10.0, 200.0))
        sm.transition_to(StateType.GOTO_NAMED, name="base")
        assert sm.current_state == StateType.GOTO_NAMED

    def test_transicao_para_explore(self):
        sm = MovementStateMachine()
        sm.transition_to(StateType.EXPLORE)
        assert sm.current_state == StateType.EXPLORE


class TestMovementStateMachineCooldown:
    """Cooldown impede transições rápidas."""

    def test_cooldown_bloqueia_transicao_rapida(self):
        sm = MovementStateMachine(cooldown=0.3)
        sm.transition_to(StateType.STAY)
        # Tenta transicionar de novo imediatamente — bloqueado pelo cooldown
        sm.advance_time(0.1)
        result = sm.try_transition(StateType.ORBIT)
        assert result is False
        assert sm.current_state == StateType.STAY

    def test_cooldown_permite_apos_espera(self):
        sm = MovementStateMachine(cooldown=0.3)
        sm.transition_to(StateType.STAY)
        sm.advance_time(0.4)
        result = sm.try_transition(StateType.ORBIT)
        assert result is True
        assert sm.current_state == StateType.ORBIT

    def test_manual_transition_ignora_cooldown(self):
        """transition_to() é manual (via MCP tool), ignora cooldown."""
        sm = MovementStateMachine(cooldown=0.3)
        sm.transition_to(StateType.STAY)
        sm.advance_time(0.05)
        sm.transition_to(StateType.GOTO_COORDS, target=(1.0, 2.0, 3.0))
        assert sm.current_state == StateType.GOTO_COORDS


class TestMovementStateMachinePriority:
    """Prioridade de transição automática."""

    def test_prioridade_speaking_maior_que_orbit(self):
        """speaking > orbit."""
        sm = MovementStateMachine()
        # simulate speaking state wants to activate
        ctx = _ctx(is_speaking=True)
        sm.update(ctx)
        assert sm.current_state == StateType.SPEAKING

    def test_prioridade_speaking_maior_que_goto(self):
        """speaking > goto/stay."""
        sm = MovementStateMachine()
        sm.transition_to(StateType.GOTO_COORDS, target=(10.0, 0.0, 0.0))
        sm.advance_time(1.0)  # past cooldown
        ctx = _ctx(is_speaking=True)
        sm.update(ctx)
        assert sm.current_state == StateType.SPEAKING

    def test_retorna_ao_estado_anterior_apos_speaking(self):
        """Speaking salva estado anterior para retorno."""
        sm = MovementStateMachine()
        sm.transition_to(StateType.STAY)
        sm.advance_time(1.0)
        ctx = _ctx(is_speaking=True)
        sm.update(ctx)
        assert sm.current_state == StateType.SPEAKING
        # Speaking termina
        ctx2 = _ctx(is_speaking=False)
        sm.advance_time(1.0)
        sm.update(ctx2)
        assert sm.current_state == StateType.STAY


class TestMovementStateMachineNamedLocations:
    """Registro de localizações nomeadas."""

    def test_registra_e_busca_local(self):
        sm = MovementStateMachine()
        sm.register_location("base", (100.0, 10.0, 200.0))
        loc = sm.get_location("base")
        assert loc == (100.0, 10.0, 200.0)

    def test_local_inexistente_retorna_none(self):
        sm = MovementStateMachine()
        assert sm.get_location("unknown") is None
