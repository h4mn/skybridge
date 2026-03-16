# coding: utf-8
"""
ToastNotification - Widget para notificações temporárias.

Exibe notificações no canto superior direito da tela,
com auto-descarte após 5 segundos.
"""

import asyncio
from textual.widgets import Static
from textual.timer import Timer
from textual import on


class ToastNotification(Static):
    """
    Notificação toast temporária.

    Aparece no canto superior direito e desaparece após 5 segundos.
    Pode ser dispensada com ESC.
    """

    DEFAULT_CSS = """
    ToastNotification {
        dock: top right;
        background: $panel;
        border: round $warning;
        margin: 1;
        padding: 1;
        width: 40;
        text-align: center;
    }

    ToastNotification.success {
        border: round $success;
    }

    ToastNotification.error {
        border: round $error;
        color: red;
    }

    ToastNotification.info {
        border: round $primary;
    }
    """

    def __init__(
        self,
        message: str,
        toast_type: str = "info",
        duration: float = 5.0,
    ) -> None:
        """
        Inicializa ToastNotification.

        Args:
            message: Mensagem a exibir.
            toast_type: Tipo do toast ("info", "success", "error").
            duration: Duração em segundos (padrão: 5.0).
        """
        super().__init__(message)
        self.toast_type = toast_type
        self.duration = duration
        self._timer: Timer | None = None

    def on_mount(self) -> None:
        """Ao montar, inicia o timer para auto-descarte."""
        self.set_class(True, self.toast_type)
        self._start_dismiss_timer()

    def _start_dismiss_timer(self) -> None:
        """Inicia o timer para auto-descartar o toast."""
        async def _dismiss():
            await asyncio.sleep(self.duration)
            if self.is_mounted:
                self.remove()

        self._timer = self.set_timer(self.duration, lambda: self.app.call_from_thread(self.remove))

    def dismiss(self) -> None:
        """Descarta o toast imediatamente."""
        if self._timer:
            self._timer.stop()
        self.remove()


__all__ = ["ToastNotification"]
