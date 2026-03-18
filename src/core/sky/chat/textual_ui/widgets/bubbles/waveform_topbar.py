# -*- coding: utf-8 -*-
"""
WaveformTopBar - Barra animada de waveform para feedback de áudio.

Widget de 3 linhas que aparece apenas durante reprodução de áudio.
Usa caracteres Unicode para animação (▀█).
"""

import random
from typing import Literal

from textual.reactive import reactive
from textual.widgets import Static


class WaveformTopBar(Static):
    """
    TopBar de waveform que só aparece durante áudio.

    Características:
    - height: 0 por padrão (invisível)
    - height: 3 quando ativo (speaking/thinking)
    - Animação Unicode de 3 linhas com timer 100ms
    - Cores diferentes para speaking ($primary) e thinking ($warning)
    """

    DEFAULT_CSS = """
    WaveformTopBar {
        height: 0;
        width: 100%;
        background: $surface;
        padding: 0 1;
        overflow: hidden;
        content-align: center middle;
    }

    WaveformTopBar.active {
        height: 3;
    }

    WaveformTopBar.speaking {
        color: $primary;
    }

    WaveformTopBar.thinking {
        color: $warning;
    }
    """

    # Número de barras no waveform
    BAR_COUNT = 12

    # Alturas possíveis (0-3)
    HEIGHT_CHARS = {
        0: " ",   # vazio
        1: "▀",   # baixo (metade inferior)
        2: "█",   # cheio
        3: "█",   # cheio (topo)
    }

    def __init__(self, **kwargs):
        super().__init__("", **kwargs)
        self._bars = [0] * self.BAR_COUNT
        self._timer = None
        self._mode: Literal["idle", "speaking", "thinking"] = "idle"

    def on_mount(self) -> None:
        """Timer só é iniciado quando ativo (lazy)."""
        # Não inicia timer aqui - só quando start_speaking/start_thinking
        pass

    def on_unmount(self) -> None:
        """Para timer ao desmontar."""
        self._stop_timer()

    def _start_timer(self) -> None:
        """Inicia timer de animação se não estiver rodando."""
        if self._timer is None:
            self._timer = self.set_interval(0.1, self._animate)

    def _stop_timer(self) -> None:
        """Para timer de animação."""
        if self._timer:
            self._timer.stop()
            self._timer = None

    def _animate(self) -> None:
        """Atualiza waveform se ativo."""
        if not self.has_class("active"):
            return

        # Gera alturas aleatórias baseado no modo
        if self._mode == "thinking":
            # Thinking: mais lento, menos variação
            heights = [random.randint(0, 2) for _ in range(self.BAR_COUNT)]
        else:
            # Speaking: mais dinâmico
            heights = [random.randint(1, 3) for _ in range(self.BAR_COUNT)]

        # Monta 3 linhas (bottom-up)
        lines = []
        for row in range(2, -1, -1):
            chars = []
            for h in heights:
                if h > row:
                    chars.append("█")
                elif h == row:
                    chars.append("▀")
                else:
                    chars.append(" ")
            lines.append("".join(chars))

        self.update("\n".join(lines))

    # -------------------------------------------------------------------------
    # API Pública
    # -------------------------------------------------------------------------

    def start_speaking(self) -> None:
        """Inicia animação de fala."""
        self._mode = "speaking"
        self.add_class("active", "speaking")
        self.remove_class("thinking")
        self._start_timer()

    def start_thinking(self) -> None:
        """Inicia animação de pensamento."""
        self._mode = "thinking"
        self.add_class("active", "thinking")
        self.remove_class("speaking")
        self._start_timer()

    def stop(self) -> None:
        """Para e oculta a barra."""
        self._mode = "idle"
        self.remove_class("active", "speaking", "thinking")
        self.update("")
        self._stop_timer()


__all__ = ["WaveformTopBar"]
