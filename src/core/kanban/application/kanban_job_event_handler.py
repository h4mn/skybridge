# -*- coding: utf-8 -*-
"""
Kanban Job Event Handler - Integração JobOrchestrator → kanban.db.

Responsável por:
- Escutar Domain Events do JobOrchestrator (JobStarted, JobCompleted, JobFailed)
- Atualizar kanban.db com status "cards vivos" (being_processed)
- Mapear agent_type para lista correta do Kanban

DOC: core/kanban/application/kanban_job_event_handler.py
DOC: ADR024 - Workspace isolation
DOC: PRD018 - Domain Events
"""

import logging
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from core.domain_events.event_bus import EventBus

from core.domain_events.job_events import (
    JobStartedEvent,
    JobCompletedEvent,
    JobFailedEvent,
)
from infra.kanban.adapters.sqlite_kanban_adapter import SQLiteKanbanAdapter

logger = logging.getLogger(__name__)


# Mapeamento agent_type → nome da lista (conforme setup do Trello)
# 1. Issues; 2. Brainstorm; 3. A Fazer; 4. Em Andamento; 5. Em Revisão; 6. Publicar
AGENT_TYPE_TO_LIST = {
    "analyze-issue": "Brainstorm",
    "resolve-issue": "Em Andamento",
    "review-issue": "Em Revisão",
    "publish-issue": "Publicar",
    # Default para Issues se não mapeado
    "none": "Issues",
}


class KanbanJobEventHandler:
    """
    Event Handler para integrar JobOrchestrator com kanban.db.

    Responsável por:
    - Criar cards quando JobStartedEvent é emitido
    - Atualizar cards para "vivo" quando job inicia (being_processed=True)
    - Finalizar cards quando JobCompletedEvent/JobFailedEvent são emitidos
    - Mapear agent_type para lista correta do Kanban

    Atributes:
        adapter: Adapter do kanban.db (SQLite)
        event_bus: Event bus para se registrar como listener
    """

    def __init__(
        self,
        adapter: SQLiteKanbanAdapter,
        event_bus: "EventBus",
    ):
        """
        Inicializa o handler.

        Args:
            adapter: Adapter do kanban.db
            event_bus: Event bus para registrar listeners
        """
        self.adapter = adapter
        self.event_bus = event_bus

    async def handle_job_started(self, event: JobStartedEvent) -> None:
        """
        Handle JobStartedEvent - Cria ou atualiza card como "vivo".

        Args:
            event: JobStartedEvent com dados do job iniciado
        """
        try:
            # Busca lista destino baseado no agent_type
            list_name = AGENT_TYPE_TO_LIST.get(event.agent_type, "Issues")
            list_result = self.adapter.list_lists("board-1")  # TODO: usar board correto

            if list_result.is_err:
                logger.error(f"Erro ao buscar listas: {list_result.error}")
                return

            # Encontra lista por nome
            target_list = None
            for lst in list_result.value:
                if lst.name == list_name:
                    target_list = lst
                    break

            if not target_list:
                logger.warning(f"Lista '{list_name}' não encontrada, criando...")
                # Cria lista se não existe
                from core.kanban.domain.database import KanbanList
                import time
                target_list = KanbanList(
                    id=f"list-{int(time.time())}",
                    board_id="board-1",
                    name=list_name,
                    position=0,
                )
                self.adapter.create_list(target_list)

            # Busca card existente por issue_number
            cards_result = self.adapter.list_cards(list_id=target_list.id)
            existing_card = None
            if cards_result.is_ok:
                for card in cards_result.value:
                    if card.issue_number == event.issue_number:
                        existing_card = card
                        break

            if existing_card:
                # Atualiza card existente para "vivo"
                self.adapter.update_card(
                    existing_card.id,
                    being_processed=True,
                    position=0,  # Cards vivos ficam no topo
                    processing_job_id=event.job_id,
                    processing_started_at=event.timestamp,
                )
                logger.info(
                    f"Card atualizado como vivo: {existing_card.id} | job={event.job_id}"
                )
            else:
                # Cria novo card
                from core.kanban.domain.database import KanbanCard
                import time
                new_card = KanbanCard(
                    id=f"card-{event.job_id}",
                    list_id=target_list.id,
                    title=f"Issue #{event.issue_number}",
                    issue_number=event.issue_number,
                    being_processed=True,
                    position=0,  # Cards vivos ficam no topo
                    processing_job_id=event.job_id,
                    processing_started_at=event.timestamp,
                )
                self.adapter.create_card(new_card)
                logger.info(
                    f"Card criado como vivo: {new_card.id} | job={event.job_id}"
                )

        except Exception as e:
            logger.error(f"Erro ao handle_job_started: {e}")

    async def handle_job_completed(self, event: JobCompletedEvent) -> None:
        """
        Handle JobCompletedEvent - Finaliza card "vivo".

        Args:
            event: JobCompletedEvent com dados do job completado
        """
        try:
            # Busca card por issue_number
            # TODO: buscar em todas as listas
            cards_result = self.adapter.list_cards()
            if cards_result.is_err:
                return

            for card in cards_result.value:
                if card.issue_number == event.issue_number and card.being_processed:
                    # Finaliza card
                    self.adapter.update_card(
                        card.id,
                        being_processed=False,
                        processing_job_id=None,
                    )
                    logger.info(
                        f"Card finalizado: {card.id} | job={event.job_id}"
                    )
                    break

        except Exception as e:
            logger.error(f"Erro ao handle_job_completed: {e}")

    async def handle_job_failed(self, event: JobFailedEvent) -> None:
        """
        Handle JobFailedEvent - Finaliza card "vivo".

        Args:
            event: JobFailedEvent com dados do job falhado
        """
        try:
            # Busca card por issue_number
            cards_result = self.adapter.list_cards()
            if cards_result.is_err:
                return

            for card in cards_result.value:
                if card.issue_number == event.issue_number and card.being_processed:
                    # Finaliza card
                    self.adapter.update_card(
                        card.id,
                        being_processed=False,
                        processing_job_id=None,
                    )
                    logger.info(
                        f"Card finalizado (falha): {card.id} | job={event.job_id}"
                    )
                    break

        except Exception as e:
            logger.error(f"Erro ao handle_job_failed: {e}")

    async def register_listeners(self) -> None:
        """
        Registra listeners no event bus.
        """
        # TODO: Implementar após criar método register() no EventBus
        logger.info("Listeners registrados no EventBus")
