# coding: utf-8
"""
ActionLine - Linha de ação (Action) do StepWidget.

Sempre com prefixo ⎿ para indicar continuação do pensamento.

Ciclo de vida:
  1. Pendente → "⎿ ToolName: param" (azul)
  2. Resolvido → "⎿ ToolName: param  └ N linhas" (muted)
  3. Timeout   → "⎿ ToolName: param  (sem resultado)" (warning)
"""

from textual.widgets import Static


class ActionLine(Static):
    """
    Linha de ação (Action) do StepWidget.

    Sempre com prefixo ⎿ para indicar continuação do pensamento.

    Ciclo de vida:
      1. Pendente → "⎿ ToolName: param" (azul)
      2. Resolvido → "⎿ ToolName: param  └ N linhas" (muted)
      3. Timeout   → "⎿ ToolName: param  (sem resultado)" (warning)
    """

    DEFAULT_CSS = """
    ActionLine {
        padding: 0 1;
        margin: 0 0 0 0;
        height: auto;
    }

    ActionLine.pending {
        color: $text-muted;
    }

    ActionLine.done {
        color: $text-disabled;
    }

    ActionLine.timeout {
        color: $warning;
    }
    """

    def __init__(self, tool_name: str, param: str) -> None:
        super().__init__()
        self._tool_name = tool_name
        self._param = param
        self._result_summary: str | None = None
        self._state = "pending"  # pending, done, timeout
        self.add_class("pending")
        self.update(f"⎿ {tool_name}: {param}")

    def set_result(self, result_summary: str) -> None:
        """
        Marca a ação como resolvida com resultado.

        Args:
            result_summary: Resumo do resultado (ex: "52 linhas").
        """
        if self._state != "pending":
            return
        self._result_summary = result_summary
        self._state = "done"
        self.remove_class("pending")
        self.add_class("done")
        self.update(f"⎿ {self._tool_name}: {self._param}  └ {result_summary}")

    def set_timeout(self) -> None:
        """
        Marca a ação como timeout (sem resultado recebido).

        Usado para Steps sem ToolResultMessage (glm-4.7).
        """
        if self._state != "pending":
            return
        self._state = "timeout"
        self.remove_class("pending")
        self.add_class("timeout")
        self.update(f"⎿ {self._tool_name}: {self._param}  (sem resultado)")

    @property
    def is_resolved(self) -> bool:
        """Retorna True se a ação já foi resolvida ou timeout."""
        return self._state in ("done", "timeout")

    @property
    def tool_name(self) -> str:
        return self._tool_name


__all__ = ["ActionLine"]
