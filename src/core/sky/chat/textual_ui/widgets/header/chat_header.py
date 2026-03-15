# coding: utf-8
"""
ChatHeader - Header customizado para o chat Sky.

Layout de 4 linhas:
  Linha 1-2: AnimatedTitle completo ("Sky verbo predicado")
  Linha 3:   ContextBar (barra de progresso do contexto)
  Linha 4:   métricas dinâmicas (RAG, mems, latência, tokens, modelo)
"""

from textual.app import ComposeResult
from textual.widget import Widget
from textual.widgets import Static

from core.sky.chat.textual_ui.widgets.header.title.animated_title import AnimatedTitle, TitleStatic
from core.sky.chat.textual_ui.widgets.header.context_bar import ContextBar
from core.sky.chat.textual_ui.widgets.header.animated_verb import EstadoLLM
from core.sky.chat.textual_ui.widgets.header.title.history import TitleHistory


class ChatHeader(Widget):
    """Header com 4 linhas."""

    DEFAULT_CSS = """
    ChatHeader {
        height: 6;
        width: 100%;
        layout: vertical;
        padding: 0 1;
        background: $surface;
        border-bottom: solid $panel;
    }
    ChatHeader > AnimatedTitle {
        height: 2;
        width: 1fr;
        margin-top: 1;
        text-style: bold;
    }
    ChatHeader > ContextBar {
        height: 1;
        width: 1fr;
        margin: 0;
        padding: 0;
    }
    ChatHeader > #components {
        height: 1;
        width: 1fr;
        content-align: right middle;
        text-style: dim;
    }
    """

    def __init__(self, verbo: str = "iniciando", predicado: str = "conversa"):
        super().__init__()
        self._verbo = verbo
        self._predicado = predicado
        self._title_history = TitleHistory()

    def compose(self) -> ComposeResult:
        yield AnimatedTitle("Sky", self._verbo, self._predicado)
        yield ContextBar(total=20, id="context-bar")
        yield Static("", id="components")

    # ------------------------------------------------------------------
    # API de atualização
    # ------------------------------------------------------------------

    def update_estado(self, estado: EstadoLLM, predicado: str | None = None) -> None:
        """
        Atualiza verbo animado via EstadoLLM.

        predicado=None mantém o atual OU usa estado.predicado como fallback.
        Isso permite que EstadoLLM transporte todos os dados do título.
        """
        # Usa estado.predicado como fallback se predicado não fornecido
        if predicado is None:
            predicado = estado.predicado
        self._predicado = predicado

        # Adiciona ao histórico
        self._title_history.add(estado)

        # Atualiza título
        title = self.query_one(AnimatedTitle)
        title.update_estado(estado, self._predicado)

        # Atualiza tooltips dos TitleStatic
        try:
            sujeito = title.query_one("#sujeito", TitleStatic)
            predicado_widget = title.query_one("#predicado", TitleStatic)
            sujeito.update_tooltip(self._title_history)
            predicado_widget.update_tooltip(self._title_history)
        except Exception:
            # TitleStatic pode não existir ainda durante composição inicial
            pass

    def update_title(self, verbo: str, predicado: str) -> None:
        """Atualiza título (verbo + predicado) diretamente."""
        self._verbo = verbo
        self._predicado = predicado
        self.query_one(AnimatedTitle).update_title(verbo, predicado)

    def update_metricas(
        self,
        turn_count: int = 0,
        tokens_in: int = 0,
        tokens_out: int = 0,
        latency_ms: float = 0.0,
        memories_used: int = 0,
        rag_enabled: bool = True,
        model: str = "GLM-4.7",
    ) -> None:
        """Atualiza linha 4 com métricas reais da sessão."""
        total_tokens = tokens_in + tokens_out
        tokens_k = f"{total_tokens / 1000:.1f}k" if total_tokens >= 1000 else str(total_tokens)
        latency_s = f"⚡{latency_ms / 1000:.1f}s" if latency_ms > 0 else ""
        rag_status = "RAG: on" if rag_enabled else "RAG: off"
        mems = f"{memories_used} mems" if memories_used else ""

        parts = [p for p in [
            f"🔥 {turn_count} msgs",
            rag_status,
            mems,
            latency_s,
            f"💰 {tokens_k}" if total_tokens > 0 else "",
            model,
        ] if p]

        self.query_one("#components", Static).update(" | ".join(parts))

    def update_context_bar(self, history_len: int) -> None:
        """Atualiza a ContextBar com o tamanho atual do histórico."""
        self.query_one("#context-bar", ContextBar).update_progress(history_len)

    # ------------------------------------------------------------------
    # Event handlers
    # ------------------------------------------------------------------

    def on_title_static_clicked(self, event: TitleStatic.Clicked) -> None:
        """
        Handler para clique no TitleStatic (sujeito ou predicado).

        Abre o diálogo de histórico com todos os estados acumulados.
        """
        from core.sky.chat.textual_ui.widgets.header.title.history_dialog import TitleHistoryDialog
        self.app.push_screen(TitleHistoryDialog(self._title_history))


__all__ = ["ChatHeader"]
