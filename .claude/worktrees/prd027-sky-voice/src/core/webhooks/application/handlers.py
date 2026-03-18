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

# Cache de job queues por workspace (ADR024 - isolamento por workspace)
_job_queues: dict[str, JobQueuePort] = {}

# AgentExecutionStore (cache por workspace para persistência de execuções de agentes)
_agent_execution_stores: dict[str, any] = {}

# TrelloIntegrationService (opcional, singleton)
_trello_service = None

# TrelloService (opcional, singleton)
_trello_kanban_service = None

# PRD020: Mapeamento listas Trello → AutonomyLevel
# Usa nomes COM emoji porque o webhook do Trello envia nomes com emoji
# DOC: core.kanban.domain.kanban_lists_config - FONTE ÚNICA DA VERDADE para emojis
LIST_TO_AUTONOMY = {
    "📥 Issues": "analysis",
    "🧠 Brainstorm": "analysis",
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
            logger.info(f"TRELLO_API_KEY: {bool(trello_config.api_key)}, TRELLO_API_TOKEN: {bool(trello_config.api_token)}")

            if trello_config.api_key and trello_config.api_token:
                board_id = getenv("TRELLO_BOARD_ID")
                logger.info(f"TRELLO_BOARD_ID: {board_id}")
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
                    logger.info("TrelloService criado com sucesso")
                else:
                    logger.warning("TRELLO_BOARD_ID não encontrado")
            else:
                logger.warning("TRELLO_API_KEY ou TRELLO_API_TOKEN não configurados")
        except Exception as e:
            logger.error(f"Erro ao criar TrelloService: {e}")
    return _trello_kanban_service


def get_job_queue() -> JobQueuePort:
    """
    Retorna instância do job queue RESPEITANDO O WORKSPACE.

    DOC: ADR024 - Cache por workspace, não singleton global.
    DOC: ADR024 - Cada workspace tem seu próprio jobs.db isolado.

    O job queue é criado baseado no workspace atual do contexto:
    - Workspace "core" → workspace/core/data/jobs.db
    - Workspace "trading" → workspace/trading/data/jobs.db
    - Testes → tmp_path/test.db (via fixture isolated_job_queue)

    Returns:
        Instância de JobQueuePort para o workspace atual

    Example:
        >>> # Em produção (request context)
        >>> queue = get_job_queue()  # Retorna queue do workspace do header
        >>>
        >>> # Em testes
        >>> set_current_workspace("test")
        >>> queue = get_job_queue()  # Retorna queue do workspace "test"
    """
    global _job_queues

    # Obter workspace atual do contexto
    from runtime.workspace.workspace_context import get_current_workspace
    from pathlib import Path

    workspace_id = get_current_workspace()

    # Cache por workspace
    if workspace_id not in _job_queues:
        from infra.webhooks.adapters.sqlite_job_queue import SQLiteJobQueue

        # Construir caminho do banco baseado no workspace
        # ADR024: workspace/{workspace_id}/data/jobs.db
        base_path = Path.cwd()
        db_path = base_path / "workspace" / workspace_id / "data" / "jobs.db"

        _job_queues[workspace_id] = SQLiteJobQueue(db_path=db_path)
        logger.info(
            f"JobQueue inicializado para workspace '{workspace_id}': {db_path}"
        )

    return _job_queues[workspace_id]


def get_event_bus():
    """
    Retorna instância singleton do event bus.

    PRD018 ARCH-07/09: EventBus para Domain Events desacoplando componentes.

    Uses the global EventBus from kernel to ensure all components
    (webhook processor, TrelloEventListener, etc.) share the same instance.

    Returns:
        Instância de EventBus
    """
    from kernel import get_event_bus as kernel_get_event_bus

    return kernel_get_event_bus()


def get_agent_execution_store():
    """
    Retorna instância do AgentExecutionStore RESPEITANDO O WORKSPACE.

    DOC: ADR024 - Cache por workspace, não singleton global.
    DOC: ADR024 - Cada workspace tem seu próprio agent_executions.db isolado.

    O store é criado baseado no workspace atual do contexto:
    - Workspace "core" → workspace/core/data/agent_executions.db
    - Workspace "trading" → workspace/trading/data/agent_executions.db
    - Testes → tmp_path/test_executions.db (via fixture)

    Returns:
        Instância de AgentExecutionStore para o workspace atual

    Example:
        >>> # Em produção (request context)
        >>> store = get_agent_execution_store()  # Retorna store do workspace do header
        >>>
        >>> # Em testes
        >>> set_current_workspace("test")
        >>> store = get_agent_execution_store()  # Retorna store do workspace "test"
    """
    global _agent_execution_stores

    # Obter workspace atual do contexto
    from runtime.workspace.workspace_context import get_current_workspace

    workspace_id = get_current_workspace()

    # Cache por workspace
    if workspace_id not in _agent_execution_stores:
        from infra.agents.agent_execution_store import AgentExecutionStore

        # AgentExecutionStore já usa get_workspace_data_dir() que respeita workspace
        _agent_execution_stores[workspace_id] = AgentExecutionStore()
        logger.info(
            f"AgentExecutionStore inicializado para workspace '{workspace_id}'"
        )

    return _agent_execution_stores[workspace_id]


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

    # Lista TODO é usada em múltiplos lugares, definir antes do bloco condicional
    todo_list_name = "📋 A Fazer"

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

            # PRD026: Detectar arquivamento/deleção de card
            # Se card.closed == true, trata como arquivado/deletado
            card_closed = card_data.get("closed", False)

            # Extrai informações de movimento do payload
            list_before = action_data.get("listBefore", {})
            list_after = action_data.get("listAfter", {})

            list_before_name = list_before.get("name", "Desconhecido")
            list_after_name = list_after.get("name", "Desconhecido")

            # Log da transição detectada (INFO para sempre aparecer)
            logger.info(
                f"📦 Card atualizado: '{card_name}' | "
                f"listas: {list_before_name} → {list_after_name}"
            )
            logger.info(f"   Card ID: {card_id}")

            # PRD020: Emitir TrelloWebhookReceivedEvent (obter event_bus PRIMEIRO)
            event_bus = get_event_bus()

            # Se card foi arquivado/deletado, não processar movimento
            if card_closed:
                logger.info(
                    f"📦 Card arquivado/deletado: '{card_name}' (ID: {card_id})"
                )

                # PRD026: Emitir TrelloCardArchivedEvent
                from core.domain_events.trello_events import TrelloCardArchivedEvent
                await event_bus.publish(
                    TrelloCardArchivedEvent(
                        aggregate_id=card_id,
                        card_id=card_id,
                        card_name=card_name,
                        reason="archived via webhook"
                    )
                )
                logger.info(f"✅ TrelloCardArchivedEvent emitido para card '{card_name}'")
            else:
                # Se não foi arquivado, processa movimento normalmente (para jobs)
                # PRD020: Emitir TrelloWebhookReceivedEvent
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
                # Nomes das listas (não IDs) para comparação
                in_progress_list_name = "🚧 Em Andamento"

                if list_after_name == todo_list_name:
                    logger.info(f"✅ Card detectado em '{todo_list_name}' - movendo para '{in_progress_list_name}'...")

                    # Card foi movido para "📋 A Fazer" - mover automaticamente para "🚧 Em Andamento"
                    handle_result = await trello_service.handle_card_moved_to_todo(
                        card_id=card_id
                    )
                    if handle_result.is_err:
                        logger.error(f"❌ Erro ao processar card movido para '📋 A Fazer': {handle_result.error}")
                        return Result.err(handle_result.error)

                    logger.info(f"✅ Card movido automaticamente para '{in_progress_list_name}'")

                    # PRD020: Extrair issue_number do card e criar job
                    issue_number = extract_issue_number_from_card(card_name, card_desc)
                    repository = extract_repository_from_card(card_desc)

                    if issue_number:
                        # Criar WebhookEvent e WebhookJob
                        from core.webhooks.domain import WebhookSource, WebhookEvent, WebhookJob
                        from core.domain_events.job_events import JobCreatedEvent
                        from core.webhooks.domain.trigger_mappings import get_trello_list_slug, build_card_moved_event_type

                        # Usa slug da lista Trello para event_type (evita problemas com emojis)
                        list_slug = get_trello_list_slug(list_after_name)
                        event_type = build_card_moved_event_type(list_slug) if list_slug else f"card.moved.{list_after_name}"

                        webhook_event = WebhookEvent(
                            source=WebhookSource.TRELLO,
                            event_type=event_type,
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
                            "trello_list_name": list_after_name,  # Mantém nome original com emoji
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
                        from core.webhooks.domain.trigger_mappings import get_trello_list_slug, build_card_moved_event_type

                        # Usa slug da lista Trello para event_type (evita problemas com emojis)
                        list_slug = get_trello_list_slug(list_after_name)
                        event_type = build_card_moved_event_type(list_slug) if list_slug else f"card.moved.{list_after_name}"

                        webhook_event = WebhookEvent(
                            source=WebhookSource.TRELLO,
                            event_type=event_type,
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
    # Cria um NOVO event loop explicitamente ao invés de usar asyncio.run()
    import concurrent.futures

    def run_in_new_loop():
        """Cria um novo event loop e rota a função async."""
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            return loop.run_until_complete(_process())
        finally:
            loop.close()

    with concurrent.futures.ThreadPoolExecutor(max_workers=1) as executor:
        future = executor.submit(run_in_new_loop)
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
