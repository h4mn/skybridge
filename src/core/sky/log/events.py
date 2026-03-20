# coding: utf-8
"""
Eventos do subsistema de log.

Mensagens emitidas pelos widgets de log para comunicação
entre componentes.
"""

from textual.message import Message

from core.sky.log.entry import LogEntry


class VisibleEntriesChanged(Message):
    """Mensagem emitida quando as entries visíveis mudam."""

    bubble = True

    def __init__(self, entries: list[LogEntry]) -> None:
        """Inicializa mensagem.

        Args:
            entries: Lista de entries visíveis (após filtros)
        """
        super().__init__()
        self.entries = entries


__all__ = ["VisibleEntriesChanged"]
