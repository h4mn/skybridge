# coding: utf-8
"""
OverlayContainer - Container que tenta simular overlay no Textual.

O Textual não suporta position: absolute, então tentamos alternativas:
1. Usar dock: bottom com layer: overlay
2. Se ainda empurrar widgets, usamos height fixo menor

NOTA: Esta é uma "best effort" solução - o Textual tem limitações de layout.
"""

from textual.containers import Vertical, VerticalScroll
from textual.widgets import Static


class OverlayContainer(VerticalScroll):
    """
    Container que tenta funcionar como overlay sobre o conteúdo.

    Usa dock: bottom + layer: overlay para tentar sobreposição
    sem empurrar widgets. Se ainda assim empurrar, o usuário
    pode ajustar a altura.
    """

    DEFAULT_CSS = """
    OverlayContainer {
        height: 20;
        width: 100%;
        dock: bottom;
        display: none;
        background: $panel;
        border-top: thick $primary;
        layer: overlay;
    }

    OverlayContainer.visible {
        display: block;
    }

    OverlayContainer Static {
        width: 100%;
        padding: 0 1;
    }
    """

    def __init__(self) -> None:
        super().__init__()
        self._visible: bool = False

    def show(self) -> None:
        """Mostra o overlay."""
        self._visible = True
        self.add_class("visible")

    def hide(self) -> None:
        """Esconde o overlay."""
        self._visible = False
        self.remove_class("visible")

    def toggle(self) -> None:
        """Toggle visibilidade."""
        if self._visible:
            self.hide()
        else:
            self.show()

    @property
    def is_visible(self) -> bool:
        """Retorna se está visível."""
        return self._visible


__all__ = ["OverlayContainer"]
