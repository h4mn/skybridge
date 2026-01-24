# -*- coding: utf-8 -*-
"""
Notification Event Listener.

Listens to Domain Events and sends notifications via Discord, Slack, Email.

PRD018 ARCH-10: NotificationEventListener desacoplado via Domain Events.
"""
from __future__ import annotations

import logging
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from core.domain_events.event_bus import EventBus

from core.domain_events.job_events import (
    JobCompletedEvent,
    JobFailedEvent,
)

logger = logging.getLogger(__name__)


class NotificationEventListener:
    """
    Listener for Domain Events that trigger notifications.

    Responsibilities:
    - Subscribe to JobCompletedEvent to send success notifications
    - Subscribe to JobFailedEvent to send failure notifications
    - Send notifications to configured channels (Discord, Slack, Email)

    PRD018 ARCH-10: Desacoplado - JobOrchestrator não conhece canais de notificação.
    """

    def __init__(
        self,
        event_bus: "EventBus",
        discord_webhook_url: str | None = None,
        slack_webhook_url: str | None = None,
        email_config: dict | None = None,
    ):
        """
        Inicializa listener.

        Args:
            event_bus: Event bus para se inscrever nos eventos
            discord_webhook_url: URL do webhook do Discord (opcional)
            slack_webhook_url: URL do webhook do Slack (opcional)
            email_config: Configuração de email (opcional)
        """
        self.event_bus = event_bus
        self.discord_webhook_url = discord_webhook_url
        self.slack_webhook_url = slack_webhook_url
        self.email_config = email_config
        self._subscription_ids: list[str] = []

    async def start(self) -> None:
        """
        Inicia o listener, inscrevendo-se nos eventos de interesse.

        Deve ser chamado durante a inicialização da aplicação.
        """
        # Subscribe to JobCompletedEvent
        sub_id = self.event_bus.subscribe(
            JobCompletedEvent,
            self._on_job_completed,
        )
        self._subscription_ids.append(sub_id)

        # Subscribe to JobFailedEvent
        sub_id = self.event_bus.subscribe(
            JobFailedEvent,
            self._on_job_failed,
        )
        self._subscription_ids.append(sub_id)

        logger.info(
            f"NotificationEventListener iniciado com {len(self._subscription_ids)} inscrições"
        )

    async def stop(self) -> None:
        """
        Para o listener, cancelando todas as inscrições.

        Deve ser chamado durante o shutdown da aplicação.
        """
        for sub_id in self._subscription_ids:
            try:
                self.event_bus.unsubscribe(sub_id)
            except Exception as e:
                logger.warning(f"Erro ao cancelar inscrição {sub_id}: {e}")

        self._subscription_ids.clear()
        logger.info("NotificationEventListener parado")

    async def _on_job_completed(self, event: JobCompletedEvent) -> None:
        """
        Handler para JobCompletedEvent.

        Envia notificação de sucesso via canais configurados.

        Args:
            event: JobCompletedEvent com os dados do job
        """
        try:
            logger.info(
                f"Job {event.job_id} completado | "
                f"issue=#{event.issue_number} | "
                f"duration={event.duration_seconds:.2f}s | "
                f"files={event.files_modified}"
            )

            # Envia notificação para Discord
            if self.discord_webhook_url:
                await self._send_discord_notification(
                    event.event_type,
                    event,
                    success=True,
                )

            # Envia notificação para Slack
            if self.slack_webhook_url:
                await self._send_slack_notification(
                    event.event_type,
                    event,
                    success=True,
                )

            # Envia notificação por email
            if self.email_config:
                await self._send_email_notification(
                    event.event_type,
                    event,
                    success=True,
                )

        except Exception as e:
            logger.error(
                f"Erro ao processar JobCompletedEvent para job {event.job_id}: {e}",
                exc_info=True,
            )

    async def _on_job_failed(self, event: JobFailedEvent) -> None:
        """
        Handler para JobFailedEvent.

        Envia notificação de falha via canais configurados.

        Args:
            event: JobFailedEvent com os dados do job
        """
        try:
            logger.warning(
                f"Job {event.job_id} falhou | "
                f"issue=#{event.issue_number} | "
                f"error={event.error_type}: {event.error_message}"
            )

            # Envia notificação para Discord
            if self.discord_webhook_url:
                await self._send_discord_notification(
                    event.event_type,
                    event,
                    success=False,
                )

            # Envia notificação para Slack
            if self.slack_webhook_url:
                await self._send_slack_notification(
                    event.event_type,
                    event,
                    success=False,
                )

            # Envia notificação por email
            if self.email_config:
                await self._send_email_notification(
                    event.event_type,
                    event,
                    success=False,
                )

        except Exception as e:
            logger.error(
                f"Erro ao processar JobFailedEvent para job {event.job_id}: {e}",
                exc_info=True,
            )

    async def _send_discord_notification(
        self,
        event_type: str,
        event: "JobCompletedEvent | JobFailedEvent",
        success: bool,
    ) -> None:
        """
        Envia notificação para Discord.

        Args:
            event_type: Tipo do evento (JobCompletedEvent ou JobFailedEvent)
            event: Dados do evento
            success: Se o job foi bem-sucedido
        """
        import httpx

        try:
            if success:
                # JobCompletedEvent
                event = event  # type: ignore
                color = 0x57F287  # Verde
                title = f"✅ Job Completado: #{event.issue_number}"
                description = (
                    f"**Repositório:** {event.repository}\n"
                    f"**Duração:** {event.duration_seconds:.2f}s\n"
                    f"**Arquivos modificados:** {event.files_modified}"
                )
            else:
                # JobFailedEvent
                event = event  # type: ignore
                color = 0xED4245  # Vermelho
                title = f"❌ Job Falhou: #{event.issue_number}"
                description = (
                    f"**Repositório:** {event.repository}\n"
                    f"**Erro:** {event.error_type}\n"
                    f"**Mensagem:** {event.error_message}\n"
                    f"**Duração:** {event.duration_seconds:.2f}s"
                )

            payload = {
                "embeds": [
                    {
                        "title": title,
                        "description": description,
                        "color": color,
                        "timestamp": event.timestamp.isoformat(),
                    }
                ]
            }

            async with httpx.AsyncClient() as client:
                response = await client.post(self.discord_webhook_url, json=payload)
                response.raise_for_status()

            logger.debug(f"Notificação Discord enviada para {event_type}")

        except Exception as e:
            logger.warning(f"Falha ao enviar notificação Discord: {e}")

    async def _send_slack_notification(
        self,
        event_type: str,
        event: "JobCompletedEvent | JobFailedEvent",
        success: bool,
    ) -> None:
        """
        Envia notificação para Slack.

        Args:
            event_type: Tipo do evento (JobCompletedEvent ou JobFailedEvent)
            event: Dados do evento
            success: Se o job foi bem-sucedido
        """
        import httpx

        try:
            if success:
                # JobCompletedEvent
                event = event  # type: ignore
                emoji = ":white_check_mark:"
                text = f"{emoji} Job completado: *#{event.issue_number}*"
                fields = [
                    {"title": "Repositório", "value": event.repository, "short": True},
                    {"title": "Duração", "value": f"{event.duration_seconds:.2f}s", "short": True},
                    {"title": "Arquivos", "value": str(event.files_modified), "short": True},
                ]
            else:
                # JobFailedEvent
                event = event  # type: ignore
                emoji = ":x:"
                text = f"{emoji} Job falhou: *#{event.issue_number}*"
                fields = [
                    {"title": "Repositório", "value": event.repository, "short": True},
                    {"title": "Erro", "value": event.error_type, "short": True},
                    {"title": "Mensagem", "value": event.error_message, "short": False},
                ]

            payload = {
                "text": text,
                "attachments": [
                    {
                        "color": "#36a64f" if success else "#dc3545",
                        "fields": fields,
                        "ts": int(event.timestamp.timestamp()),
                    }
                ],
            }

            async with httpx.AsyncClient() as client:
                response = await client.post(self.slack_webhook_url, json=payload)
                response.raise_for_status()

            logger.debug(f"Notificação Slack enviada para {event_type}")

        except Exception as e:
            logger.warning(f"Falha ao enviar notificação Slack: {e}")

    async def _send_email_notification(
        self,
        event_type: str,
        event: "JobCompletedEvent | JobFailedEvent",
        success: bool,
    ) -> None:
        """
        Envia notificação por email.

        Args:
            event_type: Tipo do evento (JobCompletedEvent ou JobFailedEvent)
            event: Dados do evento
            success: Se o job foi bem-sucedido
        """
        # TODO: Implementar envio de email
        # Isso requer configuração de SMTP, templates, etc.
        logger.debug(f"Envio de email ainda não implementado para {event_type}")
