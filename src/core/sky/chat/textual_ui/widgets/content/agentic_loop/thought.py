# coding: utf-8
"""
ThoughtLine - Linha de pensamento (Thought) do StepWidget.

Exibe o texto de intenção narrado pelo modelo antes de usar uma ferramenta.
Estilo: itálico muted, sutil.

Usado para pensamentos curtos (<= 80 caracteres).
Para pensamentos longos, use ThoughtLineMarkdown.
"""

from textual.widgets import Static, Markdown


class ThoughtLine(Static):
    """
    Linha de pensamento (Thought) do StepWidget.

    Exibe o texto de intenção narrado pelo modelo antes de usar uma ferramenta.
    Estilo: itálico muted, sutil.

    Usado para pensamentos curtos (<= 80 caracteres).
    Para pensamentos longos, use ThoughtLineMarkdown.
    """

    DEFAULT_CSS = """
    ThoughtLine {
        text-style: italic;
        color: $text;  /* Mudado de $text-muted para $text para visibilidade */
        padding: 0 1;
        margin: 0 0 0 0;
        height: auto;
    }
    """

    def __init__(self, text: str) -> None:
        super().__init__(text)
        self._text = text

    def set_text(self, text: str) -> None:
        """Atualiza o texto do pensamento."""
        self._text = text
        # Remove aspas se presentes
        display_text = text.strip('"').strip("'")
        self.update(f"_{display_text}")


class ThoughtLineMarkdown(Markdown):
    """
    Linha de pensamento longo renderizada como Markdown.

    Usada para pensamentos > 80 caracteres que contêm markdown ou
    informações estruturadas (não apenas raciocínio simples).

    Diferente de ThoughtLine, não usa itálico e permite renderização
    completa de markdown (listas, código, etc).
    """

    DEFAULT_CSS = """
    ThoughtLineMarkdown {
        color: $text;
        padding: 0 1;
        margin: 0 0 0 0;
        height: auto;
        background: transparent;
        text-style: none;  /* NÃO itálico */
    }
    """

    def __init__(self, text: str) -> None:
        # Remove aspas se presentes
        clean_text = text.strip('"').strip("'")
        super().__init__(clean_text)

    def set_text(self, text: str) -> None:
        """Atualiza o texto markdown."""
        clean_text = text.strip('"').strip("'")
        self.update(clean_text)


__all__ = ["ThoughtLine", "ThoughtLineMarkdown"]
