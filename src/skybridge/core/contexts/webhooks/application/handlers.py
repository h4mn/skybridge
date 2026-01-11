# -*- coding: utf-8 -*-
"""
Webhook Sky-RPC Handlers.

Handlers registrados para processamento de webhooks via Sky-RPC.
"""
from __future__ import annotations

from skybridge.kernel.registry.decorators import command
from skybridge.kernel.contracts.result import Result
from skybridge.core.contexts.webhooks.application.webhook_processor import (
    WebhookProcessor,
)
from skybridge.infra.contexts.webhooks.adapters.in_memory_queue import (
    InMemoryJobQueue,
)

# Singleton global do job queue (compartilhado entre handler e worker)
_job_queue: InMemoryJobQueue | None = None


def get_job_queue() -> InMemoryJobQueue:
    """Retorna instância singleton do job queue."""
    global _job_queue
    if _job_queue is None:
        _job_queue = InMemoryJobQueue()
    return _job_queue


@command(
    name="webhooks.github.receive",
    description="Recebe e processa webhook do GitHub",
    auth=None,  # Webhooks usam signature verification próprio
    input_schema={
        "type": "object",
        "properties": {
            "payload": {"type": "object"},
            "signature": {"type": "string"},
            "event_type": {"type": "string"},
        },
        "required": ["payload", "signature", "event_type"],
    },
    output_schema={
        "type": "object",
        "properties": {
            "job_id": {"type": "string"},
        },
    },
)
def receive_github_webhook(args: dict) -> Result:
    """
    Recebe webhook do GitHub e cria job para processamento assíncrono.

    Args:
        args: Dicionário contendo:
            - payload: Payload JSON do webhook
            - signature: Assinatura HMAC (já validada pelo middleware)
            - event_type: Tipo do evento (ex: "issues.opened")

    Returns:
        Result com job_id do job criado ou erro

    Example:
        >>> result = receive_github_webhook({
        ...     "payload": {"issue": {"number": 225}},
        ...     "signature": "sha256=abc123...",
        ...     "event_type": "issues.opened"
        ... })
        >>> assert result.is_ok
        >>> job_id = result.value
    """
    # Obtém processor com fila compartilhada
    job_queue = get_job_queue()
    processor = WebhookProcessor(job_queue)

    # Processa webhook (detecta se já existe event loop)
    import asyncio
    import concurrent.futures

    async def _process():
        return await processor.process_github_issue(
            payload=args["payload"],
            event_type=args["event_type"],
            signature=args.get("signature"),
        )

    try:
        # Já existe um loop rodando (FastAPI)
        loop = asyncio.get_running_loop()
        # Executa em uma thread separada para evitar conflito
        with concurrent.futures.ThreadPoolExecutor() as pool:
            future = pool.submit(lambda: asyncio.run(_process()))
            result = future.result(timeout=10)
    except RuntimeError:
        # Não existe loop, pode usar asyncio.run
        result = asyncio.run(_process())

    return result
