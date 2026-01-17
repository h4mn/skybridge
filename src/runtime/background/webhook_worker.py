# -*- coding: utf-8 -*-
"""
Webhook Background Worker.

Worker assíncrono que processa jobs de webhook em background.
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
from infra.webhooks.adapters.in_memory_queue import (
    InMemoryJobQueue,
)
from runtime.config.config import get_webhook_config
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
        job_queue: InMemoryJobQueue,
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
                # Aguarda job com timeout
                job = await self.job_queue.wait_for_dequeue(
                    timeout=self.poll_interval
                )

                if job:
                    logger.info(
                        f"Processando job {job.job_id}",
                        extra={
                            "job_id": job.job_id,
                            "source": job.event.source.value,
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
                    # Verifica se deve shutdown
                    if self._shutdown_event.is_set():
                        break

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


async def main() -> None:
    """
    Entry point para o worker.

    Inicializa dependências e inicia loop de processamento.
    """
    # Carrega configuração
    config = get_webhook_config()

    # Inicializa dependências
    job_queue = InMemoryJobQueue()
    worktree_manager = WorktreeManager(config.worktree_base_path)
    orchestrator = JobOrchestrator(job_queue, worktree_manager)

    # Cria worker
    worker = WebhookWorker(job_queue, orchestrator)

    # Setup signal handlers para graceful shutdown
    def signal_handler() -> None:
        logger.info("Sinal de shutdown recebido")
        worker.stop()

    loop = asyncio.get_running_loop()
    for sig in (signal.SIGINT, signal.SIGTERM):
        loop.add_signal_handler(sig, signal_handler)

    # Inicia worker
    await worker.start()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Worker interrompido")
        sys.exit(0)
