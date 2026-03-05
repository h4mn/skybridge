# coding: utf-8
"""
AnimatedVerb - Widget de verbo animado com color sweep programático.

Este módulo implementa:
- EstadoLLM: dataclass com estado emocional/cognitivo da LLM
- AnimatedVerb: widget com animação de color sweep em Python
- EstadoModal: modal para inspeção de estado completo
- Sistema de paletas de cores por emoção
- Funções auxiliares de interpolação de cores
"""

from dataclasses import dataclass
import math

from textual.events import Message
from textual.reactive import reactive
from textual.screen import ModalScreen
from textual.widgets import Static
from textual.app import ComposeResult, RenderResult
from textual.containers import Vertical


# =============================================================================
# Dataclasses
# =============================================================================


@dataclass
class EstadoLLM:
    """
    Estado emocional/cognitivo da LLM.
    Controla todas as dimensões da animação do verbo.

    certeza  : 0.0=incerto  → 1.0=certo     (velocidade, oscilação - oscila mais com incerteza)
    esforco  : 0.0=raso     → 1.0=profundo  (intensidade das cores - esforço alto = cores mais quentes)
    emocao   : categoria semântica          (paleta de cores - urgente=vermelho, pensativo=azul, neutro=verde, etc.)
    direcao  : +1=avançando, -1=revisando   (sentido do sweep)

    Texto do título:
        verbo    - palavra animada (ex: "debugando")
        predicado - resto da frase (ex: "erro na API")
    """

    # === TEXTO ===
    verbo: str = "iniciando"
    predicado: str = "conversa"

    # === ANIMAÇÃO ===
    certeza: float = 0.8
    esforco: float = 0.5
    emocao: str = "neutro"
    direcao: int = 1


@dataclass
class _TemplateCores:
    """Gradiente de duas cores para um estado emocional."""

    de: str  # hex inicial
    ate: str  # hex final


# =============================================================================
# Paletas de Cores por Emoção
# =============================================================================
# (quente=ação intensa, frio=introspecção, neutro=idle)
# Para melhor visibilidade, as cores "de" devem ser saturadas e as cores "até" devem ser mais claras.

_PALETAS: dict[str, _TemplateCores] = {
    # 🔥 Quentes
    "urgente": _TemplateCores(de="#ff1c1c", ate="#ff9c8f"),
    "debugando": _TemplateCores(de="#ff1c1c", ate="#ffaa00"),
    "empolgado": _TemplateCores(de="#ff1c1c", ate="#ffd93d"),
    # 🌊 Frios
    "em_duvida": _TemplateCores(de="#006aff", ate="#a3e2ff"),
    "pensando": _TemplateCores(de="#006aff", ate="#c77dff"),
    "cuidadoso": _TemplateCores(de="#006aff", ate="#97f8a4"),
    # 🌿 Neutros
    "concluindo": _TemplateCores(de="#007510", ate="#97f8a4"),
    "neutro": _TemplateCores(de="#007510", ate="#a3e2ff"),
    "curioso": _TemplateCores(de="#007510", ate="#ffd93d"),
}
_PALETA_FALLBACK = _TemplateCores(de="#000000", ate="#ffffff")


# =============================================================================
# Descrições Linguísticas do EstadoLLM
# =============================================================================

_EMOCAO_EMOJI: dict[str, tuple[str, str]] = {
    "empolgado": ("🔥", "empolgada com o tema"),
    "urgente": ("⚡", "tratando com urgência"),
    "debugando": ("🔍", "investigando um problema"),
    "pensando": ("💭", "em reflexão profunda"),
    "cuidadoso": ("🌿", "sendo cuidadosa e precisa"),
    "em_duvida": ("🌀", "sentindo incerteza"),
    "neutro": ("✨", "em estado neutro"),
    "curioso": ("🔭", "curiosa sobre o assunto"),
    "concluindo": ("🎯", "chegando a uma conclusão"),
}


def _barra(valor: float, total: int = 12) -> str:
    """Gera barra de progresso unicode. valor 0.0→1.0"""
    cheios = round(valor * total)
    return "█" * cheios + "░" * (total - cheios)


def _desc_certeza(v: float) -> str:
    if v >= 0.85:
        return "muito confiante"
    if v >= 0.60:
        return "razoavelmente segura"
    if v >= 0.35:
        return "com alguma dúvida"
    return "bem incerta"


def _desc_esforco(v: float) -> str:
    if v >= 0.85:
        return "máximo esforço cognitivo"
    if v >= 0.60:
        return "raciocínio intenso"
    if v >= 0.35:
        return "processamento moderado"
    return "pensamento leve"


def _tooltip_estado(estado: EstadoLLM) -> str:
    """Texto compacto para o tooltip de hover."""
    emoji, desc_emocao = _EMOCAO_EMOJI.get(estado.emocao, ("✨", estado.emocao))
    dir_seta = "→ avançando" if estado.direcao == 1 else "← revisando"
    pct_c = int(estado.certeza * 100)
    pct_e = int(estado.esforco * 100)
    return "\n".join(
        [
            f"Sky {estado.verbo}",
            "━" * 28,
            f"🎯 certeza   {pct_c}%  {_desc_certeza(estado.certeza)}",
            f"⚡ esforço   {pct_e}%  {_desc_esforco(estado.esforco)}",
            f"🧭 {dir_seta}",
            f"{emoji} {desc_emocao}",
            "━" * 28,
            "clique para detalhes",
        ]
    )


def _card_estado(estado: EstadoLLM) -> str:
    """Markup Rich completo para o modal de clique."""
    emoji, desc_emocao = _EMOCAO_EMOJI.get(estado.emocao, ("✨", estado.emocao))
    dir_seta = (
        "[green]→ avançando[/]" if estado.direcao == 1 else "[yellow]← revisando[/]"
    )
    pct_c = int(estado.certeza * 100)
    pct_e = int(estado.esforco * 100)

    # Cor da barra de certeza: verde→amarelo→vermelho
    if estado.certeza >= 0.7:
        cor_c = "green"
    elif estado.certeza >= 0.4:
        cor_c = "yellow"
    else:
        cor_c = "red"

    # Cor da barra de esforço: frio→quente
    if estado.esforco >= 0.7:
        cor_e = "#ff6b6b"
    elif estado.esforco >= 0.4:
        cor_e = "#ffd93d"
    else:
        cor_e = "#4d96ff"

    return (
        f"[bold]Sky [italic]{estado.verbo}[/italic][/bold]\n\n"
        f"  [{cor_c}]🎯 certeza  {_barra(estado.certeza)} {pct_c}%[/]\n"
        f"     [dim]{_desc_certeza(estado.certeza)}[/dim]\n\n"
        f"  [{cor_e}]⚡ esforço  {_barra(estado.esforco)} {pct_e}%[/]\n"
        f"     [dim]{_desc_esforco(estado.esforco)}[/dim]\n\n"
        f"  🧭 direção   {dir_seta}\n\n"
        f"  {emoji} emoção    [bold]{desc_emocao}[/bold]\n"
    )


# =============================================================================
# Funções Auxiliares de Cores
# =============================================================================


def _hex_para_rgb(hex_cor: str) -> tuple[int, int, int]:
    """Converte cor hex para tupla RGB."""
    h = hex_cor.lstrip("#")
    return int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)


def _rgb_para_hex(r: int, g: int, b: int) -> str:
    """Converte tupla RGB para cor hex."""
    return f"#{r:02x}{g:02x}{b:02x}"


def _lerp_cor(cor_a: str, cor_b: str, t: float) -> str:
    """Interpola linearmente entre duas cores hex. t=0.0→cor_a, t=1.0→cor_b."""
    t = max(0.0, min(1.0, t))
    ra, ga, ba = _hex_para_rgb(cor_a)
    rb, gb, bb = _hex_para_rgb(cor_b)
    return _rgb_para_hex(
        int(ra + (rb - ra) * t),
        int(ga + (gb - ga) * t),
        int(ba + (bb - ba) * t),
    )


# =============================================================================
# AnimatedVerb Widget
# =============================================================================


class AnimatedVerb(Static):
    """
    Widget de palavra animada com três dimensões independentes:

    sweep   → gradiente se move pelas letras (timer_sweep)
    oscila  → as próprias cores pulsam entre de↔ate (timer_oscila)
    direção → sweep avança (+1) ou regride (-1) conforme EstadoLLM.direcao
    """

    # texto como reactive com layout=True:
    # quando o verbo muda (ex: "buscando" → "buscou"), o Textual
    # recalcula automaticamente get_content_width() e reposiciona
    # os widgets vizinhos no layout horizontal — sem gap.
    texto: reactive[str] = reactive("iniciando", layout=True)

    # Demais reativos (sem layout — só redesenho visual)
    _offset: reactive = reactive(0.0)  # posição do sweep (float para suavidade)
    _pulso: reactive = reactive(0.0)  # fase da oscilação  0.0 → 2π
    _estado: reactive = reactive(None)  # EstadoLLM atual

    def __init__(
        self, texto: str = "iniciando", estado: EstadoLLM | None = None
    ) -> None:
        super().__init__()
        self.texto = texto
        self._estado_inicial = estado or EstadoLLM(verbo=texto)

    def on_mount(self) -> None:
        """Inicia timers de animação."""
        self._estado = self._estado_inicial
        # Timer sweep — velocidade base modulada por certeza e esforço
        self._timer_sweep = self.set_interval(self._intervalo_sweep(), self._tick_sweep)
        # Timer oscila — só ativo se certeza < 0.8
        self._timer_oscila = self.set_interval(0.05, self._tick_oscila)

    # ------------------------------------------------------------------
    # Ticks dos timers
    # ------------------------------------------------------------------

    def _tick_sweep(self) -> None:
        """Incrementa offset do sweep."""
        estado = self._estado
        if estado is None:
            return
        passo = 0.8 + estado.esforco * 0.6  # esforço alto = saltos maiores
        self._offset += passo * estado.direcao

    def _tick_oscila(self) -> None:
        """Incrementa fase da oscilação."""
        estado = self._estado
        if estado is None or estado.certeza >= 0.91:
            return  # alta certeza = cores estáveis, não oscila
        # Velocidade da oscilação inversamente proporcional à certeza
        velocidade = 0.04 + (1.0 - estado.certeza) * 0.12
        self._pulso = (self._pulso + velocidade) % (2 * math.pi)

    # ------------------------------------------------------------------
    # Render
    # ------------------------------------------------------------------

    def render(self) -> RenderResult:
        """Renderiza o texto com cores aplicadas letra-por-letra."""
        estado = self._estado
        if estado is None:
            return self.texto

        paleta = _PALETAS.get(estado.emocao, _PALETA_FALLBACK)

        # Oscilação: seno suave que pulsa entre de e ate
        # certeza alta → t_oscila fixo em 0.5 (meio-termo estável)
        if estado.certeza >= 0.91:
            t_oscila = 0.5
        else:
            amplitude = (1.0 - estado.certeza) * 0.5  # incerteza = amplitude maior
            t_oscila = 0.5 + math.sin(self._pulso) * amplitude

        # Cores do gradiente neste instante (após oscilação)
        cor_de_agora = _lerp_cor(paleta.de, paleta.ate, 1.0 - t_oscila)
        cor_ate_agora = _lerp_cor(paleta.de, paleta.ate, t_oscila)

        # Sweep: distribui o gradiente pelas letras
        resultado = ""
        JANELA = 7
        for i, letra in enumerate(self.texto):
            t_letra = ((i - self._offset) % JANELA) / JANELA
            cor = _lerp_cor(cor_de_agora, cor_ate_agora, t_letra)
            resultado += f"[{cor}]{letra}[/]"
        return resultado

    # ------------------------------------------------------------------
    # API pública
    # ------------------------------------------------------------------

    def watch__estado(self, estado: EstadoLLM | None) -> None:
        """Atualiza tooltip sempre que o estado muda."""
        if estado is not None:
            self.tooltip = _tooltip_estado(estado)

    def on_click(self) -> None:
        """Abre o modal com o card completo."""
        if self._estado:
            self.post_message(self.Inspecionado(self._estado))

    class Inspecionado(Message):
        """Postada quando o usuário clica no verbo."""

        def __init__(self, estado: EstadoLLM) -> None:
            super().__init__()
            self.estado = estado

    def get_content_width(self, container, viewport) -> int:
        """
        Retorna a largura real do texto visível (sem markup Rich).

        Sem isso, width:auto mede o comprimento da string de markup
        (com todas as tags de cor), que é muito maior que o texto exibido.
        Isso faz o layout horizontal calcular posições erradas para os
        widgets vizinhos (#predicado fica 'flutuando').
        """
        return len(self.texto)

    def update_verbo(self, novo_verbo: str) -> None:
        """Troca o texto (sem resetar animação)."""
        # reactive(layout=True) já dispara reflow + redesenho automaticamente
        self.texto = novo_verbo

    def update_estado(self, estado: EstadoLLM) -> None:
        """
        Aplica um novo EstadoLLM.
        Mudança de direção é imediata; cores e velocidade transitam suavemente.
        """
        antigo = self._estado
        self._estado = estado
        # atribuir texto já dispara layout=True automaticamente
        self.texto = estado.verbo

        # Reinicia timer do sweep com nova velocidade
        self._timer_sweep.stop()
        self._timer_sweep = self.set_interval(self._intervalo_sweep(), self._tick_sweep)

        # Mudança brusca de direção: inverte offset para comunicar visualmente
        if antigo and antigo.direcao != estado.direcao:
            self._offset = -self._offset

    def _intervalo_sweep(self) -> float:
        """Intervalo em segundos entre ticks do sweep.

        certeza alta + esforço baixo  → sweep lento  (0.15s)
        certeza baixa + esforço alto  → sweep rápido (0.04s)
        """
        estado = self._estado or self._estado_inicial
        base = 0.15
        fator_certeza = (1.0 - estado.certeza) * 0.08  # incerteza acelera
        fator_esforco = estado.esforco * 0.03  # esforço acelera um pouco
        return max(0.04, base - fator_certeza - fator_esforco)


# =============================================================================
# EstadoModal
# =============================================================================


class EstadoModal(ModalScreen):
    """Modal que exibe o EstadoLLM atual em linguagem natural."""

    DEFAULT_CSS = """
    EstadoModal {
        align: center middle;
    }
    EstadoModal > Vertical {
        width: 44;
        height: auto;
        border: round $accent;
        background: $surface;
        padding: 1 2;
    }
    EstadoModal #titulo {
        text-align: center;
        color: $text-muted;
        margin-bottom: 1;
    }
    EstadoModal #card {
        height: auto;
    }
    EstadoModal #dica {
        text-align: center;
        color: $text-muted;
        margin-top: 1;
    }
    """

    BINDINGS = [("escape", "dismiss", "")]

    def __init__(self, estado: EstadoLLM) -> None:
        super().__init__()
        self._estado = estado

    def compose(self) -> ComposeResult:
        """Compõe o modal com estado completo."""
        with Vertical():
            yield Static("[dim]─── estado interno da Sky ───[/dim]", id="titulo")
            yield Static(_card_estado(self._estado), id="card", markup=True)
            yield Static("[dim]clique em qualquer lugar para fechar[/dim]", id="dica")

    def on_click(self) -> None:
        """Fecha o modal ao clicar."""
        self.dismiss()


# =============================================================================
# Conjugação Gerúndio → Passado
# =============================================================================

_PASSADO_IRREGULAR: dict[str, str] = {
    # Verbos que fogem das regras regulares
    "sendo": "foi",
    "indo": "foi",
    "vindo": "veio",
    "fazendo": "fez",
    "trazendo": "trouxe",
    "podendo": "pôde",
    "dizendo": "disse",
    "tendo": "teve",
}


def conjugar_passado(verbo_gerundio: str) -> str:
    """
    Converte verbo no gerúndio para 3ª pessoa singular do pretérito perfeito.

    Regras regulares:
      -ando  →  -ou    (buscar → buscou, analisar → analisou)
      -endo  →  -eu    (escrever → escreveu, correr → correu)
      -indo  →  -iu    (corrigir → corrigiu, emitir → emitiu)

    Args:
        verbo_gerundio: Verbo no gerúndio (ex: "buscando", "escrevendo").

    Returns:
        Verbo no pretérito perfeito (ex: "buscou", "escreveu").
    """
    v = verbo_gerundio.lower().strip()

    # Irregulares primeiro
    if v in _PASSADO_IRREGULAR:
        return _PASSADO_IRREGULAR[v]

    # Regras regulares por terminação
    if v.endswith("ando"):
        return v[:-4] + "ou"   # buscando → buscou
    if v.endswith("endo"):
        return v[:-4] + "eu"   # escrevendo → escreveu
    if v.endswith("indo"):
        return v[:-4] + "iu"   # corrigindo → corrigiu

    # Fallback: retorna o gerúndio sem transformação
    return v


__all__ = [
    "EstadoLLM",
    "AnimatedVerb",
    "EstadoModal",
    "conjugar_passado",
]
