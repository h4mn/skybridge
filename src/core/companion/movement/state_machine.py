"""MovementStateMachine — gerencia transições de movimento do companion.

Spec ref: movement-state-machine
"""
from __future__ import annotations

import enum
import logging
import math
import random
from dataclasses import dataclass, field
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    pass

logger = logging.getLogger(__name__)


class StateType(enum.Enum):
    """Tipos de estado de movimentação, ordenados por prioridade (maior = mais urgente)."""
    ORBIT = "orbit"
    EXPLORE = "explore"
    PERCH = "perch"
    STAY = "stay"
    GOTO_COORDS = "goto_coords"
    GOTO_NAMED = "goto_named"
    FLEE = "flee"
    LEAD = "lead"
    LISTENING = "listening"
    CELEBRATE = "celebrate"
    SPEAKING = "speaking"
    GREETING = "greeting"
    THINKING = "thinking"


# Prioridade: maior valor = maior prioridade
PRIORITY = {
    StateType.SPEAKING: 10,
    StateType.CELEBRATE: 9,
    StateType.LISTENING: 8,
    StateType.LEAD: 7,
    StateType.FLEE: 6,
    StateType.GOTO_COORDS: 5,
    StateType.GOTO_NAMED: 5,
    StateType.STAY: 5,
    StateType.PERCH: 4,
    StateType.EXPLORE: 3,
    StateType.ORBIT: 1,
    StateType.THINKING: 0,
    StateType.GREETING: 0,
}


@dataclass
class MovementConfig:
    """Parâmetros configuráveis da movimentação."""
    orbit_radius: float = 3.0
    orbit_height: float = 2.0
    orbit_speed: float = 0.8
    orbit_wobble: float = 0.5
    perch_delay: float = 30.0
    lead_distance: float = 3.0
    lead_height: float = 2.0
    lead_min_speed: float = 2.0
    lead_speed_bonus: float = 0.1
    lead_stop_delay: float = 2.0
    teleport_threshold: float = 50.0
    speaking_offset: float = 1.5
    speaking_viewport_x: float = 0.15
    speaking_viewport_y: float = 0.85
    move_speed: float = 5.0
    celebrate_duration: float = 3.0
    celebrate_spirals: float = 1.5
    celebrate_height: float = 5.0
    greeting_duration: float = 2.0
    listening_timeout: float = 10.0
    flee_duration: float = 5.0
    flee_distance: float = 5.0
    explore_radius: float = 5.0
    explore_max_distance: float = 8.0


def _distance_3d(a: tuple[float, float, float], b: tuple[float, float, float]) -> float:
    return math.sqrt((a[0]-b[0])**2 + (a[1]-b[1])**2 + (a[2]-b[2])**2)


def _add(a: tuple[float, float, float], b: tuple[float, float, float]) -> tuple[float, float, float]:
    return (a[0]+b[0], a[1]+b[1], a[2]+b[2])


def _sub(a: tuple[float, float, float], b: tuple[float, float, float]) -> tuple[float, float, float]:
    return (a[0]-b[0], a[1]-b[1], a[2]-b[2])


def _scale(v: tuple[float, float, float], s: float) -> tuple[float, float, float]:
    return (v[0]*s, v[1]*s, v[2]*s)


def _normalize(v: tuple[float, float, float]) -> tuple[float, float, float]:
    mag = math.sqrt(v[0]**2 + v[1]**2 + v[2]**2)
    if mag < 1e-6:
        return (0.0, 0.0, 0.0)
    return (v[0]/mag, v[1]/mag, v[2]/mag)


class MovementStateMachine:
    """State machine central que gerencia o estado de movimentação do companion.

    Apenas UM estado ativo por vez. Transições manuais (MCP tool) ignoram cooldown.
    Transições automáticas (contexto) respeitam cooldown e prioridade.
    """

    def __init__(self, config: MovementConfig | None = None, cooldown: float = 0.3):
        self.config = config or MovementConfig()
        self.cooldown = cooldown
        self._current: StateType = StateType.ORBIT
        self._last_transition_time: float = 0.0
        self._current_time: float = 0.0
        self._previous_state: StateType | None = None
        self._named_locations: dict[str, tuple[float, float, float]] = {}

        # State-specific data
        self._target: tuple[float, float, float] | None = None
        self._stay_position: tuple[float, float, float] | None = None
        self._explore_target: tuple[float, float, float] | None = None
        self._orbit_angle: float = 0.0
        self._state_enter_time: float = 0.0
        self._companion_position: tuple[float, float, float] = (0.0, 0.0, 0.0)

        # Velocity buffer for smoothing
        self._velocity_buffer: list[float] = []
        self._velocity_buffer_max: int = 5

    @property
    def current_state(self) -> StateType:
        return self._current

    @property
    def current_state_type(self) -> StateType:
        return self._current

    def advance_time(self, dt: float) -> None:
        """Avança o tempo interno (para testes)."""
        self._current_time += dt

    def _can_auto_transition(self) -> bool:
        """Verifica se cooldown permite transição automática."""
        return (self._current_time - self._last_transition_time) >= self.cooldown

    def transition_to(self, state: StateType, **kwargs) -> None:
        """Transição manual (via MCP tool) — ignora cooldown."""
        if state == self._current:
            return
        self._previous_state = self._current
        self._current = state
        self._last_transition_time = self._current_time
        self._state_enter_time = self._current_time
        self._apply_state_params(**kwargs)

    def try_transition(self, state: StateType, **kwargs) -> bool:
        """Tenta transição automática — respeita cooldown. Retorna True se sucesso."""
        if not self._can_auto_transition():
            return False
        # Permite qualquer transição automática (não só upgrade de prioridade)
        if state == self._current:
            return False
        self._previous_state = self._current
        self._current = state
        self._last_transition_time = self._current_time
        self._state_enter_time = self._current_time
        self._apply_state_params(**kwargs)
        return True

    def _apply_state_params(self, **kwargs) -> None:
        target = kwargs.get("target")
        if target:
            self._target = target

        name = kwargs.get("name")
        if name and name in self._named_locations:
            self._target = self._named_locations[name]
        elif name:
            logger.warning(f"Local '{name}' não encontrado no registro")

        if self._current == StateType.STAY:
            self._stay_position = self._companion_position

    def register_location(self, name: str, position: tuple[float, float, float]) -> None:
        self._named_locations[name] = position

    def get_location(self, name: str) -> tuple[float, float, float] | None:
        return self._named_locations.get(name)

    def update(self, ctx) -> None:
        """Update principal — verifica transições automáticas baseadas no contexto."""
        # Speaking tem prioridade máxima — sempre transiciona, ignora cooldown
        if ctx.is_speaking and self._current != StateType.SPEAKING:
            self.transition_to(StateType.SPEAKING)
            return

        # Speaking terminou — retorna ao estado anterior
        if not ctx.is_speaking and self._current == StateType.SPEAKING:
            prev = self._previous_state or StateType.ORBIT
            self.transition_to(prev)
            return

        # Lead: jogador se movendo horizontalmente
        if self._current in (StateType.ORBIT, StateType.LEAD):
            if ctx.horizontal_speed > self.config.lead_min_speed:
                if self._current != StateType.LEAD and self._can_auto_transition():
                    self.transition_to(StateType.LEAD)
            elif self._current == StateType.LEAD and ctx.horizontal_speed < self.config.lead_min_speed:
                if self._can_auto_transition():
                    self.transition_to(StateType.ORBIT)

        # Perch: jogador parado por tempo suficiente
        if (self._current == StateType.ORBIT
                and ctx.time_since_player_stopped > self.config.perch_delay):
            if self._can_auto_transition():
                self.transition_to(StateType.PERCH)

        # Perch → Orbit: jogador se moveu
        if self._current == StateType.PERCH and ctx.is_player_moving:
            self.transition_to(StateType.ORBIT)

    def get_target_position(self, ctx) -> tuple[float, float, float] | None:
        """Calcula posição alvo baseada no estado atual."""
        elapsed = self._current_time - self._state_enter_time
        cfg = self.config
        pp = ctx.player_position
        pf = ctx.player_forward

        if self._current == StateType.ORBIT:
            self._orbit_angle += 0.016 * cfg.orbit_speed  # ~60fps
            ox = math.cos(self._orbit_angle) * cfg.orbit_radius
            oz = math.sin(self._orbit_angle) * cfg.orbit_radius
            oy = cfg.orbit_height + math.sin(self._current_time * 2.0) * cfg.orbit_wobble
            return _add(pp, (ox, oy, oz))

        if self._current == StateType.STAY:
            if self._stay_position is None:
                self._stay_position = self._companion_position
            base = self._stay_position
            wobble = math.sin(self._current_time * 2.0) * 0.1
            return (base[0], base[1] + wobble, base[2])

        if self._current == StateType.GOTO_COORDS:
            return self._target

        if self._current == StateType.GOTO_NAMED:
            return self._target

        if self._current == StateType.LEAD:
            lead_pos = _add(pp, _add(
                _scale(pf, cfg.lead_distance),
                (0.0, cfg.lead_height, 0.0),
            ))
            return lead_pos

        if self._current == StateType.SPEAKING:
            # ViewportToWorldPoint(0.15, 0.85, offset) — simplificado como offset da câmera
            cam = ctx.camera_position
            cam_fwd = ctx.camera_forward
            cam_right = (-cam_fwd[2], 0.0, cam_fwd[0])  # perpendicular horizontal
            cam_right = _normalize(cam_right)
            # Canto superior esquerdo = left + up
            return _add(cam, _add(
                _scale(cam_fwd, cfg.speaking_offset),
                _add(
                    _scale(cam_right, -cfg.speaking_offset * 0.5),
                    (0.0, cfg.speaking_offset * 0.3, 0.0),
                ),
            ))

        if self._current == StateType.PERCH:
            # Ombro direito do jogador
            right = (-pf[2], 0.0, pf[0])
            right = _normalize(right)
            return _add(pp, _add(
                _scale(right, 0.3),
                (0.0, 1.5, 0.0),
            ))

        if self._current == StateType.THINKING:
            if self._stay_position is None:
                self._stay_position = self._companion_position
            base = self._stay_position
            wobble = math.sin(self._current_time * 2.0) * 0.1
            return (base[0], base[1] + wobble, base[2])

        if self._current == StateType.FLEE:
            # Afasta na direção oposta, retorna após flee_duration
            if elapsed > cfg.flee_duration:
                self.transition_to(StateType.ORBIT)
                return self.get_target_position(ctx)
            # Posição: 5u na direção oposta ao companion
            away = _normalize(_sub(self._companion_position, pp))
            return _add(pp, _scale(away, cfg.flee_distance))

        if self._current == StateType.CELEBRATE:
            if elapsed > cfg.celebrate_duration:
                self.transition_to(StateType.ORBIT)
                return self.get_target_position(ctx)
            # Espiral ascendente
            t = elapsed / cfg.celebrate_duration
            angle = t * cfg.celebrate_spirals * 2 * math.pi
            radius = 2.0 * (1.0 - t)
            height = pp[1] + 2.0 + t * cfg.celebrate_height
            return (pp[0] + math.cos(angle) * radius, height, pp[2] + math.sin(angle) * radius)

        if self._current == StateType.GREETING:
            if elapsed > cfg.greeting_duration:
                self.transition_to(StateType.ORBIT)
                return self.get_target_position(ctx)
            # Arco descendente
            t = elapsed / cfg.greeting_duration
            start_h = pp[1] + 5.0
            end_h = pp[1] + 2.0
            h = start_h + (end_h - start_h) * t
            fwd = _scale(pf, 2.0)
            return _add(pp, (fwd[0], h, fwd[2]))

        if self._current == StateType.LISTENING:
            if elapsed > cfg.listening_timeout:
                self.transition_to(StateType.ORBIT)
                return self.get_target_position(ctx)
            # Aproxima do jogador
            fwd = _scale(pf, 1.5)
            return _add(pp, (fwd[0], pp[1] + 1.5, fwd[2]))

        if self._current == StateType.EXPLORE:
            # Limita distância do jogador
            if self._explore_target is None or _distance_3d(self._companion_position, pp) > cfg.explore_max_distance:
                angle = random.uniform(0, 2 * math.pi)
                dist = random.uniform(2.0, cfg.explore_radius)
                self._explore_target = _add(pp, (math.cos(angle) * dist, 1.0 + random.uniform(-1, 1), math.sin(angle) * dist))
            # Chegou perto do target? Novo ponto
            if self._explore_target and _distance_3d(self._companion_position, self._explore_target) < 0.5:
                self._explore_target = None
            return self._explore_target

        return None

    def get_look_at(self, ctx) -> tuple[float, float, float] | None:
        """Retorna ponto para onde olhar."""
        if self._current == StateType.ORBIT:
            # Tangente ao círculo (direção de voo)
            angle = self._orbit_angle + math.pi / 2
            ox = math.cos(angle)
            oz = math.sin(angle)
            return _add(self._companion_position, (ox, 0.0, oz))

        if self._current == StateType.SPEAKING:
            return ctx.camera_position

        if self._current == StateType.CELEBRATE:
            return _add(ctx.player_position, (0.0, 100.0, 0.0))  # sky

        if self._current == StateType.LISTENING:
            # Rosto do jogador
            return _add(ctx.player_position, (0.0, 1.7, 0.0))

        if self._current == StateType.LEAD:
            return ctx.player_position

        # Default: olha pro jogador
        return ctx.player_position

    def get_wing_speed(self) -> float:
        """Velocidade das asas em Hz."""
        speeds = {
            StateType.PERCH: 0.0,
            StateType.THINKING: 1.0,
            StateType.LISTENING: 3.0,
            StateType.SPEAKING: 4.0,
            StateType.FLEE: 4.0,
            StateType.CELEBRATE: 4.0,
            StateType.GREETING: 3.0,
        }
        return speeds.get(self._current, 2.0)

    def set_companion_position(self, pos: tuple[float, float, float]) -> None:
        self._companion_position = pos
