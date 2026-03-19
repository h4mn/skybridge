# coding: utf-8
"""
LogConsumer - Protocol para consumidores de log.

Define interface simples para escrita de logs. Qualquer classe
que implemente write_log(entry: LogEntry) pode ser usada como consumidor.
"""

from typing import Protocol

from core.sky.log.entry import LogEntry


class LogConsumer(Protocol):
    """Protocol para consumidores de log.

    Define interface simples para escrita de logs.
    Qualquer classe que implemente write_log(entry: LogEntry) pode
    ser usada como consumidor.

    Example:
        >>> class MyConsumer:
        ...     def write_log(self, entry: LogEntry) -> None:
        ...         print(entry.message)
        ...
        >>> consumer: LogConsumer = MyConsumer()
        >>> consumer.write_log(LogEntry(...))
    """

    def write_log(self, entry: LogEntry) -> None:
        """Escreve um log entry.

        Args:
            entry: LogEntry contendo nível, mensagem, timestamp, escopo e contexto
        """
        ...


__all__ = ["LogConsumer"]
