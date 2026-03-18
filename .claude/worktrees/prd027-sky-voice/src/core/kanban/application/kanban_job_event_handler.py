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

from core.domain_events.issue_events import IssueReceivedEvent
from core.domain_events.job_events import (
    JobStartedEvent,
    JobCompletedEvent,
    JobFailedEvent,
    PRCreatedEvent,
)
from core.domain_events.trello_events import (
    TrelloWebhookReceivedEvent,
    TrelloCardArchivedEvent,
)
from infra.kanban.adapters.sqlite_kanban_adapter import SQLiteKanbanAdapter

logger = logging.getLogger(__name__)


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

    # DEBUG: Contador de instâncias para detectar múltiplos handlers
    _instance_count = 0

    def __init__(
        self,
        adapter: SQLiteKanbanAdapter,
        event_bus: "EventBus",
        board_id: str = "board-1",
    ):
        """
        Inicializa o handler.

        Args:
            adapter: Adapter do kanban.db
            event_bus: Event bus para registrar listeners
            board_id: ID do board Kanban (default: "board-1" para compatibilidade)

        NOTA: O default "board-1" é apenas para compatibilidade com código
        legado. Novo código deve SEMPRE fornecer board_id explicitamente.
        """
        # DEBUG: Incrementa contador de instâncias
        KanbanJobEventHandler._instance_count += 1
        logger.warning(f"⚠️ KanbanJobEventHandler #{KanbanJobEventHandler._instance_count} criado")

        self.adapter = adapter
        self.event_bus = event_bus
        self.board_id = board_id
        self._subscription_ids: list[str] = []

    async def handle_job_started(self, event: JobStartedEvent) -> None:
        """
        Handle JobStartedEvent - Cria ou atualiza card como "vivo".

        Args:
            event: JobStartedEvent com dados do job iniciado
        """
        try:
            # Busca lista destino baseado no agent_type
            from core.kanban.domain.database import get_agent_type_to_list_mapping

            agent_type_mapping = get_agent_type_to_list_mapping()
            list_name = agent_type_mapping.get(event.agent_type, "Issues")
            list_result = self.adapter.list_lists(self.board_id)

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
                logger.warning(f"⚠️ [LIST-NOT-FOUND] Lista '{list_name}' não encontrada, criando...")
                # Cria lista se não existe
                from core.kanban.domain.database import KanbanList
                import time
                target_list = KanbanList(
                    id=f"list-{int(time.time())}",
                    board_id=self.board_id,
                    name=list_name,
                    position=0,
                )
                logger.debug(f"📝 Criando lista: {target_list.id} - {target_list.name}")
                self.adapter.create_list(target_list)
                logger.info(f"✅ [LIST-CREATED] Lista criada: {target_list.id}")

            # Busca card existente por issue_number
            logger.debug(f"[SEARCH] Buscando card com issue_number={event.issue_number}")
            cards_result = self.adapter.list_cards(list_id=target_list.id)
            existing_card = None
            if cards_result.is_ok:
                logger.debug(f"[SEARCH] cards_result.ok=True, encontrados {len(cards_result.value)} cards")
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
        Handle JobCompletedEvent - Finaliza card "vivo" e move para "Em Revisão".

        PRD026 RF-010: Mover para "Em Revisão" quando job completa.

        Args:
            event: JobCompletedEvent com dados do job completado
        """
        try:
            # Busca card por issue_number
            cards_result = self.adapter.list_cards()
            if cards_result.is_err:
                return

            for card in cards_result.value:
                if card.issue_number == event.issue_number and card.being_processed:
                    # PRD026 RF-010: Mover para "Em Revisão"
                    list_result = self.adapter.list_lists("board-1")
                    if list_result.is_ok:
                        # Encontra lista "Em Revisão"
                        review_list = None
                        for lst in list_result.value:
                            if lst.name == "Em Revisão":
                                review_list = lst
                                break

                        if review_list:
                            # Finaliza card E move para "Em Revisão"
                            self.adapter.update_card(
                                card.id,
                                being_processed=False,
                                processing_job_id=None,
                                list_id=review_list.id,
                            )
                            logger.info(
                                f"Card movido para 'Em Revisão': {card.id} | job={event.job_id}"
                            )
                        else:
                            # Lista não encontrada, apenas finaliza
                            self.adapter.update_card(
                                card.id,
                                being_processed=False,
                                processing_job_id=None,
                            )
                            logger.warning(
                                f"Lista 'Em Revisão' não encontrada, card apenas finalizado: {card.id}"
                            )
                    break

        except Exception as e:
            logger.error(f"Erro ao handle_job_completed: {e}")

    async def handle_job_failed(self, event: JobFailedEvent) -> None:
        """
        Handle JobFailedEvent - Finaliza card "vivo" e move para "Issues" com label erro.

        PRD026 RF-012: Mover para "Issues" com label "❌ Erro".

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
                    # PRD026 RF-012: Mover para "Issues" com label erro
                    list_result = self.adapter.list_lists("board-1")
                    if list_result.is_ok:
                        # Encontra lista "Issues"
                        issues_list = None
                        for lst in list_result.value:
                            if lst.name == "Issues":
                                issues_list = lst
                                break

                        if issues_list:
                            # Adiciona label de erro
                            error_label = "❌ Erro"
                            updated_labels = list(card.labels or [])
                            if error_label not in updated_labels:
                                updated_labels.append(error_label)

                            # Finaliza card E move para "Issues"
                            self.adapter.update_card(
                                card.id,
                                being_processed=False,
                                processing_job_id=None,
                                list_id=issues_list.id,
                                labels=updated_labels,
                            )
                            logger.info(
                                f"Card movido para 'Issues' com erro: {card.id} | job={event.job_id}"
                            )
                        else:
                            # Lista não encontrada, apenas finaliza
                            self.adapter.update_card(
                                card.id,
                                being_processed=False,
                                processing_job_id=None,
                            )
                            logger.warning(
                                f"Lista 'Issues' não encontrada, card apenas finalizado: {card.id}"
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

    async def start(self) -> None:
        """
        Inicia o handler, inscrevendo-se nos eventos de interesse.

        PRD026 RF-001: Deve registrar listeners no EventBus durante startup.

        Registra inscrições para:
        - IssueReceivedEvent: criar cards quando webhook chega
        - JobStartedEvent: marcar cards como "vivos"
        - JobCompletedEvent: finalizar cards "vivos"
        - JobFailedEvent: finalizar cards "vivos" com erro
        - PRCreatedEvent: guardar pr_url no card
        """
        # Subscribe to IssueReceivedEvent (PRD026 Fase 3)
        sub_id = await self.event_bus.subscribe(
            IssueReceivedEvent,
            self._on_issue_received,
        )
        self._subscription_ids.append(sub_id)

        # Subscribe to JobStartedEvent (PRD026 Fase 4)
        sub_id = await self.event_bus.subscribe(
            JobStartedEvent,
            self.handle_job_started,
        )
        self._subscription_ids.append(sub_id)

        # Subscribe to JobCompletedEvent (PRD026 Fase 5)
        sub_id = await self.event_bus.subscribe(
            JobCompletedEvent,
            self.handle_job_completed,
        )
        self._subscription_ids.append(sub_id)

        # Subscribe to JobFailedEvent (PRD026 Fase 5)
        sub_id = await self.event_bus.subscribe(
            JobFailedEvent,
            self.handle_job_failed,
        )
        self._subscription_ids.append(sub_id)

        # Subscribe to TrelloCardArchivedEvent (PRD026 RF-0XX)
        sub_id = await self.event_bus.subscribe(
            TrelloCardArchivedEvent,
            self.handle_card_archived,
        )
        self._subscription_ids.append(sub_id)

        # Subscribe to PRCreatedEvent (PRD026 Fase 5)
        sub_id = await self.event_bus.subscribe(
            PRCreatedEvent,
            self._on_pr_created,
        )
        self._subscription_ids.append(sub_id)

        # Subscribe to TrelloWebhookReceivedEvent (PRD026 RF-013)
        sub_id = await self.event_bus.subscribe(
            TrelloWebhookReceivedEvent,
            self._on_trello_webhook_received,
        )
        self._subscription_ids.append(sub_id)

        logger.info(
            f"KanbanJobEventHandler iniciado com {len(self._subscription_ids)} inscrições"
        )

    async def stop(self) -> None:
        """
        Para o handler, cancelando todas as inscrições.

        Deve ser chamado durante o shutdown da aplicação.
        """
        for sub_id in self._subscription_ids:
            try:
                self.event_bus.unsubscribe(sub_id)
            except Exception as e:
                logger.warning(f"Erro ao cancelar inscrição {sub_id}: {e}")

        self._subscription_ids.clear()
        logger.info("KanbanJobEventHandler parado")

    async def _on_issue_received(self, event: IssueReceivedEvent) -> None:
        """
        Handler para IssueReceivedEvent.

        PRD026 RF-006: Cria card na lista "Issues" quando webhook chega.

        Args:
            event: IssueReceivedEvent com dados da issue
        """
        if not self.adapter:
            logger.debug("Adapter não configurado, ignorando IssueReceivedEvent")
            return

        try:
            # Só cria card para issues abertas
            if event.action != "opened":
                logger.debug(
                    f"Issue #{event.issue_number} action={event.action}, "
                    "não é 'opened', ignorando"
                )
                return

            logger.info(
                f"Criando card Kanban para issue #{event.issue_number} "
                f"em {event.repository}"
            )

            # Busca lista "Issues"
            list_result = self.adapter.list_lists("board-1")
            if list_result.is_err:
                logger.error(f"Erro ao buscar listas: {list_result.error}")
                return

            # Encontra lista "Issues"
            issues_list = None
            for lst in list_result.value:
                if lst.name == "Issues":
                    issues_list = lst
                    break

            if not issues_list:
                logger.warning("Lista 'Issues' não encontrada, criando...")
                from core.kanban.domain.database import KanbanList
                import time
                issues_list = KanbanList(
                    id=f"list-issues-{int(time.time())}",
                    board_id="board-1",
                    name="Issues",
                    position=0,
                )
                self.adapter.create_list(issues_list)

            # Verifica se card já existe
            cards_result = self.adapter.list_cards(list_id=issues_list.id)
            existing_card = None
            if cards_result.is_ok:
                for card in cards_result.value:
                    if card.issue_number == event.issue_number:
                        existing_card = card
                        break

            if existing_card:
                logger.info(
                    f"Card já existe para issue #{event.issue_number}: {existing_card.id}"
                )
                return

            # Cria novo card
            from core.kanban.domain.database import KanbanCard
            import time
            issue_url = f"https://github.com/{event.repository}/issues/{event.issue_number}"
            new_card = KanbanCard(
                id=f"card-issue-{event.issue_number}",
                list_id=issues_list.id,
                title=event.title or f"Issue #{event.issue_number}",
                issue_number=event.issue_number,
                issue_url=issue_url,
                position=0,  # Cards novos ficam no topo
                being_processed=False,
            )
            self.adapter.create_card(new_card)
            logger.info(
                f"Card criado para issue #{event.issue_number}: {new_card.id}"
            )

        except Exception as e:
            logger.error(f"Erro ao processar IssueReceivedEvent: {e}")

    async def _on_pr_created(self, event: PRCreatedEvent) -> None:
        """
        Handler para PRCreatedEvent.

        PRD026 RF-011: Guarda pr_url no card.

        Args:
            event: PRCreatedEvent com dados do PR
        """
        if not self.adapter:
            logger.debug("Adapter não configurado, ignorando PRCreatedEvent")
            return

        try:
            logger.info(
                f"PR #{event.pr_number} criado, atualizando card Kanban "
                f"(issue #{event.issue_number})"
            )

            # Busca card por issue_number em todas as listas
            cards_result = self.adapter.list_cards()
            if cards_result.is_err:
                return

            target_card = None
            for card in cards_result.value:
                if card.issue_number == event.issue_number:
                    target_card = card
                    break

            if not target_card:
                logger.debug(
                    f"Card não encontrado para issue #{event.issue_number}"
                )
                return

            # Atualiza card com pr_url
            self.adapter.update_card(
                target_card.id,
                pr_url=event.pr_url,
            )
            logger.info(
                f"Card {target_card.id} atualizado com PR #{event.pr_number}"
            )

        except Exception as e:
            logger.error(f"Erro ao processar PRCreatedEvent: {e}")

    async def handle_card_archived(self, event: TrelloCardArchivedEvent) -> None:
        """
        Handler para TrelloCardArchivedEvent.

        Deleta o card do kanban.db quando card é arquivado/deletado no Trello.

        Args:
            event: TrelloCardArchivedEvent com dados do card

        PRD026 RF-0XX: Implementar tratamento de arquivamento.
        """
        try:
            if not self.adapter:
                logger.debug("Adapter não configurado, ignorando TrelloCardArchivedEvent")
                return

            logger.warning(
                f"🗑️ [DELETE-START] Card arquivado/deletado: {event.card_name} "
                f"(trello_card_id: {event.card_id})"
            )

            # Buscar card por trello_card_id no kanban.db
            cards_result = self.adapter.list_cards()
            if cards_result.is_err:
                logger.error(f"Erro ao listar cards: {cards_result.error}")
                return

            # DEBUG: Listar TODOS os cards encontrados antes de buscar
            all_cards = cards_result.value
            logger.info(f"📋 [ALL-CARDS] Total de cards no kanban.db: {len(all_cards)}")
            for idx, c in enumerate(all_cards):
                logger.info(f"   [{idx}] id={c.id}, trello_card_id={c.trello_card_id}, title={c.title[:30]}, list_id={c.list_id}")

            found_card = None
            for card in cards_result.value:
                if card.trello_card_id == event.card_id:
                    found_card = card
                    break

            if not found_card:
                logger.warning(
                    f"Card com trello_card_id={event.card_id} não encontrado no kanban.db"
                )
                return

            # Deletar card
            delete_result = self.adapter.delete_card(found_card.id)
            if delete_result.is_ok:
                logger.info(
                    f"✅ Card {found_card.id} deletado (arquivado/deletado)"
                )

                # Emitir evento card_deleted para SSE (atualização em tempo real)
                from core.kanban.application.kanban_event_bus import KanbanEventBus

                event_bus = KanbanEventBus.get_instance()
                await event_bus.publish(
                    event_type="card_deleted",
                    data={"id": found_card.id, "trello_card_id": event.card_id},
                    workspace_id=self.board_id
                )
                logger.info(f"✅ Evento card_deleted emitido para SSE")
            else:
                logger.error(f"❌ Erro ao deletar card {found_card.id}: {delete_result.error}")

        except Exception as e:
            logger.error(f"Erro ao processar TrelloCardArchivedEvent: {e}")

    async def _on_trello_webhook_received(self, event: TrelloWebhookReceivedEvent) -> None:
        """
        Handler para TrelloWebhookReceivedEvent.

        PRD026 RF-013: Quando card é movido no Trello, atualiza card no kanban.db.

        Fluxo:
        1. Recebe evento com card_id do Trello e lista de destino
        2. Busca card no kanban.db por trello_card_id
        3. Muda list_id baseado no mapeamento do domínio (get_trello_to_kanban_mapping)
        4. SSE emite card_updated

        Args:
            event: TrelloWebhookReceivedEvent com dados do movimento
        """
        if not self.adapter:
            logger.debug("Adapter não configurado, ignorando TrelloWebhookReceivedEvent")
            return

        try:
            logger.info(
                f"TrelloWebhookReceivedEvent: card '{event.card_name}' "
                f"movido para '{event.list_after_name}'"
            )

            # Mapeia nome da lista Trello para nome da lista Kanban (usa domínio)
            from core.kanban.domain.database import get_kanban_lists_config

            trello_mapping = get_kanban_lists_config().get_trello_to_kanban_mapping()

            if event.list_after_name not in trello_mapping:
                logger.warning(
                    f"Lista Trello '{event.list_after_name}' não está no mapeamento! "
                    f"Isso indica problema de configuração do Trello. "
                    f"Listas conhecidas: {list(trello_mapping.keys())}"
                )
                return

            kanban_list_name = trello_mapping[event.list_after_name]

            logger.info(
                f"  Mapeamento: Trello '{event.list_after_name}' → Kanban '{kanban_list_name}'"
            )

            # Busca card no kanban.db por trello_card_id
            cards_result = self.adapter.list_cards()
            if cards_result.is_err:
                logger.error(f"Erro ao listar cards: {cards_result.error}")
                return

            target_card = None
            for card in cards_result.value:
                if card.trello_card_id == event.card_id:
                    target_card = card
                    break

            if not target_card:
                # Card não existe no kanban.db - pode ser um card criado diretamente no Trello
                logger.info(
                    f"Card Trello {event.card_id} não encontrado no kanban.db "
                    f"(card pode ter sido criado diretamente no Trello)"
                )
                return

            # Busca lista destino no kanban.db
            list_result = self.adapter.list_lists("board-1")
            if list_result.is_err:
                logger.error(f"Erro ao buscar listas: {list_result.error}")
                return

            # Encontra lista destino por nome
            target_list = None
            for lst in list_result.value:
                if lst.name == kanban_list_name:
                    target_list = lst
                    break

            if not target_list:
                logger.warning(
                    f"Lista Kanban '{kanban_list_name}' não encontrada, "
                    f"card permanece em '{target_card.list_id}'"
                )
                return

            # Se card já está na lista de destino, não faz nada
            if target_card.list_id == target_list.id:
                logger.info(
                    f"Card {target_card.id} já está na lista '{kanban_list_name}'"
                )
                return

            # Move card para nova lista
            self.adapter.update_card(
                target_card.id,
                list_id=target_list.id,
            )

            logger.info(
                f"✅ Card {target_card.id} movido: "
                f"'{event.list_before_name}' → '{kanban_list_name}' "
                f"(trello_card_id={event.card_id})"
            )

            # TODO: Emitir SSE para WebUI (quando SSE implementado)

        except Exception as e:
            logger.error(f"Erro ao processar TrelloWebhookReceivedEvent: {e}")
