# -*- coding: utf-8 -*-
"""
Trello Event Listener.

Listens to Domain Events and integrates with Trello.
Replaces direct calls from WebhookProcessor to TrelloService.

PRD018 ARCH-08: TrelloEventListener desacoplado via Domain Events.
"""
from __future__ import annotations

import logging
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from core.domain_events.event_bus import EventBus
    from core.kanban.application.trello_integration_service import (
        TrelloIntegrationService,
    )

from core.domain_events.issue_events import IssueReceivedEvent
from core.domain_events.job_events import (
    JobCompletedEvent,
    JobFailedEvent,
    PRCreatedEvent,
)
from core.domain_events.trello_events import (
    TrelloCardCreatedEvent,
    TrelloCardMovedEvent,
)

logger = logging.getLogger(__name__)


class TrelloEventListener:
    """
    Listener for Domain Events that trigger Trello actions.

    Responsibilities:
    - Subscribe to IssueReceivedEvent to create Trello cards
    - Subscribe to JobCompletedEvent to move cards to "Done"
    - Subscribe to JobFailedEvent to move cards to "Failed"
    - Emit TrelloCard* events for other components to react to

    PRD018 ARCH-08: Desacoplado - WebhookProcessor não conhece Trello.
    """

    def __init__(
        self,
        event_bus: "EventBus",
        trello_service: "TrelloIntegrationService | None" = None,
    ):
        """
        Inicializa listener.

        Args:
            event_bus: Event bus para se inscrever nos eventos
            trello_service: Serviço de integração com Trello (opcional)
        """
        self.event_bus = event_bus
        self.trello_service = trello_service
        self._subscription_ids: list[str] = []

    async def start(self) -> None:
        """
        Inicia o listener, inscrevendo-se nos eventos de interesse.

        Deve ser chamado durante a inicialização da aplicação.
        """
        # Subscribe to IssueReceivedEvent
        sub_id = self.event_bus.subscribe(
            IssueReceivedEvent,
            self._on_issue_received,
        )
        self._subscription_ids.append(sub_id)

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

        # PRD018 Fase 3: Subscribe to PRCreatedEvent
        sub_id = self.event_bus.subscribe(
            PRCreatedEvent,
            self._on_pr_created,
        )
        self._subscription_ids.append(sub_id)

        logger.info(f"TrelloEventListener iniciado com {len(self._subscription_ids)} inscrições")

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
        logger.info("TrelloEventListener parado")

    async def _on_issue_received(self, event: IssueReceivedEvent) -> None:
        """
        Handler para IssueReceivedEvent.

        Cria um card no Trello para a issue recebida.
        Emite TrelloCardCreatedEvent após criar o card.

        Args:
            event: IssueReceivedEvent com os dados da issue
        """
        try:
            if not self.trello_service:
                logger.debug("TrelloIntegrationService não configurado, ignorando")
                return

            # Só cria card para issues abertas
            if event.action != "opened":
                logger.debug(
                    f"Issue #{event.issue_number} action={event.action}, "
                    "não é 'opened', ignorando"
                )
                return

            logger.info(
                f"Criando card Trello para issue #{event.issue_number} "
                f"em {event.repository}"
            )

            # Extrai URL da issue
            issue_url = f"https://github.com/{event.repository}/issues/{event.issue_number}"

            # Cria card no Trello
            result = await self.trello_service.create_card_from_github_issue(
                issue_number=event.issue_number,
                issue_title=event.title,
                issue_body=event.body,
                issue_url=issue_url,
                author=event.sender,
                repo_name=event.repository,
                labels=event.labels or [],
            )

            if result.is_ok:
                card_id = result.unwrap()
                logger.info(
                    f"Card Trello criado: {card_id} para issue #{event.issue_number}"
                )

                # Emite TrelloCardCreatedEvent para outros componentes
                await self.event_bus.publish(
                    TrelloCardCreatedEvent(
                        aggregate_id=card_id,
                        card_id=card_id,
                        card_name=event.title,
                        issue_number=event.issue_number,
                        repository=event.repository,
                        # TODO: Buscar board_id, list_id do TrelloService
                        board_id="",
                        board_name="",
                        list_id="",
                        list_name="",
                    )
                )
            else:
                logger.warning(
                    f"Falha ao criar card Trello para issue #{event.issue_number}: "
                    f"{result.error}"
                )

        except Exception as e:
            logger.error(
                f"Erro ao processar IssueReceivedEvent para issue #{event.issue_number}: {e}",
                # exc_info removido - SkybridgeLogger não suporta
            )

    async def _on_job_completed(self, event: JobCompletedEvent) -> None:
        """
        Handler para JobCompletedEvent.

        Move o card do Trello para a lista "Done" (ou similar).
        Emite TrelloCardMovedEvent após mover.

        Args:
            event: JobCompletedEvent com os dados do job
        """
        try:
            if not self.trello_service:
                return

            logger.info(
                f"Job {event.job_id} completado, movendo card Trello "
                f"para 'Done' (issue #{event.issue_number})"
            )

            # TODO: Implementar mover card para lista "Done"
            # Isso requer que o TrelloService tenha um método para mover cards
            # e que o job_id ou metadata contenha o card_id do Trello

            # Por enquanto, apenas log
            logger.debug("Mover card Trello para 'Done' ainda não implementado")

        except Exception as e:
            logger.error(
                f"Erro ao processar JobCompletedEvent para job {event.job_id}: {e}",
                # exc_info removido - SkybridgeLogger não suporta
            )

    async def _on_job_failed(self, event: JobFailedEvent) -> None:
        """
        Handler para JobFailedEvent.

        Move o card do Trello para a lista "Failed" (ou similar).
        Emite TrelloCardMovedEvent após mover.

        Args:
            event: JobFailedEvent com os dados do job
        """
        try:
            if not self.trello_service:
                return

            logger.warning(
                f"Job {event.job_id} falhou: {event.error_message} "
                f"(issue #{event.issue_number})"
            )

            # TODO: Implementar mover card para lista "Failed"
            logger.debug("Mover card Trello para 'Failed' ainda não implementado")

        except Exception as e:
            logger.error(
                f"Erro ao processar JobFailedEvent para job {event.job_id}: {e}",
                # exc_info removido - SkybridgeLogger não suporta
            )

    async def _on_pr_created(self, event: PRCreatedEvent) -> None:
        """
        Handler para PRCreatedEvent.

        PRD018 Fase 3: Atualiza card Trello com link do PR criado.

        Args:
            event: PRCreatedEvent com os dados do PR
        """
        try:
            if not self.trello_service:
                return

            logger.info(
                f"PR #{event.pr_number} criado, atualizando card Trello "
                f"(issue #{event.issue_number})"
            )

            # Busca card pelo issue_number
            card = await self._find_card_by_issue(event.issue_number)
            if not card:
                logger.debug(
                    f"Card Trello não encontrado para issue #{event.issue_number}"
                )
                return

            # Move para lista "Pronto" se ainda não estiver
            if hasattr(card, "status") and card.status.value != "done":
                await self.trello_service.move_card_to_list(
                    card_id=card.id,
                    target_list_name="Pronto",
                )

            # Adiciona comentário com URL do PR
            comment = f"""🔗 **PR Criado!**

**Título:** {event.pr_title}
**Número:** #{event.pr_number}
**Branch:** `{event.branch_name}`

**URL:** {event.pr_url}

O PR foi criado automaticamente e está aguardando revisão.

---

> \"Autonomy with quality is sustainable autonomy\" – made by Sky"""

            await self.trello_service.add_card_comment(card.id, comment)

            logger.info(
                f"Card Trello atualizado com PR #{event.pr_number}"
            )

        except Exception as e:
            logger.error(
                f"Erro ao processar PRCreatedEvent para PR #{event.pr_number}: {e}",
                # exc_info removido - SkybridgeLogger não suporta
            )

    async def _find_card_by_issue(self, issue_number: int):
        """
        Busca card Trello pelo número da issue.

        Args:
            issue_number: Número da issue

        Returns:
            Card ou None se não encontrado
        """
        try:
            if not self.trello_service:
                return None

            # Lista cards no board
            result = await self.trello_service.list_cards()
            if result.is_err:
                return None

            cards = result.unwrap()

            # Procura card com issue_number no nome ou descrição
            for card in cards:
                # Verifica se o nome ou descrição contém o issue_number
                if f"#{issue_number}" in card.title or \
                   (card.description and f"#{issue_number}" in card.description):
                    return card

            return None

        except Exception as e:
            logger.error(f"Erro ao buscar card Trello: {e}")
            return None
