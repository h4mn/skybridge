# coding: utf-8
"""
ConfigScreen - Tela de configurações.

Permite ajustar opções como RAG, verbose, modelo, etc.
"""

import os
from textual.app import ComposeResult
from textual.containers import Horizontal
from textual.screen import Screen
from textual.widgets import (
    Header,
    Footer,
    Switch,
    Label,
    Button,
    Static,
)


class ConfigScreen(Screen):
    """Screen de configurações."""

    DEFAULT_CSS = """
    ConfigScreen {
        layout: vertical;
    }
    .config-row {
        height: 3;
        margin: 1 2;
    }
    .config-label {
        width: 30;
        text-align: left;
    }
    .config-value {
        width: 20;
    }
    .info-text {
        margin: 2 2;
        text-style: italic;
        color: $text-muted;
    }
    """

    BINDINGS = [
        ("esc", "pop_screen", "Voltar"),
        ("s", "save_and_exit", "Salvar"),
    ]

    def compose(self) -> ComposeResult:
        """Compôe a tela de configurações."""
        yield Header()

        yield Static("⚙️ Configurações", classes="header")

        # RAG Toggle
        yield Horizontal(
            Label("RAG (Busca Semântica)", classes="config-label"),
            Switch(
                value=os.getenv("RAG_ENABLED", "true").lower() == "true",
                id="rag-switch",
            ),
            classes="config-row",
        )

        # Verbose Toggle
        yield Horizontal(
            Label("Verbose (Logs detalhados)", classes="config-label"),
            Switch(
                value=os.getenv("VERBOSE", "false").lower() == "true",
                id="verbose-switch",
            ),
            classes="config-row",
        )

        # Model info (read-only)
        yield Static(
            f"Modelo: {os.getenv('CLAUDE_MODEL', 'glm-4.7')}",
            classes="info-text",
        )

        # API Key status
        api_key = os.getenv("ANTHROPIC_AUTH_TOKEN", "")
        api_status = "✅ Configurada" if api_key else "❌ Não configurada"
        yield Static(
            f"API Key: {api_status}",
            classes="info-text",
        )

        yield Footer()

    def action_save_and_exit(self) -> None:
        """Salva configurações e volta para o chat."""
        # Atualmente as configs são apenas variáveis de ambiente
        # TODO: Implementar persistência de configurações
        self.app.pop_screen()


__all__ = ["ConfigScreen"]
