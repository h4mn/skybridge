# coding: utf-8
"""
ThinkingIndicator e ThinkingPanel - UI de raciocínio da Sky.

Arquitetura profissional (padrão Claude.ai / Cursor):

  ThinkingIndicator  — spinner simples "pensando..." antes de qualquer tool
  ToolCallWidget     — linha pareada tool_start → tool_result (atualiza in-place)
  ThinkingPanel      — Collapsible com ToolCallWidgets; auto-colapsa ao responder
"""

from __future__ import annotations

import time
from datetime import datetime
from typing import TYPE_CHECKING

from textual.app import ComposeResult
from textual.containers import Container
from textual.reactive import reactive
from textual.widgets import Collapsible, Static, Label, Markdown

if TYPE_CHECKING:
    from core.sky.chat.textual_ui.widgets.content.turn import ThinkingEntry


# ---------------------------------------------------------------------------
# ThinkingIndicator — spinner antes das tools aparecerem
# ---------------------------------------------------------------------------

class ThinkingIndicator(Static):
    """
    Indicador de thinking animado.

    Visível apenas entre o envio da mensagem e o primeiro evento do SDK.
    Assim que tools ou texto chegam, some automaticamente.
    """

    DEFAULT_CSS = """
    ThinkingIndicator {
        text-style: italic;
        color: $warning;
        /* margin: 0 2 1 2; */
        height: 1;
    }
    """

    def __init__(self, message: str = "🤔 pensando...") -> None:
        super().__init__(message)
        self._animating = False
        self.display = False

    def show(self, message: str | None = None) -> None:
        if message:
            self.update(message)
        self.display = True
        self._animating = True

    def hide(self) -> None:
        self.display = False
        self._animating = False


# ---------------------------------------------------------------------------
# ToolCallWidget — linha única que pareia tool_start com tool_result
# ---------------------------------------------------------------------------

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


# ---------------------------------------------------------------------------
# SimpleEntryWidget — para thought / error (não são tool calls)
# ---------------------------------------------------------------------------

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


# ---------------------------------------------------------------------------
# ThinkingPanel — container principal do raciocínio
# ---------------------------------------------------------------------------

class ThinkingPanel(Collapsible):
    """
    Painel colapsável de raciocínio — padrão profissional.

    Comportamento:
    - Expandido durante o processamento
    - Auto-colapsa quando a resposta começa a chegar (append_response)
    - Título dinâmico: "🧠 Raciocínio · N ações"
    - ToolCallWidgets são resolvidos in-place (sem duplicar linhas)
    """

    DEFAULT_CSS = """
    ThinkingPanel {
        margin: 1 2 0 2;
        border: round $primary-darken-3;
        background: $panel-darken-1;
        height: auto;
    }

    ThinkingPanel.collapsed {
        border: round $panel-lighten-1;
    }

    ThinkingPanel > CollapsibleTitle {
        text-style: bold;
        color: $primary;
        padding: 0 1;
        background: $panel-darken-1;
    }

    ThinkingPanel.collapsed > CollapsibleTitle {
        color: $text-muted;
        text-style: none;
        background: transparent;
    }

    ThinkingPanel #entries-container {
        height: auto;
        max-height: 20;
        overflow-y: auto;
        padding: 0 0 1 0;
    }
    """

    def __init__(self) -> None:
        super().__init__(title="🧠 Raciocínio", collapsed=False)
        # Lista de tool widgets para resolução por nome
        self._tool_widgets: list[ToolCallWidget] = []
        self._action_count: int = 0

    def compose(self) -> ComposeResult:
        yield Container(id="entries-container")

    # ------------------------------------------------------------------
    # API pública
    # ------------------------------------------------------------------

    async def add_tool_call(self, tool_name: str, param: str, timestamp: datetime) -> ToolCallWidget:
        """
        Adiciona um ToolCallWidget pendente (tool_start).

        Retorna o widget para referência futura.
        """
        widget = ToolCallWidget(tool_name, param, timestamp)
        self._tool_widgets.append(widget)
        self._action_count += 1
        self._update_title()

        try:
            container = self.query_one("#entries-container", Container)
            await container.mount(widget)
            container.scroll_end()
        except Exception:
            pass

        return widget

    def resolve_tool(self, tool_name: str, result_summary: str) -> bool:
        """
        Resolve o último ToolCallWidget pendente com este nome.

        Chamado quando tool_result chega. Retorna True se encontrou.
        """
        for widget in reversed(self._tool_widgets):
            if widget.tool_name == tool_name and not widget.is_resolved:
                widget.set_result(result_summary)
                return True
        # Fallback: resolve qualquer pendente com esse nome
        for widget in reversed(self._tool_widgets):
            if widget.tool_name == tool_name:
                widget.set_result(result_summary)
                return True
        return False

    async def add_simple_entry(self, entry_type: str, content: str) -> None:
        """Adiciona thought ou error (linha simples, sem pareamento)."""
        widget = SimpleEntryWidget(entry_type, content)
        self._action_count += 1
        self._update_title()
        try:
            container = self.query_one("#entries-container", Container)
            await container.mount(widget)
            container.scroll_end()
        except Exception:
            pass

    def collapse_done(self, action_count: int | None = None) -> None:
        """
        Colapsa o painel quando a resposta chega.

        Atualiza o título com o total de ações realizadas.
        """
        if action_count is not None:
            self._action_count = action_count
        self._update_title()
        self.collapsed = True

    # ------------------------------------------------------------------
    # Interno
    # ------------------------------------------------------------------

    def _update_title(self) -> None:
        """Atualiza o título do Collapsible com o contador de ações."""
        n = self._action_count
        label = "ação" if n == 1 else "ações"
        try:
            # Textual não expõe setter fácil de title — usa o atributo interno
            self.title = f"🧠 Raciocínio · {n} {label}"
        except Exception:
            pass

    @property
    def action_count(self) -> int:
        return self._action_count


# ---------------------------------------------------------------------------
# DiffWidget — visualização colorida de diffs (estilo Claude Code)
# ---------------------------------------------------------------------------

import difflib


def _gerar_linhas_diff(old: str, new: str) -> list[tuple[str, str]]:
    """
    Gera linhas do diff com tag de cor.

    Retorna lista de (markup_rich, tipo) onde tipo é:
      'add'     → linha adicionada  (+)  verde
      'remove'  → linha removida    (-)  vermelha
      'context' → contexto               dim
      'hunk'    → @@ linha          @@   cyan dim

    Usa unified_diff com 2 linhas de contexto — mesmo padrão do Claude Code.

    IMPORTANTE: escape() é obrigatório pois o conteúdo do código pode ter
    colchetes (ex: yield Static(markup=True)) que o Rich interpretaria
    como tags, causando MarkupError.
    """
    from rich.markup import escape

    old_lines = old.splitlines()
    new_lines = new.splitlines()

    result: list[tuple[str, str]] = []
    diff = difflib.unified_diff(old_lines, new_lines, lineterm="", n=2)

    for line in diff:
        if line.startswith("---") or line.startswith("+++"):
            continue  # cabeçalhos de arquivo — omite como no Claude Code
        # Escapa o conteúdo ANTES de embrulhar nas tags de cor
        safe = escape(line)
        if line.startswith("@@"):
            result.append((f"[dim cyan]{safe}[/]", "hunk"))
        elif line.startswith("+"):
            result.append((f"[bold green]{safe}[/]", "add"))
        elif line.startswith("-"):
            result.append((f"[bold red]{safe}[/]", "remove"))
        else:
            result.append((f"[dim]{safe}[/]", "context"))

    return result


class BashResultWidget(Collapsible):
    """
    Widget colapsável com output de qualquer ferramenta que retorne texto.

    Não é específico para Bash — funciona para qualquer tool que tenha
    full_output: Bash, CLIs customizados, Read, Grep, etc.

    O critério de exibição é simples: tem output? mostra. Não tem? só summary.

    Visual:
      ▼ ✓ exit 0 · 12 linhas          ← colapsado se sucesso
        $ python -m pytest test.py -v
        2 passed in 0.3s

      ▼ ✗ exit 1 · 8 linhas           ← EXPANDIDO se falhou
        ERROR: file not found

    Comportamento profissional:
    - Sucesso (exit 0)  → colapsado  (ok, segue em frente)
    - Falha   (exit!=0) → expandido  (precisa atenção imediata)
    - Exit desconhecido → colapsado
    """

    DEFAULT_CSS = """
    BashResultWidget {
        height: auto;
        margin: 0 0 0 2;
        border: none;
        background: transparent;
    }

    BashResultWidget > CollapsibleTitle {
        padding: 0;
        background: transparent;
    }

    BashResultWidget.success > CollapsibleTitle {
        color: $success-darken-1;
        text-style: dim;
    }

    BashResultWidget.failure > CollapsibleTitle {
        color: $error;
        text-style: bold;
    }

    BashResultWidget.unknown > CollapsibleTitle {
        color: $text-muted;
        text-style: dim;
    }

    BashResultWidget #output-body {
        height: auto;
        max-height: 20;
        overflow-y: auto;
        padding: 0 1;
        background: $panel-darken-2;
        border-left: thick $panel;
    }

    BashResultWidget #output-body Static {
        height: auto;
        padding: 0;
        color: $text;
    }
    """

    def __init__(self, output: str, exit_code: int | None, command: str = "") -> None:
        """
        Args:
            output:    Output completo do comando (stdout + stderr).
            exit_code: Código de saída (None se não detectado).
            command:   Comando executado (para exibir no cabeçalho).
        """
        self._output   = output
        self._exit_code = exit_code
        self._command  = command

        # Determina estado e título
        lines = output.strip().splitlines()
        n = len(lines)

        if exit_code is None:
            estado = "unknown"
            icone  = "□"
            titulo = f"{icone} {n} linhas"
            collapsed = False  # Sempre expandido
        elif exit_code == 0:
            estado = "success"
            icone  = "✓"
            titulo = f"{icone} exit 0 · {n} linhas"
            collapsed = False  # SEMPRE expandido!
        else:
            estado = "failure"
            icone  = "✗"
            titulo = f"{icone} exit {exit_code} · {n} linhas"
            collapsed = False  # Falha: abre automaticamente!

        super().__init__(title=titulo, collapsed=collapsed)
        self._estado = estado

    def on_mount(self) -> None:
        self.add_class(self._estado)

    def compose(self) -> ComposeResult:
        from rich.markup import escape
        with Container(id="output-body"):
            lines = self._output.strip().splitlines()
            if not lines:
                yield Static("[dim](sem output)[/]", markup=True)
                return
            # Cabecalho com o comando (se houver)
            if self._command:
                yield Static(f"[dim]$ {escape(self._command)}[/]", markup=True)
            # Linhas do output com escape para evitar MarkupError
            for line in lines:
                yield Static(escape(line), markup=False)


class DiffWidget(Collapsible):
    """
    Widget colapsável que exibe diff colorido estilo Claude Code.

    Formato:
      ▶ Edit: arquivo.py  (+3 -1)          ← título colapsável
        @@ -10,4 +10,6 @@
        - linha removida
        + linha adicionada
          contexto dim

    Montado pelo StepWidget quando a tool é Edit/Write e tem old/new string.
    """

    DEFAULT_CSS = """
    DiffWidget {
        height: auto;
        margin: 0 0 0 2;
        border: none;
        background: transparent;
    }

    DiffWidget > CollapsibleTitle {
        color: $text-muted;
        text-style: dim;
        padding: 0;
        background: transparent;
    }

    DiffWidget #diff-body {
        height: auto;
        padding: 0 0 0 1;
        background: $panel-darken-1;
        border-left: thick $panel;
    }

    DiffWidget Static {
        height: 1;
        padding: 0;
    }
    """

    def __init__(self, old: str, new: str, file_path: str = "") -> None:
        self._old = old
        self._new = new
        self._file_path = file_path
        self._linhas = _gerar_linhas_diff(old, new)

        # Conta adds e removes para o título
        adds    = sum(1 for _, t in self._linhas if t == "add")
        removes = sum(1 for _, t in self._linhas if t == "remove")
        nome    = file_path.split("\\")[-1].split("/")[-1] if file_path else "arquivo"
        titulo  = f"{nome}  [green]+{adds}[/] [red]-{removes}[/]"

        super().__init__(title=titulo, collapsed=True)

    def compose(self) -> ComposeResult:
        with Container(id="diff-body"):
            if not self._linhas:
                yield Static("[dim](sem diferenças)[/]")
            else:
                for markup, _ in self._linhas:
                    yield Static(markup, markup=True)


# ---------------------------------------------------------------------------
# PRD-REACT-001: Componentes ReAct (Reasoning + Acting)
# ---------------------------------------------------------------------------

class ThoughtLine(Static):
    """
    Linha de pensamento (Thought) do StepWidget.

    Exibe o texto de intenção narrado pelo modelo antes de usar uma ferramenta.
    Estilo: itálico muted, sutil.

    Usado para pensamentos curtos (<= 80 caracteres).
    Para pensamentos longos, use ThoughtLineMarkdown.
    """

    DEFAULT_CSS = """
    ThoughtLine {
        text-style: italic;
        color: $text;  /* Mudado de $text-muted para $text para visibilidade */
        padding: 0 1;
        margin: 0 0 0 0;
        height: auto;
    }
    """

    def __init__(self, text: str) -> None:
        super().__init__(text)
        self._text = text

    def set_text(self, text: str) -> None:
        """Atualiza o texto do pensamento."""
        self._text = text
        # Remove aspas se presentes
        display_text = text.strip('"').strip("'")
        self.update(f"_{display_text}")


# ---------------------------------------------------------------------------
# ThoughtLineMarkdown — para pensamentos longos com suporte a Markdown
# ---------------------------------------------------------------------------


class ThoughtLineMarkdown(Markdown):
    """
    Linha de pensamento longo renderizada como Markdown.

    Usada para pensamentos > 80 caracteres que contêm markdown ou
    informações estruturadas (não apenas raciocínio simples).

    Diferente de ThoughtLine, não usa itálico e permite renderização
    completa de markdown (listas, código, etc).
    """

    DEFAULT_CSS = """
    ThoughtLineMarkdown {
        color: $text;
        padding: 0 1;
        margin: 0 0 0 0;
        height: auto;
        background: transparent;
        text-style: none;  /* NÃO itálico */
    }
    """

    def __init__(self, text: str) -> None:
        # Remove aspas se presentes
        clean_text = text.strip('"').strip("'")
        super().__init__(clean_text)

    def set_text(self, text: str) -> None:
        """Atualiza o texto markdown."""
        clean_text = text.strip('"').strip("'")
        self.update(clean_text)


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


class AgenticLoopPanel(Collapsible):
    """
    Painel colapsável que agrupa Steps do loop agentic ReAct.

    Comportamento:
    - Inicia com ThinkingIndicator visível ("🤔 pensando...")
    - Quando primeiro Step é adicionado, remove ThinkingIndicator e mostra Steps
    - Expandido durante o processamento
    - Auto-colapsa quando a resposta final chega
    - Título dinâmico: "⟳ N steps • Xs"

    Estados:
    1. INIT: ThinkingIndicator visível, nenhum Step ainda
    2. ACTIVE: Pelo menos um Step adicionado, ThinkingIndicator removido
    3. FROZEN: Cancelado pelo usuário, não adiciona mais Steps
    """

    DEFAULT_CSS = """
    AgenticLoopPanel {
        margin: 0;
        padding: 1 0 0 0;
        border: none;
        background: $surface;
        height: auto;
    }

    AgenticLoopPanel.collapsed {
        border: none;
    }

    AgenticLoopPanel > CollapsibleTitle {
        text-style: bold;
        color: $primary;
        padding: 0 1;
        background: transparent;
    }

    AgenticLoopPanel.collapsed > CollapsibleTitle {
        color: $text-muted;
        text-style: none;
        background: transparent;
    }

    AgenticLoopPanel #steps-container {
        height: auto;
        overflow-y: auto;
        padding: 0;
    }

    AgenticLoopPanel ThinkingIndicator {
        margin: 0 1 1 1;
    }
    """

    def __init__(self, parent_turn=None) -> None:
        """
        Inicializa o AgenticLoopPanel.

        Args:
            parent_turn: Referência ao Turn pai para disparar scroll.
        """
        super().__init__(title="⟳ 0 steps • 0s", collapsed=False)
        self._steps: list[StepWidget] = []
        self._step_count = 0
        self._start_time: float | None = None
        self._frozen = False  # True quando cancelado (não adiciona mais Steps)
        self._indicator: ThinkingIndicator | None = None  # ThinkingIndicator interno
        self._parent_turn = parent_turn  # Referência para disparar scroll

    def compose(self) -> ComposeResult:
        # ThinkingIndicator visível inicialmente
        self._indicator = ThinkingIndicator()
        yield self._indicator
        yield Container(id="steps-container")

    def _trigger_scroll(self) -> None:
        """Dispara scroll no ChatScroll via Turn pai."""
        if self._parent_turn is not None:
            try:
                self._parent_turn.trigger_scroll()
            except Exception:
                pass

    # ------------------------------------------------------------------
    # API pública
    # ------------------------------------------------------------------

    async def add_step(self, thought: str | None = None) -> StepWidget:
        """
        Adiciona um StepWidget ao painel.

        No primeiro Step adicionado, remove o ThinkingIndicator.

        Args:
            thought: Texto de pensamento opcional (ThoughtLine).

        Returns:
            O StepWidget criado para referência futura.
        """
        if self._frozen:
            # Não adiciona mais Steps se foi cancelado
            return None  # type: ignore

        # Primeiro Step: remove ThinkingIndicator
        if self._step_count == 0 and self._indicator is not None:
            try:
                self._indicator.remove()
                self._indicator = None
            except Exception:
                pass

        # Inicia o timer no primeiro Step
        if self._start_time is None:
            self._start_time = time.time()

        step = StepWidget(thought=thought)
        self._steps.append(step)
        self._step_count += 1
        self._update_title()

        try:
            container = self.query_one("#steps-container", Container)
            await container.mount(step)
            container.scroll_end()
            # Dispara scroll no ChatScroll principal
            self._trigger_scroll()
        except Exception:
            pass

        return step

    def get_last_pending_step(self) -> StepWidget | None:
        """
        Retorna o último StepWidget pendente (não resolvido).

        Usado para resolver o Step quando tool_result chega.
        """
        for step in reversed(self._steps):
            if not step.is_resolved:
                return step
        return None

    def collapse_done(self) -> None:
        """
        Colapsa o painel quando a resposta final chega.

        Atualiza o título com a duração total.
        """
        self._update_title()
        self.collapsed = True

    def freeze(self) -> None:
        """
        Congela o painel quando o turno é cancelado.

        Mantém Steps já criados visíveis, não adiciona mais.
        """
        self._frozen = True
        self._update_title()

    # ------------------------------------------------------------------
    # Interno
    # ------------------------------------------------------------------

    def _update_title(self) -> None:
        """Atualiza o título com contador de Steps e duração."""
        n = self._step_count
        duration = self._get_duration()
        try:
            if self._frozen:
                self.title = f"⟳ {n} steps • {duration}s (interrompido)"
            else:
                self.title = f"⟳ {n} steps • {duration}s"
        except Exception:
            pass

    def _get_duration(self) -> float:
        """Retorna a duração em segundos."""
        if self._start_time is None:
            return 0.0
        return round(time.time() - self._start_time, 1)

    @property
    def step_count(self) -> int:
        return self._step_count

    @property
    def is_frozen(self) -> bool:
        return self._frozen


# Precisa importar time no topo do arquivo para AgenticLoopPanel


__all__ = [
    "ThinkingIndicator",
    "ThinkingPanel",
    "ToolCallWidget",
    "SimpleEntryWidget",
    # PRD-REACT-001: novos componentes ReAct
    "ThoughtLine",
    "ThoughtLineMarkdown",
    "ActionLine",
    "StepWidget",
    "AgenticLoopPanel",
    # Diff e output de tools
    "DiffWidget",
    "BashResultWidget",
]
