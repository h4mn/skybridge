# -*- coding: utf-8 -*-
"""
Webhook Processor Application Service.

Processa eventos de webhook recebidos e cria jobs para processamento assíncrono.
"""
from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from core.webhooks.ports.job_queue_port import JobQueuePort

from core.webhooks.domain import WebhookEvent, WebhookJob, WebhookSource
from kernel.contracts.result import Result


class WebhookProcessor:
    """
    Service de aplicação para processar webhooks.

    Responsabilidades:
    - Validar eventos recebidos
    - Criar jobs apropriados para cada tipo de evento
    - Enfileirar jobs para processamento assíncrono

    Não faz processamento real - apenas orquestra a criação de jobs.
    """

    def __init__(self, job_queue: "JobQueuePort"):
        """
        Inicializa processor.

        Args:
            job_queue: Fila para enfileirar jobs
        """
        self.job_queue = job_queue

    async def process_github_issue(
        self, payload: dict, event_type: str, signature: str | None = None
    ) -> Result[str, str]:
        """
        Processa evento de issue do GitHub.

        Args:
            payload: Payload do webhook (JSON)
            event_type: Tipo do evento (ex: "issues.opened")
            signature: Assinatura HMAC (se disponível)

        Returns:
            Result com job_id ou mensagem de erro
        """
        try:
            # Log para debug
            import logging
            logger = logging.getLogger(__name__)
            logger.info(f"Processing GitHub webhook | event_type={event_type}")

            # Trata evento ping (teste de webhook)
            if event_type == "ping":
                logger.info("Ping event received - webhook is working!")
                return Result.ok("ping")  # Retorna OK sem criar job

            # Só processa eventos de issues
            if not event_type.startswith("issues."):
                logger.warning(f"Unsupported event type: {event_type}")
                return Result.err(f"Tipo de evento não suportado: {event_type}. Use 'issues.*' events.")

            # Extrai dados do evento
            issue_data = payload.get("issue", {})
            if not issue_data:
                logger.warning(f"No issue data in payload | event_type={event_type}")
                return Result.err("Payload não contém dados da issue")

            issue_number = issue_data.get("number")
            if not issue_number:
                return Result.err("Issue number não encontrado no payload")

            # Extrai action (opened, edited, closed, etc)
            # Se action não existe, usa "opened" como default para testes
            action = payload.get("action", "opened")

            # Cria evento de domínio
            event = WebhookEvent(
                source=WebhookSource.GITHUB,
                event_type=f"issues.{action}",
                event_id=str(issue_number),
                payload=payload,
                received_at=datetime.utcnow(),
                signature=signature,
            )

            # Cria job
            job = WebhookJob.create(event)

            # Enfileira
            await self.job_queue.enqueue(job)

            return Result.ok(job.job_id)

        except Exception as e:
            return Result.err(f"Erro ao processar webhook: {str(e)}")

    async def process_webhook(
        self,
        source: str,
        event_type: str,
        payload: dict,
        signature: str | None = None,
    ) -> Result[str, str]:
        """
        Processa webhook genérico de qualquer fonte.

        Args:
            source: Fonte do webhook (github, discord, etc)
            event_type: Tipo do evento
            payload: Payload do webhook
            signature: Assinatura HMAC (se disponível)

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
                return await self.process_github_issue(payload, event_type, signature)

            return Result.err(f"Tipo de evento não suportado: {event_type}")

        except Exception as e:
            return Result.err(f"Erro ao processar webhook: {str(e)}")
