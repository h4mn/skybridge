# coding: utf-8
"""
AnimatedTitle - Título dinâmico com verbo animado.
"""

import re
from typing import TYPE_CHECKING

from textual.app import ComposeResult
from textual.events import Message
from textual.widget import Widget
from textual.widgets import Static

from core.sky.chat.textual_ui.widgets.header.animated_verb import AnimatedVerb, EstadoLLM

if TYPE_CHECKING:
    from core.sky.chat.textual_ui.widgets.header.title.history import TitleHistory


def _largura_visivel(markup: str) -> int:
    """Comprimento do texto visível, ignorando tags Rich."""
    try:
        from rich.text import Text
        return len(Text.from_markup(markup))
    except Exception:
        return len(re.sub(r"\[.*?\]", "", markup))


class TitleStatic(Static):
    """
    Static que reporta largura do texto visível, não do markup bruto.

    Static padrão: get_content_width() mede "[bold]Sky está[/] " = 18
    TitleStatic:   get_content_width() mede "Sky está "           = 9

    Com isso, quando AnimatedVerb.texto muda (reactive layout=True),
    o Textual chama get_content_width() em todos os filhos e recalcula
    as posições corretamente — sem precisar de styles.width manual.
    """

    class Clicked(Message):
        """Postada quando TitleStatic é clicado."""

        def __init__(self, widget: "TitleStatic") -> None:
            super().__init__()
            self.widget = widget

    def __init__(self, markup: str, **kwargs) -> None:
        super().__init__(markup, markup=True, **kwargs)
        self._markup = markup

    def update(self, content: str) -> None:  # type: ignore[override]
        self._markup = content
        super().update(content)

    def get_content_width(self, container, viewport) -> int:
        return _largura_visivel(self._markup)

    def on_click(self) -> None:
        """Posta mensagem Clicked quando clicado."""
        self.post_message(self.Clicked(self))

    def update_tooltip(self, history: "TitleHistory") -> None:
        """
        Atualiza o tooltip com resumo dos últimos verbos únicos do histórico.

        Formato: "Sky esteve: analisando → codando → testando → ..."

        Remove duplicatas consecutivas (gerúndio + passado do mesmo verbo)
        para evitar mostrar "processando → processou → analisando → analisou"
        """
        last_entries = history.get_last(10)  # Pega mais entradas para filtrar duplicatas
        if not last_entries:
            self.tooltip = ""
            return

        # Remove duplicatas consecutivas baseando-se no radical do verbo
        verbos_unicos = []
        ultimo_radical = None

        for entry in last_entries:
            verbo = entry.estado.verbo
            # Extrai o radical (remove terminações Ando/Endo/Indo ou Ou/Eu/Iu)
            radical = self._extrair_radical(verbo)

            # Só adiciona se for um radical diferente do último
            if radical != ultimo_radical:
                verbos_unicos.append(verbo)
                ultimo_radical = radical

            # Para após 5 verbos únicos
            if len(verbos_unicos) >= 5:
                break

        self.tooltip = f"Sky esteve: {' → '.join(verbos_unicos)}"

    @staticmethod
    def _extrair_radical(verbo: str) -> str:
        """
        Extrai o radical do verbo para comparar formas diferentes.

        Remove terminações de gerúndio (-ando, -endo, -indo) e
        pretérito (-ou, -eu, -iu) para obter o radical comum.
        """
        # Terminações de pretérito perfeito regular
        for term in ["ou", "eu", "iu"]:
            if verbo.endswith(term) and len(verbo) > len(term):
                return verbo[:-len(term)]

        # Terminações de gerúndio
        for term in ["ando", "endo", "indo"]:
            if verbo.endswith(term):
                return verbo[:-len(term)]

        # Fallback: retorna o próprio verbo
        return verbo


class AnimatedTitle(Widget):
    """
    Título animado: "Sky está buscando informações no código"

    Layout horizontal com 3 filhos:
      TitleStatic("#sujeito") + AnimatedVerb + TitleStatic("#predicado")

    Quando AnimatedVerb.texto muda (reactive layout=True), o Textual
    dispara reflow no pai e chama get_content_width() em todos os filhos.
    TitleStatic e AnimatedVerb retornam larguras do texto visível,
    então o predicado reposiciona corretamente — sem gap, sem sobreposição.
    """

    DEFAULT_CSS = """
    AnimatedTitle {
        layout: horizontal;
        height: 1;
        width: auto;
    }
    AnimatedTitle > TitleStatic  { width: auto; }
    AnimatedTitle > AnimatedVerb { width: auto; }
    """

    def __init__(self, sujeito: str = "Sky", verbo: str = "iniciando", predicado: str = "conversa") -> None:
        super().__init__()
        self._sujeito   = sujeito
        self._verbo     = verbo
        self._predicado = predicado

    @staticmethod
    def _eh_gerundio(verbo: str) -> bool:
        return verbo.endswith(("ando", "endo", "indo"))

    def compose(self) -> ComposeResult:
        prefixo = f"{self._sujeito} está" if self._eh_gerundio(self._verbo) else self._sujeito
        yield TitleStatic(f"[bold]{prefixo}[/] ", id="sujeito")
        yield AnimatedVerb(self._verbo)
        yield TitleStatic(f" {self._predicado}", id="predicado")

    def update_title(self, verbo: str, predicado: str) -> None:
        self._verbo     = verbo
        self._predicado = predicado
        prefixo = f"{self._sujeito} está" if self._eh_gerundio(verbo) else self._sujeito
        self.query_one("#sujeito",   TitleStatic).update(f"[bold]{prefixo}[/] ")
        self.query_one("#predicado", TitleStatic).update(f" {predicado}")
        self.query_one(AnimatedVerb).update_verbo(verbo)
        # update_verbo seta self.texto (reactive layout=True) → reflow automático

    def update_estado(self, estado: EstadoLLM, predicado: str | None = None) -> None:
        self._verbo = estado.verbo
        if predicado is not None:
            self._predicado = predicado

        prefixo = f"{self._sujeito} está" if self._eh_gerundio(estado.verbo) else self._sujeito
        self.query_one("#sujeito",   TitleStatic).update(f"[bold]{prefixo}[/] ")
        self.query_one("#predicado", TitleStatic).update(f" {self._predicado}")

        self.query_one(AnimatedVerb).update_estado(EstadoLLM(
            verbo=estado.verbo,
            predicado=estado.predicado,
            certeza=estado.certeza,
            esforco=estado.esforco,
            emocao=estado.emocao,
            direcao=estado.direcao,
        ))
        # update_estado seta self.texto (reactive layout=True) → reflow automático


__all__ = ["AnimatedTitle"]
