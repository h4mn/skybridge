# coding: utf-8
"""
Subsistema de log Sky.

Módulo para gerenciamento de logs com:
- Protocol simples para consumidores (LogConsumer)
- Entry imutável com logging padrão Python
- Filtro por nível e escopo
- Clipboard vendorizado
- Widgets Textual para busca, filtro e cópia

Classes Principais:
    ChatLog: Widget principal de log com ring buffer e virtualização
    ChatLogConfig: Configuração do ChatLog (max_entries, virtualização, etc.)
    LogEntry: Entry de log imutável (level, message, timestamp, scope, context)
    LogConsumer: Protocol para consumidores de log
    LogScope: Enum de escopos (ALL, SYSTEM, USER, API, DATABASE, NETWORK, VOICE, MEMORY)

Widgets:
    LogFilter: Filtro combinado por nível e escopo
    LogSearch: Busca reativa com highlight
    LogCopier: Cópia de logs para clipboard
    LogToolbar: Container agrupando Filter, Search e Copier

Uso Básico:
    >>> from core.sky.log import ChatLog, ChatLogConfig, LogEntry, LogScope
    >>> import logging
    >>>
    >>> # Criar ChatLog com configuração
    >>> chat_log = ChatLog(config=ChatLogConfig(max_entries=1000))
    >>>
    >>> # Escrever logs
    >>> entry = LogEntry(
    ...     level=logging.INFO,
    ...     message="Sistema iniciado",
    ...     timestamp=datetime.now(),
    ...     scope=LogScope.SYSTEM
    ... )
    >>> chat_log.write_log(entry)

Integração com ChatLogger:
    >>> from core.sky.chat.logging import ChatLogger
    >>>
    >>> chat_logger = ChatLogger(log_consumer=chat_log)
    >>> chat_logger.info("Mensagem via ChatLogger")
"""

from core.sky.log.chatlog import ChatLog, ChatLogConfig
from core.sky.log.entry import LogEntry
from core.sky.log.protocol import LogConsumer
from core.sky.log.scope import LogScope

# Widgets - exports públicos
from core.sky.log.widgets.filter import LogFilter, FilterChanged
from core.sky.log.widgets.search import LogSearch, SearchChanged
from core.sky.log.widgets.copier import LogCopier
from core.sky.log.widgets.toolbar import LogToolbar

__all__ = [
    # Core
    "LogEntry",
    "LogConsumer",
    "LogScope",
    "ChatLog",
    "ChatLogConfig",
    # Widgets
    "LogFilter",
    "FilterChanged",
    "LogSearch",
    "SearchChanged",
    "LogCopier",
    "LogToolbar",
]
