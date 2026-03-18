# coding: utf-8
"""
DevToolsScreen - Interface de inspeção do SkyTextualDOM.

Screen com 3 painéis:
- Tree: Hierarquia de widgets navegável
- State: Estado detalhado do widget selecionado
- Events: Timeline de eventos recentes
"""

from textual.app import ComposeResult
from textual.containers import Horizontal, Vertical
from textual.screen import Screen
from textual.widgets import Footer, Header, Static

from core.sky.chat.textual_ui.dom import SkyTextualDOM


class DevToolsScreen(Screen):
    """
    Screen de DevTools para inspeção do SkyTextualDOM.

    Acessível via Ctrl+D em qualquer parte da aplicação.
    """

    BINDINGS = [
        ("escape", "app.pop_screen", "Fechar"),
        ("ctrl+p", "toggle_pause", "Pausar/Retomar"),
        ("ctrl+r", "reset_layout", "Reset Layout"),
    ]

    DEFAULT_CSS = """
    DevToolsScreen {
        layout: vertical;
    }

    DevToolsScreen > Header {
        height: 3;
    }

    DevToolsScreen > Horizontal {
        height: 1fr;
    }

    #tree-panel {
        width: 33;
        border-right: solid $panel;
    }

    #state-panel {
        width: 1fr;
        border-right: solid $panel;
    }

    #events-panel {
        width: 1fr;
    }

    .panel-header {
        height: 1;
        background: $panel;
        text-style: bold;
        content-align: center middle;
    }
    """

    def __init__(self):
        super().__init__()
        self._paused = False

    def compose(self) -> ComposeResult:
        """Compõe a screen com 3 painéis."""
        yield Header("🔧 Sky DevTools (Ctrl+D para fechar)")

        with Horizontal():
            with Vertical(id="tree-panel"):
                yield Static("📺 Tree", classes="panel-header")
                yield Static(id="tree-content")

            with Vertical(id="state-panel"):
                yield Static("📊 State", classes="panel-header")
                yield Static(id="state-content")

            with Vertical(id="events-panel"):
                yield Static("📋 Events", classes="panel-header")
                yield Static(id="events-content")

        yield Footer()

    def on_mount(self) -> None:
        """Ao montar, inicia timer de refresh."""
        self._refresh_panels()
        self.set_interval(0.1, self._refresh_if_not_paused)

    def _refresh_if_not_paused(self) -> None:
        """Refresh dos painéis se não está pausado."""
        if not self._paused:
            self._refresh_panels()

    def _refresh_panels(self) -> None:
        """Atualiza todos os painéis."""
        dom = SkyTextualDOM()

        # Tree panel
        tree_content = self.query_one("#tree-content", Static)
        tree_content.update(dom.tree())

        # State panel - placeholder
        state_content = self.query_one("#state-content", Static)
        state_content.update("(Selecione um widget para ver estado)")

        # Events panel
        events_content = self.query_one("#events-content", Static)
        events = dom.tracer.get_events()[:10]  # Últimos 10
        if events:
            lines = []
            for event in events:
                lines.append(f"[{event.timestamp.strftime('%H:%M:%S')}] {event.event_type.value}")
                if event.widget_dom_id:
                    lines.append(f"  └─ {event.widget_dom_id}")
            events_content.update("\n".join(lines))
        else:
            events_content.update("(Nenhum evento)")

    def action_toggle_pause(self) -> None:
        """Pausa/Retoma atualizações."""
        self._paused = not self._paused

    def action_reset_layout(self) -> None:
        """Reseta layout para padrão."""
        self._paused = False


__all__ = ["DevToolsScreen"]
