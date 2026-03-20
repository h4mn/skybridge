# coding: utf-8
"""
ChatLogger - Logger específico para o domínio de chat.

Logger completamente independente do SkybridgeLogger, projetado para:
- Redirecionar stdout/stderr permanentemente para capturar saídas de bibliotecas externas
- Filtrar e silenciar saídas de sentence-transformers, torch, transformers, huggingface_hub
- Salvar logs em arquivo isolado (.sky/chat.log)
- Integrar com o widget ChatLog para exibição na UI Textual
- Integrar com LogConsumer Protocol (ChatLog 2.0)

RESTRIÇÃO: NÃO depende de runtime.observability.logger
"""

from __future__ import annotations

import json
import logging
import os
import sys
import uuid
from datetime import datetime
from pathlib import Path
from typing import TextIO, Optional, TYPE_CHECKING, Any

if TYPE_CHECKING:
    from core.sky.chat.textual_ui.widgets.chat_log import ChatLog

# Import condicional do LogConsumer (ChatLog 2.0)
try:
    from core.sky.log.protocol import LogConsumer
    from core.sky.log.entry import LogEntry
    from core.sky.log.scope import LogScope
    HAS_CHATLOG_2_0 = True
except ImportError:
    HAS_CHATLOG_2_0 = False
    LogConsumer = None  # type: ignore
    LogEntry = None  # type: ignore
    LogScope = None  # type: ignore


class _ChatLoggerStream(TextIO):
    """
    Stream interceptor que redireciona stdout/stderr para o ChatLogger.

    Tudo que é escrito neste stream passa pelo ChatLogger,
    que decide o que fazer (descartar, salvar, encaminhar).
    """

    def __init__(
        self,
        original_stream: TextIO,
        chat_logger: 'ChatLogger',
        stream_name: str = "stdout"
    ):
        self._original = original_stream
        self._chat_logger = chat_logger
        self._stream_name = stream_name

    def write(self, text: str) -> int:
        """Intercepta escrita e roteia para ChatLogger."""
        if not text:
            return 0

        # Roteia para ChatLogger decidir o que fazer
        self._chat_logger._route_output(
            text=text,
            source=self._stream_name
        )

        # NÃO escreve no stream original para não quebrar UI Textual
        return len(text)

    def flush(self):
        """Flush do buffer."""
        self._original.flush()


class ChatLogger:
    """
    Logger específico para o domínio de chat com redirecionamento
    permanente de stdout/stderr e integração com ChatLog widget.

    Suporta tanto o ChatLog legado quanto o ChatLog 2.0 (via LogConsumer Protocol).

    Uso (ChatLog 2.0 recomendado):
        from core.sky.log.chatlog import ChatLog, ChatLogConfig

        chat_log = ChatLog(config=ChatLogConfig())

        chat_logger = ChatLogger(
            session_id="abc123",
            log_consumer=chat_log  # Usa LogConsumer Protocol
        )

        chat_logger.info("Mensagem")
        chat_logger.restore()

    Uso (legado, ainda suportado):
        chat_log_widget = ChatLog()  # Widget Textual antigo

        chat_logger = ChatLogger(
            session_id="abc123",
            chat_log_widget=chat_log_widget  # Conecta ao widget legado
        )
    """

    def __init__(
        self,
        session_id: str | None = None,
        chat_log_widget: Optional['ChatLog'] = None,
        log_consumer: Optional['LogConsumer'] = None,  # ChatLog 2.0
        log_file: Path | None = None,
        verbosity: str = "WARNING",
        show_in_ui: bool = True
    ):
        self._session_id = session_id or self._generate_session_id()
        self._chat_log_widget = chat_log_widget
        self._log_consumer = log_consumer  # ChatLog 2.0 consumer
        self._log_file = log_file or self._default_log_file()
        self._verbosity = verbosity
        self._show_in_ui = show_in_ui

        # Salva streams originais para restauração
        self._original_stdout = sys.stdout
        self._original_stderr = sys.stderr

        # Configura silenciamento de bibliotecas externas
        self._setup_external_libs()

        # Configura arquivo de log
        self._setup_file_handler()

        # REDIRECIONA stdout/stderr permanentemente
        self._redirect_streams()

    def _generate_session_id(self) -> str:
        """Gera ID único para sessão."""
        return f"chat_{uuid.uuid4().hex[:8]}"

    def _default_log_file(self) -> Path:
        """Retorna caminho padrão do arquivo de log."""
        from runtime.config.config import get_workspace_logs_dir
        logs_dir = get_workspace_logs_dir()
        return logs_dir / "chat.log"

    def _setup_external_libs(self):
        """Configura silenciamento de bibliotecas externas."""
        # Variáveis de ambiente
        os.environ["HF_HUB_OFFLINE"] = "1"
        os.environ["TRANSFORMERS_VERBOSITY"] = "error"
        os.environ["TOKENIZERS_PARALLELISM"] = "false"

        # Logging do Python
        logging.getLogger("sentence_transformers").setLevel(logging.CRITICAL)
        logging.getLogger("torch").setLevel(logging.CRITICAL)
        logging.getLogger("transformers").setLevel(logging.CRITICAL)
        logging.getLogger("huggingface_hub").setLevel(logging.CRITICAL)

    def _setup_file_handler(self):
        """Configura handler de arquivo."""
        self._log_file.parent.mkdir(parents=True, exist_ok=True)
        self._file_handler = open(self._log_file, "a", encoding="utf-8")
        self._write_header()

    def _write_header(self):
        """Escreve cabeçalho de sessão no arquivo."""
        separator = "=" * 60
        self._file_handler.write(f"\n{separator}\n")
        self._file_handler.write(f"Chat Session: {self._session_id}\n")
        self._file_handler.write(f"Started: {datetime.now().isoformat()}\n")
        self._file_handler.write(f"{separator}\n\n")
        self._file_handler.flush()

    def _redirect_streams(self):
        """Redireciona stdout/stderr para este logger."""
        sys.stdout = _ChatLoggerStream(sys.stdout, self, "stdout")
        sys.stderr = _ChatLoggerStream(sys.stderr, self, "stderr")

    def restore(self):
        """Restaura stdout/stderr originais."""
        sys.stdout = self._original_stdout
        sys.stderr = self._original_stderr
        self._write_footer()
        self._file_handler.close()

    def _write_footer(self):
        """Escreve rodapé de sessão no arquivo."""
        separator = "=" * 60
        self._file_handler.write(f"\n{separator}\n")
        self._file_handler.write(f"Session Ended: {datetime.now().isoformat()}\n")
        self._file_handler.write(f"{separator}\n\n")
        self._file_handler.flush()

    def set_chat_log_widget(self, widget: 'ChatLog'):
        """Define ou atualiza o widget ChatLog."""
        self._chat_log_widget = widget

    def _route_output(self, text: str, source: str):
        """
        Roteia saída interceptada para os destinos apropriados.

        Destinos:
        1. Arquivo de log (sempre, baseado em verbosity)
        2. ChatLog widget (se disponível e show_in_ui=True)

        Console: NUNCA escreve no console (para não quebrar UI Textual)
        """
        # Sempre salva em arquivo (baseado em verbosity)
        if self._should_log(text):
            self._write_to_file(text, source)

        # Envia para ChatLog widget (se disponível)
        if self._show_in_ui and self._chat_log_widget:
            self._write_to_widget(text, source)

    def _should_log(self, text: str) -> bool:
        """Decide se deve logar baseado no conteúdo e verbosity."""
        # Se verbosity é WARNING ou ERROR, só loga erros
        if self._verbosity in ("WARNING", "ERROR"):
            error_keywords = ["error", "exception", "failed", "warning"]
            text_lower = text.lower()
            return any(kw in text_lower for kw in error_keywords)

        return True

    def _write_to_file(self, text: str, source: str):
        """Escreve no arquivo de log."""
        timestamp = datetime.now().strftime("%H:%M:%S")
        self._file_handler.write(f"[{timestamp}] [{source}] {text}")
        self._file_handler.flush()

    def _write_to_consumer(self, level: int, message: str, scope: 'LogScope' = None, context: dict[str, Any] = None) -> bool:
        """Escreve no LogConsumer (ChatLog 2.0).

        Args:
            level: Nível de logging (logging.DEBUG, logging.INFO, etc.)
            message: Mensagem de log
            scope: Escopo da mensagem (default: LogScope.USER)
            context: Contexto adicional

        Returns:
            True se escreveu no consumer, False caso contrário
        """
        if not HAS_CHATLOG_2_0 or not self._log_consumer:
            return False

        try:
            from core.sky.log.entry import LogEntry
            from core.sky.log.scope import LogScope

            entry = LogEntry(
                level=level,
                message=message,
                timestamp=datetime.now(),
                scope=scope or LogScope.USER,
                context=context
            )
            self._log_consumer.write_log(entry)
            return True
        except Exception:
            return False

    def _write_to_widget(self, text: str, source: str):
        """Escreve no ChatLog widget (legado) ou LogConsumer (ChatLog 2.0)."""
        text_stripped = text.strip()
        text_lower = text_stripped.lower()

        # Detecta nível e escopo baseado no conteúdo
        if "error" in text_lower or "exception" in text_lower:
            level = logging.ERROR
            scope = LogScope.SYSTEM if HAS_CHATLOG_2_0 else None
        elif "warning" in text_lower:
            level = logging.WARNING
            scope = LogScope.SYSTEM if HAS_CHATLOG_2_0 else None
        elif any(kw in text_lower for kw in ["loading", "carregando", "baixando"]):
            # Progresso é tratado como INFO com context de evento
            level = logging.INFO
            scope = LogScope.SYSTEM if HAS_CHATLOG_2_0 else None
            if self._write_to_consumer(level, text_stripped, scope, context={"type": "event", "event_name": "PROGRESSO"}):
                return  # Usou LogConsumer, não precisa escrever no widget legado
        else:
            level = logging.INFO
            scope = LogScope.USER if HAS_CHATLOG_2_0 else None

        # Tenta LogConsumer (ChatLog 2.0) primeiro
        if self._write_to_consumer(level, text_stripped, scope):
            return  # Usou LogConsumer, não precisa escrever no widget legado

        # Fallback para widget legado
        if not self._chat_log_widget:
            return

        if "error" in text_lower or "exception" in text_lower:
            self._chat_log_widget.error(text_stripped)
        elif "warning" in text_lower:
            self._chat_log_widget.debug(text_stripped)  # Amarelo para warning
        elif any(kw in text_lower for kw in ["loading", "carregando", "baixando"]):
            self._chat_log_widget.evento("PROGRESSO", text_stripped)
        else:
            self._chat_log_widget.info(text_stripped)

    # Interface de logging (usa LogConsumer se disponível, senão ChatLog widget)
    def debug(self, message: str, **kwargs):
        """Log debug."""
        self._write_to_file(f"[DEBUG] {message}\n", "CHAT")

        # Tenta LogConsumer (ChatLog 2.0) primeiro
        if not self._write_to_consumer(logging.DEBUG, message):
            # Fallback para widget legado
            if self._show_in_ui and self._chat_log_widget:
                self._chat_log_widget.debug(message)

    def info(self, message: str, **kwargs):
        """Log info."""
        self._write_to_file(f"[INFO] {message}\n", "CHAT")

        # Tenta LogConsumer (ChatLog 2.0) primeiro
        if not self._write_to_consumer(logging.INFO, message):
            # Fallback para widget legado
            if self._show_in_ui and self._chat_log_widget:
                self._chat_log_widget.info(message)

    def warning(self, message: str, **kwargs):
        """Log warning."""
        self._write_to_file(f"[WARNING] {message}\n", "CHAT")

        # Tenta LogConsumer (ChatLog 2.0) primeiro
        if not self._write_to_consumer(logging.WARNING, message):
            # Fallback para widget legado
            if self._show_in_ui and self._chat_log_widget:
                self._chat_log_widget.debug(message)  # Amarelo

    def error(self, message: str, **kwargs):
        """Log error."""
        self._write_to_file(f"[ERROR] {message}\n", "CHAT")

        # Tenta LogConsumer (ChatLog 2.0) primeiro
        if not self._write_to_consumer(logging.ERROR, message):
            # Fallback para widget legado
            if self._show_in_ui and self._chat_log_widget:
                self._chat_log_widget.error(message)

    def evento(self, nome: str, dados: str = ""):
        """Log de evento (verde no ChatLog).

        NOTA: Este método está DEPRECATED. Use info() com context={"type": "event", ...}
        Mantido por compatibilidade com código existente.
        """
        msg = f"{nome} {dados}".strip()
        self._write_to_file(f"[EVENT] {msg}\n", "CHAT")

        # Tenta LogConsumer (ChatLog 2.0) com context apropriado
        if not self._write_to_consumer(
            logging.INFO,
            msg,
            context={"type": "event", "event_name": nome, "event_data": dados}
        ):
            # Fallback para widget legado
            if self._show_in_ui and self._chat_log_widget:
                self._chat_log_widget.evento(nome, dados)

    def structured(self, message: str, data: dict, level: str = "info"):
        """Log estruturado."""
        data_str = json.dumps(data, ensure_ascii=False, default=str)
        log_msg = f"{message} {data_str}"

        self._write_to_file(f"[{level.upper()}] {log_msg}\n", "CHAT")

        if self._show_in_ui and self._chat_log_widget:
            if level == "error":
                self._chat_log_widget.error(log_msg)
            elif level == "warning":
                self._chat_log_widget.debug(log_msg)
            elif level == "info":
                self._chat_log_widget.info(log_msg)
            else:
                self._chat_log_widget.debug(log_msg)

    @property
    def session_id(self) -> str:
        """Retorna ID da sessão."""
        return self._session_id

    def __enter__(self):
        """Context manager entry."""
        return self

    def __exit__(self, *args):
        """Context manager exit."""
        self.restore()


# Singleton global
_chat_logger: Optional[ChatLogger] = None


def get_chat_logger(**kwargs) -> ChatLogger:
    """Retorna instância do ChatLogger (singleton ou nova)."""
    global _chat_logger
    if _chat_logger is None:
        _chat_logger = ChatLogger(**kwargs)
    return _chat_logger


def restore_chat_logger():
    """Restaura stdout/stderr e encerra ChatLogger."""
    global _chat_logger
    if _chat_logger:
        _chat_logger.restore()
        _chat_logger = None


__all__ = [
    "ChatLogger",
    "get_chat_logger",
    "restore_chat_logger",
]
