# coding: utf-8
"""
SkyBubble - Bubble para mensagem da Sky com suporte a Markdown e ActionBar.

SkyBubble usa Markdown widget para renderização rica de markdown.
ActionBar fornece botões Copy/Retry.

NOTA: WaveformTopBar foi movido para o ChatHeader (global).
"""

from typing import TYPE_CHECKING, Callable

from textual.app import ComposeResult
from textual.reactive import reactive
from textual.widget import Widget
from textual.widgets import Static, Markdown, Button

if TYPE_CHECKING:
    from core.sky.chat.textual_ui.widgets.content.agentic_loop.panel import AgenticLoopPanel


class SkyBubble(Widget):
    """Bubble para mensagem da Sky com suporte a Markdown."""

    content: reactive[str] = reactive("", layout=True)

    DEFAULT_CSS = """
    SkyBubble {
        padding: 1;
        height: auto;
        min-height: 1;
        background: $surface;
        /* border-left: thick $primary; */
    }
    SkyBubble > AgenticLoopPanel {
        margin-top: 1;
        margin-bottom: 0;
    }
    SkyBubble > Markdown {
        background: transparent;
        height: auto;
    }
    /* Estilos de markdown dentro do SkyBubble */
    SkyBubble Markdown {
        text-style: none;
    }
    /* Código inline */
    SkyBubble Markdown.--code {
        background: $panel;
        text-style: bold;
    }
    /* Blocos de código */
    SkyBubble Markdown.--code-block {
        background: $panel;
        border: solid $primary;
        padding: 0 1;
    }
    """

    def __init__(
        self,
        content: str,
        timestamp: str | None = None,
        show_actions: bool = False,
        on_retry: Callable[[], None] | None = None,
        agentic_panel: "AgenticLoopPanel | None" = None,
        parent_turn: "Widget | None" = None,
    ) -> None:
        super().__init__()
        self.timestamp = timestamp or ""
        self._show_actions = show_actions
        self._on_retry = on_retry
        self._agentic_panel = agentic_panel
        self._parent_turn = parent_turn  # Turn pai para disparar scroll
        # Atribuição após super().__init__() para acionar o reactive
        self.content = content

    def compose(self) -> ComposeResult:
        # AgenticLoopPanel (se existir)
        if self._agentic_panel:
            yield self._agentic_panel

        yield Markdown(self.content, id="sky-message")

    def watch_content(self, old_value: str, new_value: str) -> None:
        # Só tenta atualizar se o DOM já estiver montado
        try:
            markdown = self.query_one("#sky-message", Markdown)
            markdown.update(new_value)
            # Dispara scroll após atualização do Markdown
            if self._parent_turn is not None:
                try:
                    self._parent_turn.trigger_scroll()
                except Exception:
                    pass
        except Exception:
            # DOM ainda não está pronto - o valor inicial será usado no compose()
            pass

    def show_actions(self, on_retry: Callable[[], None] | None = None) -> None:
        """
        PRD-REACT-001: Mostra ActionBar com botões Copy/Retry.

        Args:
            on_retry: Callback para reenviar a mensagem.
        """
        self._show_actions = True
        self._on_retry = on_retry
        # Monta ActionBar se ainda não existe
        try:
            self.query_one(ActionBar)
        except Exception:
            self.mount(ActionBar(on_copy=None, on_retry=on_retry, retry_enabled=on_retry is not None))


class ActionBar(Widget):
    """
    Barra de ações com botões Copy e Retry.

    Aparece abaixo do SkyBubble quando a resposta está completa.
    """

    DEFAULT_CSS = """
    ActionBar {
        height: auto;
        margin: 0 0 1 0;
        padding: 0 0 0 1;
        background: transparent;
        layout: horizontal;
    }

    ActionBar Button {
        min-width: 10;
        height: 1;
        margin: 0 1 0 0;
        padding: 0 1;
    }

    ActionBar Button#copy-btn {
        background: $success;
        color: $background;
        border: none $success-darken-2;
    }

    ActionBar Button#retry-btn {
        background: $primary;
        color: $background;
        border: none $primary-darken-2;
    }

    ActionBar Button:disabled {
        background: $panel;
        color: $text-disabled;
    }

    ActionBar #feedback {
        text-style: italic;
        color: $success;
        padding: 1 1;
        display: none;
        height: 3;
    }

    ActionBar #feedback.visible {
        display: block;
    }
    """

    def __init__(
        self,
        on_copy: Callable[[], None] | None = None,
        on_retry: Callable[[], None] | None = None,
        retry_enabled: bool = True,
    ) -> None:
        super().__init__()
        self._on_copy = on_copy
        self._on_retry = on_retry
        self._retry_enabled = retry_enabled
        self._feedback_visible = False

    def compose(self) -> ComposeResult:
        yield Button("Copy", id="copy-btn", variant="success")
        yield Button("Retry", id="retry-btn", variant="primary")
        yield Static("", id="feedback")

    def on_mount(self) -> None:
        """Configura estado inicial após montagem."""
        if not self._retry_enabled:
            try:
                retry_btn = self.query_one("#retry-btn", Button)
                retry_btn.disabled = True
            except Exception:
                pass

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Trata clique nos botões."""
        if event.button.id == "copy-btn":
            self._handle_copy()
        elif event.button.id == "retry-btn":
            self._handle_retry()

    def _handle_copy(self) -> None:
        """Executa a ação de Copy."""
        try:
            import pyperclip

            # Tenta obter o conteúdo do SkyBubble pai
            content = self._get_skybubble_content()
            if content:
                pyperclip.copy(content)
                self._show_feedback("✓ Copiado!")
            else:
                self._show_feedback("Nada para copiar")
        except Exception as e:
            self._show_feedback("Erro ao copiar")

    def _handle_retry(self) -> None:
        """Executa a ação de Retry."""
        if self._on_retry:
            self._on_retry()

    def _get_skybubble_content(self) -> str | None:
        """Obtém o conteúdo do SkyBubble pai."""
        try:
            # Busca o SkyBubble pai (irmão anterior na árvore DOM)
            parent = self.parent
            if parent:
                # Busca SkyBubble entre os filhos do parent
                children = parent.children
                for child in children:
                    if isinstance(child, SkyBubble):
                        return child.content
        except Exception:
            pass
        return None

    def _show_feedback(self, message: str) -> None:
        """Mostra feedback visual por 2 segundos."""
        try:
            feedback = self.query_one("#feedback", Static)
            feedback.update(message)
            feedback.add_class("visible")
            self._feedback_visible = True

            # Agenda remoção do feedback
            import asyncio

            async def hide_feedback():
                await asyncio.sleep(2)
                feedback.remove_class("visible")
                feedback.update("")
                self._feedback_visible = False

            asyncio.create_task(hide_feedback())
        except Exception:
            pass

    def set_retry_enabled(self, enabled: bool) -> None:
        """Habilita ou desabilita o botão Retry."""
        self._retry_enabled = enabled
        try:
            retry_btn = self.query_one("#retry-btn", Button)
            retry_btn.disabled = not enabled
        except Exception:
            pass


__all__ = ["SkyBubble", "ActionBar"]
