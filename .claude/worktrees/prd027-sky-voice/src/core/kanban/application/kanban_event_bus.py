# -*- coding: utf-8 -*-
"""
Kanban EventBus - Sistema de pub/sub para eventos em tempo real.

DOC: PRD024 Task 7 - SSE com eventos dinâmicos
DOC: ADR024 - Workspace isolation

Este módulo implementa um EventBus simples que permite que operações
CRUD no Kanban emitam eventos que são consumidos pelos clientes SSE.

Cada workspace tem seu próprio bus para isolamento (ADR024).
"""
import asyncio
from dataclasses import dataclass, field
from typing import Any, Dict
from datetime import datetime
import json
import logging

logger = logging.getLogger(__name__)


@dataclass
class KanbanEvent:
    """Evento de domínio do Kanban."""

    event_type: str  # card_created, card_updated, card_deleted, etc.
    data: Dict[str, Any]
    workspace_id: str
    timestamp: datetime = field(default_factory=datetime.utcnow)

    def to_sse_format(self) -> str:
        """Converte evento para formato SSE."""
        return f"event: {self.event_type}\ndata: {json.dumps(self.data)}\n\n"


class KanbanEventBus:
    """
    EventBus para eventos Kanban com isolamento por workspace.

    Gerencia filas de eventos por workspace, permitindo que clientes SSE
    se inscrevam para receber eventos em tempo real.

    Uso:
        bus = KanbanEventBus.get_instance()

        # Publicar evento
        await bus.publish("card_created", {"id": "123"}, workspace_id="core")

        # Consumir eventos
        async for event in bus.subscribe("core"):
            yield event.to_sse_format()
    """

    _instance: "KanbanEventBus | None" = None
    _lock = asyncio.Lock()

    def __init__(self):
        # workspace_id -> asyncio.Queue[KanbanEvent]
        self._queues: Dict[str, asyncio.Queue] = {}
        self._subscribers_count: Dict[str, int] = {}

    @classmethod
    def get_instance(cls) -> "KanbanEventBus":
        """Retorna instância singleton do EventBus."""
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def _get_or_create_queue(self, workspace_id: str) -> asyncio.Queue:
        """Retorna fila para o workspace, criando se necessário."""
        if workspace_id not in self._queues:
            self._queues[workspace_id] = asyncio.Queue(maxsize=1000)
            self._subscribers_count[workspace_id] = 0
            logger.debug(f"[KanbanEventBus] Criada fila para workspace: {workspace_id}")
        return self._queues[workspace_id]

    async def publish(self, event_type: str, data: Dict[str, Any], workspace_id: str) -> None:
        """
        Publica evento no bus.

        Args:
            event_type: Tipo do evento (card_created, card_updated, etc)
            data: Dados do evento (será serializado para JSON)
            workspace_id: ID do workspace (ADR024)
        """
        event = KanbanEvent(
            event_type=event_type,
            data=data,
            workspace_id=workspace_id
        )

        queue = self._get_or_create_queue(workspace_id)

        try:
            # Não bloqueia se fila estiver cheia (descarta evento antigo)
            queue.put_nowait(event)
            logger.debug(f"[KanbanEventBus] Evento publicado: {event_type} (workspace={workspace_id})")
        except asyncio.QueueFull:
            logger.warning(f"[KanbanEventBus] Fila cheia para workspace {workspace_id}, evento descartado")

    async def subscribe(self, workspace_id: str) -> KanbanEvent:
        """
        Generator que yield eventos de um workspace.

        Args:
            workspace_id: ID do workspace para ouvir eventos

        Yields:
            KanbanEvent: Eventos do workspace em tempo real

        Usage:
            async for event in bus.subscribe("core"):
                yield event.to_sse_format()
        """
        queue = self._get_or_create_queue(workspace_id)
        self._subscribers_count[workspace_id] += 1

        logger.info(f"[KanbanEventBus] Novo subscriber para workspace: {workspace_id} (total: {self._subscribers_count[workspace_id]})")

        try:
            while True:
                # Aguarda próximo evento (timeout para permitir heartbeat)
                try:
                    event = await asyncio.wait_for(queue.get(), timeout=1.0)
                    yield event
                except asyncio.TimeoutError:
                    # Timeout normal - permite enviar heartbeat no SSE
                    continue
        finally:
            self._subscribers_count[workspace_id] -= 1
            logger.info(f"[KanbanEventBus] Subscriber removido para workspace: {workspace_id}")

    def get_subscribers_count(self, workspace_id: str) -> int:
        """Retorna número de subscribers ativos para um workspace."""
        return self._subscribers_count.get(workspace_id, 0)
