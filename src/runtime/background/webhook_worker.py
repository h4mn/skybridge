# -*- coding: utf-8 -*-
"""
Webhook Background Worker.

Worker assíncrono que processa jobs de webhook em background.

O worker é iniciado automaticamente pelo bootstrap da API (bootstrap/app.py)
e compartilha a mesma fila de jobs (JobQueuePort) configurada via JobQueueFactory.
"""
from __future__ import annotations

import asyncio
import signal
import sys

from core.webhooks.application.job_orchestrator import (
    JobOrchestrator,
)
from core.webhooks.application.worktree_manager import (
    WorktreeManager,
)
from core.webhooks.ports.job_queue_port import JobQueuePort
from runtime.config.config import get_webhook_config, get_trello_config
from runtime.observability.logger import get_logger

logger = get_logger()


class WebhookWorker:
    """
    Worker para processamento de webhooks em background.

    Responsabilidades:
    - Poll job queue continuamente
    - Executar jobs via JobOrchestrator
    - Handle erros gracefully
    - Shutdown gracefully

    Attributes:
        job_queue: Fila de jobs
        orchestrator: Orquestrador de jobs
        poll_interval: Intervalo entre polls (segundos)
    """

    def __init__(
        self,
        job_queue: JobQueuePort,
        orchestrator: JobOrchestrator,
        poll_interval: float = 1.0,
    ):
        """
        Inicializa worker.

        Args:
            job_queue: Fila de jobs
            orchestrator: Orquestrador de jobs
            poll_interval: Intervalo entre polls em segundos
        """
        self.job_queue = job_queue
        self.orchestrator = orchestrator
        self.poll_interval = poll_interval
        self._running = False
        self._shutdown_event = asyncio.Event()

    async def start(self) -> None:
        """Inicia loop de processamento."""
        self._running = True
        logger.info("Worker de webhook iniciado")

        while self._running:
            try:
                # Tenta desenfileir job
                job = await self.job_queue.dequeue()

                if job:
                    logger.info(
                        f"Processando job {job.job_id}",
                        extra={
                            "job_id": job.job_id,
                            "source": str(job.event.source),  # Conversão para string (SQLite salva como string)
                            "event_type": job.event.event_type,
                        },
                    )

                    # Executa job
                    result = await self.orchestrator.execute_job(job.job_id)

                    if result.is_ok:
                        logger.info(
                            f"Job {job.job_id} completado",
                            extra={"job_id": job.job_id},
                        )
                    else:
                        logger.error(
                            f"Job {job.job_id} falhou: {result.error}",
                            extra={"job_id": job.job_id},
                        )
                else:
                    # Sem jobs por enquanto, aguarda antes de tentar novamente
                    if self._shutdown_event.is_set():
                        break
                    await asyncio.sleep(self.poll_interval)
                    continue

            except asyncio.CancelledError:
                logger.info("Worker cancelado")
                break
            except Exception as e:
                import traceback
                logger.error(
                    f"Erro no worker: {str(e)}\n{traceback.format_exc()}",
                    extra={"exc_info": True},
                )
                # Continua processando após erro

        logger.info("Worker de webhook parado")

    def stop(self) -> None:
        """Sinaliza shutdown do worker."""
        self._running = False
        self._shutdown_event.set()
        logger.info("Sinal de shutdown do worker de webhook enviado")
