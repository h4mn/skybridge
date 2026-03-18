"""
========================================
Classes de Domínio
========================================
"""
# aqui vai a classe Mensagem (entidade: role, content, timestamp)
# aqui vai a classe ChatResponse (resposta: content, tokens_used, model)
# aqui vai a classe ChatSession (estado: messages[], title, context_usage%)



"""
========================================
Classes de Aplicação
========================================
"""
# aqui vai o caso de uso EnviarMensagem (input → worker → response)
# aqui vai o caso de uso GerarTitulo (analisa contexto → "Sky debugando API")
# aqui vai o ChatService (orquestra conversa, mantém estado da sessão)


"""
========================================
Classes de Infraestrutura (Textual UI)
========================================
"""
# AQUI: Screens
#   - PocSplashScreen (tela de apresentação centralizada)
#   - PocMainScreen (tela principal do chat com header/footer fixos)
#   - PocConfigScreen (tela de configurações - futuro)
#   - PocHelpScreen (tela de ajuda - futuro)
#
# AQUI: Widgets Customizados
#   - PocLog (widget de log para debug/observabilidade)
#   - PocVerticalScroll (container scrollável para bubbles)
#   - SkyBubble (mensagem da Sky alinhada à esquerda)
#   - UserBubble (mensagem do usuário alinhada à direita)
#   - AnimatedTitle (título com verbo animado color sweep)
#   - ContextBar (barra de progresso verde/amarelo/laranja/vermelho)
#   - ThinkingIndicator (🤔 animado durante processamento)
#
# AQUI: Workers Assíncronos
#   - ClaudeWorker (chamada ao Claude SDK em background)
#   - RagWorker (busca semântica em background)
from textual.widgets import Static, Input, Header, Footer, Label, RichLog, TextArea
from textual.widget import Widget
from textual import on
from textual.containers import Vertical, VerticalScroll
from textual.screen import Screen, ModalScreen
from textual.app import ComposeResult
from textual import events
from textual.keys import Keys
from textual.reactive import reactive
from textual.app import RenderResult


class PocLog(RichLog):
    markup = True

    def debug(self, message) -> None:
        self.write(f"[yellow][DEBUG][/] {message}")
    
    def info(self, message) -> None:
        self.write(f"[blue][INFO][/] {message}")

    def error(self, message) -> None:
        self.write(f"[red][ERROR][/] {message}")
    
    def evento(self, nome: str, dados: str = "") -> None:
        self.write(f"[green][EVENTO][/] {nome} {dados}")


class ChatTextArea(TextArea):
    """TextArea customizado: Enter envia, Shift+Enter nova linha."""

    class Submitted(events.Message):
        """Postada quando o usuário pressiona Enter."""
        def __init__(self, value: str) -> None:
            super().__init__()
            self.value = value

    def on_key(self, event: events.Key) -> None:
        if event.key == Keys.Enter:
            event.prevent_default()  # Previne nova linha
            event.stop()              # Para propagação
            self.post_message(self.Submitted(self.text))
            self.clear()
        elif event.key == Keys.Escape:
            # Esc: limpa o texto
            self.text = ""
            event.stop()


class PocSplashScreen(Screen):
    def __init__(self):
        super().__init__()

    def compose(self) -> ComposeResult:
        with Vertical():
            yield Label("[bold]Sky[/bold]Bridge")

        yield ChatTextArea(
            id="chat_input_textarea",
            placeholder="Digite algo..."
        )
        yield Footer()

    def on_chat_text_area_submitted(self, event: ChatTextArea.Submitted):
        self.app.push_screen(PocMainScreen(event.value))


class PocVerticalScroll(VerticalScroll):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    def adicionar_mensagem(self, texto: str):
        bubble = Static(texto)
        self.mount(bubble)
        self.scroll_end()

    def limpar_bubbles(self):
        self.remove_children()


# =============================================================================
# Sistema de Animação Semântica
# =============================================================================
from dataclasses import dataclass, field
import math
import random


@dataclass
class EstadoLLM:
    """
    Estado emocional/cognitivo da LLM.
    Controla todas as dimensões da animação do verbo.

    certeza  : 0.0=incerto  → 1.0=certo     (velocidade, oscilação - oscila mais com incerteza)
    esforco  : 0.0=raso     → 1.0=profundo  (intensidade das cores - esforço alto = cores mais quentes)
    emocao   : categoria semântica          (paleta de cores - urgente=vermelho, pensativo=azul, neutro=verde, etc.)
    direcao  : +1=avançando, -1=revisando   (sentido do sweep)
    """
    verbo:    str   = "iniciando"
    certeza:  float = 0.8
    esforco:  float = 0.5
    emocao:   str   = "neutro"
    direcao:  int   = 1


@dataclass
class _TemplateCores:
    """Gradiente de duas cores para um estado emocional."""
    de:  str   # hex inicial
    ate: str   # hex final


# Paletas por emoção — (quente=ação intensa, frio=introspecção, neutro=idle)
# Para melhor visibilidade, as cores "de" deve ser saturadas e as cores "até" devem ser mais claras.
_PALETAS: dict[str, _TemplateCores] = {
    # 🔥 Quentes
    "urgente":     _TemplateCores(de="#ff1c1c", ate="#ff9c8f"),
    "debugando":   _TemplateCores(de="#ff1c1c", ate="#ffaa00"),
    "empolgado":   _TemplateCores(de="#ff1c1c", ate="#ffd93d"),
    # 🌊 Frios
    "em_duvida":   _TemplateCores(de="#006aff", ate="#a3e2ff"),
    "pensando":    _TemplateCores(de="#006aff", ate="#c77dff"),
    "cuidadoso":   _TemplateCores(de="#006aff", ate="#97f8a4"),
    # 🌿 Neutros
    "concluindo":  _TemplateCores(de="#007510", ate="#97f8a4"),
    "neutro":      _TemplateCores(de="#007510", ate="#a3e2ff"),
    "curioso":     _TemplateCores(de="#007510", ate="#ffd93d"),
}
_PALETA_FALLBACK = _TemplateCores(de="#000000", ate="#ffffff")


def _hex_para_rgb(hex_cor: str) -> tuple[int, int, int]:
    h = hex_cor.lstrip("#")
    return int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)


def _rgb_para_hex(r: int, g: int, b: int) -> str:
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
# Verbos de Teste — Amostra variada para validação visual
# =============================================================================

_VERBOS_TESTE: list[tuple[str, EstadoLLM]] = [
    # verbos com estados pré-configurados para testar dimensões
    ("analisando",   EstadoLLM(verbo="analisando", certeza=0.7, esforco=0.5, emocao="pensando", direcao=1)),
    ("codando",      EstadoLLM(verbo="codando", certeza=0.9, esforco=0.8, emocao="debugando", direcao=1)),
    ("refletindo",   EstadoLLM(verbo="refletindo", certeza=0.4, esforco=0.3, emocao="em_duvida", direcao=-1)),
    ("criando",      EstadoLLM(verbo="criando", certeza=0.85, esforco=0.9, emocao="empolgado", direcao=1)),
    ("buscando",     EstadoLLM(verbo="buscando", certeza=0.6, esforco=0.6, emocao="curioso", direcao=1)),
    ("corrigindo",   EstadoLLM(verbo="corrigindo", certeza=0.75, esforco=0.7, emocao="cuidadoso", direcao=-1)),
    ("finalizando",  EstadoLLM(verbo="finalizando", certeza=0.95, esforco=0.4, emocao="concluindo", direcao=1)),
    ("correndo",     EstadoLLM(verbo="correndo", certeza=0.5, esforco=1.0, emocao="urgente", direcao=1)),
    ("sonhando",     EstadoLLM(verbo="sonhando", certeza=0.3, esforco=0.2, emocao="pensando", direcao=1)),
    ("pilotando",    EstadoLLM(verbo="pilotando", certeza=0.88, esforco=0.65, emocao="neutro", direcao=1)),
    # verbos "loucos" para testar extremos
    ("explodindo",   EstadoLLM(verbo="explodindo", certeza=1.0, esforco=1.0, emocao="empolgado", direcao=1)),
    ("viajando",      EstadoLLM(verbo="viajando", certeza=0.1, esforco=0.9, emocao="em_duvida", direcao=-1)),
    ("meditando",    EstadoLLM(verbo="meditando", certeza=1.0, esforco=0.0, emocao="concluindo", direcao=1)),
    ("boiando",      EstadoLLM(verbo="boiando", certeza=0.2, esforco=0.1, emocao="em_duvida", direcao=1)),
    ("incendiando",  EstadoLLM(verbo="incendiando", certeza=0.7, esforco=1.0, emocao="urgente", direcao=1)),
    ("desintegrando", EstadoLLM(verbo="desintegrando", certeza=0.0, esforco=0.5, emocao="em_duvida", direcao=1)),
]


# =============================================================================
# Descrições linguísticas do EstadoLLM
# =============================================================================

_EMOCAO_EMOJI: dict[str, tuple[str, str]] = {
    # emocao: (emoji, descrição)
    "empolgado":  ("🔥", "empolgada com o tema"),
    "urgente":    ("⚡", "tratando com urgência"),
    "debugando":  ("🔍", "investigando um problema"),
    "pensando":   ("💭", "em reflexão profunda"),
    "cuidadoso":  ("🌿", "sendo cuidadosa e precisa"),
    "em_duvida":  ("🌀", "sentindo incerteza"),
    "neutro":     ("✨", "em estado neutro"),
    "curioso":    ("🔭", "curiosa sobre o assunto"),
    "concluindo": ("🎯", "chegando a uma conclusão"),
}


def _barra(valor: float, total: int = 12) -> str:
    """Gera barra de progresso unicode. valor 0.0→1.0"""
    cheios = round(valor * total)
    return "█" * cheios + "░" * (total - cheios)


def _desc_certeza(v: float) -> str:
    if v >= 0.85: return "muito confiante"
    if v >= 0.60: return "razoavelmente segura"
    if v >= 0.35: return "com alguma dúvida"
    return "bem incerta"


def _desc_esforco(v: float) -> str:
    if v >= 0.85: return "máximo esforço cognitivo"
    if v >= 0.60: return "raciocínio intenso"
    if v >= 0.35: return "processamento moderado"
    return "pensamento leve"


def _tooltip_estado(estado: EstadoLLM) -> str:
    """Texto compacto para o tooltip de hover."""
    emoji, desc_emocao = _EMOCAO_EMOJI.get(estado.emocao, ("✨", estado.emocao))
    dir_seta = "→ avançando" if estado.direcao == 1 else "← revisando"
    pct_c = int(estado.certeza * 100)
    pct_e = int(estado.esforco * 100)
    return "\n".join([
        f"Sky está {estado.verbo}",
        "━" * 28,
        f"🎯 certeza   {pct_c}%  {_desc_certeza(estado.certeza)}",
        f"⚡ esforço   {pct_e}%  {_desc_esforco(estado.esforco)}",
        f"🧭 {dir_seta}",
        f"{emoji} {desc_emocao}",
        "━" * 28,
        "clique para detalhes",
    ])


def _card_estado(estado: EstadoLLM) -> str:
    """Markup Rich completo para o modal de clique."""
    emoji, desc_emocao = _EMOCAO_EMOJI.get(estado.emocao, ("✨", estado.emocao))
    dir_seta  = "[green]→ avançando[/]" if estado.direcao == 1 else "[yellow]← revisando[/]"
    pct_c = int(estado.certeza * 100)
    pct_e = int(estado.esforco * 100)

    # Cor da barra de certeza: verde→amarelo→vermelho
    if estado.certeza >= 0.7:  cor_c = "green"
    elif estado.certeza >= 0.4: cor_c = "yellow"
    else:                        cor_c = "red"

    # Cor da barra de esforço: frio→quente
    if estado.esforco >= 0.7:  cor_e = "#ff6b6b"
    elif estado.esforco >= 0.4: cor_e = "#ffd93d"
    else:                        cor_e = "#4d96ff"

    return (
        f"[bold]Sky está [italic]{estado.verbo}[/italic][/bold]\n\n"
        f"  [{cor_c}]🎯 certeza  {_barra(estado.certeza)} {pct_c}%[/]\n"
        f"     [dim]{_desc_certeza(estado.certeza)}[/dim]\n\n"
        f"  [{cor_e}]⚡ esforço  {_barra(estado.esforco)} {pct_e}%[/]\n"
        f"     [dim]{_desc_esforco(estado.esforco)}[/dim]\n\n"
        f"  🧭 direção   {dir_seta}\n\n"
        f"  {emoji} emoção    [bold]{desc_emocao}[/bold]\n"
    )


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
        with Vertical():
            yield Static("[dim]─── estado interno da Sky ───[/dim]", id="titulo")
            yield Static(_card_estado(self._estado), id="card", markup=True)
            yield Static("[dim]clique em qualquer lugar para fechar[/dim]", id="dica")

    def on_click(self) -> None:
        self.dismiss()


# =============================================================================


class AnimatedVerb(Static):
    """
    Widget de palavra animada com três dimensões independentes:

    sweep   → gradiente se move pelas letras (timer_sweep)
    oscila  → as próprias cores pulsam entre de↔ate (timer_oscila)
    direção → sweep avança (+1) ou regride (-1) conforme EstadoLLM.direcao
    """

    # Três reativos independentes — cada um tem seu próprio timer
    _offset:    reactive = reactive(0.0)   # posição do sweep (float para suavidade)
    _pulso:     reactive = reactive(0.0)   # fase da oscilação  0.0 → 2π
    _estado:    reactive = reactive(None)  # EstadoLLM atual

    def __init__(self, texto: str = "iniciando", estado: EstadoLLM | None = None) -> None:
        super().__init__()
        self.texto = texto
        self._estado_inicial = estado or EstadoLLM(verbo=texto)

    def on_mount(self) -> None:
        self._estado = self._estado_inicial
        # Timer sweep — velocidade base modulada por certeza e esforço
        self._timer_sweep  = self.set_interval(self._intervalo_sweep(),  self._tick_sweep)
        # Timer oscila — só ativo se certeza < 0.8
        self._timer_oscila = self.set_interval(0.05, self._tick_oscila)

    # ------------------------------------------------------------------
    # Ticks dos timers
    # ------------------------------------------------------------------

    def _tick_sweep(self) -> None:
        estado = self._estado
        if estado is None:
            return
        passo = 0.8 + estado.esforco * 0.6          # esforço alto = saltos maiores
        self._offset += passo * estado.direcao

    def _tick_oscila(self) -> None:
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
        estado = self._estado
        if estado is None:
            return self.texto

        paleta = _PALETAS.get(estado.emocao, _PALETA_FALLBACK)

        # Oscilação: seno suave que pulsa entre de e ate
        # certeza alta → t_oscila fixo em 0.5 (meio-termo estável)
        if estado.certeza >= 0.91:
            t_oscila = 0.5
        else:
            amplitude = (1.0 - estado.certeza) * 0.5   # incerteza = amplitude maior
            t_oscila = 0.5 + math.sin(self._pulso) * amplitude

        # Cores do gradiente neste instante (após oscilação)
        cor_de_agora  = _lerp_cor(paleta.de,  paleta.ate, 1.0 - t_oscila)
        cor_ate_agora = _lerp_cor(paleta.de,  paleta.ate, t_oscila)

        # Sweep: distribui o gradiente pelas letras
        resultado = ""
        # JANELA = 3.5  # quantas letras cabem num ciclo completo do gradiente
        JANELA = 7
        for i, letra in enumerate(self.texto):
            t_letra = ((i - self._offset) % JANELA) / JANELA
            # t_letra = ((i - self._offset))
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

    class Inspecionado(events.Message):
        """Postada quando o usuário clica no verbo."""
        def __init__(self, estado: EstadoLLM) -> None:
            super().__init__()
            self.estado = estado

    def update_verbo(self, novo_verbo: str) -> None:
        """Troca o texto (sem resetar animação)."""
        self.texto = novo_verbo

    def update_estado(self, estado: EstadoLLM) -> None:
        """
        Aplica um novo EstadoLLM.
        Mudança de direção é imediata; cores e velocidade transitam suavemente.
        """
        antigo = self._estado
        self._estado = estado
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
        fator_certeza = (1.0 - estado.certeza) * 0.08   # incerteza acelera
        fator_esforco = estado.esforco * 0.03             # esforço acelera um pouco
        return max(0.04, base - fator_certeza - fator_esforco)


class AnimatedTitle(Widget):
    """Título 'Sky [verbo animado] predicado'."""

    DEFAULT_CSS = """
    AnimatedTitle {
        layout: horizontal;
        height: 1;
        width: auto;
    }
    AnimatedTitle > Static { width: auto; }
    AnimatedTitle > AnimatedVerb { width: auto; }
    """

    def __init__(
        self,
        sujeito: str = "Sky",
        verbo: str = "iniciando",
        predicado: str = "conversa",
    ) -> None:
        super().__init__()
        self._sujeito = sujeito
        self._verbo = verbo
        self._predicado = predicado

    def compose(self) -> ComposeResult:
        yield Static(f"[bold]{self._sujeito}[/] ")
        yield AnimatedVerb(self._verbo)
        yield Static(f" {self._predicado}")

    def update_title(self, verbo: str, predicado: str) -> None:
        """Atualiza verbo e predicado dinamicamente."""
        self._predicado = predicado
        self.query_one(AnimatedVerb).update_verbo(verbo)
        self.query_one("Static:last-of-type", Static).update(f" {predicado}")

    def update_estado(self, estado: EstadoLLM, predicado: str | None = None) -> None:
        """Atualiza via EstadoLLM — verbo, cores, velocidade e direção de uma vez."""
        if predicado:
            self._predicado = predicado
            self.query_one("Static:last-of-type", Static).update(f" {predicado}")
        self.query_one(AnimatedVerb).update_estado(estado)


class PocHeader(Widget):
    """Header clicável com toggle de altura e 2 linhas."""

    def __init__(self, verbo: str = "iniciando", predicado: str = "conversa"):
        super().__init__()
        self._verbo = verbo
        self._predicado = predicado
        self._expanded = False

    def compose(self) -> ComposeResult:
        # Linha 1: Título animado
        yield AnimatedTitle("Sky", self._verbo, self._predicado)
        # Linha 2: Componentes
        yield Static("🔥 5 msgs | RAG: on | GLM-4.7", id="components")

    def on_click(self) -> None:
        self._expanded = not self._expanded
        if self._expanded:
            self.add_class("expanded")
        else:
            self.remove_class("expanded")

    def update_title(self, verbo: str, predicado: str) -> None:
        """Atualiza o título dinamicamente."""
        self._verbo = verbo
        self._predicado = predicado
        # Busca o AnimatedTitle por tipo
        title = self.query_one(AnimatedTitle)
        title.update_title(verbo, predicado)

    def update_estado(self, estado: EstadoLLM, predicado: str | None = None) -> None:
        """Atualiza via EstadoLLM — verbo, cores, velocidade e direção."""
        if predicado:
            self._predicado = predicado
        title = self.query_one(AnimatedTitle)
        title.update_estado(estado, predicado or self._predicado)


class PocMainScreen(Screen):
    BINDINGS = [
        ("ctrl+l", "toggle_log", "Toggle Log"),
        ("ctrl+v", "ciclar_verbo", "Próximo Verbo"),
    ]

    def __init__(self, input: str):
        super().__init__()
        self.input = input
        self._verbo_idx = 0
            
    def compose(self) -> ComposeResult:
        yield PocHeader()
        yield PocVerticalScroll(id="container")
        yield ChatTextArea(
            id="chat_input_textarea",
            placeholder="Digite algo..."
        )
        yield PocLog()
        yield Footer()

    def on_mount(self):
        _, estado_inicial = random.choice(_VERBOS_TESTE)
        self.query_one(PocHeader).update_estado(estado_inicial)

        log = self.query_one(PocLog)
        log.evento("Tela montada", self.input)

        scroll = self.query_one("#container", PocVerticalScroll)
        scroll.adicionar_mensagem(f"Você digitou: {self.input}")

        # Coloca foco no ChatTextArea de entrada
        textarea = self.query_one("#chat_input_textarea", ChatTextArea)
        textarea.focus()

    def on_input_submitted(self, event):
        scroll = self.query_one("#container", PocVerticalScroll)
        log = self.query_one(PocLog)
        log.evento("Input recebido", event.value)
        scroll.adicionar_mensagem(f"Você: {event.value}")

    def on_chat_text_area_submitted(self, event: ChatTextArea.Submitted):
        scroll = self.query_one("#container", PocVerticalScroll)
        log = self.query_one(PocLog)
        log.evento("TextArea submetido", event.value)
        scroll.adicionar_mensagem(f"Você: {event.value}")

    def action_toggle_log(self) -> None:
        log = self.query_one(PocLog)
        log.toggle_class("visible")

    def action_ciclar_verbo(self) -> None:
        """Cicla para o próximo verbo de teste (Ctrl+V)."""
        self._verbo_idx = (self._verbo_idx + 1) % len(_VERBOS_TESTE)
        verbo, estado = _VERBOS_TESTE[self._verbo_idx]

        header = self.query_one(PocHeader)
        header.update_estado(estado, f"[{self._verbo_idx + 1}/{len(_VERBOS_TESTE)}]")

        log = self.query_one(PocLog)
        log.evento(f"Verbo #{self._verbo_idx + 1}", f"{verbo} ({estado.emocao})")

    def on_animated_verb_inspecionado(self, event: AnimatedVerb.Inspecionado) -> None:
        self.app.push_screen(EstadoModal(event.estado))


"""
========================================
Classes de Interface (Entry Point)
========================================
"""
# aqui: PocApp (app Textual principal, entry point)
# aqui: ChatAdapter (protocol/interface para Claude SDK)
from textual.app import App as _TextualApp

class PocApp(_TextualApp):
    CSS_PATH = "app.tcss"  # CSS externo para hot-reload em dev mode

    BINDINGS = [
        ("^q", "quit", "Quit"),
        ("^d", "toggle_dark", "Toggle dark"),
    ]

    def __init__(self):
        super().__init__()

    def run(self):
        super().run()

    def on_mount(self):
        self.push_screen(PocSplashScreen())

    def push_screen(self, screen):
        super().push_screen(screen)


if __name__ == "__main__":
    app = PocApp()
    app.run()
