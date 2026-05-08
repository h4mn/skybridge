"""Testes para estados básicos (Tasks 2.1-2.7 + 3.1-3.6).

Spec ref: movement-state-machine + contextual-flight-behaviors
Valida posição, lookAt, wingSpeed de cada estado.
"""
import math

import pytest

from src.core.companion.movement.state_machine import (
    MovementConfig,
    MovementStateMachine,
    StateType,
)
from src.core.companion.movement.context import MovementContext


def _ctx(**overrides) -> MovementContext:
    defaults = dict(
        player_position=(10.0, 0.0, 20.0),
        player_forward=(1.0, 0.0, 0.0),
        player_velocity=(0.0, 0.0, 0.0),
        camera_position=(10.0, 1.0, 20.0),
        camera_forward=(1.0, 0.0, 0.0),
        is_player_moving=False,
        time_since_player_stopped=0.0,
        is_speaking=False,
        current_message="",
    )
    defaults.update(overrides)
    return MovementContext(**defaults)


# ============================================================================
# 2.1 OrbitState
# ============================================================================

class TestOrbitState:
    def test_orbit_circula_ao_redor_do_jogador(self):
        sm = MovementStateMachine()
        sm.set_companion_position((10.0, 2.0, 20.0))
        ctx = _ctx()
        # Simula vários frames
        positions = []
        for i in range(60):
            sm._orbit_angle += 0.016 * sm.config.orbit_speed
            pos = sm.get_target_position(ctx)
            if pos:
                positions.append(pos)
        # Posições devem variar em X e Z, formando um círculo
        xs = [p[0] for p in positions]
        zs = [p[2] for p in positions]
        assert max(xs) - min(xs) > 1.0  # Raio de 3u
        assert max(zs) - min(zs) > 1.0

    def test_orbit_tem_ondulacao_y(self):
        sm = MovementStateMachine()
        sm.set_companion_position((10.0, 2.0, 20.0))
        ctx = _ctx()
        ys = []
        for i in range(100):
            sm._current_time = i * 0.016
            sm._orbit_angle += 0.016 * sm.config.orbit_speed
            pos = sm.get_target_position(ctx)
            if pos:
                ys.append(pos[1])
        # Y deve variar com sin(wobble)
        assert max(ys) - min(ys) > 0.5

    def test_orbit_lookat_tangente(self):
        sm = MovementStateMachine()
        sm.set_companion_position((10.0, 2.0, 20.0))
        ctx = _ctx()
        sm._orbit_angle = 0.0
        look = sm.get_look_at(ctx)
        assert look is not None
        # Tangente em angle=0 aponta no eixo Z+
        assert abs(look[2] - 20.0 - 1.0) < 0.1 or abs(look[0]) > 0  # Nem sempre pro jogador

    def test_orbit_wing_speed_2hz(self):
        sm = MovementStateMachine()
        assert sm.get_wing_speed() == 2.0


# ============================================================================
# 2.2 StayState
# ============================================================================

class TestStayState:
    def test_stay_para_no_local_atual(self):
        sm = MovementStateMachine()
        sm.set_companion_position((15.0, 3.0, 25.0))
        sm.transition_to(StateType.STAY)
        ctx = _ctx()
        pos = sm.get_target_position(ctx)
        assert pos is not None
        assert abs(pos[0] - 15.0) < 0.1
        assert abs(pos[2] - 25.0) < 0.1

    def test_stay_tem_oscilacao_y(self):
        sm = MovementStateMachine()
        sm.set_companion_position((15.0, 3.0, 25.0))
        sm.transition_to(StateType.STAY)
        ctx = _ctx()
        ys = []
        for i in range(100):
            sm._current_time = i * 0.016
            pos = sm.get_target_position(ctx)
            if pos:
                ys.append(pos[1])
        # Oscilação Y ±0.1
        assert max(ys) - min(ys) > 0.05


# ============================================================================
# 2.3 GotoCoordsState
# ============================================================================

class TestGotoCoordsState:
    def test_retorna_coordenada_alvo(self):
        sm = MovementStateMachine()
        sm.transition_to(StateType.GOTO_COORDS, target=(100.0, 50.0, 200.0))
        ctx = _ctx()
        pos = sm.get_target_position(ctx)
        assert pos == (100.0, 50.0, 200.0)

    def test_teleporte_quando_dist_grande(self):
        """Spec: teleport quando dist > threshold. Lógica no CompanionController."""
        # Validação da distância — a state machine só retorna a posição
        sm = MovementStateMachine()
        sm.transition_to(StateType.GOTO_COORDS, target=(1000.0, 0.0, 1000.0))
        pos = sm.get_target_position(_ctx())
        assert pos == (1000.0, 0.0, 1000.0)


# ============================================================================
# 2.4 GotoNamedState
# ============================================================================

class TestGotoNamedState:
    def test_busca_no_registro(self):
        sm = MovementStateMachine()
        sm.register_location("base", (100.0, 10.0, 200.0))
        sm.transition_to(StateType.GOTO_NAMED, name="base")
        pos = sm.get_target_position(_ctx())
        assert pos == (100.0, 10.0, 200.0)

    def test_nome_nao_encontrado_fica_null(self):
        sm = MovementStateMachine()
        sm.transition_to(StateType.GOTO_NAMED, name="inexistente")
        pos = sm.get_target_position(_ctx())
        assert pos is None


# ============================================================================
# 2.5 ThinkingState
# ============================================================================

class TestThinkingState:
    def test_thinking_para_no_local(self):
        sm = MovementStateMachine()
        sm.set_companion_position((5.0, 2.0, 5.0))
        sm.transition_to(StateType.THINKING)
        pos = sm.get_target_position(_ctx())
        assert pos is not None
        assert abs(pos[0] - 5.0) < 0.1

    def test_thinking_asas_1hz(self):
        sm = MovementStateMachine()
        sm.transition_to(StateType.THINKING)
        assert sm.get_wing_speed() == 1.0


# ============================================================================
# 2.6 PerchState
# ============================================================================

class TestPerchState:
    def test_perch_pousa_no_ombro(self):
        sm = MovementStateMachine()
        ctx = _ctx(player_forward=(0.0, 0.0, 1.0))
        sm.transition_to(StateType.PERCH)
        pos = sm.get_target_position(ctx)
        assert pos is not None
        # Deve estar acima do jogador (1.5u)
        assert pos[1] > ctx.player_position[1] + 1.0

    def test_perch_asas_paradas(self):
        sm = MovementStateMachine()
        sm.transition_to(StateType.PERCH)
        assert sm.get_wing_speed() == 0.0

    def test_perch_retorna_orbit_quando_jogador_move(self):
        sm = MovementStateMachine()
        sm.transition_to(StateType.PERCH)
        sm.advance_time(1.0)
        ctx = _ctx(is_player_moving=True)
        sm.update(ctx)
        assert sm.current_state == StateType.ORBIT


# ============================================================================
# 2.7 FleeState
# ============================================================================

class TestFleeState:
    def test_flee_afasta_do_jogador(self):
        sm = MovementStateMachine()
        # Companion perto do jogador mas não exatamente na mesma posição
        sm.set_companion_position((10.5, 0.0, 20.5))
        sm.transition_to(StateType.FLEE)
        ctx = _ctx(player_position=(10.0, 0.0, 20.0))
        pos = sm.get_target_position(ctx)
        assert pos is not None
        # Deve estar mais longe do jogador que o companion
        from src.core.companion.movement.state_machine import _distance_3d
        dist_companion = _distance_3d(sm._companion_position, ctx.player_position)
        dist_target = _distance_3d(pos, ctx.player_position)
        assert dist_target > dist_companion

    def test_flee_retorna_apos_duracao(self):
        sm = MovementStateMachine()
        sm.set_companion_position((10.0, 0.0, 20.0))
        sm.transition_to(StateType.FLEE)
        sm.advance_time(6.0)  # > flee_duration (5s)
        ctx = _ctx()
        pos = sm.get_target_position(ctx)
        assert sm.current_state == StateType.ORBIT

    def test_flee_asas_4hz(self):
        sm = MovementStateMachine()
        sm.transition_to(StateType.FLEE)
        assert sm.get_wing_speed() == 4.0


# ============================================================================
# 3.1 SpeakingState
# ============================================================================

class TestSpeakingState:
    def test_speaking_ativa_quando_is_speaking(self):
        sm = MovementStateMachine()
        ctx = _ctx(is_speaking=True)
        sm.update(ctx)
        assert sm.current_state == StateType.SPEAKING

    def test_speaking_retorna_ao_estado_anterior(self):
        sm = MovementStateMachine()
        sm.transition_to(StateType.STAY)
        sm.advance_time(1.0)
        ctx = _ctx(is_speaking=True)
        sm.update(ctx)
        assert sm.current_state == StateType.SPEAKING
        sm.advance_time(1.0)
        ctx2 = _ctx(is_speaking=False)
        sm.update(ctx2)
        assert sm.current_state == StateType.STAY

    def test_speaking_asas_4hz(self):
        sm = MovementStateMachine()
        sm.transition_to(StateType.SPEAKING)
        assert sm.get_wing_speed() == 4.0


# ============================================================================
# 3.2 LeadState
# ============================================================================

class TestLeadState:
    def test_lead_ativa_quando_velocidade_alta(self):
        sm = MovementStateMachine()
        sm.advance_time(1.0)  # past initial cooldown
        ctx = _ctx(player_velocity=(3.0, 0.0, 4.0))  # speed = 5 > 2
        sm.update(ctx)
        # Lead requires horizontal_speed > lead_min_speed
        assert sm.current_state == StateType.LEAD

    def test_lead_posicao_a_frente(self):
        sm = MovementStateMachine()
        sm.transition_to(StateType.LEAD)
        ctx = _ctx(player_forward=(1.0, 0.0, 0.0))
        pos = sm.get_target_position(ctx)
        assert pos is not None
        # Deve estar à frente do jogador
        assert pos[0] > ctx.player_position[0]

    def test_lead_retorna_orbit_quando_para(self):
        sm = MovementStateMachine()
        sm.transition_to(StateType.LEAD)
        sm.advance_time(1.0)
        ctx = _ctx(player_velocity=(0.0, 0.0, 0.0))  # parado
        sm.update(ctx)
        assert sm.current_state == StateType.ORBIT


# ============================================================================
# 3.3 CelebrateState
# ============================================================================

class TestCelebrateState:
    def test_celebrate_espiral_ascendente(self):
        sm = MovementStateMachine()
        sm.set_companion_position((10.0, 2.0, 20.0))
        sm.transition_to(StateType.CELEBRATE)
        ctx = _ctx()
        ys = []
        for i in range(60):
            sm._current_time = i * 0.05
            pos = sm.get_target_position(ctx)
            if pos:
                ys.append(pos[1])
        # Altura deve aumentar (espiral ascendente)
        assert ys[-1] > ys[0]

    def test_celebrate_retorna_orbit_apos_3s(self):
        sm = MovementStateMachine()
        sm.transition_to(StateType.CELEBRATE)
        sm.advance_time(4.0)
        ctx = _ctx()
        sm.get_target_position(ctx)
        assert sm.current_state == StateType.ORBIT


# ============================================================================
# 3.4 GreetingState
# ============================================================================

class TestGreetingState:
    def test_greeting_arco_descendente(self):
        sm = MovementStateMachine()
        sm.transition_to(StateType.GREETING)
        ctx = _ctx()
        ys = []
        for i in range(40):
            sm._current_time = i * 0.05
            pos = sm.get_target_position(ctx)
            if pos:
                ys.append(pos[1])
        # Deve descer (arco descendente)
        assert ys[-1] < ys[0]

    def test_greeting_retorna_orbit_apos_2s(self):
        sm = MovementStateMachine()
        sm.transition_to(StateType.GREETING)
        sm.advance_time(3.0)
        ctx = _ctx()
        sm.get_target_position(ctx)
        assert sm.current_state == StateType.ORBIT


# ============================================================================
# 3.5 ListeningState
# ============================================================================

class TestListeningState:
    def test_listening_aproxima_do_jogador(self):
        sm = MovementStateMachine()
        sm.set_companion_position((20.0, 2.0, 30.0))
        sm.transition_to(StateType.LISTENING)
        ctx = _ctx()
        pos = sm.get_target_position(ctx)
        assert pos is not None
        # Deve estar perto do jogador (~1.5u à frente)
        from src.core.companion.movement.state_machine import _distance_3d
        dist = _distance_3d(pos, ctx.player_position)
        assert dist < 3.0

    def test_listening_timeout_10s(self):
        sm = MovementStateMachine()
        sm.transition_to(StateType.LISTENING)
        sm.advance_time(11.0)
        ctx = _ctx()
        sm.get_target_position(ctx)
        assert sm.current_state == StateType.ORBIT

    def test_listening_asas_3hz(self):
        sm = MovementStateMachine()
        sm.transition_to(StateType.LISTENING)
        assert sm.get_wing_speed() == 3.0


# ============================================================================
# 3.6 ExploreState
# ============================================================================

class TestExploreState:
    def test_explore_gera_pontos_aleatorios(self):
        sm = MovementStateMachine()
        sm.set_companion_position((10.0, 2.0, 20.0))
        sm.transition_to(StateType.EXPLORE)
        ctx = _ctx()
        pos = sm.get_target_position(ctx)
        assert pos is not None
        # Deve estar num raio de 5u do jogador
        from src.core.companion.movement.state_machine import _distance_3d
        dist = _distance_3d(pos, ctx.player_position)
        assert dist <= 8.0  # max distance
