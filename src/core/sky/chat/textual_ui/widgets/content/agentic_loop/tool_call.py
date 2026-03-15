# coding: utf-8
"""
ToolCallWidget - Widget que representa UMA chamada de ferramenta completa.

SimpleEntryWidget - Linha simples para thoughts e erros (não são tool calls).

Ciclo de vida:
  1. Criado no tool_start  → mostra "⚙ ToolName: param"   (cor primária)
  2. Atualizado no result  → mostra "✓ ToolName: param"   (cor muted)
                              └ resumo do resultado        (cor success, menor)

Todos os ToolCallWidgets ficam dentro de ThinkingPanel.
"""

from datetime import datetime

from textual.app import ComposeResult
from textual.widgets import Static


class ToolCallWidget(Static):
    """
    Widget que representa UMA chamada de ferramenta completa.

    Ciclo de vida:
      1. Criado no tool_start  → mostra "⚙ ToolName: param"   (cor primária)
      2. Atualizado no result  → mostra "✓ ToolName: param"   (cor muted)
                                  └ resumo do resultado        (cor success, menor)

    Todos os ToolCallWidgets ficam dentro de ThinkingPanel.
    """

    DEFAULT_CSS = """
    ToolCallWidget {
        height: auto;
        padding: 0 1;
        margin-bottom: 0;
    }

    ToolCallWidget #tool-header {
        color: $primary;
    }

    ToolCallWidget.done #tool-header {
        color: $text-muted;
    }

    ToolCallWidget #tool-result-line {
        color: $success;
        padding-left: 4;
        display: none;
        height: auto;
    }

    ToolCallWidget.done #tool-result-line {
        display: block;
    }

    ToolCallWidget #tool-ts {
        color: $text-disabled;
        text-style: none;
        padding-left: 4;
    }
    """

    def __init__(self, tool_name: str, param: str, timestamp: datetime) -> None:
        super().__init__()
        self._tool_name = tool_name
        self._param = param
        self._timestamp = timestamp
        self._result: str | None = None

    def compose(self) -> ComposeResult:
        ts = self._timestamp.strftime("%H:%M:%S")
        yield Static(f"⚙ {self._tool_name}: {self._param}", id="tool-header")
        yield Static("", id="tool-result-line")
        yield Static(ts, id="tool-ts")

    def set_result(self, result_summary: str) -> None:
        """
        Atualiza widget quando o resultado da tool chega.

        Chamado por ThinkingPanel.resolve_tool() quando
        um evento tool_result corresponde a este widget.
        """
        if self._result is not None:
            return  # Já foi resolvido
        self._result = result_summary
        self.add_class("done")
        try:
            self.query_one("#tool-header", Static).update(
                f"✓ {self._tool_name}: {self._param}"
            )
            self.query_one("#tool-result-line", Static).update(
                f"└ {result_summary}"
            )
        except Exception:
            pass

    @property
    def tool_name(self) -> str:
        return self._tool_name

    @property
    def is_resolved(self) -> bool:
        return self._result is not None


class SimpleEntryWidget(Static):
    """Linha simples para thoughts e erros."""

    DEFAULT_CSS = """
    SimpleEntryWidget {
        height: auto;
        padding: 0 1;
        margin-bottom: 0;
    }

    SimpleEntryWidget.thought {
        text-style: italic;
        color: $text-muted;
    }

    SimpleEntryWidget.error {
        text-style: bold;
        color: $error;
    }
    """

    ICONS = {"thought": "💭", "error": "❌"}

    def __init__(self, entry_type: str, content: str) -> None:
        icon = self.ICONS.get(entry_type, "•")
        super().__init__(f"{icon} {content}")
        self.set_class(True, entry_type)


__all__ = ["ToolCallWidget", "SimpleEntryWidget"]
