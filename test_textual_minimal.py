# coding: utf-8
"""
Teste simples da UI Textual - versão mínima para debug.
"""

import os
import sys

# Adiciona src ao path
sys.path.insert(0, "src")

# Configura ambiente
os.environ["USE_TEXTUAL_UI"] = "true"
os.environ["USE_CLAUDE_CHAT"] = "true"

from textual.app import ComposeResult
from textual.containers import Vertical
from textual.screen import Screen
from textual.widgets import Footer, Input, Static
from textual.scroll_view import ScrollView


class MinimalChatScreen(Screen):
    """Screen mínima para debug."""

    def compose(self) -> ComposeResult:
        """Compõe tela mínima."""
        yield Vertical(
            Static("🔵 HEADER - Título", id="header-text"),
            ScrollView(id="messages-scroll"),
            id="content-area",
        )
        yield Footer()

    def on_mount(self) -> None:
        """Ao montar, adiciona widget inicial."""
        print("[DEBUG] MinimalChatScreen.on_mount() chamado")

        # Tenta adicionar widget ao ScrollView
        try:
            scroll = self.query_one("#messages-scroll")
            test_widget = Static("👋 Olá! Esta é a ChatScreen mínima.")
            scroll.mount(test_widget)
            print("[DEBUG] Widget inicial montado com sucesso")
        except Exception as e:
            print(f"[DEBUG] Erro: {e}")
            import traceback
            traceback.print_exc()

    def on_input_submitted(self, event: Input.Submitted) -> None:
        """Usuário enviou mensagem."""
        print(f"[DEBUG] Mensagem recebida: {event.value}")

        try:
            scroll = self.query_one("#messages-scroll")
            bubble = Static(f"Você disse: {event.value}")
            scroll.mount(bubble)
            scroll.scroll_end()
            print("[DEBUG] Bubble montado")
        except Exception as e:
            print(f"[DEBUG] Erro ao montar bubble: {e}")
            import traceback
            traceback.print_exc()


if __name__ == "__main__":
    from textual.app import App

    class MinimalApp(App):
        """App mínima."""

        def on_mount(self) -> None:
            print("[DEBUG] MinimalApp.on_mount() chamado")
            self.push_screen(MinimalChatScreen())

    print("[DEBUG] Iniciando MinimalApp...")
    app = MinimalApp()
    app.run()
