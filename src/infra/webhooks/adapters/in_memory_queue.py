# -*- coding: utf-8 -*-
"""
In-Memory Job Queue Adapter.

Implementação em memória do JobQueuePort para MVP (Phase 1).

Limitações:
- Jobs são perdidos se o processo terminar
- Não escala horizontalmente
- Sem persistência

Para produção (Phase 3), migrar para RedisJobQueue.
"""
from __future__ import annotations

import asyncio
from collections import deque
from datetime import datetime
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from core.webhooks.domain import WebhookJob
    from core.webhooks.ports.job_queue_port import JobQueuePort

from core.webhooks.ports.job_queue_port import QueueError, JobQueuePort


class InMemoryJobQueue(JobQueuePort):
    """
    Fila de jobs em memória usando collections.deque.

    Thread-safe para uso com asyncio (single-threaded event loop).

    Attributes:
        _queue: Fila de jobs aguardando processamento
        _jobs: Dicionário de todos os jobs por ID
        _queue_event: Evento para sinalizar novos jobs
    """

    def __init__(self) -> None:
        """Inicializa fila vazia."""
        self._queue: deque[WebhookJob] = deque()
        self._jobs: dict[str, WebhookJob] = {}
        self._queue_event = asyncio.Event()

    async def enqueue(self, job: "WebhookJob") -> str:
        """
        Adiciona job à fila.

        Args:
            job: Job a ser enfileirado

        Returns:
            job_id do job enfileirado

        Raises:
            QueueError: Se job_id já existe
        """
        if job.job_id in self._jobs:
            raise QueueError(f"Job {job.job_id} já existe na fila")

        self._queue.append(job)
        self._jobs[job.job_id] = job
        self._queue_event.set()  # Sinaliza que há jobs
        self._queue_event.clear()

        return job.job_id

    async def dequeue(self) -> "WebhookJob | None":
        """
        Remove próximo job da fila.

        Returns:
            Próximo job ou None se fila vazia

        Note:
            Este método não bloqueia. Para wait com timeout,
            use wait_for_dequeue().
        """
        if not self._queue:
            return None
        return self._queue.popleft()

    async def wait_for_dequeue(self, timeout: float | None = None) -> "WebhookJob | None":
        """
        Aguarda até que haja um job disponível e o remove.

        Args:
            timeout: Tempo máximo de espera em segundos

        Returns:
            Próximo job ou None se timeout
        """
        try:
            if not self._queue:
                # Aguarda sinal de novo job
                await asyncio.wait_for(self._queue_event.wait(), timeout)
            return await self.dequeue()
        except asyncio.TimeoutError:
            return None

    async def get_job(self, job_id: str) -> "WebhookJob | None":
        """
        Busca job por ID.

        Args:
            job_id: ID do job

        Returns:
            Job encontrado ou None
        """
        return self._jobs.get(job_id)

    async def complete(self, job_id: str, result: dict | None = None) -> None:
        """
        Marca job como completado.

        Args:
            job_id: ID do job
            result: Resultado opcional (não usado na impl em memória)
        """
        job = self._jobs.get(job_id)
        if job:
            job.mark_completed()

    async def fail(self, job_id: str, error: str) -> None:
        """
        Marca job como falhou.

        Args:
            job_id: ID do job
            error: Mensagem de erro
        """
        job = self._jobs.get(job_id)
        if job:
            job.mark_failed(error)

    def size(self) -> int:
        """
        Retorna tamanho atual da fila.

        Returns:
            Número de jobs aguardando processamento
        """
        return len(self._queue)

    def get_all_jobs(self) -> dict[str, "WebhookJob"]:
        """
        Retorna todos os jobs (útil para debug/observabilidade).

        Returns:
            Dicionário de job_id → WebhookJob
        """
        return self._jobs.copy()

    def clear(self) -> None:
        """Remove todos os jobs da fila (útil para testes)."""
        self._queue.clear()
        self._jobs.clear()
