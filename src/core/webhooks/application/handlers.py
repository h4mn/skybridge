# -*- coding: utf-8 -*-
"""
Webhook Sky-RPC Handlers.

Handlers registrados para processamento de webhooks via Sky-RPC.
"""
from __future__ import annotations

from kernel.registry.decorators import command
from kernel.contracts.result import Result
from core.webhooks.application.webhook_processor import (
    WebhookProcessor,
)
from infra.webhooks.adapters.in_memory_queue import (
    InMemoryJobQueue,
)

# Singleton global do job queue (compartilhado entre handler e worker)
_job_queue: InMemoryJobQueue | None = None

# TrelloIntegrationService (opcional, singleton)
_trello_service = None


def get_trello_service():
    """Retorna instância singleton do TrelloIntegrationService."""
    global _trello_service
    if _trello_service is None:
        try:
            from runtime.config.config import get_trello_config
            from core.kanban.application.trello_integration_service import (
                TrelloIntegrationService,
            )
            from infra.kanban.adapters.trello_adapter import TrelloAdapter
            from os import getenv

            trello_config = get_trello_config()
            if trello_config.api_key and trello_config.api_token:
                board_id = getenv("TRELLO_BOARD_ID")
                if board_id:
                    trello_adapter = TrelloAdapter(
                        trello_config.api_key,
                        trello_config.api_token,
                        board_id
                    )
                    _trello_service = TrelloIntegrationService(trello_adapter)
        except Exception:
            pass
    return _trello_service


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
    trello_service = get_trello_service()
    processor = WebhookProcessor(job_queue, trello_service=trello_service)

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
