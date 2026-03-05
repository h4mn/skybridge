# coding: utf-8
"""
ToolFeedback - Feedback visual de execução de ferramentas.

Exibe indicador quando tools são executadas durante
a geração de resposta, com status (executando, sucesso, falha).
"""

from dataclasses import dataclass
from enum import Enum

from textual.containers import Horizontal
from textual.widgets import Static


class ToolStatus(Enum):
    """Status de execução de uma tool."""
    PENDING = "pending"
    RUNNING = "running"
    SUCCESS = "success"
    FAILED = "failed"


@dataclass
class ToolInfo:
    """Informações sobre uma tool executada."""
    name: str
    status: ToolStatus
    result: str = ""


class ToolFeedback(Horizontal):
    """
    Componente para exibir feedback de tools executadas.

    Lista widgets indicando o status de cada tool.
    """

    DEFAULT_CSS = """
    ToolFeedback {
        margin: 1 2;
        padding: 1;
    }
    ToolTool {
        margin: 0 1;
    }
    """

    def __init__(self) -> None:
        """Inicializa ToolFeedback."""
        super().__init__()
        self._tools: dict[str, ToolInfo] = {}

    def add_tool(self, name: str) -> None:
        """
        Adiciona uma tool ao feedback.

        Args:
            name: Nome da tool.
        """
        self._tools[name] = ToolInfo(name=name, status=ToolStatus.RUNNING)
        self._refresh()

    def update_tool(self, name: str, status: ToolStatus, result: str = "") -> None:
        """
        Atualiza o status de uma tool.

        Args:
            name: Nome da tool.
            status: Novo status.
            result: Resultado (para sucesso/falha).
        """
        if name in self._tools:
            self._tools[name].status = status
            self._tools[name].result = result
            self._refresh()

            # Se falhou, emite evento para notificar via Toast
            if status == ToolStatus.FAILED:
                self._emit_failure_notification(name, result)

    def _emit_failure_notification(self, tool_name: str, error: str) -> None:
        """
        Emite notificação de falha da tool.

        Args:
            tool_name: Nome da tool que falhou.
            error: Mensagem de erro.
        """
        # Obtém a screen atual para montar o Toast
        from core.sky.chat.textual_ui.widgets.toast import ToastNotification

        app = self.app
        if app and app.screen:
            # Monta Toast de falha
            error_msg = f"❌ Tool {tool_name} falhou"
            if error:
                error_msg += f": {error[:50]}..."
            app.screen.mount(ToastNotification(error_msg, toast_type="error"))

    def clear(self) -> None:
        """Limpa todas as tools."""
        self._tools.clear()
        self._refresh()

    def _refresh(self) -> None:
        """Re-renderiza o componente."""
        self.remove_children()
        for tool in self._tools.values():
            icon = self._get_icon(tool.status)
            self.mount(Static(f"{icon} {tool.name}"))

    def _get_icon(self, status: ToolStatus) -> str:
        """Retorna o ícone baseado no status."""
        return {
            ToolStatus.PENDING: "⏳",
            ToolStatus.RUNNING: "⏳",
            ToolStatus.SUCCESS: "✅",
            ToolStatus.FAILED: "❌",
        }.get(status, "⏳")


__all__ = ["ToolFeedback", "ToolStatus", "ToolInfo"]
