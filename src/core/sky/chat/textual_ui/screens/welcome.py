# coding: utf-8
"""
Tela de apresentação (Welcome Screen) para o chat Sky.
"""

import math
from textual.app import ComposeResult, RenderResult
from textual.containers import Vertical, Center
from textual.reactive import reactive
from textual.screen import Screen
from textual.widgets import Static, Footer

from core.sky.chat.textual_ui.widgets import ChatTextArea
from core.sky.chat.textual_ui.widgets.animated_verb import (
    _PALETAS, _PALETA_FALLBACK, _lerp_cor,
)
from core.sky.chat.textual_ui.widgets.recording_mixin import RecordingToggleMixin


_LETREIRO = """
  ███████  ████    ███  ███     ███
 ███░░░░  ░░███  ░███  ░░███  ░███
░███       ░███ ░███     ░███░███
░░██████   ░█████░        ░█████
 ░░░░░███  ░███░░███      ░░███
     ░███  ░███  ░███      ░███
 ███████   ████   ░███     █████
░░░░░░░   ░░░░    ░░░░    ░░░░░
"""


# ---------------------------------------------------------------------------
# Estados semânticos do logo — mapeiam intenção em parâmetros de animação
# ---------------------------------------------------------------------------

from dataclasses import dataclass

@dataclass
class LogoEstado:
    """
    Estado semântico da animação do logo.

    angulo    : direção do gradiente em graus
                  0° = horizontal →
                 90° = vertical ↑
                 45° = diagonal ↗
                -45° = diagonal ↘
    velocidade: pixels por tick (0.2 = lento, 2.0 = rápido)
    emocao    : paleta de cores (mesma do AnimatedVerb)
    nome      : rótulo semântico para debug
    """
    angulo:     float
    velocidade: float
    emocao:     str
    nome:       str


# Estados prontos para uso
LOGO_ESTADOS = {
    "idle":        LogoEstado(angulo=0,    velocidade=0.4, emocao="neutro",    nome="idle"),
    "ativando":    LogoEstado(angulo=45,   velocidade=1.2, emocao="empolgado", nome="ativando"),
    "processando": LogoEstado(angulo=90,   velocidade=1.8, emocao="urgente",   nome="processando"),
    "acelerando":  LogoEstado(angulo=60,   velocidade=2.5, emocao="debugando", nome="acelerando"),
    "concluindo":  LogoEstado(angulo=-45,  velocidade=0.6, emocao="concluindo",nome="concluindo"),
    "descansando": LogoEstado(angulo=0,    velocidade=0.2, emocao="pensando",  nome="descansando"),
}


class SkyLogo(Static):
    """
    Logo ASCII com color sweep animado, direção semântica e transição suave.

    Transição de estado:
      Quando set_estado() é chamado, _transicao vai de 0.0 → 1.0
      ao longo de ~1.5s. render() interpola entre as cores
      da paleta anterior e a nova paleta usando esse valor —
      sem corte brusco.

    Duração aleatória:
      Cada estado dura random.uniform(5, 12) segundos antes
      de avançar para o próximo ciclo.
    """

    _offset:     reactive = reactive(0.0)
    _pulso:      reactive = reactive(0.0)
    _angulo:     reactive = reactive(0.0)
    _velocidade: reactive = reactive(0.4)
    _transicao:  reactive = reactive(1.0)  # 0.0=inicio transicao, 1.0=concluida

    JANELA          = 36
    TRANSICAO_PASSO = 0.025   # incremento por tick (~1.5s para completar)

    def on_mount(self) -> None:
        import random
        self.set_interval(0.06, self._tick_sweep)
        self.set_interval(0.05, self._tick_pulso)
        self.set_interval(0.04, self._tick_transicao)

        # Paletas atual e target para interpolar durante transição
        self._emocao_atual  = "pensando"
        self._emocao_target = "pensando"

        self._ciclo_idx = 0
        self._ciclo = self._montar_ciclo()

        # Agenda o primeiro ciclo com duração aleatória
        self._agendar_proximo()

    @staticmethod
    def _montar_ciclo() -> list[str]:
        """
        Monta ciclo A-1-A-5-A-9-... onde A = identidade Sky (azul→lilás).

        Os outros estados são embaralhados aleatoriamente e intercalados
        com A entre cada um: A, X, A, Y, A, Z, ...
        """
        import random
        outros = ["idle", "ativando", "processando", "acelerando", "concluindo"]
        random.shuffle(outros)
        # intercala: [A, outros[0], A, outros[1], A, outros[2], ...]
        ciclo = []
        for estado in outros:
            ciclo.append("descansando")  # A — identidade Sky
            ciclo.append(estado)
        return ciclo

    def _agendar_proximo(self) -> None:
        """Agenda próxima troca com duração aleatória entre 5 e 12 segundos."""
        import random
        delay = random.uniform(5.0, 12.0)
        self.set_timer(delay, self._tick_ciclo)

    def _tick_ciclo(self) -> None:
        """Avança estado e agenda o próximo."""
        self._ciclo_idx += 1
        # Ao completar uma volta, re-embaralha para nova sequência
        if self._ciclo_idx >= len(self._ciclo):
            self._ciclo = self._montar_ciclo()
            self._ciclo_idx = 0
        self.set_estado(self._ciclo[self._ciclo_idx])
        self._agendar_proximo()

    def _tick_sweep(self) -> None:
        self._offset = (self._offset + self._velocidade) % (self.JANELA * 100)

    def _tick_pulso(self) -> None:
        self._pulso = (self._pulso + 0.04) % (2 * math.pi)

    def _tick_transicao(self) -> None:
        """Incrementa progressão da transição até 1.0."""
        if self._transicao < 1.0:
            self._transicao = min(1.0, self._transicao + self.TRANSICAO_PASSO)

    def set_estado(self, nome: str) -> None:
        """API pública — troca estado com transição suave."""
        estado = LOGO_ESTADOS.get(nome, LOGO_ESTADOS["idle"])
        # Paleta atual vira ponto de partida da transição
        self._emocao_atual  = self._emocao_target
        self._emocao_target = estado.emocao
        self._angulo        = float(estado.angulo)
        self._velocidade    = estado.velocidade
        # Reinicia progressão — _tick_transicao vai subindo até 1.0
        self._transicao     = 0.0

    def watch__offset(self, _)     -> None: self.refresh()
    def watch__pulso(self, _)      -> None: self.refresh()
    def watch__transicao(self, _)  -> None: self.refresh()

    def _paleta_interpolada(self) -> tuple[str, str]:
        """
        Interpola as cores entre paleta_atual e paleta_target
        usando _transicao (0.0 → 1.0).

        Seno suaviza a curva de easing: começa devagar,
        acelera no meio, desacelera no fim — sem corte.
        """
        p_atual  = _PALETAS.get(self._emocao_atual,  _PALETA_FALLBACK)
        p_target = _PALETAS.get(self._emocao_target, _PALETA_FALLBACK)

        # ease in-out: seno suaviza a transição
        t = 0.5 - 0.5 * math.cos(math.pi * self._transicao)

        de  = _lerp_cor(p_atual.de,  p_target.de,  t)
        ate = _lerp_cor(p_atual.ate, p_target.ate, t)
        return de, ate

    def render(self) -> RenderResult:
        from rich.markup import escape

        de, ate = self._paleta_interpolada()

        t_oscila = 0.5 + math.sin(self._pulso) * 0.35
        cor_a = _lerp_cor(de, ate, 1.0 - t_oscila)
        cor_b = _lerp_cor(de, ate, t_oscila)

        rad   = math.radians(self._angulo)
        cos_a = math.cos(rad)
        sin_a = math.sin(rad)

        col = 0
        row = 0
        resultado = ""
        for ch in _LETREIRO:
            if ch == "\n":
                resultado += "\n"
                col = 0
                row += 1
            elif ch in (" ", "\t"):
                resultado += ch
                col += 1
            else:
                pos  = col * cos_a + row * sin_a
                fase = ((pos - self._offset) % self.JANELA) / self.JANELA
                t    = 0.5 - 0.5 * math.cos(2 * math.pi * fase)
                cor  = _lerp_cor(cor_a, cor_b, t)
                resultado += f"[{cor}]{escape(ch)}[/]"
                col += 1

        return resultado


class WelcomeScreen(RecordingToggleMixin, Screen):
    """Tela de apresentação do chat Sky."""

    DEFAULT_CSS = """
    WelcomeScreen SkyLogo {
        width: auto;
        height: auto;
        margin: 0;
        padding: 0;
        background: transparent;
    }

    WelcomeScreen Static.subtitle {
        width: auto;
        height: auto;
        margin: 0;
        padding: 0;
        background: transparent;
        color: white;
        text-align: right;
    }

    WelcomeScreen Center {
        width: auto;
        height: auto;
        border: round $accent;
        background: #161b22;
        padding: 1 4;
        color: #00bcd4;
        text-style: bold;
    }
    """

    BINDINGS = [
        ("ctrl+s", "toggle_recording", "Gravar (Toggle)"),
    ]

    def compose(self) -> ComposeResult:
        with Vertical():
            with Center():
                yield SkyLogo(expand=True)
                yield Static("[bold]Sky[/bold]Bridge", classes="subtitle", expand=True)
                yield Static("Engenharia de software aumentada", classes="subtitle", expand=True)

        yield ChatTextArea(id="chat_input_textarea", placeholder="Digite algo... (Ctrl+S para gravar)")
        yield Footer()

    def on_chat_text_area_submitted(self, event: ChatTextArea.Submitted) -> None:
        from core.sky.chat.textual_ui.screens.chat import ChatScreen
        self.app.push_screen(ChatScreen(event.value))

    # ------------------------------------------------------------------
    # RecordingToggleMixin - Implementação dos métodos abstratos
    # ------------------------------------------------------------------

    def _update_placeholder(self, text: str) -> None:
        """Atualiza placeholder do TextArea."""
        try:
            textarea = self.query_one("#chat_input_textarea", ChatTextArea)
            textarea.placeholder = text
        except Exception:
            pass

    def _log_event(self, title: str, message: str) -> None:
        """Loga evento (no-op na WelcomeScreen, não tem ChatLog)."""
        pass

    def _log_error(self, message: str) -> None:
        """Loga erro (no-op na WelcomeScreen, não tem ChatLog)."""
        pass

    async def _on_recording_complete(self, transcribed_text: str) -> None:
        """Callback quando gravação completa - navega para ChatScreen."""
        if transcribed_text.strip():
            # Cria ChatScreen com a transcrição
            from core.sky.chat.textual_ui.screens.chat import ChatScreen
            self.app.push_screen(ChatScreen(transcribed_text))
        else:
            # Reseta placeholder
            self._update_placeholder("Digite algo... (Ctrl+S para gravar)")


__all__ = ["WelcomeScreen"]
