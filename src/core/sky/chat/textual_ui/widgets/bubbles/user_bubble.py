# coding: utf-8
"""
UserBubble - Bubble para mensagem do usuário com texto simples.

UserBubble usa Static para texto plano do usuário.
"""

from textual.reactive import reactive
from textual.widget import Widget
from textual.widgets import Static


class UserBubble(Widget):
    """Bubble para mensagem do usuário."""

    DEFAULT_CSS = """
    UserBubble {
        margin: 0;
        padding: 1;
        height: auto;
        min-height: 1;
        background: $panel;
        border-right: thick $accent;
    }
    #user-message {
        text-style: bold;
        text-align: right;
    }
    """

    def __init__(self, content: str, timestamp: str | None = None) -> None:
        super().__init__()
        self.content = content
        self.timestamp = timestamp or ""

    def compose(self) -> None:
        yield Static(self.content, id="user-message")

    def watch_content(self, old_value: str, new_value: str) -> None:
        # Só tenta atualizar se o DOM já estiver montado
        try:
            static = self.query_one("#user-message", Static)
            static.update(new_value)
        except Exception:
            # DOM ainda não está pronto - o valor inicial será usado no compose()
            pass


__all__ = ["UserBubble"]
