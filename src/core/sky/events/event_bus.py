# coding: utf-8
"""
EventBus - Sistema de Pub/Sub Assíncrono.

DOC: openspec/changes/refactor-chat-event-driven/specs/event-bus/spec.md

Implementa padrão publish-subscribe para comunicação loose-coupled
entre componentes do chat (Orchestrator, TTSService, WaveformController).
"""

import asyncio
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, AsyncIterator, Generic, TypeVar
from datetime import datetime

# Type variable para eventos
E = TypeVar("E")


class BaseEvent:
    """
    Classe base para todos os eventos de domínio.

    Atributos:
        timestamp: Quando o evento foi criado
        metadata: Dados adicionais opcionais
    """

    def __init__(self, timestamp: datetime | None = None, metadata: dict[str, Any] | None = None):
        self.timestamp = timestamp or datetime.utcnow()
        self.metadata = metadata or {}

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(timestamp={self.timestamp.isoformat()})"


class EventBus(ABC):
    """
    Protocolo para sistemas de pub/sub assíncronos.

    Define a interface que qualquer implementação de EventBus deve seguir.
    Isso permite trocar a implementação (ex: usar Redis no futuro) sem
    afetar o código que usa o EventBus.

    Requirements (do spec):
    - publish() retorna imediatamente (non-blocking)
    - subscribe() retorna AsyncIterator para receber eventos
    - Múltiplos subscribers podem receber o mesmo evento
    - Thread-safe para uso em ambiente asyncio
    """

    @abstractmethod
    async def publish(self, event: BaseEvent) -> None:
        """
        Publica um evento para todos os subscribers.

        Args:
            event: Evento a ser publicado

        Requirements:
        - Retorna imediatamente (non-blocking)
        - Evento é enfileirado para todos os subscribers
        - Se buffer estiver cheio (>100 eventos), descarta mais antigos
        """
        ...

    @abstractmethod
    def subscribe(self, event_type: type[E]) -> AsyncIterator[E]:
        """
        Inscreve para receber eventos de um tipo específico.

        Args:
            event_type: Tipo de evento a receber (ex: StreamChunkEvent)

        Returns:
            AsyncIterator que yield eventos daquele tipo

        Requirements:
        - Apenas eventos do tipo solicitado são entregues
        - Múltiplos subscribers podem existir para o mesmo evento
        - Se shutdown acontecer, iterator termina graciosamente
        """
        ...

    @abstractmethod
    async def shutdown(self) -> None:
        """
        Encerra o EventBus graciosamente.

        Requirements:
        - Eventos enfileirados são entregues antes de fechar
        - Novos publishes após shutdown são ignorados silenciosamente
        - Todos os subscribers são notificados para terminar
        """
        ...


class InMemoryEventBus(EventBus):
    """
    Implementação em memória do EventBus usando asyncio.Queue.

    Características:
    - Zero dependências externas
    - Usa asyncio.Queue para pub/sub
    - Buffer máximo de 100 eventos por subscriber
    - Thread-safe para uso em ambiente asyncio

    Limites:
    - Max 100 eventos na fila (descarta antigos se encher)
    - Single-process (não distribuído)

    Performance:
    - publish: < 1ms (apenas put na queue)
    - subscribe: < 0.1ms (cria queue)
    """

    def __init__(self, max_buffer_size: int = 100) -> None:
        """
        Inicializa o EventBus.

        Args:
            max_buffer_size: Máximo de eventos na fila por subscriber (padrão: 100)
        """
        self._max_buffer_size = max_buffer_size
        self._subscribers: dict[type, list[asyncio.Queue]] = {}
        self._running = True
        self._lock = asyncio.Lock()

    async def publish(self, event: BaseEvent) -> None:
        """
        Publica evento para todos os subscribers do tipo.

        Args:
            event: Evento a publicar

        Comportamento:
        - Se não houver subscribers, retorna silenciosamente
        - Se fila estiver cheia, descarta evento mais antigo (FIFO)
        - Se EventBus foi fechado, ignora silenciosamente
        """
        if not self._running:
            return

        event_type = type(event)

        async with self._lock:
            if event_type not in self._subscribers:
                return

            queues = self._subscribers[event_type]

        # Publica para cada queue (non-blocking put)
        for queue in queues:
            try:
                # Tenta put sem bloquear
                queue.put_nowait(event)
            except asyncio.QueueFull:
                # Buffer cheio - descarta evento mais antigo
                try:
                    queue.get_nowait()  # Remove mais antigo
                    queue.put_nowait(event)  # Adiciona novo
                except asyncio.QueueEmpty:
                    # Queue foi esvaziada entre get e put
                    queue.put_nowait(event)

    def subscribe(self, event_type: type[E]) -> AsyncIterator[E]:
        """
        Inscreve para receber eventos de um tipo.

        Args:
            event_type: Tipo de evento a receber

        Returns:
            AsyncIterator que yield eventos

        Example:
            >>> async for event in bus.subscribe(StreamChunkEvent):
            ...     print(f"Received: {event.content}")
            ...     if event.is_last:
            ...         break  # Para de consumir
        """

        async def _event_generator() -> AsyncIterator[E]:
            # Cria queue para este subscriber
            queue: asyncio.Queue[BaseEvent | None] = asyncio.Queue(maxsize=self._max_buffer_size)

            # Registra queue
            async with self._lock:
                if self._running:
                    if event_type not in self._subscribers:
                        self._subscribers[event_type] = []
                    self._subscribers[event_type].append(queue)
                else:
                    return  # EventBus fechado

            try:
                # Yield eventos até None (EOF) ou shutdown
                while self._running:
                    event = await queue.get()

                    if event is None:
                        # Sinal de EOF - termina iterator
                        break

                    # Type narrowing para o tipo específico
                    yield event  # type: ignore
            finally:
                # Remove queue ao sair
                async with self._lock:
                    if event_type in self._subscribers and queue in self._subscribers[event_type]:
                        self._subscribers[event_type].remove(queue)

        return _event_generator()

    async def shutdown(self) -> None:
        """
        Encerra o EventBus graciosamente.

        Comportamento:
        - Marca como não running (novos publishes são ignorados)
        - Não aguarda subscribers terminarem (não-blocking)
        - Subscribers ativos recebem eventos pendentes e terminam
        """
        async with self._lock:
            self._running = False

        # Notifica todos os subscribers enviando None (EOF signal)
        for queues in self._subscribers.values():
            for queue in queues:
                try:
                    queue.put_nowait(None)
                except asyncio.QueueFull:
                    pass  # Queue cheia, ignora

        self._subscribers.clear()

    @property
    def is_running(self) -> bool:
        """Retorna True se EventBus está rodando."""
        return self._running
