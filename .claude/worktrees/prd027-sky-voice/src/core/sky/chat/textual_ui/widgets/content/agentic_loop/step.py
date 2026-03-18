# coding: utf-8
"""
StepWidget - Widget que representa um Step completo do loop ReAct.

Um Step consiste de:
  - ThoughtLine (opcional): texto de intenção antes da ação
  - ActionLine (obrigatório): execução da ferramenta com estado

Ciclo de vida:
  1. Nasce com Thought (se houver) → ThoughtLine aparece
  2. tool_start chega → ActionLine criada em estado pending (⚙)
  3. tool_result chega → ActionLine transita para done (✓)
  4. timeout sem resultado → ActionLine transita para timeout (⚠)
"""

from textual.app import ComposeResult
from textual.widgets import Static


class StepWidget(Static):
    """
    Widget que representa um Step completo do loop ReAct.

    Um Step consiste de:
      - ThoughtLine (opcional): texto de intenção antes da ação
      - ActionLine (obrigatório): execução da ferramenta com estado

    Ciclo de vida:
      1. Nasce com Thought (se houver) → ThoughtLine aparece
      2. tool_start chega → ActionLine criada em estado pending (⚙)
      3. tool_result chega → ActionLine transita para done (✓)
      4. timeout sem resultado → ActionLine transita para timeout (⚠)
    """

    _TAMANHO_LIMITE_THOUGHT = 160  # caracteres para decidir ThoughtLine vs ThoughtLineMarkdown

    DEFAULT_CSS = """
    StepWidget {
        height: auto;
        padding: 0;
        margin-bottom: 1;
    }

    StepWidget ThoughtLine {
        margin-bottom: 0;
    }

    StepWidget ActionLine {
        margin-top: 0;
    }
    """

    def __init__(self, thought: str | None = None) -> None:
        super().__init__()
        self._thought = thought
        self._action_line: ActionLine | None = None
        self._action_tool_name: str | None = None
        self._action_param: str | None = None

    def compose(self) -> ComposeResult:
        """
        Monta o Step com ThoughtLine ou ThoughtLineMarkdown.

        Textos > 80 caracteres → Markdown (informação estruturada)
        Textos <= 80 caracteres → ThoughtLine itálico (raciocínio simples)
        """
        from core.sky.chat.textual_ui.widgets.content.agentic_loop.thought import ThoughtLine, ThoughtLineMarkdown

        if self._thought:
            # Texto > 80 caracteres → Markdown (informação estruturada)
            # Texto <= 80 caracteres → ThoughtLine itálico (raciocínio simples)
            if len(self._thought) > self._TAMANHO_LIMITE_THOUGHT:
                yield ThoughtLineMarkdown(self._thought)
            else:
                yield ThoughtLine(self._thought)

    def set_action(self, tool_name: str, param: str) -> None:
        """
        Define a ação (tool_start) do Step.

        Cria e monta a ActionLine com prefixo ⎿.

        Args:
            tool_name: Nome da ferramenta.
            param: Parâmetro principal da ferramenta.
        """
        from core.sky.chat.textual_ui.widgets.content.agentic_loop.action import ActionLine

        self._action_tool_name = tool_name
        self._action_param = param

        # Cria e monta a ActionLine (já tem ⎿ embutido)
        self._action_line = ActionLine(tool_name, param)
        self.mount(self._action_line)

    def set_result(
        self,
        result_summary: str,
        full_output: str = "",
        exit_code: int | None = None,
        command: str = "",
    ) -> None:
        """
        Resolve o Step com o resultado da ferramenta.

        Para Bash: monta BashResultWidget com output completo.
        Para outras tools: atualiza texto da ActionLine.

        Args:
            result_summary: Resumo curto para a ActionLine.
            full_output:    Output completo (Bash).
            exit_code:      Código de saída (Bash).
            command:        Comando executado (Bash).
        """
        from core.sky.chat.textual_ui.widgets.content.agentic_loop.diff import BashResultWidget

        if self._action_line:
            self._action_line.set_result(result_summary)

        # Qualquer tool com output: monta widget colapsável
        # O critério é ter output — não importa qual ferramenta
        # call_after_refresh garante execução no thread correto da UI
        if full_output:
            display_command = command or self._action_param or ""
            widget = BashResultWidget(
                output=full_output,
                exit_code=exit_code,
                command=display_command,
            )
            # mount() precisa rodar no event loop da UI.
            # set_result() é síncrono — call_after_refresh agenda para o próximo tick.
            self.call_after_refresh(lambda w=widget: self.mount(w))

    def set_diff(self, old: str, new: str, file_path: str = "") -> None:
        """
        Monta um DiffWidget colapsável embaixo da ActionLine.

        Chamado quando a tool é Edit/Write e temos old_string + new_string.
        O diff fica colapsado por padrão — usuário expande se quiser ver.

        Args:
            old: Conteúdo original (old_string do Edit).
            new: Conteúdo novo (new_string do Edit).
            file_path: Caminho do arquivo para o título do diff.
        """
        from core.sky.chat.textual_ui.widgets.content.agentic_loop.diff import DiffWidget

        diff = DiffWidget(old, new, file_path)
        self.mount(diff)

    def set_timeout(self) -> None:
        """Marca o Step como timeout (sem resultado)."""
        if self._action_line:
            self._action_line.set_timeout()

    @property
    def is_resolved(self) -> bool:
        """Retorna True se o Step já foi resolvido."""
        return self._action_line is not None and self._action_line.is_resolved

    @property
    def has_thought(self) -> bool:
        """Retorna True se o Step tem texto de pensamento."""
        return self._thought is not None


__all__ = ["StepWidget"]
