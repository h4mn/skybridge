# -*- coding: utf-8 -*-
"""
Webhook Sky-RPC Handlers.

Handlers registrados para processamento de webhooks via Sky-RPC.
"""
from __future__ import annotations

import logging

from kernel.registry.decorators import command
from kernel.contracts.result import Result
from core.webhooks.application.webhook_processor import (
    WebhookProcessor,
)
from core.webhooks.ports.job_queue_port import JobQueuePort

logger = logging.getLogger(__name__)

# Singleton global do job queue (compartilhado entre handler e worker)
_job_queue: JobQueuePort | None = None

# EventBus (singleton para Domain Events)
_event_bus = None

# TrelloIntegrationService (opcional, singleton)
_trello_service = None

# TrelloService (opcional, singleton)
_trello_kanban_service = None

# PRD020: Mapeamento listas Trello → AutonomyLevel
LIST_TO_AUTONOMY = {
    "💡 Brainstorm": "analysis",
    "📋 A Fazer": "development",
    "🚧 Em Andamento": "development",
    "👁️ Em Revisão": "review",
    "🚀 Publicar": "publish",
}


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


def get_job_queue() -> JobQueuePort:
    """
    Retorna instância singleton do job queue.

    Usa JobQueueFactory para criar a fila apropriada baseado em
    JOB_QUEUE_PROVIDER do ambiente:
    - sqlite: SQLiteJobQueue (padrão, zero dependências)
    - redis: RedisJobQueue (tradicional)
    - dragonfly: RedisJobQueue (DragonflyDB)
    - file: FileBasedJobQueue (fallback local)

    Returns:
        Instância de JobQueuePort
    """
    global _job_queue
    if _job_queue is None:
        from infra.webhooks.adapters.job_queue_factory import (
            JobQueueFactory,
        )

        _job_queue = JobQueueFactory.create_from_env()
        logger.info(f"JobQueue inicializado: {type(_job_queue).__name__}")
    return _job_queue


def get_event_bus():
    """
    Retorna instância singleton do event bus.

    PRD018 ARCH-07/09: EventBus para Domain Events desacoplando componentes.

    Returns:
        Instância de EventBus
    """
    global _event_bus
    if _event_bus is None:
        from infra.domain_events.in_memory_event_bus import InMemoryEventBus

        _event_bus = InMemoryEventBus()
        logger.info("EventBus inicializado: InMemoryEventBus")
    return _event_bus


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
    # Obtém processor com fila e event bus compartilhados
    job_queue = get_job_queue()
    event_bus = get_event_bus()
    processor = WebhookProcessor(job_queue, event_bus=event_bus)

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

    PRD020: Fluxo bidirecional Trello → GitHub.
    Detecta movimentos de cards entre listas e cria jobs apropriados
    baseado no autonomy level da lista de destino.

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
    trello_webhook_id = args.get("trello_webhook_id", "")

    # Detecta tipo de evento
    action_type = payload.get("action", {}).get("type", "")
    action_data = payload.get("action", {}).get("data", {})
    model = payload.get("model", {})

    import asyncio
    import json
    import logging
    import re
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
            card_desc = card_data.get("desc", "")

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

            # PRD020: Emitir TrelloWebhookReceivedEvent
            event_bus = get_event_bus()
            from core.domain_events.trello_events import TrelloWebhookReceivedEvent
            await event_bus.publish(
                TrelloWebhookReceivedEvent(
                    aggregate_id=card_id,
                    webhook_id=trello_webhook_id,
                    action_type=action_type,
                    card_id=card_id,
                    card_name=card_name,
                    list_before_name=list_before_name,
                    list_after_name=list_after_name,
                )
            )
            logger.info(f"✅ TrelloWebhookReceivedEvent emitido para card '{card_name}'")

            # Determinar autonomy_level baseado na lista de destino
            from core.webhooks.domain.autonomy_level import AutonomyLevel
            autonomy_level_str = LIST_TO_AUTONOMY.get(list_after_name, "development")
            try:
                autonomy_level = AutonomyLevel(autonomy_level_str)
            except ValueError:
                autonomy_level = AutonomyLevel.DEVELOPMENT

            logger.info(f"   Autonomy Level: {autonomy_level.value} (baseado na lista '{list_after_name}')")

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

                # PRD020: Extrair issue_number do card e criar job
                issue_number = extract_issue_number_from_card(card_name, card_desc)
                repository = extract_repository_from_card(card_desc)

                if issue_number:
                    # Criar WebhookEvent e WebhookJob
                    from core.webhooks.domain import WebhookSource, WebhookEvent, WebhookJob
                    from core.domain_events.job_events import JobCreatedEvent

                    webhook_event = WebhookEvent(
                        source=WebhookSource.TRELLO,
                        event_type=f"card.moved.{list_after_name}",
                        event_id=card_id,
                        payload=payload,
                        received_at=datetime.utcnow(),
                        delivery_id=trello_webhook_id,
                    )

                    job = WebhookJob.create(webhook_event)
                    job.autonomy_level = autonomy_level
                    job.metadata.update({
                        "trello_card_id": card_id,
                        "trello_card_name": card_name,
                        "trello_list_name": list_after_name,
                    })

                    # Enfileirar job
                    job_queue = get_job_queue()
                    job_id = await job_queue.enqueue(job)

                    logger.info(f"✅ Job criado: job_id={job_id} | issue=#{issue_number} | autonomy={autonomy_level.value}")

                    # Emitir JobCreatedEvent
                    await event_bus.publish(
                        JobCreatedEvent(
                            aggregate_id=job_id,
                            job_id=job_id,
                            issue_number=issue_number,
                        )
                    )

                    return Result.ok(
                        {"processed": True, "action": "moved_to_progress", "job_id": job_id}
                    )
                else:
                    logger.warning(f"⚠️ Card '{card_name}' não possui issue_number - pulando criação de job")

            # PRD020: Para outras listas, também criar job se tiver issue_number
            if list_after_name in LIST_TO_AUTONOMY and list_after_name != todo_list_name:
                issue_number = extract_issue_number_from_card(card_name, card_desc)
                if issue_number:
                    from core.webhooks.domain import WebhookSource, WebhookEvent, WebhookJob
                    from core.domain_events.job_events import JobCreatedEvent

                    webhook_event = WebhookEvent(
                        source=WebhookSource.TRELLO,
                        event_type=f"card.moved.{list_after_name}",
                        event_id=card_id,
                        payload=payload,
                        received_at=datetime.utcnow(),
                        delivery_id=trello_webhook_id,
                    )

                    job = WebhookJob.create(webhook_event)
                    job.autonomy_level = autonomy_level
                    job.metadata.update({
                        "trello_card_id": card_id,
                        "trello_card_name": card_name,
                        "trello_list_name": list_after_name,
                    })

                    job_queue = get_job_queue()
                    job_id = await job_queue.enqueue(job)

                    logger.info(f"✅ Job criado: job_id={job_id} | issue=#{issue_number} | autonomy={autonomy_level.value} | lista={list_after_name}")

                    event_bus = get_event_bus()
                    await event_bus.publish(
                        JobCreatedEvent(
                            aggregate_id=job_id,
                            job_id=job_id,
                            issue_number=issue_number,
                        )
                    )

                    return Result.ok(
                        {"processed": True, "action": "job_created", "job_id": job_id}
                    )

        return Result.ok({"processed": True, "action": "ignored"})

    def extract_issue_number_from_card(card_name: str, card_desc: str) -> int | None:
        """Extrai issue number do nome ou descrição do card."""
        # Tenta extrair do nome (ex: "#123 Issue Title")
        match = re.search(r"#(\d+)", card_name)
        if match:
            return int(match.group(1))

        # Tenta extrair da descrição (ex: "Issue #123")
        match = re.search(r"#(\d+)", card_desc or "")
        if match:
            return int(match.group(1))

        return None

    def extract_repository_from_card(card_desc: str) -> str | None:
        """Extrai repositório da descrição do card."""
        if not card_desc:
            return None

        # Tenta extrair formato "owner/repo"
        match = re.search(r"([a-zA-Z0-9_-]+)/([a-zA-Z0-9_-]+)", card_desc)
        if match:
            return f"{match.group(1)}/{match.group(2)}"

        return None

    # Executa em thread separada para evitar conflitos de loop
    import concurrent.futures
    with concurrent.futures.ThreadPoolExecutor(max_workers=1) as executor:
        future = executor.submit(lambda: asyncio.run(_process()))
        result = future.result(timeout=30)

    return result


def extract_issue_number_from_card(card_name: str, card_desc: str) -> int | None:
    """Extrai issue number do nome ou descrição do card."""
    import re

    # Tenta extrair do nome (ex: "#123 Issue Title")
    match = re.search(r"#(\d+)", card_name)
    if match:
        return int(match.group(1))

    # Tenta extrair da descrição (ex: "Issue #123")
    match = re.search(r"#(\d+)", card_desc or "")
    if match:
        return int(match.group(1))

    return None


def extract_repository_from_card(card_desc: str) -> str | None:
    """Extrai repositório da descrição do card."""
    import re

    if not card_desc:
        return None

    # Tenta extrair formato "owner/repo"
    match = re.search(r"([a-zA-Z0-9_-]+)/([a-zA-Z0-9_-]+)", card_desc)
    if match:
        return f"{match.group(1)}/{match.group(2)}"

    return None
