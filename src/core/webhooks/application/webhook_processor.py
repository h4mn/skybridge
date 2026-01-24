# -*- coding: utf-8 -*-
"""
Webhook Processor Application Service.

Processa eventos de webhook recebidos e cria jobs para processamento assíncrono.
Emite Domain Events para desacoplar integrações (Trello, notificações, etc.).

PRD018 ARCH-07: Migrado para usar Domain Events ao invés de chamadas diretas.
"""
from __future__ import annotations

import logging
from datetime import datetime
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from core.webhooks.ports.job_queue_port import JobQueuePort
    from core.domain_events.event_bus import EventBus

from core.webhooks.domain import WebhookEvent, WebhookJob, WebhookSource
from core.domain_events.issue_events import IssueReceivedEvent
from kernel.contracts.result import Result

logger = logging.getLogger(__name__)


class WebhookProcessor:
    """
    Service de aplicação para processar webhooks.

    Responsabilidades:
    - Validar eventos recebidos
    - Criar jobs apropriados para cada tipo de evento
    - Enfileirar jobs para processamento assíncrono
    - Emitir Domain Events (desacoplado de integrações específicas)

    Não faz processamento real - apenas orquestra a criação de jobs
    e emite eventos para outros componentes reagirem.

    PRD018 ARCH-07: Desacoplado via Domain Events.
    """

    def __init__(
        self,
        job_queue: "JobQueuePort",
        event_bus: "EventBus",
    ):
        """
        Inicializa processor.

        Args:
            job_queue: Fila para enfileirar jobs
            event_bus: Event bus para emitir Domain Events
        """
        self.job_queue = job_queue
        self.event_bus = event_bus

    async def process_github_issue(
        self, payload: dict, event_type: str, signature: str | None = None, delivery_id: str | None = None
    ) -> Result[str, str]:
        """
        Processa evento de issue do GitHub.

        Emite IssueReceivedEvent para desacoplar de integrações específicas.
        O TrelloEventListener ouvirá esse evento e criará o card.

        Args:
            payload: Payload do webhook (JSON)
            event_type: Tipo do evento (ex: "issues.opened")
            signature: Assinatura HMAC (se disponível)
            delivery_id: ID único da entrega (para evitar duplicação)

        Returns:
            Result com job_id ou mensagem de erro
        """
        try:
            correlation_id = delivery_id or "unknown"
            logger.info(
                f"Processing GitHub webhook | correlation_id={correlation_id} | "
                f"event_type={event_type} | delivery={delivery_id}"
            )

            # Verifica duplicidade por delivery_id
            if delivery_id and await self.job_queue.exists_by_delivery(delivery_id):
                logger.info(f"Webhook já processado anteriormente | delivery_id={delivery_id}")
                return Result.ok(None)  # Retorna ok mas sem job_id (já processado)

            # Só processa eventos de issues
            if not event_type.startswith("issues."):
                logger.warning(f"Unsupported event type: {event_type}")
                return Result.err(
                    f"Tipo de evento não suportado: {event_type}. Use 'issues.*' events."
                )

            # Extrai dados do evento
            issue_data = payload.get("issue", {})
            if not issue_data:
                logger.warning(f"No issue data in payload | event_type={event_type}")
                return Result.err("Payload não contém dados da issue")

            issue_number = issue_data.get("number")
            if not issue_number:
                return Result.err("Issue number não encontrado no payload")

            # Extrai action (opened, edited, closed, etc)
            action = payload.get("action", "opened")

            # Extrai informações para o Domain Event
            issue_title = issue_data.get("title", "")
            issue_body = issue_data.get("body", "")
            sender_info = payload.get("sender", {})
            sender = sender_info.get("login", "unknown")
            repository = payload.get("repository", {})
            repo_name = repository.get("full_name", "unknown/repo")
            labels_data = issue_data.get("labels", [])
            labels = [label.get("name") for label in labels_data] if labels_data else []
            assignee = issue_data.get("assignee", {}).get("login") if issue_data.get("assignee") else None

            # PRD018 ARCH-07: Emite Domain Event ao invés de chamar Trello diretamente
            # O TrelloEventListener ouvirá esse evento e criará o card
            await self.event_bus.publish(
                IssueReceivedEvent(
                    aggregate_id=f"{repo_name}#{issue_number}",
                    issue_number=issue_number,
                    repository=repo_name,
                    title=issue_title,
                    body=issue_body,
                    sender=sender,
                    action=action,
                    labels=labels,
                    assignee=assignee,
                )
            )
            logger.info(
                f"IssueReceivedEvent emitido | issue=#{issue_number} | repo={repo_name}"
            )

            # Cria evento de domínio interno
            event = WebhookEvent(
                source=WebhookSource.GITHUB,
                event_type=f"issues.{action}",
                event_id=str(issue_number),
                payload=payload,
                received_at=datetime.utcnow(),
                signature=signature,
                delivery_id=delivery_id,
            )

            # Cria job
            job = WebhookJob.create(event)

            # Enfileira
            await self.job_queue.enqueue(job)

            logger.info(
                f"Job enfileirado | job_id={job.job_id} | correlation_id={job.correlation_id}"
            )

            return Result.ok(job.job_id)

        except Exception as e:
            logger.error(
                f"Erro ao processar webhook | correlation_id={correlation_id} | error={e}"
            )
            return Result.err(f"Erro ao processar webhook: {str(e)}")

    async def process_webhook(
        self,
        source: str,
        event_type: str,
        payload: dict,
        signature: str | None = None,
        delivery_id: str | None = None,
    ) -> Result[str, str]:
        """
        Processa webhook genérico de qualquer fonte.

        Args:
            source: Fonte do webhook (github, discord, etc)
            event_type: Tipo do evento
            payload: Payload do webhook
            signature: Assinatura HMAC (se disponível)
            delivery_id: ID único da entrega (para evitar duplicação)

        Returns:
            Result com job_id ou mensagem de erro
        """
        try:
            # Converte string para enum
            try:
                webhook_source = WebhookSource(source)
            except ValueError:
                return Result.err(f"Fonte de webhook não suportada: {source}")

            # Para Phase 1, só GitHub
            if webhook_source != WebhookSource.GITHUB:
                return Result.err(f"Fonte {source} ainda não implementada (Phase 2)")

            # Delega para método específico
            if event_type.startswith("issues."):
                return await self.process_github_issue(payload, event_type, signature, delivery_id)

            return Result.err(f"Tipo de evento não suportado: {event_type}")

        except Exception as e:
            return Result.err(f"Erro ao processar webhook: {str(e)}")
