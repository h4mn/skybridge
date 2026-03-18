# coding: utf-8
"""
DiffWidget - Widget colapsável que exibe diff colorido estilo Claude Code.

BashResultWidget - Widget colapsável com output de qualquer ferramenta que retorne texto.

Formato:
  ▶ Edit: arquivo.py  (+3 -1)          ← título colapsável
    @@ -10,4 +10,6 @@
    - linha removida
    + linha adicionada
      contexto dim

Montado pelo StepWidget quando a tool é Edit/Write e tem old/new string.
"""

import difflib

from textual.app import ComposeResult
from textual.containers import Container
from textual.widgets import Collapsible, Static


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


__all__ = ["DiffWidget", "BashResultWidget", "_gerar_linhas_diff"]
