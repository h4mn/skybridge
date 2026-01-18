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
# TrelloService (opcional, singleton)
_trello_kanban_service = None


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


def get_trello_kanban_service():
    """Retorna instância singleton do TrelloService."""
    global _trello_kanban_service
    if _trello_kanban_service is None:
        try:
            from runtime.config.config import (
                get_trello_config,
                get_trello_kanban_lists_config,
            )
            from core.kanban.application.trello_service import TrelloService
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
                    kanban_config = get_trello_kanban_lists_config()
                    _trello_kanban_service = TrelloService(
                        trello_adapter=trello_adapter,
                        kanban_config=kanban_config,
                    )
        except Exception:
            pass
    return _trello_kanban_service


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

    # Processa webhook (executa async em thread separada)
    import asyncio
    import concurrent.futures

    async def _process():
        return await processor.process_github_issue(
            payload=args["payload"],
            event_type=args["event_type"],
            signature=args.get("signature"),
        )

    # Executa em thread separada para evitar conflitos de loop
    with concurrent.futures.ThreadPoolExecutor(max_workers=1) as executor:
        future = executor.submit(lambda: asyncio.run(_process()))
        result = future.result(timeout=30)

    return result


@command(
    name="webhooks.trello.receive",
    description="Recebe e processa webhook do Trello",
    auth=None,  # Webhooks do Trello usam verificação própria
    input_schema={
        "type": "object",
        "properties": {
            "payload": {"type": "object"},
            "trello_webhook_id": {"type": "string"},
        },
        "required": ["payload"],
    },
    output_schema={
        "type": "object",
        "properties": {
            "processed": {"type": "boolean"},
            "action": {"type": "string"},
        },
    },
)
def receive_trello_webhook(args: dict) -> Result:
    """
    Recebe webhook do Trello e processa eventos de cards.

    Detecta movimentos de cards entre listas, especialmente:
    - Card movido para "📋 A Fazer" → Inicia agente

    Args:
        args: Dicionário contendo:
            - payload: Payload JSON do webhook do Trello
            - trello_webhook_id: ID do webhook (opcional, para verificação)

    Returns:
        Result com status do processamento ou erro

    Example:
        >>> result = receive_trello_webhook({
        ...     "payload": {
        ...         "action": {"type": "updateCard"},
        ...         "model": {"id": "card123", "idList": "list456"}
        ...     }
        ... })
    """
    trello_service = get_trello_kanban_service()
    if not trello_service:
        return Result.err("TrelloService não configurado")

    payload = args.get("payload", {})

    # Detecta tipo de evento
    action_type = payload.get("action", {}).get("type", "")
    action_data = payload.get("action", {}).get("data", {})
    model = payload.get("model", {})

    import asyncio
    import json
    import logging
    from datetime import datetime

    logger = logging.getLogger(__name__)

    # Timestamp preciso para medição de latência
    timestamp_ms = datetime.now().isoformat(timespec='milliseconds')

    # Log ANTES de processar (fora da thread) - usa print para garantir que aparece
    print(f"📩 [DEBUG] Webhook Trello recebido | action_type={action_type} | timestamp={timestamp_ms}")
    print(f"📦 [PAYLOAD COMPLETO]:\n{json.dumps(payload, indent=2, ensure_ascii=False)}")
    logger.info(f"📩 Webhook Trello recebido | action_type={action_type} | timestamp={timestamp_ms}")
    logger.info(f"   Payload keys: {list(payload.keys())}")

    async def _process():
        # Evento: Card atualizado (movido entre listas)
        if action_type == "updateCard":
            # IMPORTANTE: action.data.card contém o ID do card, não model.id (que é o board)
            card_data = action_data.get("card", {})
            card_id = card_data.get("id")
            card_name = card_data.get("name", "")

            # Extrai informações de movimento do payload
            list_before = action_data.get("listBefore", {})
            list_after = action_data.get("listAfter", {})

            list_before_name = list_before.get("name", "Desconhecido")
            list_after_name = list_after.get("name", "Desconhecido")

            # Log da transição detectada (INFO para sempre aparecer)
            logger.info(
                f"📦 Card movido: '{card_name}' | "
                f"{list_before_name} → {list_after_name}"
            )
            logger.info(f"   Card ID: {card_id}")
            logger.info(f"   De: {list_before_name} ({list_before.get('id', 'N/A')})")
            logger.info(f"   Para: {list_after_name} ({list_after.get('id', 'N/A')})")

            # Verifica se foi movido PARA "📋 A Fazer"
            from runtime.config.config import get_trello_kanban_lists_config

            kanban_config = get_trello_kanban_lists_config()
            todo_list_name = kanban_config.todo

            if list_after_name == todo_list_name:
                logger.info(f"✅ Card detectado em '{todo_list_name}' - movendo para '{kanban_config.progress}'...")

                # Card foi movido para "📋 A Fazer" - mover automaticamente para "🚧 Em Andamento"
                handle_result = await trello_service.handle_card_moved_to_todo(
                    card_id=card_id
                )
                if handle_result.is_err:
                    logger.error(f"❌ Erro ao processar card movido para '📋 A Fazer': {handle_result.error}")
                    return Result.err(handle_result.error)

                logger.info(f"✅ Card movido automaticamente para '{kanban_config.progress}'")
                return Result.ok(
                    {"processed": True, "action": "moved_to_progress"}
                )

        return Result.ok({"processed": True, "action": "ignored"})

    # Executa em thread separada para evitar conflitos de loop
    import concurrent.futures
    with concurrent.futures.ThreadPoolExecutor(max_workers=1) as executor:
        future = executor.submit(lambda: asyncio.run(_process()))
        result = future.result(timeout=30)

    return result
