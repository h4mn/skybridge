# coding: utf-8
"""
Textual TUI para chat com a Sky.

Interface moderna baseada em Textual framework com:
- Header fixo com título animado e métricas
- Footer com input field
- Message bubbles estilizados via CSS
- Workers assíncronos para operações pesadas
"""

from textual.app import App

from core.sky.chat.textual_ui.screens.welcome import WelcomeScreen
from core.sky.chat.textual_ui.screens.main import MainScreen

# DevTools - importado sob demanda para não afetar performance
# Use: from core.sky.chat.textual_ui.dom import SkyTextualDOM


class SkyApp(App):
    """
    Aplicação Textual para chat com a Sky.

    Inicia com WelcomeScreen e transita para MainScreen
    ao enviar a primeira mensagem.

    Idêntico à PoC PocApp - CSS_PATH relativo ao módulo.
    """

    TITLE = "Sky Chat"
    CSS_PATH = "app.tcss"

    BINDINGS = [
        ("^q", "quit", "Quit"),
        ("^d", "toggle_dark", "Toggle dark"),
    ]

    def on_mount(self) -> None:
        """Inicializa a aplicação com a WelcomeScreen."""
        self.push_screen(WelcomeScreen())


__all__ = ["SkyApp"]
