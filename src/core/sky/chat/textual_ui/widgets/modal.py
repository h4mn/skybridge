# coding: utf-8
"""
ConfirmModal - Modal genérico para confirmações.

Modal que exibe uma mensagem e pede confirmação do usuário
através de botões ou teclas de atalho.
"""

from textual.app import ComposeResult
from textual.containers import Center, Horizontal, Vertical
from textual.screen import ModalScreen
from textual.widgets import Button, Label, Static


class ConfirmModal(ModalScreen):
    """
    Modal genérico para confirmações.

    Exibe uma mensagem centralizada com botões de confirmação
    e cancelamento. Suporta atalhos de teclado.
    """

    DEFAULT_CSS = """
    ConfirmModal {
        align: center middle;
    }

    ConfirmModal > Vertical {
        background: $panel;
        border: thick $primary;
        padding: 2 4;
        width: 60;
        height: auto;
    }

    #modal-message {
        text-align: center;
        margin: 1 0;
        text-style: bold;
    }

    #modal-detail {
        text-align: center;
        margin: 1 0;
        text-style: dim;
    }

    #modal-buttons {
        align: center middle;
        margin: 2 0;
    }

    Button {
        margin: 0 1;
        min-width: 12;
    }

    #confirm-btn {
        background: $success;
    }

    #cancel-btn {
        background: $error;
    }
    """

    BINDINGS = [
        ("s", "confirm", "Confirmar"),
        ("y", "confirm", "Confirmar"),
        ("enter", "confirm", "Confirmar"),
        ("n", "app.pop_screen", "Cancelar"),
        ("escape", "app.pop_screen", "Cancelar"),
    ]

    def __init__(
        self,
        message: str,
        detail: str | None = None,
        confirm_label: str = "Confirmar",
        cancel_label: str = "Cancelar",
    ) -> None:
        """
        Inicializa ConfirmModal.

        Args:
            message: Mensagem principal do modal.
            detail: Detalhes adicionais (opcional).
            confirm_label: Texto do botão de confirmar.
            cancel_label: Texto do botão de cancelar.
        """
        super().__init__()
        self.message = message
        self.detail = detail
        self.confirm_label = confirm_label
        self.cancel_label = cancel_label
        self.confirmed = False

    def compose(self) -> ComposeResult:
        """Compõe o modal."""
        with Vertical():
            yield Label(self.message, id="modal-message")
            if self.detail:
                yield Label(self.detail, id="modal-detail")
            with Horizontal(id="modal-buttons"):
                yield Button(self.confirm_label, id="confirm-btn", variant="success")
                yield Button(self.cancel_label, id="cancel-btn", variant="error")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """
        Botão foi pressionado.

        Args:
            event: Evento do botão.
        """
        if event.button.id == "confirm-btn":
            self.action_confirm()
        else:
            self.app.pop_screen()

    def action_confirm(self) -> None:
        """Ação de confirmar (pode ser sobreescrito)."""
        self.confirmed = True
        # Dispara evento de confirmação
        self.dismiss(result=True)


__all__ = ["ConfirmModal"]
