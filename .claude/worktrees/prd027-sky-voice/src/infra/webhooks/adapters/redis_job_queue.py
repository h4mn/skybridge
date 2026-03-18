# -*- coding: utf-8 -*-
"""
Redis Job Queue Adapter for DragonflyDB/Redis.

PRD018 Fase 2 - INFRA-06/07/08: RedisJobQueue Adapter.

Implements JobQueuePort using redis-py with DragonflyDB.
"""

from __future__ import annotations

import json
import logging
from datetime import datetime
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from core.webhooks.domain import WebhookJob

from core.webhooks.ports.job_queue_port import JobQueuePort

logger = logging.getLogger(__name__)


class RedisJobQueue(JobQueuePort):
    """
    Redis-based job queue using redis-py.

    Compatible with DragonflyDB and traditional Redis.
    Uses the following structure:
    - skybridge:jobs:queue → List (LPUSH/BRPOP)
    - skybridge:jobs:{job_id} → Hash (job data)
    - skybridge:jobs:processing → Set (jobs in progress)
    - skybridge:jobs:completed → Set (completed jobs)
    - skybridge:jobs:failed → Set (failed jobs)
    """

    # Key prefixes
    QUEUE_KEY = "skybridge:jobs:queue"
    JOB_DATA_PREFIX = "skybridge:jobs:"
    PROCESSING_KEY = "skybridge:jobs:processing"
    COMPLETED_KEY = "skybridge:jobs:completed"
    FAILED_KEY = "skybridge:jobs:failed"
    METRICS_PREFIX = "skybridge:metrics:"

    def __init__(
        self,
        host: str = "localhost",
        port: int = 6379,
        db: int = 0,
        decode_responses: bool = False,
    ):
        """
        Inicializa Redis job queue.

        Args:
            host: Redis host
            port: Redis port
            db: Redis database number
            decode_responses: Decode bytes to strings automatically
        """
        self._host = host
        _port = port
        self._db = db
        self._decode_responses = decode_responses

        # Lazy import - redis só é necessário quando este adapter é usado
        try:
            import redis
            self._redis_client = redis.Redis(
                host=host,
                port=port,
                db=db,
                decode_responses=decode_responses,
                socket_connect_timeout=5,
                socket_timeout=5,
                retry_on_timeout=True,
            )
            # Test connection
            self._redis_client.ping()
            logger.info(f"RedisJobQueue conectado a {host}:{port}")
        except ImportError:
            raise ImportError(
                "Package 'redis' não instalado. Execute: pip install redis"
            )
        except Exception as e:
            raise ConnectionError(
                f"Falha ao conectar ao Redis/DragonflyDB em {host}:{port}: {e}"
            )

    async def enqueue(self, job: "WebhookJob") -> None:
        """
        Adiciona job à fila.

        Args:
            job: WebhookJob para enfileirar
        """
        job_dict = job.to_dict()

        # Armazenar dados do job (Hash)
        job_key = f"{self.JOB_DATA_PREFIX}{job.job_id}"
        self._redis_client.hset(
            job_key,
            mapping={
                "job_id": job.job_id,
                "correlation_id": job.correlation_id,
                "created_at": job.created_at.isoformat(),
                "status": job.status.value,
                "payload": json.dumps(job.event.payload),
                "metadata": json.dumps(job.metadata),
            },
        )

        # Adicionar à fila (Lista)
        self._redis_client.lpush(self.QUEUE_KEY, job.job_id)

        # Registrar métrica
        self._increment_metric("jobs_enqueued")

        logger.info(f"Job {job.job_id} enfileirado no Redis")

    async def dequeue(
        self, timeout_seconds: float = 1.0
    ) -> "WebhookJob | None":
        """
        Remove job da fila (bloqueia até timeout).

        Args:
            timeout_seconds: Tempo máximo de espera

        Returns:
            WebhookJob ou None se timeout
        """
        # BRPOP bloqueia até timeout ou item disponível
        result = self._redis_client.brpop(
            self.QUEUE_KEY, timeout=int(timeout_seconds)
        )

        if not result:
            return None

        job_id = result[1]  # BRPOP retorna (queue_name, job_id)

        # Buscar dados do job
        job_key = f"{self.JOB_DATA_PREFIX}{job_id}"
        job_data = self._redis_client.hgetall(job_key)

        if not job_data:
            logger.warning(f"Job {job_id} não encontrado no Redis")
            return None

        # Marcar como em processamento
        self._redis_client.sadd(self.PROCESSING_KEY, job_id)

        # Carregar dependências
        from core.webhooks.domain import WebhookJob, WebhookEvent

        # Reconstruir job
        job = WebhookJob(
            job_id=job_data.get("job_id"),
            correlation_id=job_data.get("correlation_id"),
            created_at=datetime.fromisoformat(job_data.get("created_at")),
            event=WebhookEvent(
                source=job_data.get("event_source"),
                event_type=job_data.get("event_type"),
                event_id=job_data.get("event_id"),
                payload=json.loads(job_data.get("payload")),
                received_at=datetime.fromisoformat(job_data.get("created_at")),
            ),
            metadata=json.loads(job_data.get("metadata", "{}")),
        )

        logger.info(f"Job {job_id} desenfileirado do Redis")
        return job

    async def get_job(self, job_id: str) -> "WebhookJob | None":
        """
        Busca job por ID.

        Args:
            job_id: ID do job

        Returns:
            WebhookJob ou None se não encontrado
        """
        job_key = f"{self.JOB_DATA_PREFIX}{job_id}"
        job_data = self._redis_client.hgetall(job_key)

        if not job_data:
            return None

        # Carregar dependências
        from core.webhooks.domain import WebhookJob, WebhookEvent

        # Reconstruir job
        job = WebhookJob(
            job_id=job_data.get("job_id"),
            correlation_id=job_data.get("correlation_id"),
            created_at=datetime.fromisoformat(job_data.get("created_at")),
            event=WebhookEvent(
                source=job_data.get("event_source"),
                event_type=job_data.get("event_type"),
                event_id=job_data.get("event_id"),
                payload=json.loads(job_data.get("payload")),
                received_at=datetime.fromisoformat(job_data.get("created_at")),
            ),
            metadata=json.loads(job_data.get("metadata", "{}")),
        )

        return job

    async def update_status(
        self,
        job_id: str,
        status: "str",
        result: dict | None = None,
    ) -> None:
        """
        Atualiza status do job.

        Args:
            job_id: ID do job
            status: Novo status
            result: Dados do resultado (opcional)
        """
        job_key = f"{self.JOB_DATA_PREFIX}{job_id}"

        # Atualizar Hash
        self._redis_client.hset(job_key, "status", status)

        # Mover entre sets conforme status
        self._redis_client.srem(self.PROCESSING_KEY, job_id)

        if status == "completed":
            self._redis_client.sadd(self.COMPLETED_KEY, job_id)
            self._increment_metric("jobs_completed")
        elif status == "failed":
            self._redis_client.sadd(self.FAILED_KEY, job_id)
            self._increment_metric("jobs_failed")

        # Armazenar resultado se fornecido
        if result:
            self._redis_client.hset(
                job_key,
                "result",
                json.dumps(result)
            )

        logger.info(f"Job {job_id} status atualizado para {status}")

    async def complete(self, job_id: str, result: dict | None = None) -> None:
        """Marca job como completado."""
        await self.update_status(job_id, "completed", result)

    async def fail(self, job_id: str, error: str) -> None:
        """Marca job como falhou."""
        await self.update_status(
            job_id,
            "failed",
            result={"error": error, "failed_at": datetime.utcnow().isoformat()},
        )

    async def exists_by_delivery(self, delivery_id: str) -> bool:
        """
        Verifica se job com delivery_id já foi processado.

        Args:
            delivery_id: ID de entrega do webhook

        Returns:
            True se já processado, False caso contrário
        """
        key = f"{self.METRICS_PREFIX}delivery:{delivery_id}"
        return self._redis_client.exists(key) == 1

    async def mark_delivery_processed(self, delivery_id: str, job_id: str) -> None:
        """
        Marca delivery como processado.

        Args:
            delivery_id: ID de entrega
            job_id: ID do job processado
        """
        key = f"{self.METRICS_PREFIX}delivery:{delivery_id}"
        # Expira em 24 horas
        self._redis_client.setex(key, 86400, job_id)

    async def get_metrics(self) -> dict[str, object]:
        """
        Retorna métricas da fila.

        Returns:
            Dicionário com métricas
        """
        queue_size = self._redis_client.llen(self.QUEUE_KEY)
        processing_size = self._redis_client.scard(self.PROCESSING_KEY)
        completed_size = self._redis_client.scard(self.COMPLETED_KEY)
        failed_size = self._redis_client.scard(self.FAILED_KEY)

        # Buscar métricas registradas
        jobs_enqueued = int(self._redis_client.get(f"{self.METRICS_PREFIX}jobs_enqueued") or 0)
        jobs_completed = int(self._redis_client.get(f"{self.METRICS_PREFIX}jobs_completed") or 0)
        jobs_failed = int(self._redis_client.get(f"{self.METRICS_PREFIX}jobs_failed") or 0)

        return {
            "queue_size": queue_size,
            "processing": processing_size,
            "completed": completed_size,
            "failed": failed_size,
            "total_enqueued": jobs_enqueued,
            "total_completed": jobs_completed,
            "total_failed": jobs_failed,
            "success_rate": jobs_completed / jobs_enqueued if jobs_enqueued > 0 else 0.0,
        }

    def _increment_metric(self, metric_name: str) -> None:
        """Incrementa uma métrica."""
        key = f"{self.METRICS_PREFIX}{metric_name}"
        self._redis_client.incr(key)

    async def close(self) -> None:
        """Fecha conexão com Redis."""
        self._redis_client.close()
        logger.info("RedisJobQueue fechado")
