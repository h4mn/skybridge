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
from datetime import datetime, timedelta
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
        _delivery_ids: Dict de delivery_id → timestamp (para TTL)
    """

    def __init__(self, ttl_hours: int = 24) -> None:
        """
        Inicializa fila vazia.

        Args:
            ttl_hours: Tempo de vida dos delivery IDs em horas (padrão: 24h)
        """
        self._queue: deque[WebhookJob] = deque()
        self._jobs: dict[str, WebhookJob] = {}
        self._queue_event = asyncio.Event()
        self._delivery_ids: dict[str, datetime] = {}  # delivery_id → timestamp
        self._ttl = timedelta(hours=ttl_hours)

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

        # Cleanup de deliveries expirados antes de processar
        self._cleanup_expired_deliveries()

        self._queue.append(job)
        self._jobs[job.job_id] = job

        # Registra delivery_id com timestamp atual
        if job.event.delivery_id:
            self._delivery_ids[job.event.delivery_id] = datetime.utcnow()

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
        self._delivery_ids.clear()

    def _cleanup_expired_deliveries(self) -> None:
        """
        Remove delivery IDs expirados para evitar memory leak.

        Deliveries mais antigos que o TTL são removidos automaticamente.
        Isso é chamado automaticamente no enqueue().
        """
        if not self._delivery_ids:
            return

        now = datetime.utcnow()
        expired = [
            delivery_id
            for delivery_id, timestamp in self._delivery_ids.items()
            if now - timestamp > self._ttl
        ]

        for delivery_id in expired:
            del self._delivery_ids[delivery_id]

        if expired:
            from core.webhooks.application.webhook_processor import logger
            logger.debug(f"Cleanup: removidos {len(expired)} delivery IDs expirados")

    async def exists_by_delivery(self, delivery_id: str) -> bool:
        """
        Verifica se já existe job com este delivery ID.

        Args:
            delivery_id: ID único da entrega do webhook

        Returns:
            True se job com este delivery_id já existe, False caso contrário
        """
        # Cleanup antes de verificar
        self._cleanup_expired_deliveries()

        return delivery_id in self._delivery_ids

    async def list_jobs(
        self,
        limit: int = 100,
        status_filter: str | None = None,
    ) -> list[dict[str, object]]:
        """
        Lista jobs da fila para o WebUI.

        Args:
            limit: Número máximo de jobs a retornar
            status_filter: Filtrar por status (opcional)

        Returns:
            Lista de dicionários com dados dos jobs no formato esperado pelo frontend
        """
        jobs_list = []
        count = 0

        # Itera sobre os jobs em ordem reversa (mais recentes primeiro)
        for job in reversed(list(self._jobs.values())):
            if count >= limit:
                break

            # Aplica filtro de status se especificado
            if status_filter and job.status.value != status_filter.lower():
                continue

            jobs_list.append({
                "job_id": job.job_id,
                "source": job.event.source.value,
                "event_type": job.event.event_type,
                "status": job.status.value.upper(),
                "created_at": job.created_at.isoformat(),
                "worktree_path": job.worktree_path,
            })
            count += 1

        return jobs_list

    async def update_metadata(self, job_id: str, metadata: dict[str, object]) -> None:
        """
        Atualiza metadata de um job.

        Args:
            job_id: ID do job
            metadata: Novo metadata (será mesclado com o existente)
        """
        job = self._jobs.get(job_id)
        if job:
            # Atualiza worktree_path se presente no metadata
            if "worktree_path" in metadata:
                job.worktree_path = str(metadata["worktree_path"])
            # Atualiza branch_name se presente
            if "branch_name" in metadata:
                job.branch_name = str(metadata["branch_name"])
            # Mescla com metadata existente
            job.metadata.update(metadata)
