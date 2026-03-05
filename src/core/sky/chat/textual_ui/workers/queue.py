# coding: utf-8
"""
Fila de comunicação Worker ↔ UI.

Sistema de fila para comunicação thread-safe entre
workers assíncronos e a UI Textual.
"""

import asyncio
from dataclasses import dataclass
from enum import Enum
from typing import Any, Awaitable


class WorkerEventType(Enum):
    """Tipos de eventos da fila."""
    CLAUDE_RESPONSE = "claude_response"
    RAG_RESPONSE = "rag_response"
    MEMORY_SAVED = "memory_saved"
    TOOL_EXECUTED = "tool_executed"
    ERROR = "error"


@dataclass
class WorkerEvent:
    """Evento na fila de comunicação."""

    event_type: WorkerEventType
    data: Any
    timestamp: float


class WorkerQueue:
    """
    Fila para comunicação worker ↔ UI.

    Permite que workers enviem atualizações para a UI
    de forma thread-safe.
    """

    def __init__(self) -> None:
        """Inicializa WorkerQueue."""
        self._queue: asyncio.Queue[WorkerEvent] = asyncio.Queue()

    async def put(self, event_type: WorkerEventType, data: Any) -> None:
        """
        Coloca um evento na fila.

        Args:
            event_type: Tipo do evento.
            data: Dados do evento.
        """
        import time

        event = WorkerEvent(
            event_type=event_type,
            data=data,
            timestamp=time.time(),
        )
        await self._queue.put(event)

    async def get(self) -> WorkerEvent:
        """
        Retorna o próximo evento da fila (bloqueia se vazio).

        Returns:
            WorkerEvent com o evento.
        """
        return await self._queue.get()

    def task_done(self) -> None:
        """Marca o processamento do evento como completo."""
        self._queue.task_done()


__all__ = ["WorkerQueue", "WorkerEvent", "WorkerEventType"]
