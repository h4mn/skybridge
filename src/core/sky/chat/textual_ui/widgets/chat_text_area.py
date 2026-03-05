# coding: utf-8
"""
ChatTextArea - TextArea customizado com comportamento de chat.

Enter envia mensagem, Shift+Enter nova linha, Escape limpa texto.
Idêntico à POC app.py - class ChatTextArea.
"""

from textual import events
from textual.keys import Keys
from textual.widgets import TextArea


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


__all__ = ["ChatTextArea"]
