# coding: utf-8
"""
POC - App de Desenvolvimento para ChatLog 2.0.

App Textual standalone para testar visualmente o subsistema de log.
Layout simplificado: busca na linha 1, filtros + botões na linha 2.
"""

import logging
from datetime import datetime, timedelta

from textual.app import App, ComposeResult
from textual.widgets import Footer, Header

from core.sky.log.chatlog import ChatLog, ChatLogConfig
from core.sky.log.entry import LogEntry
from core.sky.log.scope import LogScope
from core.sky.log.widgets.filter import FilterChanged
from core.sky.log.widgets.search import SearchChanged
from core.sky.log.widgets.toolbar import LogToolbar


class ChatLogPOC(App):
    """POC App para testar ChatLog 2.0."""

    TITLE = "ChatLog 2.0 - POC"
    SUB_TITLE = "Subsistema de log com filtros e busca"

    CSS = """
    Screen {
        layout: vertical;
    }

    ChatLog {
        border: solid $primary;
    }
    """

    def compose(self) -> ComposeResult:
        """Compõe a UI do POC."""
        yield Header()
        yield LogToolbar()
        yield ChatLog(config=ChatLogConfig(max_entries=1000), id="chatlog")
        yield Footer()

    def on_mount(self) -> None:
        """Gera logs de exemplo ao montar."""
        # Aguarda UI montar
        self.set_timer(0.5, self._generate_sample_logs)

    def _generate_sample_logs(self) -> None:
        """Gera logs de exemplo para todos os níveis e escopos."""
        chatlog = self.query_one("#chatlog", ChatLog)

        # Timestamp base (começa 5 minutos atrás)
        base_time = datetime.now() - timedelta(minutes=5)

        # Logs de sistema
        for i in range(5):
            chatlog.write_log(
                LogEntry(
                    level=logging.INFO,
                    message=f"Inicializando componente {i+1}/5...",
                    timestamp=base_time + timedelta(seconds=i * 2),
                    scope=LogScope.SYSTEM,
                )
            )

        # Logs de API
        for i in range(8):
            level = logging.DEBUG if i % 3 == 0 else logging.INFO
            chatlog.write_log(
                LogEntry(
                    level=level,
                    message=f"API request to /api/v1/resource/{i+1}",
                    timestamp=base_time + timedelta(seconds=10 + i * 3),
                    scope=LogScope.API,
                )
            )

        # Logs de banco de dados
        chatlog.write_log(
            LogEntry(
                level=logging.WARNING,
                message="Query lenta detectada: SELECT * FROM users (2.3s)",
                timestamp=base_time + timedelta(seconds=35),
                scope=LogScope.DATABASE,
            )
        )

        chatlog.write_log(
            LogEntry(
                level=logging.INFO,
                message="Connection pool: 5/10 conexões ativas",
                timestamp=base_time + timedelta(seconds=36),
                scope=LogScope.DATABASE,
            )
        )

        # Logs de rede
        chatlog.write_log(
            LogEntry(
                level=logging.ERROR,
                message="Timeout na conexão com external-service.com",
                timestamp=base_time + timedelta(seconds=40),
                scope=LogScope.NETWORK,
            )
        )

        chatlog.write_log(
            LogEntry(
                level=logging.INFO,
                message="Reconectando... (tentativa 1/3)",
                timestamp=base_time + timedelta(seconds=41),
                scope=LogScope.NETWORK,
            )
        )

        # Logs de voz
        chatlog.write_log(
            LogEntry(
                level=logging.DEBUG,
                message="Audio frame received: 160 samples @ 16kHz",
                timestamp=base_time + timedelta(seconds=45),
                scope=LogScope.VOICE,
            )
        )

        chatlog.write_log(
            LogEntry(
                level=logging.INFO,
                message="STT: transcript = 'olá mundo'",
                timestamp=base_time + timedelta(seconds=46),
                scope=LogScope.VOICE,
            )
        )

        # Logs de memória
        chatlog.write_log(
            LogEntry(
                level=logging.WARNING,
                message="Memória: 75% utilizada (1.5GB/2GB)",
                timestamp=base_time + timedelta(seconds=50),
                scope=LogScope.MEMORY,
            )
        )

        # Logs de usuário
        for i in range(4):
            chatlog.write_log(
                LogEntry(
                    level=logging.INFO,
                    message=f"User action: click no botão {i+1}",
                    timestamp=base_time + timedelta(seconds=55 + i),
                    scope=LogScope.USER,
                )
            )

        # Logs críticos
        chatlog.write_log(
            LogEntry(
                level=logging.CRITICAL,
                message="PANIC: inconsistência no estado da aplicação!",
                timestamp=base_time + timedelta(seconds=60),
                scope=LogScope.SYSTEM,
            )
        )

        # Mensagem final
        chatlog.write_log(
            LogEntry(
                level=logging.INFO,
                message="✓ POC inicializado - experimente os filtros e busca!",
                timestamp=datetime.now(),
                scope=LogScope.SYSTEM,
            )
        )

    def on_filter_changed(self, event: FilterChanged) -> None:
        """Handle mudança de filtro do toolbar."""
        chatlog = self.query_one("#chatlog", ChatLog)
        chatlog._min_level = event.level
        chatlog._scope_filter = LogScope.ALL  # Sempre ALL (sem filtro de escopo)
        chatlog._schedule_refresh()

    def on_search_changed(self, event: SearchChanged) -> None:
        """Handle mudança de busca do toolbar."""
        chatlog = self.query_one("#chatlog", ChatLog)
        chatlog._search_term = event.search_term
        chatlog._schedule_refresh()


def main():
    """EntryPoint do POC."""
    app = ChatLogPOC()
    app.run()


if __name__ == "__main__":
    main()
