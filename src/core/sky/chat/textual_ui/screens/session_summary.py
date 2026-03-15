# coding: utf-8
"""
SessionSummaryScreen - Resumo de sessão ao encerrar.

Exibe um resumo da sessão com métricas e estatísticas
em formato de tabela ao encerrar o chat.
"""

from datetime import datetime
from typing import TYPE_CHECKING
from textual.app import ComposeResult
from textual.screen import Screen
from textual.widgets import DataTable, Header, Footer, Static

if TYPE_CHECKING:
    from core.sky.chat.textual_ui.widgets.header.title.history import TitleHistory


class SessionSummaryScreen(Screen):
    """Screen de resumo de sessão."""

    DEFAULT_CSS = """
    SessionSummaryScreen {
        layout: vertical;
    }
    #summary-title {
        text-align: center;
        text-style: bold;
        margin: 1 0;
    }
    DataTable {
        height: 1fr;
    }
    """

    BINDINGS = [
        ("q", "app.exit", "Sair"),
        ("escape", "app.exit", "Sair"),
        ("enter", "app.exit", "Sair"),
    ]

    def __init__(
        self,
        message_count: int = 0,
        total_tokens: int = 0,
        avg_latency: float = 0.0,
        memories_used: int = 0,
        session_duration: float = 0.0,
        title_history: "TitleHistory | None" = None,
    ) -> None:
        """
        Inicializa SessionSummaryScreen.

        Args:
            message_count: Total de mensagens trocadas.
            total_tokens: Total de tokens consumidos.
            avg_latency: Latência média em segundos.
            memories_used: Total de memórias usadas.
            session_duration: Duração da sessão em segundos.
            title_history: Histórico de títulos para gerar resumo de atividades.
        """
        super().__init__()
        self.message_count = message_count
        self.total_tokens = total_tokens
        self.avg_latency = avg_latency
        self.memories_used = memories_used
        self.session_duration = session_duration
        self._title_history = title_history

    def compose(self) -> ComposeResult:
        """Compôe a tela de resumo."""
        yield Header()
        yield Static("📊 Resumo da Sessão", id="summary-title")
        yield DataTable(id="summary-table")
        yield Footer()

    def on_mount(self) -> None:
        """Popula a tabela ao montar."""
        table = self.query_one("#summary-table", DataTable)
        table.zebra_stripes = True

        # Adiciona colunas
        table.add_column("Métrica", width=30)
        table.add_column("Valor", width=40)

        # Formata duração
        duration_min = int(self.session_duration // 60)
        duration_sec = int(self.session_duration % 60)
        duration_str = f"{duration_min}m {duration_sec}s"

        # Formata latência média
        latency_str = f"{self.avg_latency:.2f}s"

        # Formata tokens
        tokens_k = self.total_tokens / 1000
        tokens_str = f"{tokens_k:.1f}k"

        # Adiciona linhas básicas
        table.add_row("Mensagens trocadas", str(self.message_count))
        table.add_row("Turnos de conversa", str(self.message_count // 2))
        table.add_row("Tokens consumidos", tokens_str)
        table.add_row("Latência média", latency_str)
        table.add_row("Memórias usadas (RAG)", str(self.memories_used))
        table.add_row("Duração da sessão", duration_str)
        table.add_row("Encerrada em", datetime.now().strftime("%d/%m/%Y %H:%M"))

        # Linha separadora
        table.add_row("", "")

        # Resumo de atividades (se title_history fornecido)
        if self._title_history:
            resumo = self._title_history.gerar_resumo()

            # Tempo por emoção
            tempo_por_emocao = resumo["tempo_por_emocao"]
            if tempo_por_emocao:
                table.add_row("━━━", "━━━")  # Separador
                for emocao, tempo in sorted(tempo_por_emocao.items(), key=lambda x: -x[1]):
                    minutos = int(tempo // 60)
                    segs = int(tempo % 60)
                    tempo_str = f"{minutos}m {segs}s" if minutos > 0 else f"{segs}s"
                    table.add_row(f"Tempo em {emocao}", tempo_str)

            # Estatísticas
            table.add_row("", "")
            table.add_row("Revisões (correções)", str(resumo["contagem_revisoes"]))

            # Top 3 estados
            top_estados = resumo["top_estados"]
            if top_estados:
                for i, (verbo, predicado, count) in enumerate(top_estados, 1):
                    table.add_row(f"Top {i} estado", f"{verbo} ({count}x)")

            table.add_row("", "")

        # Mensagem de despedida
        table.add_row(
            "Até logo! 👋",
            "Obrigado por conversar com a Sky!",
        )

        # Foca na tabela
        table.focus()


__all__ = ["SessionSummaryScreen"]
