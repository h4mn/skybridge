# coding: utf-8
"""
ChatUI - Interface de chat usando prompt_toolkit + Rich.

DOC: openspec/changes/chat-claude-sdk/design.md - Componentes de UI
"""

from typing import List, Optional
from dataclasses import dataclass

from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.markdown import Markdown
from rich.text import Text


# ChatMessage é definido em __init__.py para evitar imports circulares
# Não importamos aqui para evitar circular import


@dataclass
class ChatMetrics:
    """
    Métricas de uma resposta do chat.

    DOC: spec.md - Requirement: Métricas de latência registradas
    """
    latency_ms: float
    tokens_in: int
    tokens_out: int
    memory_hits: int
    model: str


class ChatUI:
    """
    Interface de chat com renderização rica.

    DOC: spec.md - Componentes de UI
    """

    def __init__(self, console: Optional[Console] = None, verbose: bool = False):
        """
        Inicializa a UI.

        Args:
            console: Console Rich para renderização.
            verbose: Se True, exibe métricas detalhadas.
        """
        self.console = console or Console()
        self.verbose = verbose

    def render_header(self, rag_enabled: bool = True, memory_count: int = 0) -> None:
        """
        Renderiza cabeçalho com status.

        DOC: spec.md - Cenário: render_header() com status bar

        Args:
            rag_enabled: Se RAG está habilitado.
            memory_count: Quantidade de memórias disponíveis.
        """
        # DOC: "render_header() com status bar (Sky, RAG, memória)"
        rag_status = "[green]ON[/green]" if rag_enabled else "[red]OFF[/red]"
        memory_text = f"{memory_count} memórias" if memory_count > 0 else "0 memórias"

        header = Text()
        header.append("🌌 SKY ", style="bold blue")
        header.append(f"│ RAG: {rag_status} ", style="dim")
        header.append(f"│ {memory_text}", style="dim")

        self.console.print(Panel(header, style="dim blue", padding=(0, 1)))

    def render_thinking(self, message: str = "🤔 Pensando...") -> None:
        """
        Renderiza indicador de thinking.

        DOC: spec.md - Cenário: render_thinking() com anim "🤔 Pensando..."

        Args:
            message: Mensagem a exibir.
        """
        # DOC: "render_thinking() com anim '🤔 Pensando...'"
        self.console.print(f"[yellow italic]{message}[/yellow italic]")

    def render_tools(self, tools_executed: List[dict]) -> None:
        """
        Renderiza tabela de tools executadas.

        DOC: spec.md - Cenário: render_tools() com tabela de tools executadas

        Args:
            tools_executed: Lista de tools executadas com nome e resultado.
        """
        if not tools_executed:
            return

        # DOC: "render_tools() com tabela de tools executadas"
        # DOC: "formato é tabela com nome e resultado"
        table = Table(title="🔧 Tools Executadas", show_header=True, header_style="bold magenta")
        table.add_column("Tool", style="cyan")
        table.add_column("Resultado", style="green")

        for tool in tools_executed:
            status = "✅" if tool.get("success", True) else "❌"
            table.add_row(f"{status} {tool.get('name', 'unknown')}", tool.get("result", ""))

        self.console.print(table)

    def render_memory(self, memories: List[dict], verbose: bool = False) -> None:
        """
        Renderiza preview de memórias usadas.

        DOC: spec.md - Cenário: render_memory() com preview de memórias usadas

        Args:
            memories: Lista de memórias recuperadas.
            verbose: Se True, exibe conteúdo completo das memórias.
        """
        if not memories:
            return

        # DOC: "render_memory() com preview de memórias usadas"
        count = len(memories)
        self.console.print(f"[dim]📚 {count} memória(s) usada(s)[/dim]")

        if verbose:
            # DOC: "preview das memórias é exibido em modo verbose"
            for memory in memories[:5]:  # Top 5
                content = memory.get("content", "")[:100]  # Primeiros 100 chars
                similarity = memory.get("similarity", 0)
                self.console.print(f"  [dim]- {content}... (sim: {similarity:.2f})[/dim]")

    def render_message(self, role: str, content: str, metrics: Optional[ChatMetrics] = None) -> None:
        """
        Renderiza uma mensagem do chat.

        DOC: spec.md - Cenário: render_message() com renderização Markdown

        Args:
            role: "user" ou "sky".
            content: Conteúdo da mensagem.
            metrics: Métricas da resposta (opcional).
        """
        if role == "user":
            self.console.print(f"\n[cyan]Você:[/cyan] {content}")
        else:
            # Sky message - renderiza como Markdown
            # DOC: "render_message() com renderização Markdown"
            self.console.print(f"\n[bold blue]🌌 Sky:[/bold blue]")
            md = Markdown(content)
            self.console.print(md)

            # Métricas em modo verbose
            if metrics and self.verbose:
                # DOC: "latência de cada resposta é exibida ao usuário"
                # DOC: "formato é '⏱️ Resposta em 1.2s (1234ms)'"
                latency_s = metrics.latency_ms / 1000
                self.console.print(
                    f"[dim]⏱️ Resposta em {latency_s:.2f}s ({metrics.latency_ms:.0f}ms) "
                    f"│ {metrics.tokens_in} tokens in, {metrics.tokens_out} tokens out[/dim]"
                )

                # Alerta de latência alta
                # DOC: spec.md - Cenário: Alerta de latência alta
                if metrics.latency_ms > 5000:
                    self.console.print("[yellow]⚠️ Resposta demorou mais que o normal[/yellow]")

    def render_footer(self) -> None:
        """
        Renderiza rodapé com atalhos.

        DOC: spec.md - Cenário: render_footer() com atalhos e comandos
        """
        # DOC: "render_footer() com atalhos e comandos"
        footer = Text()
        footer.append("Comandos: ", style="dim")
        footer.append("/new ", style="cyan")
        footer.append("limpar sessão │ ", style="dim")
        footer.append("/cancel ", style="cyan")
        footer.append("cancelar │ ", style="dim")
        footer.append("/sair ", style="cyan")
        footer.append("encerrar", style="dim")

        self.console.print(Panel(footer, style="dim", padding=(0, 1)))

    def render_error(self, message: str) -> None:
        """
        Renderiza mensagem de erro.

        Args:
            message: Mensagem de erro.
        """
        self.console.print(f"[red]❌ Erro: {message}[/red]")

    def render_session_summary(self, metrics: List[ChatMetrics]) -> None:
        """
        Renderiza resumo da sessão ao encerrar.

        DOC: spec.md - Cenário: Resumo ao encerrar sessão

        Args:
            metrics: Lista de métricas de todas as respostas.
        """
        if not metrics:
            return

        # DOC: "resumo inclui: mensagens trocadas, latência média, tokens totais"
        total_latency = sum(m.latency_ms for m in metrics)
        avg_latency = total_latency / len(metrics)
        total_tokens_in = sum(m.tokens_in for m in metrics)
        total_tokens_out = sum(m.tokens_out for m in metrics)

        # DOC: "formato é tabela Rich com bordas"
        table = Table(title="📊 Resumo da Sessão", show_header=True, header_style="bold blue")
        table.add_column("Métrica", style="cyan")
        table.add_column("Valor", style="green")

        table.add_row("Mensagens trocadas", str(len(metrics)))
        table.add_row("Latência média", f"{avg_latency:.0f}ms")
        table.add_row("Tokens (entrada)", str(total_tokens_in))
        table.add_row("Tokens (saída)", str(total_tokens_out))

        self.console.print(table)


__all__ = [
    "ChatUI",
    "ChatMetrics",
]
