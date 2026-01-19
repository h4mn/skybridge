# -*- coding: utf-8 -*-
"""
Webhook Processor Application Service.

Processa eventos de webhook recebidos e cria jobs para processamento assíncrono.
Integra com Trello para criar cards automaticamente quando issues são abertas.
"""
from __future__ import annotations

import logging
from datetime import datetime
from typing import TYPE_CHECKING, Optional

if TYPE_CHECKING:
    from core.webhooks.ports.job_queue_port import JobQueuePort

from core.webhooks.domain import WebhookEvent, WebhookJob, WebhookSource
from kernel.contracts.result import Result

logger = logging.getLogger(__name__)


class WebhookProcessor:
    """
    Service de aplicação para processar webhooks.

    Responsabilidades:
    - Validar eventos recebidos
    - Criar jobs apropriados para cada tipo de evento
    - Enfileirar jobs para processamento assíncrono
    - Criar cards no Trello para issues abertas (integração opcional)

    Não faz processamento real - apenas orquestra a criação de jobs.
    """

    def __init__(
        self,
        job_queue: "JobQueuePort",
        trello_service: Optional["TrelloIntegrationService"] = None,
    ):
        """
        Inicializa processor.

        Args:
            job_queue: Fila para enfileirar jobs
            trello_service: Serviço de integração com Trello (opcional)
        """
        self.job_queue = job_queue
        self.trello_service = trello_service

    async def process_github_issue(
        self, payload: dict, event_type: str, signature: str | None = None, delivery_id: str | None = None
    ) -> Result[str, str]:
        """
        Processa evento de issue do GitHub.

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

            # Cria card no Trello para issues abertas
            trello_card_id = None
            if action == "opened" and self.trello_service:
                trello_card_id = await self._create_trello_card(
                    payload, issue_data, issue_number
                )

            # Cria evento de domínio
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

            # Armazena card_id do Trello para uso posterior
            if trello_card_id:
                job.metadata["trello_card_id"] = trello_card_id
                logger.info(
                    f"Job {job.job_id} | correlation_id={job.correlation_id} | "
                    f"vinculado ao card Trello: {trello_card_id}"
                )

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

    async def _create_trello_card(
        self, payload: dict, issue_data: dict, issue_number: int
    ) -> Optional[str]:
        """
        Cria card no Trello para uma issue do GitHub.

        Args:
            payload: Payload completo do webhook
            issue_data: Dados da issue
            issue_number: Número da issue

        Returns:
            card_id do Trello ou None se falhou/ não configurado
        """
        try:
            # Extrai informações da issue
            issue_title = issue_data.get("title", "")
            issue_body = issue_data.get("body")
            issue_url = issue_data.get("html_url", "")
            author = issue_data.get("user", {}).get("login", "unknown")
            repository = payload.get("repository", {})
            repo_name = repository.get("full_name", "unknown/repo")

            # Extrai labels
            labels_data = issue_data.get("labels", [])
            labels = [label.get("name") for label in labels_data] if labels_data else []

            # Cria card no Trello
            result = await self.trello_service.create_card_from_github_issue(
                issue_number=issue_number,
                issue_title=issue_title,
                issue_body=issue_body,
                issue_url=issue_url,
                author=author,
                repo_name=repo_name,
                labels=labels,
            )

            if result.is_ok:
                card_id = result.unwrap()
                logger.info(
                    f"Card Trello criado: {card_id} para issue #{issue_number}"
                )
                return card_id
            else:
                logger.warning(
                    f"Falha ao criar card Trello para issue #{issue_number}: {result.error}"
                )
                return None

        except Exception as e:
            logger.error(f"Erro ao criar card Trello: {e}")
            return None

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
