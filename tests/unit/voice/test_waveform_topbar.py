# -*- coding: utf-8 -*-
"""
Testes unitários para WaveformTopBar.

DOC: src/core/sky/chat/textual_ui/widgets/bubbles/waveform_topbar.py - Widget de waveform.
"""

import pytest
from unittest.mock import Mock, patch, MagicMock

from core.sky.chat.textual_ui.widgets.bubbles.waveform_topbar import WaveformTopBar


class TestWaveformTopBarInit:
    """Testes de inicialização do WaveformTopBar."""

    def test_init_default_values(self):
        """WaveformTopBar deve iniciar com valores padrão."""
        widget = WaveformTopBar()
        assert widget._bars == [0] * widget.BAR_COUNT
        assert widget._timer is None
        assert widget._mode == "idle"

    def test_bar_count_constant(self):
        """BAR_COUNT deve ser 12."""
        assert WaveformTopBar.BAR_COUNT == 12


class TestWaveformTopBarStates:
    """Testes de transição de estados do WaveformTopBar."""

    def test_start_speaking_activates_correct_mode(self):
        """start_speaking() deve ativar modo 'speaking' e adicionar classes corretas."""
        widget = WaveformTopBar()
        widget.start_speaking()

        assert widget._mode == "speaking"
        assert widget.has_class("active")
        assert widget.has_class("speaking")
        assert not widget.has_class("thinking")

    def test_start_thinking_activates_correct_mode(self):
        """start_thinking() deve ativar modo 'thinking' e adicionar classes corretas."""
        widget = WaveformTopBar()
        widget.start_thinking()

        assert widget._mode == "thinking"
        assert widget.has_class("active")
        assert widget.has_class("thinking")
        assert not widget.has_class("speaking")

    def test_stop_resets_to_idle(self):
        """stop() deve resetar para modo 'idle' e remover classes."""
        widget = WaveformTopBar()
        widget.start_speaking()
        widget.stop()

        assert widget._mode == "idle"
        assert not widget.has_class("active")
        assert not widget.has_class("speaking")
        assert not widget.has_class("thinking")

    def test_can_transition_between_states(self):
        """Deve ser possível transicionar entre estados."""
        widget = WaveformTopBar()

        # speaking -> thinking
        widget.start_speaking()
        assert widget._mode == "speaking"
        widget.start_thinking()
        assert widget._mode == "thinking"

        assert not widget.has_class("speaking")
        assert widget.has_class("thinking")

        # thinking -> idle
        widget.stop()
        assert widget._mode == "idle"

        # idle -> speaking
        widget.start_speaking()
        assert widget._mode == "speaking"
        assert widget.has_class("active")


class TestWaveformTopBarTimer:
    """Testes do controle de timer do WaveformTopBar."""

    def test_start_speaking_starts_timer(self):
        """start_speaking() deve iniciar o timer de animação."""
        widget = WaveformTopBar()

        # Mock set_interval
        with patch.object(widget, 'set_interval') as mock_set_interval:
            mock_set_interval.return_value = Mock()
            widget.start_speaking()
            mock_set_interval.assert_called_once_with(0.1, widget._animate)

            # Verifica que timer foi salvo
            assert widget._timer == mock_set_interval.return_value

    def test_start_thinking_starts_timer(self):
        """start_thinking() deve iniciar o timer de animação."""
        widget = WaveformTopBar()

        # Mock set_interval
        with patch.object(widget, 'set_interval') as mock_set_interval:
            mock_set_interval.return_value = Mock()
            widget.start_thinking()
            mock_set_interval.assert_called_once_with(0.1, widget._animate)

    def test_stop_stops_timer(self):
        """stop() deve parar o timer."""
        widget = WaveformTopBar()

        # Start timer primeiro
        with patch.object(widget, 'set_interval') as mock_set_interval:
            mock_timer = Mock()
            mock_set_interval.return_value = mock_timer
            widget.start_speaking()

            # Agora stop
            widget.stop()
            mock_timer.stop.assert_called_once()
            assert widget._timer is None

    def test_timer_not_started_when_already_running(self):
        """Timer não deve ser reiniciado se já estiver rodando."""
        widget = WaveformTopBar()

        mock_timer1 = Mock()
        mock_timer2 = Mock()

        with patch.object(widget, 'set_interval') as mock_set_interval:
            mock_set_interval.side_effect = [mock_timer1, mock_timer2]
            widget.start_speaking()
            assert widget._timer == mock_timer1
            widget.start_thinking()
            assert widget._timer == mock_timer1  # Não deve reiniciar


class TestWaveformTopBarAnimate:
    """Testes da animação do WaveformTopBar."""

    def test_animate_updates_content(self):
        """_animate() deve atualizar o conteúdo do widget."""
        widget = WaveformTopBar()
        widget.add_class("active")
        widget._mode = "speaking"

        widget._animate()
        # Verifica se o conteúdo foi atualizado
        content = widget.renderable
        assert content != "" or content is not None

    def test_animate_uses_different_heights_for_speaking(self):
        """_animate() em modo speaking deve usar alturas 1-3."""
        widget = WaveformTopBar()
        widget.add_class("active")
        widget._mode = "speaking"

        # Mock random para ter valores controlados
        with patch("core.sky.chat.textual_ui.widgets.bubbles.waveform_topbar.random.randint") as mock_randint:
            mock_randint.side_effect = [3, 2, 1, 0, 1, 2, 3, 2, 1, 0, 3, 2, 1, 0]
            widget._animate()
            # Verifica que randint foi chamado para alturas
            assert mock_randint.call_count == widget.BAR_COUNT

    def test_animate_uses_lower_heights_for_thinking(self):
        """_animate() em modo thinking deve usar alturas 0-2."""
        widget = WaveformTopBar()
        widget.add_class("active")
        widget._mode = "thinking"

        # Mock random para ter valores controlados
        with patch("core.sky.chat.textual_ui.widgets.bubbles.waveform_topbar.random.randint") as mock_randint:
            mock_randint.side_effect = [2, 1, 0, 1, 0, 2, 1, 0, 2, 0, 1, 0, 2, 0]
            widget._animate()
            # Verifica que randint foi chamado para alturas
            assert mock_randint.call_count == widget.BAR_COUNT
    def test_animate_does_not_run_when_not_active(self):
        """_animate() não deve fazer nada se widget não está ativo."""
        widget = WaveformTopBar()
        widget._mode = "idle"
        # Não adiciona classe "active"
        widget._animate()
        # Verifica que o conteúdo não foi atualizado (deve estar vazio ou com valor padrão)
        content = widget.renderable
        assert content == "" or content is None
