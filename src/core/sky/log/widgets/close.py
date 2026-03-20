# coding: utf-8
"""
LogClose - Botão para limpar/limpar filtros.
"""

from textual.message import Message
from textual.widgets import Button


class ClearAll(Message):
    """Mensagem emitida quando todos os filtros devem ser limpos."""

    bubble = True


class LogClose(Button):
    """Botão para limpar filtros."""

    DEFAULT_CSS = """
    LogClose {
        width: 5;
        min-width: 5;
    }
    """

    def __init__(self, **kwargs) -> None:
        """Inicializa widget."""
        super().__init__(label="X", id="close-button", **kwargs)

    def on_press(self) -> None:
        """Handle botão pressionado - limpa tudo."""
        # DEBUG
        print(f"[DEBUG] LogClose.on_press chamado, app={self.app}")

        # Emite evento centralizado de limpar tudo
        self.post_message(ClearAll())
        print(f"[DEBUG] ClearAll() emitido")


__all__ = ["LogClose"]
