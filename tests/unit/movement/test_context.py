"""Testes para MovementContext (Task 1.2).

Spec ref: movement-state-machine — MovementContext fornecido a cada frame
- Context reflete estado atual do jogo (dados frescos)
- Velocidade suavizada com média móvel de 5 frames
"""
import math

import pytest

from src.core.companion.movement.context import MovementContext


class TestMovementContextBuild:
    """MovementContext.Build() gera struct imutável com dados do frame."""

    def test_build_com_dados_basicos(self):
        ctx = MovementContext(
            player_position=(10.0, 5.0, 20.0),
            player_forward=(1.0, 0.0, 0.0),
            player_velocity=(2.0, 0.0, 1.0),
            camera_position=(10.0, 6.0, 20.0),
            camera_forward=(1.0, 0.0, 0.0),
            is_player_moving=True,
            time_since_player_stopped=0.0,
            is_speaking=False,
            current_message="",
        )
        assert ctx.player_position == (10.0, 5.0, 20.0)
        assert ctx.player_forward == (1.0, 0.0, 0.0)
        assert ctx.is_player_moving is True

    def test_build_imutavel(self):
        """Context SHALL ser imutável após criação."""
        ctx = MovementContext(
            player_position=(0.0, 0.0, 0.0),
            player_forward=(1.0, 0.0, 0.0),
            player_velocity=(0.0, 0.0, 0.0),
            camera_position=(0.0, 1.0, 0.0),
            camera_forward=(1.0, 0.0, 0.0),
            is_player_moving=False,
            time_since_player_stopped=5.0,
            is_speaking=False,
            current_message="",
        )
        with pytest.raises(AttributeError):
            ctx.player_position = (99.0, 99.0, 99.0)


class TestMovementContextVelocitySmooth:
    """Velocidade suavizada com média móvel de 5 frames."""

    def test_media_movel_simples(self):
        """Média móvel dos últimos 5 valores de velocidade."""
        buffer = [1.0, 2.0, 3.0, 4.0, 5.0]
        result = MovementContext.smooth_velocity(buffer)
        assert result == pytest.approx(3.0)

    def test_media_movel_menor_que_5(self):
        """Com menos de 5 frames, usa o que tem."""
        buffer = [2.0, 4.0]
        result = MovementContext.smooth_velocity(buffer)
        assert result == pytest.approx(3.0)

    def test_media_movel_vazia(self):
        """Buffer vazio retorna 0."""
        result = MovementContext.smooth_velocity([])
        assert result == 0.0

    def test_horizontal_speed_ignora_y(self):
        """Lead ignora eixo Y — velocidade horizontal only."""
        ctx = MovementContext(
            player_position=(0.0, 0.0, 0.0),
            player_forward=(1.0, 0.0, 0.0),
            player_velocity=(3.0, 10.0, 4.0),
            camera_position=(0.0, 1.0, 0.0),
            camera_forward=(1.0, 0.0, 0.0),
            is_player_moving=True,
            time_since_player_stopped=0.0,
            is_speaking=False,
            current_message="",
        )
        # sqrt(3² + 4²) = 5.0, ignorando Y=10
        assert ctx.horizontal_speed == pytest.approx(5.0)
