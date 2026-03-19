# coding: utf-8
"""
Subsistema de log Sky.

Módulo para gerenciamento de logs com:
- Protocol simples para consumidores (LogConsumer)
- Entry imutável com logging padrão Python
- Filtro por nível e escopo
- Clipboard vendorizado
- Widgets Textual com tema cyberpunk toggleável
"""

from core.sky.log.chatlog import ChatLog, ChatLogConfig
from core.sky.log.entry import LogEntry
from core.sky.log.protocol import LogConsumer
from core.sky.log.scope import LogScope

# Widgets são importados sob demanda para evitar dependências Textual desnecessárias
# from core.sky.log.widgets import LogFilter, FilterChanged, LogSearch, LogCopier, LogToolbar

__all__ = [
    "LogEntry",
    "LogConsumer",
    "LogScope",
    "ChatLog",
    "ChatLogConfig",
]
